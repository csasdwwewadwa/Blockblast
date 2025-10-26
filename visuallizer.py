import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

import pygame
import sys
import math
from game import BlockBlast

class BlockBlastVisuallized(BlockBlast):
    def __init__(self, board_size: tuple[int, int] = (8, 8), seed: int = None, is_guranteed_valid_moves = True):
        super().__init__(board_size, seed, is_guranteed_valid_moves)

        pygame.init()

        # UI constants
        self.cell_size = 50
        self.margin = 10
        self.tray_scale_factor = 0.5
        self.block_padding = 2
        self.hud_top_offset = 120

        # Screen Dimensions
        board_pixel_width = self.width * self.cell_size
        board_pixel_height = self.height * self.cell_size
        pieces_panel_width = int(5 * self.cell_size)
        window_width = board_pixel_width + pieces_panel_width + 3 * self.margin
        window_height = board_pixel_height + 2 * self.margin

        self.screen = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption("Block Blast")

        # Colors
        self.colors = {
            "background": (20, 30, 40), "grid": (40, 60, 80),
            "block": (0, 150, 255), "ghost": (0, 150, 255, 100),
            "text": (255, 255, 255), "game_over": (255, 0, 0),
            "combo_text": (255, 223, 0),
            "score_increment": (100, 255, 100)
        }
        
        # Fonts
        try:
            self.score_font = pygame.font.SysFont('comicsansms', 30)
            self.combo_font = pygame.font.SysFont('comicsansms', 22)
            self.increment_font = pygame.font.SysFont('comicsansms', 22, bold=True)
        except pygame.error:
            self.score_font = pygame.font.Font(None, 36)
            self.combo_font = pygame.font.Font(None, 28)
            self.increment_font = pygame.font.Font(None, 28)

        self.game_over_font = pygame.font.Font(None, 72)
        
        # UI State & HUD
        self.ui_state = 'IDLE'
        self.piece_tray_rects = {}
        self.last_score_increment = 0
        self.score_increment_alpha = 0
        
        # Dragging and Animation
        self.drag_info = {}
        self.animation = {}
        
        # Bot control
        self.autoplay = False
    
    # Overriding make_move to capture the score change for the HUD
    def make_move(self, piece_name: str, position: tuple[int, int]) -> dict:
        score_before = self.score
        result = super().make_move(piece_name, position)
        
        if result.get("status") == "success":
            score_after = self.score
            increment = score_after - score_before
            if increment > 0:
                self.last_score_increment = increment
                self.score_increment_alpha = 255
        
        return result

    def _create_piece_surface(self, piece_name, cell_size, padding):
        """Helper to create a surface for a given piece."""
        piece_w, piece_h = self.name_to_size[piece_name]
        surface = pygame.Surface((piece_w * cell_size, piece_h * cell_size), pygame.SRCALPHA)
        piece_mask = self.name_to_pieces[piece_name]
        
        for r in range(piece_h):
            for c in range(piece_w):
                if (piece_mask >> (r * piece_w + c)) & 1:
                    rect = pygame.Rect(c * cell_size + padding, r * cell_size + padding,
                                      cell_size - 2 * padding, cell_size - 2 * padding)
                    pygame.draw.rect(surface, self.colors["block"], rect, border_radius=3)
        return surface

    def draw_board(self):
        """Renders the game board with borders around the blocks."""
        self.screen.fill(self.colors["background"])
        
        for r in range(self.height):
            for c in range(self.width):
                rect = pygame.Rect(self.margin + c * self.cell_size, self.margin + r * self.cell_size,
                                  self.cell_size, self.cell_size)
                is_filled = (self.board >> (r * self.width + c)) & 1
                color = self.colors["grid"]
                pygame.draw.rect(self.screen, color, rect)
                if is_filled:
                    block_rect = rect.inflate(-self.block_padding * 2, -self.block_padding * 2)
                    pygame.draw.rect(self.screen, self.colors["block"], block_rect, border_radius=3)
    
    def draw_hud(self):
        """Renders the full HUD: Score, Score Increment, and Combo."""
        panel_x_start = self.width * self.cell_size + 2 * self.margin
        panel_center_x = panel_x_start + (self.screen.get_width() - panel_x_start) / 2

        score_surface = self.score_font.render(f"Score: {self.score}", True, self.colors["text"])
        score_rect = score_surface.get_rect(center=(panel_center_x, 40))
        self.screen.blit(score_surface, score_rect)

        if self.score_increment_alpha > 0:
            increment_surface = self.increment_font.render(f"+{self.last_score_increment}", True, self.colors["score_increment"])
            increment_surface.set_alpha(self.score_increment_alpha)
            increment_rect = increment_surface.get_rect(center=(panel_center_x, 70))
            self.screen.blit(increment_surface, increment_rect)

        combo_text = f"Combo: {self.combo + 1}x"
        combo_color = self.colors["combo_text"] if self.combo > 0 else self.colors["text"]
        combo_surface = self.combo_font.render(combo_text, True, combo_color)
        combo_rect = combo_surface.get_rect(center=(panel_center_x, 95))
        self.screen.blit(combo_surface, combo_rect)


    def draw_pieces_in_tray(self):
        """Renders available pieces below the HUD."""
        self.piece_tray_rects.clear()
        
        tray_x_start = self.width * self.cell_size + 2 * self.margin
        available_height = self.screen.get_height() - self.hud_top_offset
        slot_height = available_height / 3
        tray_cell_size = int(self.cell_size * self.tray_scale_factor)

        for i, piece_name in enumerate(self.current_pieces):
            if self.ui_state != 'IDLE' and self.drag_info.get('name') == piece_name:
                continue

            surface = self._create_piece_surface(piece_name, tray_cell_size, self.block_padding / 2)
            
            slot_center_y = self.hud_top_offset + (i * slot_height) + (slot_height / 2)
            piece_y = slot_center_y - surface.get_height() / 2
            slot_center_x = tray_x_start + (self.screen.get_width() - tray_x_start) / 2
            piece_x = slot_center_x - surface.get_width() / 2
            
            self.piece_tray_rects[piece_name] = self.screen.blit(surface, (piece_x, piece_y))

    def draw_ghost_piece(self, piece_name, grid_pos):
        """Draws a semi-transparent preview with borders."""
        px, py = grid_pos
        if self.is_valid_move(self.board, piece_name, (px, py)):
            piece_w, piece_h = self.name_to_size[piece_name]
            for r in range(piece_h):
                for c in range(piece_w):
                    if (self.name_to_pieces[piece_name] >> (r * piece_w + c)) & 1:
                        rect = pygame.Rect(self.margin + (c + px) * self.cell_size,
                                           self.margin + (r + py) * self.cell_size,
                                           self.cell_size, self.cell_size)
                        block_rect = rect.inflate(-self.block_padding * 2, -self.block_padding * 2)
                        
                        s = pygame.Surface(block_rect.size, pygame.SRCALPHA)
                        pygame.draw.rect(s, self.colors["ghost"], s.get_rect(), border_radius=3)
                        self.screen.blit(s, block_rect.topleft)

    def handle_input(self):
        """Manages user input, starting animations but not during them."""
        if self.ui_state not in ['IDLE', 'DRAGGING']: return

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(), sys.exit()

            if self.game_over: continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.ui_state == 'IDLE':
                for piece_name, rect in self.piece_tray_rects.items():
                    if rect.collidepoint(event.pos):
                        self.ui_state = 'ANIMATING_PICKUP'
                        self.drag_info = {
                            'name': piece_name,
                            'surface': self._create_piece_surface(piece_name, self.cell_size, self.block_padding),
                            'tray_rect': rect, 'offset': (event.pos[0] - rect.x, event.pos[1] - rect.y)
                        }
                        self.animation = {'start_time': pygame.time.get_ticks(), 'duration': 150,
                                          'start_pos': rect.topleft, 'start_scale': self.tray_scale_factor}
                        break
            
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.ui_state == 'DRAGGING':
                mouse_pos = event.pos
                scaled_offset = (self.drag_info['offset'][0] / self.tray_scale_factor, self.drag_info['offset'][1] / self.tray_scale_factor)
                top_left_pos = (mouse_pos[0] - scaled_offset[0], mouse_pos[1] - scaled_offset[1])
                grid_pos = (round((top_left_pos[0] - self.margin) / self.cell_size),
                            round((top_left_pos[1] - self.margin) / self.cell_size))
                
                self.ui_state = 'ANIMATING_DROP'
                is_valid = self.is_valid_move(self.board, self.drag_info['name'], grid_pos)
                self.animation = {
                    'start_time': pygame.time.get_ticks(), 'duration': 150 if is_valid else 250,
                    'start_pos': top_left_pos, 'end_pos': (self.margin + grid_pos[0] * self.cell_size, self.margin + grid_pos[1] * self.cell_size),
                    'target_grid_pos': grid_pos, 'is_valid': is_valid
                }

    def update(self):
        """Handles all per-frame state updates, like animations and fades."""
        if self.score_increment_alpha > 0:
            self.score_increment_alpha = max(0, self.score_increment_alpha - 4)

        if self.ui_state in ['ANIMATING_PICKUP', 'ANIMATING_DROP']:
            self._update_piece_animations()


    def _update_piece_animations(self):
        """Calculates and draws the current frame of any active piece animation."""
        if not self.animation: return
        
        now = pygame.time.get_ticks()
        progress = min((now - self.animation['start_time']) / self.animation['duration'], 1.0)
        eased_progress = math.sin(progress * math.pi / 2)

        if self.ui_state == 'ANIMATING_PICKUP':
            current_scale = self.animation['start_scale'] + (1.0 - self.animation['start_scale']) * eased_progress
            mouse_pos = pygame.mouse.get_pos()
            print(pygame.mouse.get_pos())
            scaled_offset = (self.drag_info['offset'][0] * (current_scale / self.tray_scale_factor),
                             self.drag_info['offset'][1] * (current_scale / self.tray_scale_factor))
            end_pos = (mouse_pos[0] - scaled_offset[0], mouse_pos[1] - scaled_offset[1])
            start_pos = self.animation['start_pos']
            current_pos = (start_pos[0] + (end_pos[0] - start_pos[0]) * eased_progress,
                           start_pos[1] + (end_pos[1] - start_pos[1]) * eased_progress)

            w, h = self.drag_info['surface'].get_size()
            scaled_surface = pygame.transform.smoothscale(self.drag_info['surface'], (int(w * current_scale), int(h * current_scale)))
            self.screen.blit(scaled_surface, current_pos)
            
            if progress >= 1.0:
                self.ui_state = 'DRAGGING'
                self.animation = {}

        elif self.ui_state == 'ANIMATING_DROP':
            start_pos = self.animation['start_pos']
            end_pos = self.animation['end_pos'] if self.animation['is_valid'] else self.drag_info['tray_rect'].topleft
            current_pos = (start_pos[0] + (end_pos[0] - start_pos[0]) * eased_progress,
                           start_pos[1] + (end_pos[1] - start_pos[1]) * eased_progress)

            current_scale = 1.0 - (1.0 - self.tray_scale_factor) * eased_progress if not self.animation['is_valid'] else 1.0
            w, h = self.drag_info['surface'].get_size()
            scaled_surface = pygame.transform.smoothscale(self.drag_info['surface'], (int(w * current_scale), int(h * current_scale)))
            self.screen.blit(scaled_surface, current_pos)

            if progress >= 1.0:
                if self.animation['is_valid']:
                    self.make_move(self.drag_info['name'], self.animation['target_grid_pos'])
                self.ui_state = 'IDLE'
                self.animation = {}
                self.drag_info = {}

    def run(self):
        """Main game loop for manual play."""
        clock = pygame.time.Clock()
        while True:
            self.handle_input()
            self.update()
            
            self.draw_board()
            self.draw_hud()
            self.draw_pieces_in_tray()

            if self.ui_state == 'DRAGGING':
                mouse_pos = pygame.mouse.get_pos()
                scaled_offset = (self.drag_info['offset'][0] / self.tray_scale_factor, self.drag_info['offset'][1] / self.tray_scale_factor)
                top_left = (mouse_pos[0] - scaled_offset[0], mouse_pos[1] - scaled_offset[1])
                grid_pos = (round((top_left[0] - self.margin) / self.cell_size), round((top_left[1] - self.margin) / self.cell_size))

                self.draw_ghost_piece(self.drag_info['name'], grid_pos)
                self.screen.blit(self.drag_info['surface'], top_left)
            
            if self.ui_state in ['ANIMATING_PICKUP', 'ANIMATING_DROP']:
                self._update_piece_animations()


            if self.game_over:
                text = self.game_over_font.render("GAME OVER", True, self.colors["game_over"])
                text_rect = text.get_rect(center=(
                    (self.width * self.cell_size + 2 * self.margin) / 2, self.screen.get_height() / 2))
                self.screen.blit(text, text_rect)

            pygame.display.flip()
            clock.tick(60)

    def run_bot_play(self, bot):
        """
        Main game loop for bot-controlled play.
        - Press 'P' to play a single move from the bot.
        - Press 'Q' to toggle autoplay, making the bot play continuously.
        """
        clock = pygame.time.Clock()
        self.autoplay = False

        while True:
            # --- Event Handling for Bot Control ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self.autoplay = not self.autoplay
                        print(f"Autoplay turned {'ON' if self.autoplay else 'OFF'}")
                    
                    if event.key == pygame.K_p and not self.autoplay:
                        if self.ui_state == 'IDLE' and not self.game_over:
                            piece, position = bot(self)
                            if piece and position is not None:
                                self.make_move(piece, position)

            # --- Autoplay Logic ---
            if self.autoplay and self.ui_state == 'IDLE' and not self.game_over:
                piece, position = bot(self)
                if piece and position is not None:
                    self.make_move(piece, position)
            
            # --- Standard Game Updates and Drawing ---
            self.update()
            
            self.draw_board()
            self.draw_hud()
            self.draw_pieces_in_tray()

            if self.game_over:
                text = self.game_over_font.render("GAME OVER", True, self.colors["game_over"])
                text_rect = text.get_rect(center=(
                    (self.width * self.cell_size + 2 * self.margin) / 2, self.screen.get_height() / 2))
                self.screen.blit(text, text_rect)

            pygame.display.flip()
            clock.tick(60)


if __name__ == '__main__':
    from bots.simple import Solver

    solver = None
    solution = []

    def bot(game):
        global solver, solution
        if not solver:
            solver = Solver(game)
        return solver.solve()

    game = BlockBlastVisuallized(board_size=(8, 8), seed=42)
    # game.run_bot_play(bot)
    game.run()
