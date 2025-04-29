import random
import math
import pygame
import time

class ChessVisualizer:
    def __init__(self):
        pygame.init()
        self.SQUARE_SIZE = 80
        self.BOARD_WIDTH = 8 * self.SQUARE_SIZE
        self.PANEL_WIDTH = 300
        self.HEIGHT = 8 * self.SQUARE_SIZE
        self.WIDTH = self.BOARD_WIDTH + self.PANEL_WIDTH
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Chess Game")
        self.colors = [(245, 245, 220), (139, 69, 19)]
        self.highlight_color = (255, 255, 0, 100)  # Yellow with transparency
        self.check_color = (255, 0, 0)  # Red for king in check
        self.piece_images = {
            'wp': pygame.transform.scale(pygame.image.load("images/chess-pawn-white.png"), (self.SQUARE_SIZE, self.SQUARE_SIZE)),
            'wn': pygame.transform.scale(pygame.image.load("images/chess-knight-white.png"), (self.SQUARE_SIZE, self.SQUARE_SIZE)),
            'wb': pygame.transform.scale(pygame.image.load("images/chess-bishop-white.png"), (self.SQUARE_SIZE, self.SQUARE_SIZE)),
            'wr': pygame.transform.scale(pygame.image.load("images/chess-rook-white.png"), (self.SQUARE_SIZE, self.SQUARE_SIZE)),
            'wq': pygame.transform.scale(pygame.image.load("images/chess-queen-white.png"), (self.SQUARE_SIZE, self.SQUARE_SIZE)),
            'wk': pygame.transform.scale(pygame.image.load("images/chess-king-white.png"), (self.SQUARE_SIZE, self.SQUARE_SIZE)),
            'bp': pygame.transform.scale(pygame.image.load("images/chess-pawn-black.png"), (self.SQUARE_SIZE, self.SQUARE_SIZE)),
            'bn': pygame.transform.scale(pygame.image.load("images/chess-knight-black.png"), (self.SQUARE_SIZE, self.SQUARE_SIZE)),
            'bb': pygame.transform.scale(pygame.image.load("images/chess-bishop-black.png"), (self.SQUARE_SIZE, self.SQUARE_SIZE)),
            'br': pygame.transform.scale(pygame.image.load("images/chess-rook-black.png"), (self.SQUARE_SIZE, self.SQUARE_SIZE)),
            'bq': pygame.transform.scale(pygame.image.load("images/chess-queen-black.png"), (self.SQUARE_SIZE, self.SQUARE_SIZE)),
            'bk': pygame.transform.scale(pygame.image.load("images/chess-king-black.png"), (self.SQUARE_SIZE, self.SQUARE_SIZE))
        }
        self.font = pygame.font.SysFont("Arial", 20)
        self.small_piece_images = {k: pygame.transform.scale(v, (30, 30)) for k, v in self.piece_images.items()}
        self.colors = [(245, 245, 220), (139, 69, 19)]
        self.highlight_color = (255, 255, 0, 100)
        self.check_color = (255, 0, 0)
        self.panel_bg_color = (220, 220, 220)  # Light grey for panel
        self.button_colors = [(100, 200, 100), (200, 100, 100), (100, 100, 200)]  # Green, Red, Blue
        self.font = pygame.font.SysFont("Arial", 24)
        self.small_piece_images = {k: pygame.transform.scale(v, (30, 30)) for k, v in self.piece_images.items()}
        self.move_scroll_offset = 0  # For scrolling move list
        self.big_font = pygame.font.SysFont("Arial", 60, bold=True)


    def draw_board(self, game, selected_piece=None, valid_moves=[], animating_piece=None):
        # Draw chessboard
        for r in range(8):
            for c in range(8):
                color = self.colors[(r + c) % 2]
                pygame.draw.rect(self.screen, color, (c * self.SQUARE_SIZE, r * self.SQUARE_SIZE, self.SQUARE_SIZE, self.SQUARE_SIZE))

        # Highlight king in checkmate (losing side)
        if game.checkmate:
            king_loc = game.white_king_location if not game.white_to_move else game.black_king_location
            if king_loc:
                pygame.draw.rect(self.screen, self.check_color, (king_loc[1] * self.SQUARE_SIZE, king_loc[0] * self.SQUARE_SIZE, self.SQUARE_SIZE, self.SQUARE_SIZE), 4)

        # Highlight selected piece and valid moves
        if selected_piece:
            r, c = selected_piece
            pygame.draw.rect(self.screen, self.highlight_color, (c * self.SQUARE_SIZE, r * self.SQUARE_SIZE, self.SQUARE_SIZE, self.SQUARE_SIZE), 4)
            for move in valid_moves:
                if move.start_row == r and move.start_col == c:
                    pygame.draw.circle(self.screen, self.highlight_color, 
                                    (move.end_col * self.SQUARE_SIZE + self.SQUARE_SIZE // 2, 
                                        move.end_row * self.SQUARE_SIZE + self.SQUARE_SIZE // 2), 10)

        # Draw all pieces except the animating one
        for r in range(8):
            for c in range(8):
                piece = game.board[r][c]
                if piece != "--" and piece in self.piece_images:
                    # Skip drawing the animating piece at its final position until animation completes
                    if not animating_piece or (r, c) != (animating_piece[1][1] // self.SQUARE_SIZE, animating_piece[1][0] // self.SQUARE_SIZE):
                        self.screen.blit(self.piece_images[piece], (c * self.SQUARE_SIZE, r * self.SQUARE_SIZE))

        # Draw animating piece if present
        if animating_piece:
            start_pos, end_pos, piece, progress = animating_piece
            x = start_pos[0] + (end_pos[0] - start_pos[0]) * progress
            y = start_pos[1] + (end_pos[1] - start_pos[1]) * progress
            self.screen.blit(self.piece_images[piece], (x, y))

        # Draw panel
        pygame.draw.rect(self.screen, self.panel_bg_color, (self.BOARD_WIDTH, 0, self.PANEL_WIDTH, self.HEIGHT))
        
        # Move history with scrolling
        white_moves = [m.get_notation() for m in game.move_log if m.piece_moved[0] == 'w']
        black_moves = [m.get_notation() for m in game.move_log if m.piece_moved[0] == 'b']
        self.screen.blit(self.font.render("Move History", True, (0, 0, 0)), (self.BOARD_WIDTH + 10, 10))
        max_moves_display = 10  # Limit visible moves to avoid overlap
        for i in range(max_moves_display):
            idx = i + self.move_scroll_offset
            if idx < len(white_moves):
                w = white_moves[idx]
                b = black_moves[idx] if idx < len(black_moves) else ''
                self.screen.blit(self.font.render(f"{idx+1}. {w} {b}", True, (0, 0, 0)), 
                                (self.BOARD_WIDTH + 10, 40 + i * 25))

        # Captured pieces (fixed position below move list)
        captured_white = [m.piece_captured for m in game.move_log if m.piece_captured[0] == 'w' and m.piece_captured != '--']
        captured_black = [m.piece_captured for m in game.move_log if m.piece_captured[0] == 'b' and m.piece_captured != '--']
        self.screen.blit(self.font.render("Captured White", True, (0, 0, 0)), (self.BOARD_WIDTH + 10, 300))
        for i, piece in enumerate(captured_white[:8]):  # Limit to 8 to fit
            self.screen.blit(self.small_piece_images[piece], (self.BOARD_WIDTH + 10 + i * 35, 330))
        self.screen.blit(self.font.render("Captured Black", True, (0, 0, 0)), (self.BOARD_WIDTH + 10, 370))
        for i, piece in enumerate(captured_black[:8]):
            self.screen.blit(self.small_piece_images[piece], (self.BOARD_WIDTH + 10 + i * 35, 400))

        pygame.display.flip()

    
    def draw_menu(self):
        self.screen.fill((240, 240, 240))
        options = ["Player vs Player", "Player vs AI", "AI vs Random"]
        buttons = []
        for i, option in enumerate(options):
            text = self.font.render(option, True, (0, 0, 0))
            rect = pygame.Rect(self.WIDTH // 2 - 150, 200 + i * 100, 300, 80)
            pygame.draw.rect(self.screen, self.button_colors[i], rect)
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)
            buttons.append(rect)
        pygame.display.flip()
        return buttons
    
    def draw_color_menu(self):
        self.screen.fill((240, 240, 240))
        options = ["Play as White", "Play as Black"]
        buttons = []
        colors = [(255, 255, 255), (50, 50, 50)]
        for i, option in enumerate(options):
            text = self.font.render(option, True, (0, 0, 0))
            rect = pygame.Rect(self.WIDTH // 2 - 150, 300 + i * 100, 300, 80)
            pygame.draw.rect(self.screen, colors[i], rect)
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)
            buttons.append(rect)
        pygame.display.flip()
        return buttons
    
    def draw_endgame_message(self, result):
        message = "White Wins!" if result == 'white' else "Black Wins!" if result == 'black' else "Draw!"
        text = self.big_font.render(message, True, (255, 0, 0))  # Red bold text
        text_rect = text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
        # Semi-transparent background for contrast
        bg_surface = pygame.Surface((text_rect.width + 20, text_rect.height + 20), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 150))  # Black with 150 alpha
        self.screen.blit(bg_surface, (text_rect.x - 10, text_rect.y - 10))
        self.screen.blit(text, text_rect)

    def close(self):
        pygame.quit()
