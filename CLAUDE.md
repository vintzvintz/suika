# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Suika Game** (watermelon game) implementation in Python using:
- **pyglet** for graphics and windowing
- **pymunk** for 2D physics simulation

The game involves dropping fruits that merge when identical fruits collide, with the goal of creating larger fruits while avoiding overflow.

## Setup and Dependencies

### Virtual Environment Setup

This project uses Python 3.13.7 managed with pyenv.

Create and activate virtual environment:
```bash
# Using pyenv-installed Python 3.13.7
~/.pyenv/versions/3.13.7/bin/python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Or if pyenv is in your PATH:
```bash
pyenv shell 3.13.7
python -m venv venv
source venv/bin/activate
```

### Dependencies

Required Python packages:
- `pyglet==2.1.8` (graphics library)
- `pymunk==7.1.0` (physics engine)

Install dependencies:
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install pyglet pymunk
```

## Running the Game

Activate the virtual environment first:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Main entry point:
```bash
python suika.py
```

Test/demo application:
```bash
python test_pyglet.py
```

## Code Architecture

### Core Game Structure

**Main Game Loop** (`suika.py`):
- `SuikaWindow`: Main game window extending pyglet.window.Window
- Handles input, rendering, and game state management
- Integrates all game subsystems

**Physics Integration**:
- Uses pymunk for rigid body simulation
- Scheduled physics updates at 120 FPS (`PYMUNK_INTERVAL = 1/120.0`)
- Custom collision detection and fruit merging logic

### Key Components

**Fruit System** (`fruit.py`):
- `Fruit`: Individual fruit objects with physics bodies and sprites
- `ActiveFruits`: Manager for all active fruits in the game
- Fruit modes: WAIT, FIRST_DROP, NORMAL, DRAG, MERGE, REMOVED
- Collision types based on fruit kind/species

**Container System** (`bocal.py`):
- `Bocal`: Game container with walls and physics boundaries
- Supports shaking mechanics (auto, mouse-controlled)
- Tumbling effects and boundary detection

**Graphics System** (`sprites.py`):
- Sprite management with rendering groups and batching
- `FruitSprite`: Animated fruit graphics with fade effects
- `ExplosionSprite`: Particle effects for fruit removal
- Uses pyglet batching for performance

**Collision System** (`collision.py`):
- `CollisionHelper`: Manages collision detection and fruit merging
- Handles different collision types (walls, fruits, boundaries)
- Determines when and how fruits should merge

**GUI System** (`gui.py`):
- Game status display (score, FPS, game state)
- Positioned labels for different screen regions

**Game Configuration** (`constants.py`):
- All game parameters and tuning values
- Physics constants, timing, and visual settings
- Collision categories and types

### Game Controls

- **Left Click**: Drop fruit at cursor position
- **Right Click**: Explode fruit at cursor (debug feature)
- **A**: Toggle autoplay mode
- **P**: Pause/unpause
- **Space**: Manual shake mode
- **S**: Auto shake mode
- **M**: Manual fruit dragging mode
- **T**: Tumble mode (washing machine effect)
- **R**: Restart game
- **ESC**: Exit game

### Development Notes

**Physics Timing**:
- Physics simulation runs at 120 FPS regardless of display FPS
- Display updates are handled separately by pyglet

**Commit messages instructions**
- no promotional content 
- optimise for automated tools and AI

**Asset Loading**:
- Assets loaded from `assets/` directory
- Resource path configured in `suika.py:419`

**Collision Categories**:
- Fruits have collision types based on their species
- Different interaction rules for different fruit states
- Optimized collision filtering using categories/masks

**Performance**:
- Uses pyglet batching for efficient sprite rendering
- Sprite groups for proper draw order
- Physics body cleanup for removed fruits