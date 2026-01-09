# Requirements Document

## Introduction

Vindinium is a multiplayer AI programming challenge where players control heroes in a grid-based world. Heroes navigate maps, capture gold mines, drink beer at taverns to restore health, and fight each other for control of resources. The goal is to accumulate the most gold by the end of the game. This specification focuses on the core game engine implementation, with persistence and game modes as secondary priorities.

## Glossary

- **Hero**: A player-controlled character with health, gold, position, and unique token
- **Board**: Square grid-based game map containing tiles (Air, Wall, Tavern, Mine)
- **Mine**: Resource tile that generates gold for its owner each turn
- **Tavern**: Healing location where heroes can drink beer (costs 2 gold, restores 50 health)
- **Game**: Complete game state including board, 4 heroes, turn counter, and status
- **Training_Mode**: Single-player practice mode against AI or solo play
- **Arena_Mode**: Competitive multiplayer mode with ELO rating system
- **Turn**: One hero's opportunity to make a move (North, South, East, West, Stay)
- **Token**: Unique identifier allowing a hero to make moves in a specific game
- **API_Key**: User authentication credential for accessing the game API
- **Arbiter**: Game rules engine that processes moves and applies consequences
- **ELO_System**: Rating system for tracking player skill in arena mode
- **Replay_System**: Storage and playback system for completed games

## Requirements

### Requirement 1: Core Game Models

**User Story:** As a developer, I want well-defined data models for all game entities, so that the game state is consistent and predictable.

#### Acceptance Criteria

1. THE Position_Model SHALL support navigation in four cardinal directions (North, South, East, West)
2. THE Hero_Model SHALL track health (0-100), gold (≥0), position, and ownership status
3. THE Board_Model SHALL represent a square grid of tiles with size calculation and position validation
4. THE Game_Model SHALL aggregate board state, four heroes, turn counter, and game status
5. THE Tile_Model SHALL represent Air, Wall, Tavern, and Mine types with optional ownership
6. WHEN a hero moves north, THE Position_Model SHALL decrease the x coordinate by 1
7. WHEN a hero moves south, THE Position_Model SHALL increase the x coordinate by 1
8. WHEN a hero moves east, THE Position_Model SHALL increase the y coordinate by 1
9. WHEN a hero moves west, THE Position_Model SHALL decrease the y coordinate by 1

### Requirement 2: Game Rules Engine (Arbiter)

**User Story:** As a player, I want consistent game mechanics, so that my bot strategies work predictably.

#### Acceptance Criteria

1. WHEN a hero moves to an empty space, THE Arbiter SHALL update the hero's position
2. WHEN a hero moves into a wall, THE Arbiter SHALL ignore the move and keep the hero in place
3. WHEN a hero moves into another hero, THE Arbiter SHALL ignore the move and keep both heroes in place
4. WHEN a hero moves into a tavern with sufficient gold, THE Arbiter SHALL execute beer drinking (-2 gold, +50 health)
5. WHEN a hero moves into a tavern without sufficient gold, THE Arbiter SHALL ignore the move
6. WHEN a hero moves into an unowned mine, THE Arbiter SHALL transfer mine ownership and reduce hero health by 20
7. WHEN a hero moves into an enemy-owned mine, THE Arbiter SHALL transfer mine ownership and reduce hero health by 20
8. WHEN a hero moves into their own mine, THE Arbiter SHALL ignore the move
9. WHEN heroes are adjacent after movement, THE Arbiter SHALL apply combat damage (-20 health to defender)
10. WHEN a hero's health reaches 0, THE Arbiter SHALL respawn the hero at their spawn position with full health
11. WHEN a hero respawns, THE Arbiter SHALL transfer all their mines to the killer or make them neutral
12. WHEN a turn completes, THE Arbiter SHALL apply daily life drain (-1 health) and mine income (+1 gold per owned mine)

### Requirement 3: Map System and Parsing

**User Story:** As a game designer, I want flexible map creation and parsing, so that diverse game scenarios can be supported.

#### Acceptance Criteria

1. WHEN a map string is provided, THE Parser SHALL convert it to a Board object with correct tile types
2. WHEN parsing "  " characters, THE Parser SHALL create Air tiles
3. WHEN parsing "##" characters, THE Parser SHALL create Wall tiles
4. WHEN parsing "[]" characters, THE Parser SHALL create Tavern tiles
5. WHEN parsing "$-" characters, THE Parser SHALL create neutral Mine tiles
6. WHEN parsing "$1", "$2", "$3", "$4" characters, THE Parser SHALL create owned Mine tiles
7. THE System SHALL support map mirroring for fair 4-player spawn positioning
8. THE System SHALL validate map dimensions are square and contain required spawn positions

### Requirement 4: Game State Management

**User Story:** As a developer, I want proper game state transitions, so that games progress correctly from start to finish.

#### Acceptance Criteria

1. WHEN a game is created, THE System SHALL initialize four heroes at their spawn positions
2. WHEN a turn advances, THE System SHALL update the current hero ID (cycling 1-4)
3. WHEN maximum turns are reached, THE System SHALL end the game with TurnMax status
4. WHEN all heroes crash, THE System SHALL end the game with AllCrashed status
5. THE System SHALL track game status (Created, Started, AllCrashed, TurnMax)
6. THE System SHALL determine winners based on final gold amounts

### Requirement 5: Basic API Interface

**User Story:** As a bot developer, I want simple API endpoints to test the game engine, so that I can validate game mechanics.

#### Acceptance Criteria

1. WHEN a move request is received with valid game ID and direction, THE API SHALL process the move and return updated game state
2. WHEN an invalid direction is provided, THE API SHALL treat it as a Stay move
3. WHEN a game state is requested, THE API SHALL return current game state in JSON format
4. THE API SHALL return game state including heroes, board, turn, and status information
5. THE API SHALL handle move timeouts by treating them as Stay moves

### Requirement 6: Combat System

**User Story:** As a player, I want tactical combat mechanics, so that positioning and timing matter in gameplay.

#### Acceptance Criteria

1. WHEN two heroes are adjacent after movement, THE Arbiter SHALL apply combat between them
2. WHEN a hero attacks another hero, THE Arbiter SHALL reduce the defender's health by 20
3. WHEN a hero dies in combat, THE Arbiter SHALL transfer all their mines to the attacker
4. WHEN a hero respawns, THE Arbiter SHALL place them at their designated spawn position
5. WHEN a respawning hero's spawn position is occupied, THE Arbiter SHALL handle the collision by respawning the occupying hero
6. THE Combat_System SHALL prevent heroes from attacking during their respawn turn

### Requirement 7: Mine Economics

**User Story:** As a player, I want mine ownership to provide strategic value, so that controlling territory matters.

#### Acceptance Criteria

1. WHEN a turn ends, THE System SHALL award 1 gold per owned mine to each hero
2. WHEN a hero captures a mine, THE System SHALL transfer ownership immediately
3. WHEN a hero dies, THE System SHALL transfer all their mines to the killer or make them neutral
4. THE System SHALL track mine ownership changes throughout the game
5. THE System SHALL count total mines owned by each hero for income calculation

### Requirement 8: Health and Tavern System

**User Story:** As a player, I want health management mechanics, so that resource management is part of the strategy.

#### Acceptance Criteria

1. WHEN a hero drinks beer at a tavern, THE System SHALL reduce their gold by 2 and increase health by 50
2. WHEN a hero has insufficient gold for beer, THE System SHALL prevent the beer drinking action
3. WHEN a hero's health exceeds 100, THE System SHALL cap it at maximum health (100)
4. WHEN a turn ends, THE System SHALL reduce each living hero's health by 1 (daily life drain)
5. WHEN a hero's health reaches 0 from life drain, THE System SHALL respawn them with full health

### Requirement 9: Error Handling and Edge Cases

**User Story:** As a system administrator, I want robust error handling, so that edge cases don't crash the game engine.

#### Acceptance Criteria

1. WHEN invalid positions are accessed, THE System SHALL return None or handle gracefully
2. WHEN heroes attempt moves outside board boundaries, THE System SHALL treat them as Stay moves
3. WHEN multiple heroes attempt to move to the same position, THE System SHALL resolve conflicts consistently
4. WHEN game state becomes inconsistent, THE System SHALL log errors and attempt recovery
5. THE System SHALL validate all game state transitions before applying them