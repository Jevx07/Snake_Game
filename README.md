# Snake Master - Multiplayer Edition

A modern, feature-rich implementation of the classic Snake game built with Python and Pygame. Features both single-player and multiplayer modes, power-ups, particle effects, and difficulty settings.

## Features

### Game Modes
- **Single Player**: Classic snake gameplay with modern enhancements
- **Multiplayer**: Two-player competitive mode with head-to-head gameplay
- **Multiple Difficulty Levels**: Easy, Medium, and Hard with different speeds and scoring multipliers

### Power-ups System
- **Speed Boost** (Yellow): Temporarily increases snake movement speed
- **Slow Down** (Blue): Temporarily decreases snake movement speed  
- **Double Points** (Purple): Doubles points gained from eating food
- **Shrink** (Orange): Reduces snake length by half
- **Wall Phase** (Cyan): Allows snake to pass through walls and grants temporary invulnerability
- **Multiplier** (Pink): Score multiplier bonus

### Visual Effects
- **Particle Systems**: Dynamic particle effects for eating, dying, and movement trails
- **Smooth Animations**: Pulsing food, glowing effects, and visual feedback
- **Modern UI**: Clean interface with real-time power-up displays
- **Grid-based Graphics**: Classic snake aesthetic with modern polish

### Game Features
- **High Score System**: Persistent high scores for both single and multiplayer modes
- **Sound Effects**: Procedurally generated sound effects for game events
- **Pause System**: Full pause/resume functionality
- **Settings Menu**: Difficulty selection and game information
- **Collision Detection**: Advanced collision system with multiplayer snake-to-snake interactions

## Installation

### Requirements
- Python 3.7 or higher
- Pygame library

### Setup
1. Clone or download the game files
2. Install Pygame:
   ```bash
   pip install pygame
   ```
3. Run the game:
   ```bash
   python snake_master.py
   ```

## Controls

### Single Player
- **W/A/S/D**: Move snake (Up/Left/Down/Right)
- **ESC**: Pause/Resume game

### Multiplayer
- **Player 1**: W/A/S/D keys
- **Player 2**: Arrow keys (↑/←/↓/→)
- **ESC**: Pause/Resume game

### Menu Navigation
- **Arrow Keys**: Navigate menu options
- **Enter**: Select option
- **ESC**: Back to previous menu

### Pause Menu
- **ESC**: Resume game
- **R**: Restart game  
- **M**: Return to main menu

### Game Over
- **R**: Play again
- **M**: Return to main menu

## Gameplay

### Objective
- Eat red food pellets to grow your snake and increase your score
- Avoid colliding with walls, your own tail, or other snakes (in multiplayer)
- Collect power-ups to gain temporary advantages
- Achieve the highest score possible

### Scoring System
- **Basic Food**: 10 points × difficulty multiplier
- **Difficulty Multipliers**: Easy (1.0x), Medium (1.5x), Hard (2.0x)
- **Power-up Bonuses**: Double Points power-up doubles food value
- **Growth**: Snake grows by 2 segments per food eaten

### Difficulty Levels

| Difficulty | Speed | Score Multiplier | Power-ups |
|------------|-------|------------------|-----------|
| Easy       | 8     | 1.0x             | Enabled   |
| Medium     | 12    | 1.5x             | Enabled   |
| Hard       | 18    | 2.0x             | Disabled  |

### Power-up Details
- **Spawn Rate**: Power-ups appear every 10 seconds (maximum 3 active)
- **Duration**: Most power-ups last 5 seconds
- **Availability**: Disabled on Hard difficulty for pure challenge

## Technical Features

### Architecture
- **Object-Oriented Design**: Clean separation of game components
- **State Management**: Robust game state system (Menu, Playing, Paused, Game Over, etc.)
- **Event-Driven**: Responsive input handling and game events
- **Modular Code**: Separate classes for Snake, Food, Power-ups, Particles, etc.

### Performance
- **60 FPS**: Smooth gameplay with consistent frame rate
- **Efficient Rendering**: Optimized drawing routines
- **Memory Management**: Proper cleanup of particles and temporary objects

### Data Persistence
- **High Scores**: Automatically saved to `snake_high_scores.json`
- **Settings**: Game preferences maintained between sessions

## File Structure
```
snake_master.py          # Main game file
snake_high_scores.json   # High scores data (created automatically)
README.md               # This file
```

## Customization

### Modifying Game Constants
Edit the constants at the top of `snake_master.py`:
- `WINDOW_WIDTH/HEIGHT`: Change game window size
- `GRID_SIZE`: Adjust game grid resolution
- `Colors`: Modify color scheme

### Adding New Power-ups
1. Add new `PowerUpType` enum value
2. Implement power-up logic in `Snake.add_power_up()`
3. Add visual representation in `PowerUpManager.spawn_powerup()`

### Difficulty Adjustment
Modify the `Difficulty` enum values to adjust:
- `speed`: Movement frequency
- `multiplier`: Score multiplier
- `powerups`: Enable/disable power-ups

## Troubleshooting

### Common Issues
- **No Sound**: Sound system uses procedural generation - if issues occur, game continues without sound
- **High Scores Not Saving**: Ensure write permissions in game directory
- **Performance Issues**: Reduce particle count or window size if needed

### System Requirements
- **Minimum**: Python 3.7, 512MB RAM, OpenGL-compatible graphics
- **Recommended**: Python 3.9+, 1GB RAM, dedicated graphics card

## Development

### Code Style
- **Type Hints**: Extensive use of type annotations
- **Docstrings**: Comprehensive documentation
- **Error Handling**: Graceful degradation for optional features

### Extension Ideas
- **AI Players**: Computer-controlled snakes
- **Network Multiplayer**: Online play capability
- **Level Editor**: Custom maps and obstacles
- **Tournament Mode**: Bracket-style competitions
- **Theme System**: Multiple visual themes

## License

This project is open source. Feel free to modify and distribute according to your needs.

## Credits

Created with Python and Pygame. Features modern game development patterns and practices for educational and entertainment purposes.

---

**Enjoy playing Snake Master!** 🐍
