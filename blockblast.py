import math



class BlockBlast:
    '''
    Blockblast nhung no la lam :pensive:
    '''
    def __init__(self, board_size:tuple[int, int]=None):
        '''
        Initiallize the game.\n
        default board_size: (8, 8)
        '''
        self.board = 0
        self.board_size = board_size if board_size else (8, 8)

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
            'l1'        : 0b10_10_11,
            'l2'        : 0b111_100,
            'l3'        : 0b11_01_01,
            'l4'        : 0b001_111,
            'diag2'     : 0b01_10,
            'diag3'     : 0b001_010_100,
            'diag2f'    : 0b10_01,
            'diag3f'    : 0b100_010_001,
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
            'l1'        : (2, 3),
            'l2'        : (3, 2),
            'l3'        : (2, 3),
            'l4'        : (3, 2),
            'diag2'     : (2, 2),
            'diag3'     : (3, 3),
            'diag2f'    : (2, 2),
            'diag3f'    : (3, 3),
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
        }
    
        self.name_to_pieces_scaled = {}
        
        for k, v in self.name_to_pieces.items():
            resized = 0
            piece_size_x = self.name_to_size[k][0]
            for y in range(self.name_to_size[k][1]):
                resized |= ((v >> y*piece_size_x) & ((1 << piece_size_x) - 1)) << y*self.board_size[0]

            self.name_to_pieces_scaled[k] = resized

    def place(self, piece_name:str, position:tuple[int, int]):
        p = self.name_to_pieces_scaled[piece_name]
        self.board |= p >> position[0] + position[1]*self.board_size[0]

    def render(self):
        sl = []
        b = bin(self.board)[2:].ljust(math.prod(self.board_size), '0')
        board_size_x = self.board_size[0]
        for y in range(self.board_size[1]):
            sl.append(b[y*board_size_x : (y+1)*board_size_x])
        s = '\n'.join(sl)
        s = s.replace('0', ' .').replace('1', '[]')
        print(s)


if __name__ == '__main__':
    game = BlockBlast()
    game.place('sq3', (0, 0))

    game.render()

    # print(*map(lambda v: bin(v), game.name_to_pieces_scaled.values()), sep='\n')