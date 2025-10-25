import random
from typing import Optional

class BlockBlast:
    """
    An efficient, bitboard-based implementation of the Block Blast game.
    """
    def __init__(self, board_size: tuple[int, int] = (8, 8), seed: int | None = None, is_guranteed_valid_moves: bool = True):
        if board_size[0] > 64 or board_size[1] > 64:
            raise ValueError("Board dimensions cannot exceed 64.")
        
        self.is_guranteed_valid_moves = is_guranteed_valid_moves

        self.width, self.height = board_size
        self.board: int = 0
        self.score: int = 0
        self.combo: int = -1
        self.not_combo_counter: int = 3
        self.score_increment: float = 0
        self.score_incremental_acceleration: float = 0
        self.game_over: bool = False

        self.SCORE_MULTIPLIERS = {1: 1.0, 2: 2.0, 3: 6.0, 4: 12.0, 5: 20.0, 6: 30.0}
        self.BASE_SCORE_ACCELERATION = 34.2

        self._initialize_piece_data()
        self._precompute_masks()

        self.all_piece_names = list(self.name_to_pieces.keys())
        self.current_pieces = []
        
        if seed is not None:
            random.seed(seed)
        
        self._deal_new_pieces()

    def _initialize_piece_data(self):
        self.name_to_pieces = {
            'sq1'       : 0b1,
            'sq2'       : 0b11_11,
            'sq3'       : 0b111_111_111,
            'line2h'    : 0b11,
            'line3h'    : 0b111,
            'line4h'    : 0b1111,
            'line5h'    : 0b11111,
            'line2v'    : 0b1_1,
            'line3v'    : 0b1_1_1,
            'line4v'    : 0b1_1_1_1,
            'line5v'    : 0b1_1_1_1_1,
            'diag2'     : 0b01_10,
            'diag3'     : 0b001_010_100,
            'diag2f'    : 0b10_01,
            'diag3f'    : 0b100_010_001,
            'l1'        : 0b10_10_11,
            'l2'        : 0b111_100,
            'l3'        : 0b11_01_01,
            'l4'        : 0b001_111,
            'l1f'       : 0b01_01_11,
            'l2f'       : 0b100_111,
            'l3f'       : 0b11_10_10,
            'l4f'       : 0b111_001,
            't1'        : 0b010_111,
            't2'        : 0b01_11_01,
            't3'        : 0b111_010,
            't4'        : 0b10_11_10,
            's1'        : 0b011_110,
            's2'        : 0b10_11_01,
            's1f'       : 0b110_011,
            's2f'       : 0b01_11_10,
            'L1'        : 0b100_100_111,
            'L2'        : 0b111_100_100,
            'L3'        : 0b111_001_001,
            'L4'        : 0b001_001_111,
            'sL1'       : 0b10_11,
            'sL2'       : 0b11_10,
            'sL3'       : 0b11_01,
            'sL4'       : 0b01_11
        }
        self.name_to_size = {
            'sq1'       : (1, 1),
            'sq2'       : (2, 2),
            'sq3'       : (3, 3),
            'line2h'    : (2, 1),
            'line3h'    : (3, 1),
            'line4h'    : (4, 1),
            'line5h'    : (5, 1),
            'line2v'    : (1, 2),
            'line3v'    : (1, 3),
            'line4v'    : (1, 4),
            'line5v'    : (1, 5),
            'diag2'     : (2, 2),
            'diag3'     : (3, 3),
            'diag2f'    : (2, 2),
            'diag3f'    : (3, 3),
            'l1'        : (2, 3),
            'l2'        : (3, 2),
            'l3'        : (2, 3),
            'l4'        : (3, 2),
            'l1f'       : (2, 3),
            'l2f'       : (3, 2),
            'l3f'       : (2, 3),
            'l4f'       : (3, 2),
            't1'        : (3, 2),
            't2'        : (2, 3),
            't3'        : (3, 2),
            't4'        : (2, 3),
            's1'        : (3, 2),
            's2'        : (2, 3),
            's1f'       : (3, 2),
            's2f'       : (2, 3),
            'L1'        : (3, 3),
            'L2'        : (3, 3),
            'L3'        : (3, 3),
            'L4'        : (3, 3),
            'sL1'       : (2, 2),
            'sL2'       : (2, 2),
            'sL3'       : (2, 2),
            'sL4'       : (2, 2)
        }
        
    def _precompute_masks(self):
        self.name_to_piece_masks = {}
        for name, compact_mask in self.name_to_pieces.items():
            piece_w, piece_h = self.name_to_size[name]
            scaled_mask = 0
            for r in range(piece_h):
                row_bits = (compact_mask >> (r * piece_w)) & ((1 << piece_w) - 1)
                scaled_mask |= row_bits << (r * self.width)
            self.name_to_piece_masks[name] = scaled_mask
        
        self.row_masks = [((1 << self.width) - 1) << (r * self.width) for r in range(self.height)]
        self.col_masks = [0] * self.width
        for c in range(self.width):
            for r in range(self.height):
                self.col_masks[c] |= 1 << (r * self.width + c)

    def _can_place_piece(self, board:int, piece_name: str) -> bool:
        """Checks if a given piece can be placed anywhere on the board. Returns valid position if there is"""
        for y in range(self.height):
            for x in range(self.width):
                if self.is_valid_move(board, piece_name, (x, y)):
                    return (x, y)
        return False

    def _deal_new_pieces(self):
        self.current_pieces = random.sample(self.all_piece_names, 3)

    def _guaranteed_deal_new_pieces(self):
        """
        Deals a set of 3 new pieces, guarantees at least a way to place all 3 of them on board
        """
        self.current_pieces = []
        all_pieces_choices = self.all_piece_names.copy()
        random.shuffle(all_pieces_choices)

        board = self.board

        while True:
            for name in all_pieces_choices:
                placable_position = self._can_place_piece(board, name)
                if placable_position:
                    board = self.try_move(board, name, placable_position)['board']
                    self.current_pieces.append(name)
                    if len(self.current_pieces) == 3:
                        break
            if len(self.current_pieces) == 3:
                break

        random.shuffle(self.current_pieces)

    def get_piece_mask(self, piece_name: str, position: tuple[int, int]) -> int:
        px, py = position
        return self.name_to_piece_masks[piece_name] << (py * self.width + px)

    def is_valid_move(self, board:int, piece_name: str, position: tuple[int, int]) -> bool:
        piece_w, piece_h = self.name_to_size[piece_name]
        px, py = position

        if px < 0 or py < 0 or px + piece_w > self.width or py + piece_h > self.height:
            return False

        if (board & self.get_piece_mask(piece_name, position)) != 0:
            return False
            
        return True

    def get_possible_moves(self) -> dict[str, list[tuple[int, int]]]:
        possible_moves = {}
        for name in self.current_pieces:
            moves = []
            for r in range(self.height):
                for c in range(self.width):
                    if self.is_valid_move(self.board, name, (c, r)):
                        moves.append((c, r))
            if moves:
                possible_moves[name] = moves
        return possible_moves

    def make_move(self, piece_name: str, position: tuple[int, int]) -> dict:
        if self.game_over:
            return {"status": "error", "message": "Game is over."}
        if piece_name not in self.current_pieces:
            return {"status": "error", "message": f"Piece '{piece_name}' unavailable."}
        if not self.is_valid_move(self.board, piece_name, position):
            return {"status": "error", "message": "Invalid move."}
        
        self.board |= self.get_piece_mask(piece_name, position)
        self.score += self.name_to_pieces[piece_name].bit_count()
        
        lines_cleared = 0
        cleared_mask = 0
        
        for row_mask in self.row_masks:
            if (self.board & row_mask) == row_mask:
                lines_cleared += 1
                cleared_mask |= row_mask
                
        for col_mask in self.col_masks:
            if (self.board & col_mask) == col_mask:
                lines_cleared += 1
                cleared_mask |= col_mask
        
        if lines_cleared > 0:
            self.board &= ~cleared_mask
            self.not_combo_counter = 3

            if self.not_combo_counter + lines_cleared <= 1:
                self.combo = -1
                self.score_increment = 0

            self.combo += 1
            
            match self.combo:
                case 0: self.score_incremental_acceleration = self.BASE_SCORE_ACCELERATION
                case 5: self.score_incremental_acceleration *= 4
                case 6: self.score_incremental_acceleration *= 0.375
                case 10: self.score_incremental_acceleration *= 4.6666
                case 11: self.score_incremental_acceleration *= 0.2857
            
            self.score_increment += self.score_incremental_acceleration
            self.score += int(self.score_increment * self.SCORE_MULTIPLIERS.get(lines_cleared, 30.0))
        else:
            self.not_combo_counter -= 1

        self.current_pieces.remove(piece_name)
        if not self.current_pieces:
            if self.is_guranteed_valid_moves:
                self._guaranteed_deal_new_pieces()
            else:
                self._deal_new_pieces()
        
        if not self.get_possible_moves():
            self.game_over = True
            
        return {
            "status": "success",
            "board": self.board,
            "score": self.score,
            "lines_cleared": lines_cleared,
            "game_over": self.game_over
        }

    def try_move(self, board: int, piece_name: str, position: tuple[int, int]) -> dict[str, str|int|bool]:
        if not self.is_valid_move(board, piece_name, position):
            return {"status": "error", "message": "Invalid move."}
        
        board |= self.get_piece_mask(piece_name, position)
        
        lines_cleared = 0
        cleared_mask = 0
        
        for row_mask in self.row_masks:
            if (board & row_mask) == row_mask:
                lines_cleared += 1
                cleared_mask |= row_mask
                
        for col_mask in self.col_masks:
            if (board & col_mask) == col_mask:
                lines_cleared += 1
                cleared_mask |= col_mask
        
        if lines_cleared > 0:
            board &= ~cleared_mask
        
        game_over = False
        if not self.get_possible_moves():
            game_over = True
            
        return {
            "status": "success",
            "board": board,
            "lines_cleared": lines_cleared,
            "game_over": game_over
        }



    def render(self):
        print(f"Score: {self.score}")
        print("_" * (self.width * 2 + 1))
        for r in range(self.height):
            row_str = "|"
            for c in range(self.width):
                row_str += "■ " if (self.board >> (r * self.width + c)) & 1 else ". "
            print(row_str.strip() + "|")
        print("-" * (self.width * 2 + 1))
        if not self.game_over:
            print("Available Pieces:", self.current_pieces)
        else:
            print("GAME OVER")

print('Loaded Game')

if __name__ == '__main__':
    game = BlockBlast(board_size=(8, 8))
    game.render()

    while True:
        if game.game_over:
            break

        input()
        
        moves = game.get_possible_moves()
        if not moves:
            game.game_over = True
            break
            
        piece = list(moves.keys())[0]
        pos = moves[piece][0]
        
        print(f"\nPlacing '{piece}' at {pos}...")
        print(f"Result: {game.make_move(piece, pos)}")
        game.render()