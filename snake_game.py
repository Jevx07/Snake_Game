import pygame
import random
import sys
import json
import os
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
import time

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Game Constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
GRID_SIZE = 20
GRID_WIDTH = WINDOW_WIDTH // GRID_SIZE
GRID_HEIGHT = WINDOW_HEIGHT // GRID_SIZE

# Colors
class Colors:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREEN = (0, 255, 0)
    DARK_GREEN = (0, 180, 0)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    CYAN = (0, 255, 255)
    YELLOW = (255, 255, 0)
    PURPLE = (255, 0, 255)
    ORANGE = (255, 165, 0)
    PINK = (255, 192, 203)
    GRAY = (128, 128, 128)
    DARK_GRAY = (64, 64, 64)
    LIGHT_GRAY = (192, 192, 192)
    NEON_GREEN = (57, 255, 20)
    NEON_BLUE = (77, 77, 255)

class GameState(Enum):
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    HIGH_SCORES = "high_scores"
    SETTINGS = "settings"

class Difficulty(Enum):
    EASY = {"speed": 8, "multiplier": 1.0, "powerups": True}
    MEDIUM = {"speed": 12, "multiplier": 1.5, "powerups": True}
    HARD = {"speed": 18, "multiplier": 2.0, "powerups": False}

class PowerUpType(Enum):
    SPEED_BOOST = "speed_boost"
    SLOW_DOWN = "slow_down"
    DOUBLE_POINTS = "double_points"
    SHRINK = "shrink"
    WALL_PHASE = "wall_phase"
    MULTIPLIER = "multiplier"

@dataclass
class PowerUp:
    type: PowerUpType
    position: Tuple[int, int]
    duration: float
    spawn_time: float
    color: Tuple[int, int, int]

class Particle:
    def __init__(self, x, y, color, velocity, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.velocity = velocity
        self.lifetime = lifetime
        self.age = 0
        self.size = random.randint(2, 6)
    
    def update(self, dt):
        self.age += dt
        self.x += self.velocity[0] * dt
        self.y += self.velocity[1] * dt
        return self.age < self.lifetime
    
    def draw(self, screen):
        alpha = max(0, 255 * (1 - self.age / self.lifetime))
        size = max(1, int(self.size * (1 - self.age / self.lifetime)))
        color = (*self.color, int(alpha))
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), size)

class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.music_volume = 0.3
        self.sfx_volume = 0.5
        self.load_sounds()
    
    def load_sounds(self):
        # Create simple sound effects programmatically
        try:
            # Generate eat sound
            eat_sound = pygame.sndarray.make_sound(
                self.generate_tone(440, 0.1, 44100, 'sine')
            )
            self.sounds['eat'] = eat_sound
            
            # Generate powerup sound
            powerup_sound = pygame.sndarray.make_sound(
                self.generate_tone(660, 0.2, 44100, 'square')
            )
            self.sounds['powerup'] = powerup_sound
            
            # Generate game over sound
            gameover_sound = pygame.sndarray.make_sound(
                self.generate_tone(220, 0.5, 44100, 'sawtooth')
            )
            self.sounds['game_over'] = gameover_sound
            
        except:
            # Fallback if sound generation fails
            pass
    
    def generate_tone(self, frequency, duration, sample_rate, wave_type):
        frames = int(duration * sample_rate)
        arr = []
        for i in range(frames):
            time_val = float(i) / sample_rate
            if wave_type == 'sine':
                wave = 4096 * math.sin(frequency * 2 * math.pi * time_val)
            elif wave_type == 'square':
                wave = 4096 * (1 if math.sin(frequency * 2 * math.pi * time_val) > 0 else -1)
            else:  # sawtooth
                wave = 4096 * (2 * (time_val * frequency - math.floor(time_val * frequency + 0.5)))
            arr.append([int(wave), int(wave)])
        return arr
    
    def play_sound(self, sound_name):
        if sound_name in self.sounds:
            sound = self.sounds[sound_name]
            sound.set_volume(self.sfx_volume)
            sound.play()

class Snake:
    def __init__(self, player_id: int, color: Tuple[int, int, int], controls: Dict, start_pos: Tuple[int, int]):
        self.player_id = player_id
        self.color = color
        self.controls = controls
        self.positions = [start_pos]
        self.direction = (1, 0)
        self.grow_pending = 0
        self.score = 0
        self.alive = True
        self.power_ups = {}
        self.invulnerable_time = 0
        self.speed_multiplier = 1.0
        self.wall_phase = False
        self.last_move_time = 0
        self.trail_particles = []
    
    def update(self, dt, current_time):
        # Update power-ups
        expired_powerups = []
        for powerup_type, end_time in self.power_ups.items():
            if current_time > end_time:
                expired_powerups.append(powerup_type)
        
        for powerup_type in expired_powerups:
            self.remove_power_up(powerup_type)
        
        # Update invulnerability
        if self.invulnerable_time > 0:
            self.invulnerable_time -= dt
        
        # Add trail particles
        if len(self.positions) > 0:
            head_x, head_y = self.positions[0]
            if random.random() < 0.3:
                particle = Particle(
                    head_x * GRID_SIZE + GRID_SIZE // 2,
                    head_y * GRID_SIZE + GRID_SIZE // 2,
                    self.color,
                    (random.randint(-20, 20), random.randint(-20, 20)),
                    0.5
                )
                self.trail_particles.append(particle)
        
        # Update trail particles
        self.trail_particles = [p for p in self.trail_particles if p.update(dt)]
    
    def move(self):
        if not self.alive:
            return True
        
        head_x, head_y = self.positions[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])
        
        # Wall collision (unless wall phase is active)
        if not self.wall_phase:
            if (new_head[0] < 0 or new_head[0] >= GRID_WIDTH or 
                new_head[1] < 0 or new_head[1] >= GRID_HEIGHT):
                self.alive = False
                return False
        else:
            # Wrap around if wall phase is active
            new_head = (new_head[0] % GRID_WIDTH, new_head[1] % GRID_HEIGHT)
        
        # Self collision (if not invulnerable)
        if self.invulnerable_time <= 0 and new_head in self.positions:
            self.alive = False
            return False
        
        self.positions.insert(0, new_head)
        
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.positions.pop()
        
        return True
    
    def change_direction(self, direction):
        # Prevent reverse direction
        if (direction[0] * -1, direction[1] * -1) != self.direction:
            self.direction = direction
    
    def grow(self, amount=1):
        self.grow_pending += amount
    
    def add_power_up(self, powerup_type: PowerUpType, duration: float, current_time: float):
        self.power_ups[powerup_type] = current_time + duration
        
        if powerup_type == PowerUpType.SPEED_BOOST:
            self.speed_multiplier = 2.0
        elif powerup_type == PowerUpType.SLOW_DOWN:
            self.speed_multiplier = 0.5
        elif powerup_type == PowerUpType.SHRINK:
            if len(self.positions) > 3:
                self.positions = self.positions[:len(self.positions)//2]
        elif powerup_type == PowerUpType.WALL_PHASE:
            self.wall_phase = True
            self.invulnerable_time = 2.0
    
    def remove_power_up(self, powerup_type: PowerUpType):
        if powerup_type in self.power_ups:
            del self.power_ups[powerup_type]
            
            if powerup_type == PowerUpType.SPEED_BOOST:
                self.speed_multiplier = 1.0
            elif powerup_type == PowerUpType.SLOW_DOWN:
                self.speed_multiplier = 1.0
            elif powerup_type == PowerUpType.WALL_PHASE:
                self.wall_phase = False
    
    def draw(self, screen):
        # Draw trail particles
        for particle in self.trail_particles:
            particle.draw(screen)
        
        # Draw snake body
        for i, pos in enumerate(self.positions):
            x, y = pos[0] * GRID_SIZE, pos[1] * GRID_SIZE
            
            # Head is different from body
            if i == 0:
                color = self.color if self.alive else Colors.GRAY
                # Add glow effect for head
                if self.invulnerable_time > 0:
                    glow_color = Colors.WHITE
                    pygame.draw.rect(screen, glow_color, (x-2, y-2, GRID_SIZE+4, GRID_SIZE+4))
                pygame.draw.rect(screen, color, (x, y, GRID_SIZE, GRID_SIZE))
                # Draw eyes
                eye_size = 3
                pygame.draw.circle(screen, Colors.WHITE, (x + 5, y + 5), eye_size)
                pygame.draw.circle(screen, Colors.WHITE, (x + 15, y + 5), eye_size)
                pygame.draw.circle(screen, Colors.BLACK, (x + 5, y + 5), 1)
                pygame.draw.circle(screen, Colors.BLACK, (x + 15, y + 5), 1)
            else:
                # Body segments get progressively darker
                darkness = min(50, i * 2)
                body_color = tuple(max(0, c - darkness) for c in self.color)
                pygame.draw.rect(screen, body_color, (x, y, GRID_SIZE, GRID_SIZE))
            
            # Border
            pygame.draw.rect(screen, Colors.BLACK, (x, y, GRID_SIZE, GRID_SIZE), 1)

class Food:
    def __init__(self):
        self.position = self.generate_position()
        self.value = 10
        self.color = Colors.RED
        self.pulse_time = 0
    
    def generate_position(self):
        return (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
    
    def update(self, dt):
        self.pulse_time += dt * 5
    
    def draw(self, screen):
        x, y = self.position[0] * GRID_SIZE, self.position[1] * GRID_SIZE
        
        # Pulsing effect
        pulse = abs(math.sin(self.pulse_time))
        size_offset = int(3 * pulse)
        
        pygame.draw.rect(screen, self.color, 
                        (x - size_offset, y - size_offset, 
                         GRID_SIZE + 2*size_offset, GRID_SIZE + 2*size_offset))
        pygame.draw.rect(screen, Colors.BLACK, (x, y, GRID_SIZE, GRID_SIZE), 1)

class PowerUpManager:
    def __init__(self):
        self.active_powerups = []
        self.spawn_timer = 0
        self.spawn_interval = 10.0  # seconds
    
    def update(self, dt, current_time):
        self.spawn_timer += dt
        
        # Remove expired powerups
        self.active_powerups = [p for p in self.active_powerups 
                               if current_time - p.spawn_time < 15.0]
        
        # Spawn new powerups
        if self.spawn_timer > self.spawn_interval and len(self.active_powerups) < 3:
            self.spawn_powerup(current_time)
            self.spawn_timer = 0
    
    def spawn_powerup(self, current_time):
        powerup_types = list(PowerUpType)
        powerup_type = random.choice(powerup_types)
        
        position = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
        
        color_map = {
            PowerUpType.SPEED_BOOST: Colors.YELLOW,
            PowerUpType.SLOW_DOWN: Colors.BLUE,
            PowerUpType.DOUBLE_POINTS: Colors.PURPLE,
            PowerUpType.SHRINK: Colors.ORANGE,
            PowerUpType.WALL_PHASE: Colors.CYAN,
            PowerUpType.MULTIPLIER: Colors.PINK
        }
        
        powerup = PowerUp(
            type=powerup_type,
            position=position,
            duration=5.0,
            spawn_time=current_time,
            color=color_map[powerup_type]
        )
        
        self.active_powerups.append(powerup)
    
    def check_collision(self, snake_pos):
        for powerup in self.active_powerups:
            if powerup.position == snake_pos:
                self.active_powerups.remove(powerup)
                return powerup
        return None
    
    def draw(self, screen, current_time):
        for powerup in self.active_powerups:
            x, y = powerup.position[0] * GRID_SIZE, powerup.position[1] * GRID_SIZE
            
            # Rotating effect
            rotation = (current_time - powerup.spawn_time) * 90
            
            # Draw powerup with special effects
            pygame.draw.rect(screen, powerup.color, (x, y, GRID_SIZE, GRID_SIZE))
            pygame.draw.rect(screen, Colors.WHITE, (x+2, y+2, GRID_SIZE-4, GRID_SIZE-4), 2)
            
            # Draw symbol based on type
            center_x, center_y = x + GRID_SIZE//2, y + GRID_SIZE//2
            if powerup.type == PowerUpType.SPEED_BOOST:
                pygame.draw.polygon(screen, Colors.WHITE, 
                                  [(center_x-5, center_y-3), (center_x+5, center_y), (center_x-5, center_y+3)])

class HighScoreManager:
    def __init__(self):
        self.high_scores_file = "snake_high_scores.json"
        self.high_scores = self.load_high_scores()
    
    def load_high_scores(self):
        try:
            if os.path.exists(self.high_scores_file):
                with open(self.high_scores_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {"single": [], "multi": []}
    
    def save_high_scores(self):
        try:
            with open(self.high_scores_file, 'w') as f:
                json.dump(self.high_scores, f, indent=2)
        except:
            pass
    
    def add_score(self, score, player_name, mode="single"):
        self.high_scores[mode].append({"name": player_name, "score": score, "time": time.time()})
        self.high_scores[mode].sort(key=lambda x: x["score"], reverse=True)
        self.high_scores[mode] = self.high_scores[mode][:10]  # Keep top 10
        self.save_high_scores()

class MenuSystem:
    def __init__(self, screen, font, sound_manager):
        self.screen = screen
        self.font = font
        self.large_font = pygame.font.Font(None, 72)
        self.sound_manager = sound_manager
        self.selected_option = 0
        self.menu_options = ["Single Player", "Multiplayer", "High Scores", "Settings", "Quit"]
        self.settings_options = ["Difficulty: Easy", "Sound: On", "Back"]
        self.difficulty = Difficulty.EASY
        self.sound_enabled = True
    
    def handle_menu_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(self.menu_options)
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(self.menu_options)
            elif event.key == pygame.K_RETURN:
                return self.menu_options[self.selected_option]
        return None
    
    def draw_menu(self):
        self.screen.fill(Colors.BLACK)
        
        # Title
        title = self.large_font.render("SNAKE MASTER", True, Colors.NEON_GREEN)
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 150))
        self.screen.blit(title, title_rect)
        
        # Menu options
        for i, option in enumerate(self.menu_options):
            color = Colors.WHITE if i == self.selected_option else Colors.GRAY
            text = self.font.render(option, True, color)
            text_rect = text.get_rect(center=(WINDOW_WIDTH//2, 300 + i*60))
            self.screen.blit(text, text_rect)
        
        # Instructions
        instructions = [
            "Use ARROW KEYS to navigate",
            "Press ENTER to select",
            "Player 1: WASD",
            "Player 2: Arrow Keys"
        ]
        
        for i, instruction in enumerate(instructions):
            text = pygame.font.Font(None, 24).render(instruction, True, Colors.LIGHT_GRAY)
            text_rect = text.get_rect(center=(WINDOW_WIDTH//2, 600 + i*25))
            self.screen.blit(text, text_rect)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Snake Master - Multiplayer Edition")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Game state
        self.state = GameState.MENU
        self.difficulty = Difficulty.EASY
        self.multiplayer = False
        
        # Managers
        self.sound_manager = SoundManager()
        self.menu_system = MenuSystem(self.screen, self.font, self.sound_manager)
        self.high_score_manager = HighScoreManager()
        self.powerup_manager = PowerUpManager()
        
        # Game objects
        self.snakes = []
        self.food = None
        self.particles = []
        
        # Timing
        self.last_update_time = time.time()
        self.move_timer = 0
        
        self.reset_game()
    
    def reset_game(self):
        self.snakes = []
        
        # Player 1 controls
        p1_controls = {
            pygame.K_w: (0, -1),
            pygame.K_s: (0, 1),
            pygame.K_a: (-1, 0),
            pygame.K_d: (1, 0)
        }
        
        # Player 2 controls
        p2_controls = {
            pygame.K_UP: (0, -1),
            pygame.K_DOWN: (0, 1),
            pygame.K_LEFT: (-1, 0),
            pygame.K_RIGHT: (1, 0)
        }
        
        # Create snakes
        snake1 = Snake(1, Colors.NEON_GREEN, p1_controls, (GRID_WIDTH//4, GRID_HEIGHT//2))
        self.snakes.append(snake1)
        
        if self.multiplayer:
            snake2 = Snake(2, Colors.NEON_BLUE, p2_controls, (3*GRID_WIDTH//4, GRID_HEIGHT//2))
            snake2.direction = (-1, 0)  # Start moving left
            self.snakes.append(snake2)
        
        self.food = Food()
        self.powerup_manager = PowerUpManager()
        self.particles = []
        self.move_timer = 0
        
        # Ensure food doesn't spawn on snakes
        self.respawn_food()
    
    def respawn_food(self):
        while True:
            self.food.position = self.food.generate_position()
            occupied = False
            for snake in self.snakes:
                if self.food.position in snake.positions:
                    occupied = True
                    break
            if not occupied:
                break
    
    def handle_events(self):
        current_time = time.time()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.KEYDOWN:
                if self.state == GameState.MENU:
                    action = self.menu_system.handle_menu_input(event)
                    if action == "Single Player":
                        self.multiplayer = False
                        self.state = GameState.PLAYING
                        self.reset_game()
                    elif action == "Multiplayer":
                        self.multiplayer = True
                        self.state = GameState.PLAYING
                        self.reset_game()
                    elif action == "High Scores":
                        self.state = GameState.HIGH_SCORES
                    elif action == "Settings":
                        self.state = GameState.SETTINGS
                    elif action == "Quit":
                        return False
                
                elif self.state == GameState.PLAYING:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.PAUSED
                    else:
                        # Handle snake controls
                        for snake in self.snakes:
                            if event.key in snake.controls:
                                snake.change_direction(snake.controls[event.key])
                
                elif self.state == GameState.PAUSED:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.PLAYING
                    elif event.key == pygame.K_r:
                        self.reset_game()
                        self.state = GameState.PLAYING
                    elif event.key == pygame.K_m:
                        self.state = GameState.MENU
                
                elif self.state == GameState.GAME_OVER:
                    if event.key == pygame.K_r:
                        self.reset_game()
                        self.state = GameState.PLAYING
                    elif event.key == pygame.K_m:
                        self.state = GameState.MENU
                
                elif self.state in [GameState.HIGH_SCORES, GameState.SETTINGS]:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.MENU
        
        return True
    
    def update(self):
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        if self.state != GameState.PLAYING:
            return
        
        # Update snakes
        for snake in self.snakes:
            snake.update(dt, current_time)
        
        # Update food
        self.food.update(dt)
        
        # Update power-ups
        if self.difficulty.value["powerups"]:
            self.powerup_manager.update(dt, current_time)
        
        # Move snakes based on difficulty
        move_interval = 1.0 / (self.difficulty.value["speed"] * max(snake.speed_multiplier for snake in self.snakes if snake.alive))
        self.move_timer += dt
        
        if self.move_timer >= move_interval:
            self.move_timer = 0
            
            alive_snakes = [s for s in self.snakes if s.alive]
            
            for snake in alive_snakes:
                if not snake.move():
                    self.sound_manager.play_sound('game_over')
                    # Create death particles
                    for pos in snake.positions[:5]:  # Only first 5 segments
                        for _ in range(10):
                            particle = Particle(
                                pos[0] * GRID_SIZE + GRID_SIZE // 2,
                                pos[1] * GRID_SIZE + GRID_SIZE // 2,
                                snake.color,
                                (random.randint(-100, 100), random.randint(-100, 100)),
                                2.0
                            )
                            self.particles.append(particle)
            
            # Check food collision
            for snake in alive_snakes:
                if snake.positions[0] == self.food.position:
                    snake.grow(2)
                    points = int(self.food.value * self.difficulty.value["multiplier"])
                    
                    # Double points power-up
                    if PowerUpType.DOUBLE_POINTS in snake.power_ups:
                        points *= 2
                    
                    snake.score += points
                    self.sound_manager.play_sound('eat')
                    
                    # Create eat particles
                    for _ in range(15):
                        particle = Particle(
                            self.food.position[0] * GRID_SIZE + GRID_SIZE // 2,
                            self.food.position[1] * GRID_SIZE + GRID_SIZE // 2,
                            Colors.RED,
                            (random.randint(-50, 50), random.randint(-50, 50)),
                            1.0
                        )
                        self.particles.append(particle)
                    
                    self.respawn_food()
            
            # Check power-up collisions
            if self.difficulty.value["powerups"]:
                for snake in alive_snakes:
                    powerup = self.powerup_manager.check_collision(snake.positions[0])
                    if powerup:
                        snake.add_power_up(powerup.type, powerup.duration, current_time)
                        self.sound_manager.play_sound('powerup')
            
            # Check snake-to-snake collisions in multiplayer
            if self.multiplayer and len(alive_snakes) > 1:
                for i, snake1 in enumerate(alive_snakes):
                    for j, snake2 in enumerate(alive_snakes):
                        if i != j and snake1.invulnerable_time <= 0:
                            if snake1.positions[0] in snake2.positions:
                                snake1.alive = False
                                self.sound_manager.play_sound('game_over')
            
            # Check game over
            if not any(snake.alive for snake in self.snakes):
                self.state = GameState.GAME_OVER
                # Add high scores
                if self.multiplayer:
                    winner = max(self.snakes, key=lambda s: s.score)
                    self.high_score_manager.add_score(winner.score, f"Player {winner.player_id}", "multi")
                else:
                    self.high_score_manager.add_score(self.snakes[0].score, "Player", "single")
        
        # Update particles
        self.particles = [p for p in self.particles if p.update(dt)]
    
    def draw(self):
        self.screen.fill(Colors.BLACK)
        
        if self.state == GameState.MENU:
            self.menu_system.draw_menu()
        
        elif self.state == GameState.PLAYING:
            self.draw_game()
        
        elif self.state == GameState.PAUSED:
            self.draw_game()
            self.draw_pause_overlay()
        
        elif self.state == GameState.GAME_OVER:
            self.draw_game()
            self.draw_game_over()
        
        elif self.state == GameState.HIGH_SCORES:
            self.draw_high_scores()
        
        elif self.state == GameState.SETTINGS:
            self.draw_settings()
        
        pygame.display.flip()
    
    def draw_game(self):
        # Draw grid
        for x in range(0, WINDOW_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, Colors.DARK_GRAY, (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, Colors.DARK_GRAY, (0, y), (WINDOW_WIDTH, y))
        
        # Draw particles
        for particle in self.particles:
            particle.draw(self.screen)
        
        # Draw food
        self.food.draw(self.screen)
        
        # Draw power-ups
        if self.difficulty.value["powerups"]:
            self.powerup_manager.draw(self.screen, time.time())
        
        # Draw snakes
        for snake in self.snakes:
            snake.draw(self.screen)
        
        # Draw UI
        self.draw_ui()
    
    def draw_ui(self):
        # Draw scores
        y_offset = 10
        for i, snake in enumerate(self.snakes):
            color = snake.color if snake.alive else Colors.GRAY
            score_text = f"Player {snake.player_id}: {snake.score}"
            text = self.font.render(score_text, True, color)
            self.screen.blit(text, (10, y_offset + i * 40))
            
            # Draw active power-ups
            powerup_y = y_offset + i * 40 + 25
            x_offset = 10
            current_time = time.time()
            
            for powerup_type, end_time in snake.power_ups.items():
                remaining = max(0, end_time - current_time)
                if remaining > 0:
                    powerup_name = powerup_type.value.replace('_', ' ').title()
                    powerup_text = f"{powerup_name}: {remaining:.1f}s"
                    text = self.small_font.render(powerup_text, True, Colors.YELLOW)
                    self.screen.blit(text, (x_offset, powerup_y))
                    x_offset += text.get_width() + 15
        
        # Draw difficulty and mode
        diff_text = f"Difficulty: {self.difficulty.name}"
        mode_text = f"Mode: {'Multiplayer' if self.multiplayer else 'Single Player'}"
        
        diff_surface = self.small_font.render(diff_text, True, Colors.WHITE)
        mode_surface = self.small_font.render(mode_text, True, Colors.WHITE)
        
        self.screen.blit(diff_surface, (WINDOW_WIDTH - 200, 10))
        self.screen.blit(mode_surface, (WINDOW_WIDTH - 200, 35))
        
        # Draw controls hint
        controls_text = "ESC: Pause"
        controls_surface = self.small_font.render(controls_text, True, Colors.LIGHT_GRAY)
        self.screen.blit(controls_surface, (WINDOW_WIDTH - 200, WINDOW_HEIGHT - 30))
    
    def draw_pause_overlay(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(Colors.BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Pause text
        pause_text = self.font.render("PAUSED", True, Colors.WHITE)
        pause_rect = pause_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 50))
        self.screen.blit(pause_text, pause_rect)
        
        # Instructions
        instructions = [
            "ESC - Resume",
            "R - Restart",
            "M - Main Menu"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, Colors.WHITE)
            text_rect = text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + i*30))
            self.screen.blit(text, text_rect)
    
    def draw_game_over(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(Colors.BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Game Over text
        game_over_text = self.font.render("GAME OVER", True, Colors.RED)
        game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 100))
        self.screen.blit(game_over_text, game_over_rect)
        
        # Final scores
        if self.multiplayer:
            winner = max(self.snakes, key=lambda s: s.score)
            winner_text = f"Winner: Player {winner.player_id} with {winner.score} points!"
            winner_surface = self.font.render(winner_text, True, Colors.YELLOW)
            winner_rect = winner_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 50))
            self.screen.blit(winner_surface, winner_rect)
            
            for i, snake in enumerate(self.snakes):
                score_text = f"Player {snake.player_id}: {snake.score}"
                color = Colors.GREEN if snake == winner else Colors.WHITE
                text = self.small_font.render(score_text, True, color)
                text_rect = text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 10 + i*25))
                self.screen.blit(text, text_rect)
        else:
            final_score = f"Final Score: {self.snakes[0].score}"
            score_surface = self.font.render(final_score, True, Colors.WHITE)
            score_rect = score_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 50))
            self.screen.blit(score_surface, score_rect)
        
        # Instructions
        instructions = [
            "R - Play Again",
            "M - Main Menu"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, Colors.WHITE)
            text_rect = text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 50 + i*30))
            self.screen.blit(text, text_rect)
    
    def draw_high_scores(self):
        self.screen.fill(Colors.BLACK)
        
        # Title
        title = self.font.render("HIGH SCORES", True, Colors.YELLOW)
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 100))
        self.screen.blit(title, title_rect)
        
        # Single player scores
        single_title = self.small_font.render("Single Player", True, Colors.WHITE)
        single_rect = single_title.get_rect(center=(WINDOW_WIDTH//4, 180))
        self.screen.blit(single_title, single_rect)
        
        for i, score_data in enumerate(self.high_score_manager.high_scores["single"][:10]):
            score_text = f"{i+1}. {score_data['name']}: {score_data['score']}"
            text = self.small_font.render(score_text, True, Colors.WHITE)
            text_rect = text.get_rect(center=(WINDOW_WIDTH//4, 220 + i*30))
            self.screen.blit(text, text_rect)
        
        # Multiplayer scores
        multi_title = self.small_font.render("Multiplayer", True, Colors.WHITE)
        multi_rect = multi_title.get_rect(center=(3*WINDOW_WIDTH//4, 180))
        self.screen.blit(multi_title, multi_rect)
        
        for i, score_data in enumerate(self.high_score_manager.high_scores["multi"][:10]):
            score_text = f"{i+1}. {score_data['name']}: {score_data['score']}"
            text = self.small_font.render(score_text, True, Colors.WHITE)
            text_rect = text.get_rect(center=(3*WINDOW_WIDTH//4, 220 + i*30))
            self.screen.blit(text, text_rect)
        
        # Back instruction
        back_text = self.small_font.render("Press ESC to return to menu", True, Colors.LIGHT_GRAY)
        back_rect = back_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT - 50))
        self.screen.blit(back_text, back_rect)
    
    def draw_settings(self):
        self.screen.fill(Colors.BLACK)
        
        # Title
        title = self.font.render("SETTINGS", True, Colors.YELLOW)
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 100))
        self.screen.blit(title, title_rect)
        
        # Settings options
        settings = [
            f"Difficulty: {self.difficulty.name}",
            f"Sound: {'On' if self.sound_manager.sfx_volume > 0 else 'Off'}",
            "Controls:",
            "  Player 1: W/A/S/D",
            "  Player 2: Arrow Keys",
            "",
            "Power-ups:",
            "  Yellow: Speed Boost",
            "  Blue: Slow Down", 
            "  Purple: Double Points",
            "  Orange: Shrink Snake",
            "  Cyan: Phase Through Walls"
        ]
        
        for i, setting in enumerate(settings):
            color = Colors.WHITE if setting else Colors.LIGHT_GRAY
            text = self.small_font.render(setting, True, color)
            text_rect = text.get_rect(center=(WINDOW_WIDTH//2, 180 + i*30))
            self.screen.blit(text, text_rect)
        
        # Back instruction
        back_text = self.small_font.render("Press ESC to return to menu", True, Colors.LIGHT_GRAY)
        back_rect = back_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT - 50))
        self.screen.blit(back_text, back_rect)
    
    def run(self):
        running = True
        
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)  # 60 FPS for smooth gameplay
        
        pygame.quit()
        sys.exit()

# Run the game
if __name__ == "__main__":
    game = Game()
    game.run()