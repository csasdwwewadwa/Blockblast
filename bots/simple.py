from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from game import BlockBlast


class Solver:
    def __init__(self, game:BlockBlast):
        self.game = game
        self.solution = []

    def get_solution(self) -> list:
        def recurse(board: int, pieces: list[str]):
            if not pieces:
                yield []
                return

            for i, p in enumerate(pieces):
                for y in range(self.game.height):
                    for x in range(self.game.width):
                        if self.game.is_valid_move(board, p, (x, y)):
                            next_board = self.game.try_move(board, p, (x, y))['board']
                            next_pieces = pieces.copy()
                            next_pieces.pop(i)

                            for placable_move in recurse(next_board, next_pieces):
                                next_sequence = [(p, (x, y))] + placable_move
                                yield next_sequence

        current_pieces = self.game.current_pieces.copy()
        try:
            solution_sequence = next(recurse(self.game.board, current_pieces))
            return solution_sequence
        except StopIteration:
            # no solution is found
            return None

    def solve(self):
        if self.solution:
            next_move = self.solution.pop(0)
            return next_move
        else:
            self.solution = self.get_solution()
            next_move = self.solution.pop(0)
            return next_move