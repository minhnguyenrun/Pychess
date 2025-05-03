# --- START OF FILE main.py ---

import random
import math
import pygame
import time

from chess_visualizer import ChessVisualizer
from minimax_ai import ChessAI # Import the updated AI
from game_state import GameState, Move # Import GameState and Move

# --- Helper Functions ---
def random_move(game: GameState):
    """Selects a random valid move."""
    # Get valid moves for the current player
    # Need to ensure get_valid_moves doesn't modify state permanently if called here
    # It should be safe as it simulates and undos.
    moves = game.get_valid_moves()

    print("\n=== RANDOM AGENT MOVE SELECTION ===")
    # print_board(game.board) # Use AI's print board or visualizer

    if not moves:
        print("No valid moves available!")
        print("=== RANDOM AGENT MOVE SELECTION END ===\n")
        return None

    # Log available capture moves
    capture_moves = [m for m in moves if m.piece_captured != '--']
    if capture_moves:
        print(f"Available capture moves ({len(capture_moves)}):")
        # for m in capture_moves: print(f"- {m.get_notation()} captures {m.piece_captured}")

    # Make the random selection
    selected_move = random.choice(moves)

    print(f"Selected random move: {selected_move.get_notation()}")
    print("=== RANDOM AGENT MOVE SELECTION END ===\n")
    return selected_move

def print_board_simple(board):
    """Basic console print for debugging."""
    print("  a b c d e f g h")
    print(" +-----------------+")
    for r in range(8):
        print(f"{8-r}|", end=" ")
        for c in range(8):
            piece = board[r][c]
            if piece == '--': print(".", end=" ")
            else: print(piece[1].upper() if piece[0]=='w' else piece[1].lower(), end=" ")
        print(f"|{8-r}")
    print(" +-----------------+")
    print("  a b c d e f g h")

def play_game(mode, ai_depth, visualizer, player_wants_black=False):
    """Main function to run a single game."""
    game = GameState(player_wants_black=player_wants_black)
    ai = None
    ai_color = None

    # Setup AI if needed
    if "ai" in mode:
        # Determine AI color based on player choice
        ai_color = 'b' if not player_wants_black else 'w'
        ai = ChessAI(game, ai_depth, ai_color)
        print(f"AI initialized as {'Black' if ai_color == 'b' else 'White'}.")

    selected_square = ()  # Keep track of (row, col) of the selected piece
    player_clicks = []    # Keep track of player clicks (max 2) [(row, col), (row, col)]
    valid_moves_for_selected_piece = [] # Store moves for highlight
    animating_piece = None # (start_pos, end_pos, piece_code, progress)
    running = True
    game_over = False
    result = None # 'white', 'black', 'draw', or 'quit' # Added 'quit'

    # Initial draw
    visualizer.draw_board(game)
    pygame.display.flip()

    while running:
        # Determine whose turn it is and if it's a human player
        is_human_turn = False
        if mode == "player_vs_player":
            is_human_turn = True
        elif mode == "player_vs_ai":
            is_human_turn = (game.white_to_move and not player_wants_black) or \
                            (not game.white_to_move and player_wants_black)

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                result = 'quit' # Indicate game quit explicitly
                game_over = True # Ensure loop terminates cleanly
            elif event.type == pygame.MOUSEMOTION and not game_over:
                 # Basic hover effect can be added here if desired
                 pass
            # --- Human Player Move Logic ---
            elif event.type == pygame.MOUSEBUTTONDOWN and is_human_turn and not game_over:
                x, y = event.pos
                if x < visualizer.BOARD_WIDTH: # Click is on the board
                    col = x // visualizer.SQUARE_SIZE
                    row = y // visualizer.SQUARE_SIZE
                    clicked_square = (row, col)

                    if selected_square == clicked_square: # Clicked same square twice
                        selected_square = () # Deselect
                        player_clicks = []
                        valid_moves_for_selected_piece = []
                    elif not selected_square: # First click - selecting a piece
                        piece = game.board[row][col]
                        # Check if it's a valid piece for the current player
                        if piece != '--' and \
                           ((piece[0] == 'w' and game.white_to_move) or \
                            (piece[0] == 'b' and not game.white_to_move)):
                            selected_square = clicked_square
                            player_clicks.append(selected_square)
                            # Generate valid moves for highlighting
                            all_valid_moves = game.get_valid_moves() # Get all valid moves
                            valid_moves_for_selected_piece = [
                                m for m in all_valid_moves
                                if m.start_row == row and m.start_col == col
                            ]
                            if not valid_moves_for_selected_piece: # No valid moves for this piece
                                selected_square = () # Deselect
                                player_clicks = []
                        else:
                            selected_square = ()
                            player_clicks = []
                    else: # Second click - attempting to move
                        player_clicks.append(clicked_square)
                        # Check if this click corresponds to a valid move end square
                        move_to_make = None
                        for move in valid_moves_for_selected_piece:
                            if move.end_row == row and move.end_col == col:
                                move_to_make = move
                                break

                        if move_to_make:
                             print(f"Player move: {move_to_make.get_notation()}")
                             # Start animation
                             start_pos = (selected_square[1] * visualizer.SQUARE_SIZE, selected_square[0] * visualizer.SQUARE_SIZE)
                             end_pos = (col * visualizer.SQUARE_SIZE, row * visualizer.SQUARE_SIZE)
                             animating_piece = (start_pos, end_pos, move_to_make.piece_moved, 0)
                             # Make the move on the board AFTER setting up animation
                             game.make_move(move_to_make)
                             # Reset selection
                             selected_square = ()
                             player_clicks = []
                             valid_moves_for_selected_piece = []
                        else:
                             # Invalid second click, treat as new selection if possible
                             selected_square = ()
                             player_clicks = []
                             valid_moves_for_selected_piece = []
                             # Try selecting the newly clicked square if it's a valid piece
                             piece = game.board[row][col]
                             if piece != '--' and \
                                ((piece[0] == 'w' and game.white_to_move) or \
                                 (piece[0] == 'b' and not game.white_to_move)):
                                 selected_square = clicked_square
                                 player_clicks.append(selected_square)
                                 all_valid_moves = game.get_valid_moves()
                                 valid_moves_for_selected_piece = [
                                     m for m in all_valid_moves
                                     if m.start_row == row and m.start_col == col
                                 ]
                                 if not valid_moves_for_selected_piece:
                                     selected_square = ()
                                     player_clicks = []


            # --- Mouse Wheel (Optional: Move History Scroll) ---
            # elif event.type == pygame.MOUSEWHEEL:
            #     visualizer.move_scroll_offset -= event.y
            #     # Add bounds checking for scroll offset based on move_log length

        # --- Animation Handling ---
        if animating_piece:
            start_pos, end_pos, piece_code, progress = animating_piece
            progress += 0.1 # Adjust animation speed here
            if progress >= 1:
                animating_piece = None # Animation finished
            else:
                animating_piece = (start_pos, end_pos, piece_code, progress)
            # Redraw board during animation
            visualizer.draw_board(game, selected_square, valid_moves_for_selected_piece, animating_piece)
            pygame.time.wait(20) # Small delay for smoother animation
            pygame.display.flip() # Update display during animation
            continue # Don't process AI move or game over check while animating

        # --- Check Game Over State ---
        # Check only if not already over and not animating
        if not game_over and not animating_piece:
            if game.checkmate or game.stalemate:
                game_over = True
                if game.checkmate:
                    result = 'black' if game.white_to_move else 'white'
                    print(f"Game Over: Checkmate - Winner: {result.capitalize()}")
                else: # Stalemate or other draw condition
                    result = 'draw'
                    draw_reason = "Stalemate"
                    if game.is_threefold_repetition(): draw_reason = "Threefold Repetition"
                    elif game.is_insufficient_material(): draw_reason = "Insufficient Material"
                    print(f"Game Over: Draw - Reason: {draw_reason}")

                # Draw final state ONCE
                visualizer.draw_board(game) # Draw final board state
                visualizer.draw_endgame_message(result)
                pygame.display.flip()

                # Wait for user input before exiting play_game
                wait_for_input = True
                while wait_for_input:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False
                            wait_for_input = False
                            result = 'quit' # Ensure quit signal propagates
                        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                            wait_for_input = False # Exit wait on any key/click
                    pygame.time.wait(50) # Prevent busy-waiting

                running = False # Stop the main game loop after user interaction

        # --- AI / Random Move Logic ---
        # Execute only if game is not over, it's not human turn, and not animating
        if not game_over and not is_human_turn and not animating_piece:
            move = None
            print(f"Processing turn for {'White' if game.white_to_move else 'Black'}")
            if mode == "player_vs_ai":
                print("AI is thinking...")
                move = ai.get_best_move() # Use iterative deepening by default
            elif mode == "ai_vs_random":
                if (game.white_to_move and ai.ai_player_color == 'w') or \
                   (not game.white_to_move and ai.ai_player_color == 'b'):
                    print("AI (Minimax) is thinking...")
                    move = ai.get_best_move()
                else:
                    print("Random Mover is thinking...")
                    move = random_move(game)

            if move:
                 print(f"Computer move: {move.get_notation()}")
                 # Start animation
                 start_pos = (move.start_col * visualizer.SQUARE_SIZE, move.start_row * visualizer.SQUARE_SIZE)
                 end_pos = (move.end_col * visualizer.SQUARE_SIZE, move.end_row * visualizer.SQUARE_SIZE)
                 animating_piece = (start_pos, end_pos, move.piece_moved, 0)
                 # Make the move AFTER setting up animation
                 game.make_move(move)
                 # Reset player selection state just in case
                 selected_square = ()
                 player_clicks = []
                 valid_moves_for_selected_piece = []
            elif not game.checkmate and not game.stalemate:
                 # This case indicates an issue if the game isn't over
                 print("ERROR: AI/Random failed to produce a move but game not over.")
                 # Potentially break or try again? For now, just log.

            # Add a small delay after AI move for better visualization
            # time.sleep(0.1) # Removed, animation handles pacing

        # --- Drawing the Board ---
        # Draw only if not animating and game not over (final draw handled in game over block)
        if not animating_piece and not game_over:
             visualizer.draw_board(game, selected_square, valid_moves_for_selected_piece)
             pygame.display.flip() # Update the display

    # --- End of Game Loop ---
    print("Exiting game loop.")
    # Removed time.sleep(5) - replaced by wait loop above
    return result # Return 'white', 'black', 'draw', or 'quit'

# ...existing code...
def main():
    visualizer = ChessVisualizer()
    while True:
        mode = None
        ai_depth = None
        player_color_choice = 'w' # Default player color for Player vs AI
        ai_color_choice = 'b'     # Default AI color for AI vs Random (AI plays Black)

        buttons = visualizer.draw_menu()
        # --- Mode Selection Menu ---
        menu_running = True
        while menu_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    visualizer.close()
                    return
                if event.type == pygame.MOUSEMOTION:
                    x, y = event.pos
                    # Hover effect (optional)
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                    for button in buttons:
                        if button.collidepoint(x, y):
                            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                            break
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    for i, button in enumerate(buttons):
                        if button.collidepoint(x, y):
                            modes = ["player_vs_player", "player_vs_ai", "ai_vs_random", "exit"]
                            mode = modes[i]
                            menu_running = False # Exit menu loop
                            break
            pygame.display.flip() # Update display during menu loop

        if mode == "exit":
            break

        # --- AI Difficulty / Color Selection ---
        if "ai" in mode:
             # Difficulty Selection (Common for both AI modes)
             option_buttons = visualizer.draw_option_menu() # Assuming this draws Easy/Medium/Hard
             option_selected = False
             while not option_selected:
                 for event in pygame.event.get():
                     if event.type == pygame.QUIT: visualizer.close(); return
                     if event.type == pygame.MOUSEMOTION:
                         x, y = event.pos
                         pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                         for button in option_buttons:
                             if button.collidepoint(x, y): pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND); break
                     if event.type == pygame.MOUSEBUTTONDOWN:
                         x, y = event.pos
                         depths = [2, 3, 4] # Easy, Medium, Hard depth
                         for i, button in enumerate(option_buttons):
                             if button.collidepoint(x, y):
                                 ai_depth = depths[i]
                                 option_selected = True
                                 break
                 pygame.display.flip()

             # Color Selection (Specific to mode)
             if mode == "player_vs_ai":
                 # Player chooses their color
                 color_buttons = visualizer.draw_color_menu() # Assuming draws White/Black for player
                 color_selected = False
                 while not color_selected:
                     for event in pygame.event.get():
                          if event.type == pygame.QUIT: visualizer.close(); return
                          if event.type == pygame.MOUSEMOTION:
                              x, y = event.pos
                              pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                              for button in color_buttons:
                                  if button.collidepoint(x, y): pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND); break
                          if event.type == pygame.MOUSEBUTTONDOWN:
                              x, y = event.pos
                              colors = ['w', 'b']
                              for i, button in enumerate(color_buttons):
                                  if button.collidepoint(x, y):
                                      player_color_choice = colors[i]
                                      color_selected = True
                                      break
                     pygame.display.flip()
                 # Determine player_wants_black for play_game based on player's choice
                 player_wants_black_flag = (player_color_choice == 'b')

             elif mode == "ai_vs_random":
                 # User chooses the AI's color
                 # Reuse draw_color_menu, maybe add title "AI Plays As:" in visualizer if needed
                 color_buttons = visualizer.draw_color_menu("AI Plays As:")
                 color_selected = False
                 while not color_selected:
                     for event in pygame.event.get():
                          if event.type == pygame.QUIT: visualizer.close(); return
                          if event.type == pygame.MOUSEMOTION:
                              x, y = event.pos
                              pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                              for button in color_buttons:
                                  if button.collidepoint(x, y): pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND); break
                          if event.type == pygame.MOUSEBUTTONDOWN:
                              x, y = event.pos
                              colors = ['w', 'b'] # AI plays White, AI plays Black
                              for i, button in enumerate(color_buttons):
                                  if button.collidepoint(x, y):
                                      ai_color_choice = colors[i]
                                      color_selected = True
                                      break
                     pygame.display.flip()
                 # Determine player_wants_black for play_game based on AI's choice
                 # If AI is White, the 'player' (Random) wants Black.
                 player_wants_black_flag = (ai_color_choice == 'w')

        # --- Start Game ---
        # For player_vs_player, player_wants_black_flag is not set, defaults to False (Player 1 is White)
        # Consider adding color choice for PvP if desired later.
        if mode != "player_vs_player":
            print(f"Starting Game: Mode={mode}, AI Depth={ai_depth}, "
                  f"{'Player Color' if mode == 'player_vs_ai' else 'AI Color'}="
                  f"{player_color_choice if mode == 'player_vs_ai' else ai_color_choice}")
        else:
             print(f"Starting Game: Mode={mode}")

        # Pass the correctly determined flag to play_game
        result = play_game(mode, ai_depth, visualizer, player_wants_black=player_wants_black_flag if "ai" in mode else False)


        if result == 'quit': # Check for explicit quit signal
            print("Game quit.")
            break # Exit the main loop if game was quit
        elif result is not None: # Game finished normally
            print(f"Game Result: {'White wins' if result == 'white' else 'Black wins' if result == 'black' else 'Draw'}")
            print("Returning to main menu...")
            time.sleep(1) # Short pause before showing menu again
        # If result is None (shouldn't happen unless play_game has issues), loop continues

    visualizer.close()


if __name__ == "__main__":
    main()
