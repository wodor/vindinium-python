"""Game rules engine (Arbiter) for processing moves and applying game mechanics."""

from typing import Optional
from ..models import Game, Hero, Dir, Pos, Tile, TileType


class Arbiter:
    """Game rules engine that processes moves and applies consequences."""

    @staticmethod
    def process_move(game: Game, hero_id: int, direction: Dir) -> Game:
        """Process a single hero move and return updated game state."""
        hero = game.get_hero(hero_id)
        if hero is None or hero.is_dead() or hero.crashed:
            return game
        
        # Calculate target position
        target_pos = hero.pos.move_to(direction)
        
        # Update hero's last direction
        updated_hero = hero.with_last_dir(direction)
        game = game.with_hero(updated_hero)
        
        # Apply movement logic
        game = Arbiter.apply_movement(game, updated_hero, target_pos)
        
        # Resolve combat after movement
        game = Arbiter.resolve_combat(game, hero_id)
        
        # Handle respawns
        game = Arbiter.handle_respawns(game)
        
        # Finalize turn effects
        game = Arbiter.finalize_turn(game, hero_id)
        
        return game

    @staticmethod
    def apply_movement(game: Game, hero: Hero, target_pos: Pos) -> Game:
        """Handle hero movement to target position."""
        board = game.board
        
        # Check if target position is valid
        if not board.is_valid_position(target_pos):
            return game  # Stay in place
        
        # Check what's at the target position
        target_tile = board.get(target_pos)
        if target_tile is None:
            return game  # Stay in place
        
        # Check for wall collision
        if target_tile.tile_type == TileType.WALL:
            return game  # Stay in place
        
        # Check for hero collision
        hero_at_target = game.get_hero_at(target_pos)
        if hero_at_target is not None:
            return game  # Stay in place
        
        # Handle special tiles
        if target_tile.tile_type == TileType.TAVERN:
            return Arbiter._handle_tavern(game, hero, target_pos)
        elif target_tile.tile_type == TileType.MINE:
            return Arbiter._handle_mine(game, hero, target_pos, target_tile)
        else:  # AIR tile
            # Simple movement to empty space
            updated_hero = hero.move_to(target_pos)
            return game.with_hero(updated_hero)

    @staticmethod
    def _handle_tavern(game: Game, hero: Hero, target_pos: Pos) -> Game:
        """Handle hero moving into a tavern."""
        if hero.can_afford_beer():
            # Drink beer and move to tavern
            updated_hero = hero.drink_beer().move_to(target_pos)
            return game.with_hero(updated_hero)
        else:
            # Can't afford beer, stay in place
            return game

    @staticmethod
    def _handle_mine(game: Game, hero: Hero, target_pos: Pos, mine_tile: Tile) -> Game:
        """Handle hero moving into a mine."""
        # Check if hero already owns this mine
        if mine_tile.owner == hero.id:
            return game  # Can't move into own mine
        
        # Capture the mine and take damage
        updated_hero = hero.fight_mine().move_to(target_pos)
        game = game.with_hero(updated_hero)
        
        # Transfer mine ownership
        new_mine = Tile.mine(hero.id)
        updated_board = game.board.update(target_pos, new_mine)
        game = game.with_board(updated_board)
        
        return game

    @staticmethod
    def resolve_combat(game: Game, attacking_hero_id: int) -> Game:
        """Resolve combat between adjacent heroes."""
        attacker = game.get_hero(attacking_hero_id)
        if attacker is None or attacker.is_dead():
            return game
        
        # Find adjacent heroes
        for defender in game.heroes:
            if (defender.id != attacking_hero_id and 
                defender.is_alive() and 
                attacker.pos.is_adjacent_to(defender.pos)):
                
                # Apply combat damage to defender
                damaged_defender = defender.defend()
                game = game.with_hero(damaged_defender)
                
                # If defender dies, transfer their mines to attacker
                if damaged_defender.is_dead():
                    game = Arbiter._transfer_mines(game, defender.id, attacker.id)
        
        return game

    @staticmethod
    def _transfer_mines(game: Game, from_hero_id: int, to_hero_id: int) -> Game:
        """Transfer all mines from one hero to another."""
        board = game.board
        updated_tiles = []
        
        for i, tile in enumerate(board.tiles):
            if tile.tile_type == TileType.MINE and tile.owner == from_hero_id:
                updated_tiles.append(Tile.mine(to_hero_id))
            else:
                updated_tiles.append(tile)
        
        updated_board = board.with_tiles(updated_tiles)
        return game.with_board(updated_board)

    @staticmethod
    def handle_respawns(game: Game) -> Game:
        """Handle hero respawn mechanics."""
        for hero in game.heroes:
            if hero.needs_respawn():
                spawn_pos = game.spawn_pos_of(hero)
                
                # Check if spawn position is occupied
                occupying_hero = game.get_hero_at(spawn_pos)
                if occupying_hero is not None:
                    # Respawn the occupying hero first
                    occupying_spawn = game.spawn_pos_of(occupying_hero)
                    respawned_occupier = occupying_hero.respawn(occupying_spawn, game.turn)
                    game = game.with_hero(respawned_occupier)
                
                # Respawn the dead hero
                respawned_hero = hero.respawn(spawn_pos, game.turn)
                game = game.with_hero(respawned_hero)
        
        return game

    @staticmethod
    def finalize_turn(game: Game, hero_id: int) -> Game:
        """Apply end-of-turn effects (life drain, mine income)."""
        # Apply life drain to all living heroes
        for hero in game.heroes:
            if hero.is_alive():
                updated_hero = hero.day()  # -1 life
                game = game.with_hero(updated_hero)
        
        # Apply mine income
        game = Arbiter._apply_mine_income(game)
        
        return game

    @staticmethod
    def _apply_mine_income(game: Game) -> Game:
        """Apply mine income to all heroes."""
        # Count mines owned by each hero
        mine_counts = {1: 0, 2: 0, 3: 0, 4: 0}
        
        for tile in game.board.tiles:
            if tile.tile_type == TileType.MINE and tile.owner is not None:
                mine_counts[tile.owner] += 1
        
        # Apply income to each hero
        for hero in game.heroes:
            income = mine_counts.get(hero.id, 0)
            if income > 0:
                updated_hero = hero.with_gold(income)
                game = game.with_hero(updated_hero)
        
        return game