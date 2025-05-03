import random
import math
import pygame
import time

from chess_visualizer import ChessVisualizer
from minimax_ai import ChessAI, MinimaxGameState
from game_state import GameState

# def random_move(game):
#     moves = game.get_valid_moves()
#     return random.choice(moves) if moves else None

def random_move(game):
    moves = game.get_valid_moves()
    
    print("\n=== RANDOM AGENT MOVE SELECTION ===")
    print_board(game.board)  # Using a separate print_board function
    
    if not moves:
        print("No valid moves available!")
        print("=== RANDOM AGENT MOVE SELECTION END ===\n")
        return None
    
    # Check if the king is in check
    if game.in_check:
        print("KING IS IN CHECK - Prioritizing defensive moves")
        # Filter moves that get out of check
        check_escaping_moves = []
        
        for move in moves:
            # Try the move and see if it resolves check
            game.make_move(move)
            # After making the move, it's the other player's turn, so we need to switch perspective
            is_still_in_check = game.in_check  
            # Undo the move to restore the game state
            game.undo_move()
            
            if not is_still_in_check:
                check_escaping_moves.append(move)
        
        # If we found moves that escape check, use only those
        if check_escaping_moves:
            print(f"Found {len(check_escaping_moves)} moves that escape check")
            moves = check_escaping_moves
        else:
            print("WARNING: No moves escape check - this shouldn't happen!")
    
    # Log available capture moves
    capture_moves = [m for m in moves if m.piece_captured != '--']
    if capture_moves:
        print(f"Available capture moves ({len(capture_moves)}):")
        for m in capture_moves:
            piece = m.piece_moved
            target = m.piece_captured
            print(f"- {piece} {chr(97+m.start_col)}{8-m.start_row}->{chr(97+m.end_col)}{8-m.end_row} captures {target}")
    
    # Make the random selection
    selected_move = random.choice(moves)
    
    # Log the selected move
    move_str = f"{selected_move.piece_moved} {chr(97+selected_move.start_col)}{8-selected_move.start_row}->{chr(97+selected_move.end_col)}{8-selected_move.end_row}"
    if selected_move.piece_captured != '--':
        move_str += f" captures {selected_move.piece_captured}"
        
    print(f"\nSelected random move: {move_str}")
    print("=== RANDOM AGENT MOVE SELECTION END ===\n")
    
    return selected_move
# Helper function to print the board
def print_board(board):
    """Print a text representation of the board for debugging"""
    print("  a b c d e f g h")
    print(" +-----------------+")
    for r in range(8):
        print(f"{8-r}|", end=" ")
        for c in range(8):
            piece = board[r][c]
            if piece == '--':
                print(".", end=" ")
            else:
                # For white pieces use uppercase, for black lowercase
                char = piece[1]
                if piece[0] == 'w':  # White
                    char = char.upper()
                print(char, end=" ")
        print(f"|{8-r}")
    print(" +-----------------+")
    print("  a b c d e f g h")
    
def play_game(mode, ai_depth, visualizer, player_wants_black=False):
    game = GameState(player_wants_black=player_wants_black)
    selected_piece = None
    valid_moves = []
    animating_piece = None  # (start_pos, end_pos, piece, progress)

    visualizer.draw_board(game)
    time.sleep(1)

    while not (game.checkmate or game.stalemate):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                visualizer.close()
                return None
            if event.type == pygame.MOUSEMOTION:
                x, y = event.pos
                # Hand cursor for clickable pieces
                if x < visualizer.BOARD_WIDTH and not animating_piece:
                    col, row = x // visualizer.SQUARE_SIZE, y // visualizer.SQUARE_SIZE
                    if game.board[row][col] != '--' and game.board[row][col][0] == ('w' if game.white_to_move else 'b'):
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                    else:
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            if event.type == pygame.MOUSEBUTTONDOWN and (mode == "player_vs_player" or (mode == "player_vs_ai" and game.white_to_move == (not game.player_wants_black))):
                x, y = event.pos
                if x < visualizer.BOARD_WIDTH:
                    col, row = x // visualizer.SQUARE_SIZE, y // visualizer.SQUARE_SIZE
                    if selected_piece:
                        for move in valid_moves:
                            if move.start_row == selected_piece[0] and move.start_col == selected_piece[1] and move.end_row == row and move.end_col == col:
                                # Start animation
                                start_pos = (selected_piece[1] * visualizer.SQUARE_SIZE, selected_piece[0] * visualizer.SQUARE_SIZE)
                                end_pos = (col * visualizer.SQUARE_SIZE, row * visualizer.SQUARE_SIZE)
                                animating_piece = (start_pos, end_pos, move.piece_moved, 0)
                                game.make_move(move)
                                selected_piece = None
                                valid_moves = []
                                break
                        else:
                            selected_piece = None
                            valid_moves = []
                        visualizer.draw_board(game, selected_piece, valid_moves)
                    elif game.board[row][col] != '--' and game.board[row][col][0] == ('w' if game.white_to_move else 'b'):
                        selected_piece = (row, col)
                        valid_moves = game.get_valid_moves()
                        visualizer.draw_board(game, selected_piece, valid_moves)
            elif event.type == pygame.MOUSEWHEEL:
                #total_moves = len([m for m in game.move_log if m.piece_moved[0] == 'w'])
                #if total_moves > 10:
                    #visualizer.move_scroll_offset -= event.y
                    #visualizer.move_scroll_offset = max(0, min(visualizer.move_scroll_offset, total_moves - 10))
                visualizer.draw_board(game, selected_piece, valid_moves)

        # Handle piece animation
        if animating_piece:
            start_pos, end_pos, piece, progress = animating_piece
            progress += 0.05  # Adjust speed (lower = slower)
            if progress >= 1:
                animating_piece = None
            else:
                animating_piece = (start_pos, end_pos, piece, progress)
            visualizer.draw_board(game, selected_piece, valid_moves, animating_piece)
            pygame.time.wait(10)  # Small delay for smooth animation
        else:
            if game.checkmate or game.stalemate:
                break

            if mode == "player_vs_player":
                continue
            elif mode == "player_vs_ai" and game.white_to_move != (not game.player_wants_black):
                move = ChessAI(MinimaxGameState(game), ai_depth, 'w' if game.player_wants_black else 'b').get_best_move()
            elif mode == "ai_vs_random":
                move = ChessAI(MinimaxGameState(game), ai_depth, 'w' if game.player_wants_black else 'b').get_best_move() if game.white_to_move != (not game.player_wants_black) else random_move(game)
            else:
                continue

            if move:
                #print(f"{'AI' if mode != 'player_vs_player' else 'Random'} ({'white' if game.white_to_move else 'black'}) move: {move.get_notation()}")
                start_pos = (move.start_col * visualizer.SQUARE_SIZE, move.start_row * visualizer.SQUARE_SIZE)
                end_pos = (move.end_col * visualizer.SQUARE_SIZE, move.end_row * visualizer.SQUARE_SIZE)
                animating_piece = (start_pos, end_pos, move.piece_moved, 0)
                game.make_move(move)
                while animating_piece:
                    start_pos, end_pos, piece, progress = animating_piece
                    progress += 0.05
                    if progress >= 1:
                        animating_piece = None
                    else:
                        animating_piece = (start_pos, end_pos, piece, progress)
                    visualizer.draw_board(game, None, [], animating_piece)
                    pygame.time.wait(10)

    # Determine result and display endgame message
    if game.checkmate:
        result = 'white' if not game.white_to_move else 'black'
    else:
        result = 'draw'
    #print(f"Debug: checkmate={game.checkmate}, white_to_move={game.white_to_move}, result={result}")
    visualizer.draw_board(game)  # Final board state
    visualizer.draw_endgame_message(result)  # Overlay result
    pygame.display.flip()
    time.sleep(3)  # Show result for 3 seconds
    return result

def main():
    visualizer = ChessVisualizer()
    while True:
        mode = None
        buttons = visualizer.draw_menu()

        # Mode selection with hover
        while mode is None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    visualizer.close()
                    return
                if event.type == pygame.MOUSEMOTION:
                    x, y = event.pos
                    for button in buttons:
                        if button.collidepoint(x, y):
                            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                            break
                    else:
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    for i, button in enumerate(buttons):
                        if button.collidepoint(x, y):
                            mode = ["player_vs_player", "player_vs_ai", "ai_vs_random", "exit"][i]
                            break

        if mode == "exit":
            break

        if mode != "player_vs_player":
            ai_depth = None
            color_buttons = visualizer.draw_option_menu()
            while ai_depth is None:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        visualizer.close()
                        return
                    if event.type == pygame.MOUSEMOTION:
                        x, y = event.pos
                        for button in color_buttons:
                            if button.collidepoint(x, y):
                                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                                break
                        else:
                            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        x, y = event.pos
                        if color_buttons[0].collidepoint(x, y):
                            ai_depth = 2
                        elif color_buttons[1].collidepoint(x, y):
                            ai_depth = 3
                        else:
                            ai_depth = 10
            color = None
            color_buttons = visualizer.draw_color_menu()
            while color is None:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        visualizer.close()
                        return
                    if event.type == pygame.MOUSEMOTION:
                        x, y = event.pos
                        for button in color_buttons:
                            if button.collidepoint(x, y):
                                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                                break
                        else:
                            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        x, y = event.pos
                        if color_buttons[0].collidepoint(x, y):
                            color = 'w'
                        elif color_buttons[1].collidepoint(x, y):
                            color = 'b'
        else:
            color = 'w'
            ai_depth = None

        #ai_depth = 4 if "ai" in mode else None
        result = play_game(mode, ai_depth, visualizer, color == 'b')
        print(f"Game result: {'White wins' if result == 'white' else 'Black wins' if result == 'black' else 'Draw'}")
    visualizer.close()


if __name__ == "__main__":
    main()
