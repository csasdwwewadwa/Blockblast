import math
import random

class BlockBlast:
    """
    An efficient, bitboard-based implementation of the Block Blast game,
    designed for use in game-playing algorithms.
    """
    def __init__(self, board_size: tuple[int, int] = (8, 8), seed: int = None):
        """
        Initializes the game engine.
        :param board_size: A tuple representing the (width, height) of the board.
        :param seed: A random seed for piece generation to ensure reproducibility.
        """
        if board_size[0] > 64 or board_size[1] > 64:
            raise ValueError("Board dimensions cannot exceed 64 in either direction.")
            
        self.board_size = board_size
        self.width, self.height = board_size
        
        # The game state is represented by a single integer (bitboard).
        self.board:int = 0
        self.score:int = 0
        self.combo:int = -1
        self.score_increment:float = 0
        self.score_incremental_acceleration:float = 0
        self.lines_cleared_score_multiplier_map:dict[int, float] = {1:1., 2:2., 3:6., 4:12., 5:20., 6:30.,}
        self.game_over = False

        self._initialize_piece_data()
        self._precompute_masks()

        self.all_piece_names = list(self.name_to_pieces.keys())
        self.current_pieces = []
        
        if seed is not None:
            random.seed(seed)
        
        self._deal_new_pieces()

    def _initialize_piece_data(self):
        """Initializes the shapes and sizes of all game pieces."""
        self.name_to_pieces = {
            'sq1': 0b1, 'sq2': 0b11_11, 'sq3': 0b111_111_111,
            'line2h': 0b11, 'line3h': 0b111, 'line4h': 0b1111, 'line5h': 0b11111,
            'line2v': 0b1_1, 'line3v': 0b1_1_1, 'line4v': 0b1_1_1_1, 'line5v': 0b1_1_1_1_1,
            'l1': 0b10_11, 'l2': 0b111_100, 'l3': 0b11_01, 'l4': 0b01_11,
            'l1f': 0b01_11, 'l2f': 0b100_111, 'l3f': 0b11_10, 'l4f': 0b111_001,
            't1': 0b010_111, 't2': 0b10_11_10, 't3': 0b111_010, 't4': 0b01_11_01,
            's1': 0b011_110, 's2': 0b10_11_01, 's1f': 0b110_011, 's2f': 0b01_11_10
        }
        self.name_to_size = {
            'sq1': (1, 1), 'sq2': (2, 2), 'sq3': (3, 3),
            'line2h': (2, 1), 'line3h': (3, 1), 'line4h': (4, 1), 'line5h': (5, 1),
            'line2v': (1, 2), 'line3v': (1, 3), 'line4v': (1, 4), 'line5v': (1, 5),
            'l1': (2, 2), 'l2': (3, 2), 'l3': (2, 2), 'l4': (2, 2),
            'l1f': (2, 2), 'l2f': (3, 2), 'l3f': (2, 2), 'l4f': (3, 2),
            't1': (3, 2), 't2': (2, 3), 't3': (3, 2), 't4': (2, 3),
            's1': (3, 2), 's2': (2, 3), 's1f': (3, 2), 's2f': (2, 3)
        }

    def _precompute_masks(self):
        """
        Pre-computes bitmasks for pieces, rows, and columns for efficient calculations.
        """
        # Create scaled piece masks that account for board width.
        self.name_to_piece_masks = {}
        for name, compact_mask in self.name_to_pieces.items():
            piece_width, piece_height = self.name_to_size[name]
            scaled_mask = 0
            for r in range(piece_height):
                row_bits = (compact_mask >> (r * piece_width)) & ((1 << piece_width) - 1)
                scaled_mask |= row_bits << (r * self.width)
            self.name_to_piece_masks[name] = scaled_mask
        
        # Create masks for checking and clearing full rows/columns.
        self.row_masks = [( (1 << self.width) - 1 ) << (r * self.width) for r in range(self.height)]
        self.col_masks = [0] * self.width
        for c in range(self.width):
            for r in range(self.height):
                self.col_masks[c] |= 1 << (r * self.width + c)

    def _deal_new_pieces(self):
        """Selects three new random pieces for the player."""
        self.current_pieces = random.sample(self.all_piece_names, 3)

    def get_piece_mask(self, piece_name: str, position: tuple[int, int]) -> int:
        """
        Calculates the bitmask for a piece at a given (x, y) position.
        :param piece_name: The name of the piece.
        :param position: The (x, y) coordinates for the top-left of the piece.
        :return: An integer bitmask for the positioned piece.
        """
        px, py = position
        return self.name_to_piece_masks[piece_name] << (py * self.width + px)

    def is_valid_move(self, piece_name: str, position: tuple[int, int]) -> bool:
        """
        Checks if placing a piece at a given position is valid.
        :param piece_name: The name of the piece.
        :param position: The (x, y) coordinates.
        :return: True if the move is valid, False otherwise.
        """
        piece_width, piece_height = self.name_to_size[piece_name]
        px, py = position

        # 1. Boundary Check: Ensure the piece does not go off the board.
        if px < 0 or py < 0 or px + piece_width > self.width or py + piece_height > self.height:
            return False

        # 2. Collision Check: Ensure the piece does not overlap with existing blocks.
        piece_mask = self.get_piece_mask(piece_name, position)
        if (self.board & piece_mask) != 0:
            return False
            
        return True

    def get_possible_moves(self) -> dict[str, list[tuple[int,int]]]:
        """
        Finds all possible valid moves for the current set of pieces.
        :return: A dictionary mapping piece names to a list of valid (x,y) positions.
        """
        possible_moves = {}
        for piece_name in self.current_pieces:
            piece_moves = []
            for r in range(self.height):
                for c in range(self.width):
                    if self.is_valid_move(piece_name, (c, r)):
                        piece_moves.append((c, r))
            if piece_moves:
                possible_moves[piece_name] = piece_moves
        return possible_moves

    def make_move(self, piece_name: str, position: tuple[int, int]) -> dict:
        """
        Places a piece on the board, clears lines, updates score, and gets new pieces.
        :param piece_name: The name of the piece to place.
        :param position: The (x, y) coordinates to place it.
        :return: A dictionary with information about the move's result.
        """
        if self.game_over:
            return {"status": "error", "message": "Game is over."}
            
        if piece_name not in self.current_pieces:
            return {"status": "error", "message": f"Piece '{piece_name}' is not available."}

        if not self.is_valid_move(piece_name, position):
            return {"status": "error", "message": "Invalid move."}
        
        # Place the piece and update score for placement
        piece_mask = self.get_piece_mask(piece_name, position)
        self.board |= piece_mask
        
        num_blocks = bin(self.name_to_pieces[piece_name]).count('1')
        self.score += num_blocks
        
        # Check and clear lines
        lines_cleared = 0
        cleared_mask = 0
        
        # Check rows
        for row_mask in self.row_masks:
            if (self.board & row_mask) == row_mask:
                lines_cleared += 1
                cleared_mask |= row_mask
                
        # Check columns
        for col_mask in self.col_masks:
            if (self.board & col_mask) == col_mask:
                lines_cleared += 1
                cleared_mask |= col_mask
        
        # Clear the lines from the board
        if lines_cleared > 0:
            self.board &= ~cleared_mask

            self.combo += 1

            # Scoring calculation
            match self.combo:
                case 0:
                    self.score_incremental_acceleration = 34.2     # TODO: base seed affects this (idk how base seed even is calculated as of now)
                case 5:
                    self.score_incremental_acceleration *= 4       # 4
                case 6:
                    self.score_incremental_acceleration *= 0.375   # 3/8
                case 10:
                    self.score_incremental_acceleration *= 4.6666  # 14/3
                case 11:
                    self.score_incremental_acceleration *= 0.2857  # 2/7
            
            self.score_increment += self.score_incremental_acceleration
            this_is_the_true_score_increment = int(self.score_increment * self.lines_cleared_score_multiplier_map[lines_cleared])
            self.score += this_is_the_true_score_increment
        

        # Replenish pieces and check for game over
        self.current_pieces.remove(piece_name)
        if not self.current_pieces:
            self._deal_new_pieces()
        
        if not self.get_possible_moves():
            self.game_over = True
            
        return {
            "status": "success",
            "score": self.score,
            "lines_cleared": lines_cleared,
            "game_over": self.game_over
        }

    def render(self):
        """Prints a human-readable representation of the board."""
        print(f"Score: {self.score}")
        print("_" * (self.width * 2 + 1))
        for r in range(self.height):
            row_str = "|"
            for c in range(self.width):
                if (self.board >> (r * self.width + c)) & 1:
                    row_str += "■ "
                else:
                    row_str += ". "
            print(row_str.strip() + "|")
        print("-" * (self.width * 2 + 1))
        if not self.game_over:
            print("Available Pieces:", self.current_pieces)
        else:
            print("GAME OVER")


if __name__ == '__main__':
    # --- Example Usage ---
    # Initialize the game with a seed for deterministic piece generation
    game = BlockBlast(board_size=(8, 8))
    game.render()

    # --- Simulate a few moves ---
    # An algorithm would determine the best piece and position.
    # Here, we'll just pick the first available valid move.
    
    for i in range(5): # Simulate 5 moves
        if game.game_over:
            break
        
        # Get all possible moves for the current pieces
        moves = game.get_possible_moves()
        
        if not moves:
            print("No more moves possible with current pieces!")
            game.game_over = True
            break
            
        # Simple strategy: play the first possible move found
        piece_to_play = list(moves.keys())[0]
        position_to_play = moves[piece_to_play][0]
        
        print(f"\nPlacing '{piece_to_play}' at {position_to_play}...")
        
        result = game.make_move(piece_to_play, position_to_play)
        print(f"Move Result: {result}")
        
        game.render()