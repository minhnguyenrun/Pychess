import random
import math
import sys
import pygame
import time
import threading
from chess_visualizer import ChessVisualizer
from minimax_ai import ChessAI 
from game_state import GameState, Move 

def ai_thread_function(ai, use_iterative_deepening, max_time_seconds, result_container):
    """Run AI thinking in a separate thread"""
    try:
        move = ai.get_best_move(use_iterative_deepening=use_iterative_deepening, 
                              max_time_seconds=max_time_seconds)
        result_container['move'] = move
    except Exception as e:
        result_container['error'] = str(e)
        print(f"Error in AI thread: {e}")
    finally:
        result_container['done'] = True

def random_move(game: GameState):
    """Selects a random valid move."""
    moves = game.get_valid_moves()

    if not moves:
        return None

    selected_move = random.choice(moves)

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
    game = GameState(player_wants_black=player_wants_black)
    ai = None
    ai_color = None

    if "ai" in mode:
        ai_color = 'b' if not player_wants_black else 'w'
        ai = ChessAI(game, ai_depth, ai_color)

    selected_square = ()
    player_clicks = []
    valid_moves_for_selected_piece = []
    animating_piece = None
    running = True
    game_over = False
    result = None 

    awaiting_promotion_choice = False
    promotion_move_pending = None
    promotion_buttons = {}
    promotion_menu_pos = None

    visualizer.draw_board(game)
    pygame.display.flip()

    while running:
        is_human_turn = False
        if mode == "player_vs_player":
            is_human_turn = True
        elif mode == "player_vs_ai":
            is_human_turn = (game.white_to_move and not player_wants_black) or \
                            (not game.white_to_move and player_wants_black)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                result = 'quit'
                game_over = True 

            elif event.type == pygame.MOUSEBUTTONDOWN and awaiting_promotion_choice:
                x, y = event.pos
                chosen_piece = None
                for piece_type, rect in promotion_buttons.items():
                    if rect.collidepoint(x, y):
                        chosen_piece = piece_type
                        break
                if chosen_piece:
                    print(f"Promoting to: {chosen_piece.upper()}")

                    if promotion_move_pending and isinstance(promotion_move_pending, Move):
                        promotion_move_pending.promotion_choice = chosen_piece # Set the choice

                        start_pos = (promotion_move_pending.start_col * visualizer.SQUARE_SIZE, promotion_move_pending.start_row * visualizer.SQUARE_SIZE)
                        end_pos = (promotion_move_pending.end_col * visualizer.SQUARE_SIZE, promotion_move_pending.end_row * visualizer.SQUARE_SIZE)
                        animating_piece = (start_pos, end_pos, promotion_move_pending.piece_moved, 0)
                        game.make_move(promotion_move_pending) 

                        awaiting_promotion_choice = False
                        promotion_move_pending = None
                        promotion_buttons = {}
                        promotion_menu_pos = None
                    else:
                        print("Error: promotion_move_pending was not a valid Move object.")

                        awaiting_promotion_choice = False
                        promotion_move_pending = None
                        promotion_buttons = {}
                        promotion_menu_pos = None


            elif event.type == pygame.MOUSEBUTTONDOWN and is_human_turn and not game_over and not awaiting_promotion_choice:
                x, y = event.pos
                if x < visualizer.BOARD_WIDTH: 
                    col = x // visualizer.SQUARE_SIZE
                    row = y // visualizer.SQUARE_SIZE
                    clicked_square = (row, col)

                    if selected_square == clicked_square: 
                        selected_square = () 
                        player_clicks = []
                        valid_moves_for_selected_piece = []
                    elif not selected_square:
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
                        else:
                            selected_square = ()
                            player_clicks = []
                    else: 
                        player_clicks.append(clicked_square)
                        move_to_make = None
                        for move in valid_moves_for_selected_piece:
                            if move.end_row == row and move.end_col == col:
                                move_to_make = move
                                break

                        if move_to_make:
                            if move_to_make.is_pawn_promotion:
                                print("Pawn promotion! Choose piece.")
                                awaiting_promotion_choice = True
                                promotion_move_pending = move_to_make
                                promotion_menu_pos = (move_to_make.end_col * visualizer.SQUARE_SIZE, move_to_make.end_row * visualizer.SQUARE_SIZE)
                                selected_square = ()
                                player_clicks = []
                                valid_moves_for_selected_piece = []
                            else:
                                start_pos = (selected_square[1] * visualizer.SQUARE_SIZE, selected_square[0] * visualizer.SQUARE_SIZE)
                                end_pos = (col * visualizer.SQUARE_SIZE, row * visualizer.SQUARE_SIZE)
                                animating_piece = (start_pos, end_pos, move_to_make.piece_moved, 0)
                                game.make_move(move_to_make)
                                selected_square = ()
                                player_clicks = []
                                valid_moves_for_selected_piece = []
                        else:
                             selected_square = ()
                             player_clicks = []
                             valid_moves_for_selected_piece = []
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

        if animating_piece:
            start_pos, end_pos, piece_code, progress = animating_piece
            progress += 0.1
            if progress >= 1:
                animating_piece = None 
            else:
                animating_piece = (start_pos, end_pos, piece_code, progress)
            visualizer.draw_board(game, selected_square, valid_moves_for_selected_piece, animating_piece)
            pygame.time.wait(20) 
            pygame.display.flip()  
            continue  

        if not game_over and not animating_piece and not awaiting_promotion_choice:
            current_valid_moves = game.get_valid_moves() 
            if game.checkmate or game.stalemate:
                game_over = True
                if game.checkmate:
                    result = 'black' if game.white_to_move else 'white'
                    print(f"Game Over: Checkmate - Winner: {result.capitalize()}")
                else:
                    result = 'draw'
                    draw_reason = "Stalemate"
                 
                    if game.is_threefold_repetition(): draw_reason = "Threefold Repetition"
                    elif game.is_insufficient_material(): draw_reason = "Insufficient Material"
                  
                    print(f"Game Over: Draw - Reason: {draw_reason}")

              
                visualizer.draw_board(game) 
                visualizer.draw_endgame_message(result)
                pygame.display.flip()

                wait_for_input = True
                while wait_for_input:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False
                            wait_for_input = False
                            result = 'quit'
                        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                            wait_for_input = False
                    pygame.time.wait(50) 

                running = False 

        if not game_over and not is_human_turn and not animating_piece and not awaiting_promotion_choice:
            # Start AI thinking in background thread
            ai_result = {'move': None, 'done': False, 'error': None}
            ai_thread = None
            
            if mode == "player_vs_ai":
                ai_thread = threading.Thread(
                    target=ai_thread_function, 
                    args=(ai, True, 10.0, ai_result)
                )
                ai_thread.daemon = True  # Make thread exit when main program exits
                ai_thread.start()
            elif mode == "ai_vs_random":
                if (game.white_to_move and ai_color == 'w') or \
                   (not game.white_to_move and ai_color == 'b'):
                    ai_thread = threading.Thread(
                        target=ai_thread_function, 
                        args=(ai, True, 10.0, ai_result)
                    )
                    ai_thread.daemon = True
                    ai_thread.start()
                else:
                    move = random_move(game)
                    ai_result['move'] = move
                    ai_result['done'] = True
            
            # Show spinner while AI is thinking
            spinner_chars = ['|', '/', '-', '\\']
            spinner_idx = 0
            thinking_font = pygame.font.SysFont("Arial", 36, bold=True)
            
            while not ai_result['done']:
                # Draw the current board
                visualizer.draw_board(game, selected_square, valid_moves_for_selected_piece)
                
                # Draw "AI thinking" message with spinner
                thinking_text = f"AI thinking {spinner_chars[spinner_idx]}"
                text_surface = thinking_font.render(thinking_text, True, (255, 0, 0))
                text_rect = text_surface.get_rect(center=(visualizer.BOARD_WIDTH // 2, visualizer.HEIGHT // 2))
                
                # Add semi-transparent background for better visibility
                bg_rect = text_rect.inflate(20, 20)
                bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                bg_surface.fill((0, 0, 0, 150))
                visualizer.screen.blit(bg_surface, bg_rect)
                
                # Draw text
                visualizer.screen.blit(text_surface, text_rect)
                pygame.display.flip()
                
                # Process events while waiting
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        result = 'quit'
                        game_over = True
                        ai_result['done'] = True
                
                # Increment spinner index
                spinner_idx = (spinner_idx + 1) % len(spinner_chars)
                
                # Small delay to control spinner speed
                pygame.time.wait(100)
            
            # Get the move from the result container
            move = ai_result['move']
            
            if move:
                start_pos = (move.start_col * visualizer.SQUARE_SIZE, move.start_row * visualizer.SQUARE_SIZE)
                end_pos = (move.end_col * visualizer.SQUARE_SIZE, move.end_row * visualizer.SQUARE_SIZE)
                animating_piece = (start_pos, end_pos, move.piece_moved, 0)
                
                game.make_move(move)
                
                selected_square = ()
                player_clicks = []
                valid_moves_for_selected_piece = []
            elif not game.checkmate and not game.stalemate:
                print("ERROR: AI/Random failed to produce a move but game not over.")
                
        if not animating_piece and not game_over:
             visualizer.draw_board(game, selected_square, valid_moves_for_selected_piece)

             if awaiting_promotion_choice:
                
                 promoting_color = 'w' if game.white_to_move else 'b'
                 if hasattr(visualizer, 'draw_promotion_menu') and callable(getattr(visualizer, 'draw_promotion_menu')) and promotion_menu_pos:
                     promotion_buttons = visualizer.draw_promotion_menu(promoting_color, promotion_menu_pos)
                 else:
                   
                     awaiting_promotion_choice = False
                     promotion_move_pending = None
                     promotion_buttons = {}
                     promotion_menu_pos = None

             pygame.display.flip() 

    print("Exiting game loop.")
    return result 


def main():
    visualizer = ChessVisualizer()
    while True:
        mode = None
        ai_depth = None
        player_color_choice = 'w' 
        ai_color_choice = 'b'   

        buttons = visualizer.draw_menu()
        menu_running = True
        while menu_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    visualizer.close()
                    return
                if event.type == pygame.MOUSEMOTION:
                    x, y = event.pos
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
                            menu_running = False 
                            break
            pygame.display.flip() 

        if mode == "exit":
            break

        if "ai" in mode:
             option_buttons = visualizer.draw_option_menu() 
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
                         depths = [2, 3, 4] 
                         for i, button in enumerate(option_buttons):
                             if button.collidepoint(x, y):
                                 ai_depth = depths[i]
                                 option_selected = True
                                 break
                 pygame.display.flip()

             if mode == "player_vs_ai":
                 color_buttons = visualizer.draw_color_menu()
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
                 player_wants_black_flag = (player_color_choice == 'b')

             elif mode == "ai_vs_random":
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
                              colors = ['w', 'b'] 
                              for i, button in enumerate(color_buttons):
                                  if button.collidepoint(x, y):
                                      ai_color_choice = colors[i]
                                      color_selected = True
                                      break
                     pygame.display.flip()
                 player_wants_black_flag = (ai_color_choice == 'w')

        if mode != "player_vs_player":
            print(f"Starting Game: Mode={mode}, AI Depth={ai_depth}, "
                  f"{'Player Color' if mode == 'player_vs_ai' else 'AI Color'}="
                  f"{player_color_choice if mode == 'player_vs_ai' else ai_color_choice}")
        else:
             print(f"Starting Game: Mode={mode}")

        result = play_game(mode, ai_depth, visualizer, player_wants_black=player_wants_black_flag if "ai" in mode else False)


        if result == 'quit': 
            print("Game quit.")
            break 
        elif result is not None: 
            print(f"Game Result: {'White wins' if result == 'white' else 'Black wins' if result == 'black' else 'Draw'}")
            print("Returning to main menu...")
            time.sleep(1) 
    visualizer.close()

def evaluate_performance(depths_to_test=[2, 3, 4], num_moves_per_depth=10):
    """
    Runs the AI at specified depths for a number of moves and records performance metrics.
    """
    print("\n--- Starting AI Performance Evaluation ---")
    print(f"Testing depths: {depths_to_test}")
    print(f"Moves per depth: {num_moves_per_depth}\n")

    results = {} 

    for depth in depths_to_test:
        print(f"--- Evaluating Depth {depth} ---")
        game = GameState()
        ai = ChessAI(game, max_depth=depth, color='w')
        max_time_seconds_per_move = 180.0 

        times = []
        nodes = []
        q_nodes = []
        tt_hits = []
        moves_evaluated_count = 0

        for i in range(num_moves_per_depth * 2):
            if game.checkmate or game.stalemate:
                print(f"Game over during evaluation at ply {i}.")
                break

            current_move = None
            is_ai_turn = game.white_to_move

            if is_ai_turn:
                ai.nodes_visited = 0
                ai.q_nodes_visited = 0
                ai.tt_hits = 0
                ai.timeout_occurred = False 

                start_time = time.time()
                current_move = ai.get_best_move(use_iterative_deepening=True,
                                                max_time_seconds=max_time_seconds_per_move)
                end_time = time.time()

                current_time = end_time - start_time
                current_nodes = ai.nodes_visited
                current_q_nodes = ai.q_nodes_visited
                current_tt_hits = ai.tt_hits

                if current_move:
                    times.append(current_time)
                    nodes.append(current_nodes)
                    q_nodes.append(current_q_nodes)
                    tt_hits.append(current_tt_hits)
                    moves_evaluated_count += 1
                else:
                     print("  AI failed to find a move unexpectedly.")
                     break

                if ai.timeout_occurred:
                    print(f"  (Timeout occurred during search for move {moves_evaluated_count})")

            else: 
                current_move = random_move(game)
          
            if current_move:
                game.make_move(current_move)
            else:
                if not game.checkmate and not game.stalemate:
                    print(f"Error: No move found for {'AI' if is_ai_turn else 'Random'} but game not over?")
                break 

            if is_ai_turn and moves_evaluated_count >= num_moves_per_depth:
                break

        if times: 
            avg_time = sum(times) / len(times)
            avg_nodes = sum(n for n in nodes if isinstance(n, (int, float))) / len(nodes) if nodes else 0
            avg_q_nodes = sum(qn for qn in q_nodes if isinstance(qn, (int, float))) / len(q_nodes) if q_nodes else 0
            avg_tt_hits = sum(tth for tth in tt_hits if isinstance(tth, (int, float))) / len(tt_hits) if tt_hits else 0

            results[depth] = {
                'avg_time': avg_time,
                'avg_nodes': avg_nodes,
                'avg_q_nodes': avg_q_nodes,
                'avg_tt_hits': avg_tt_hits,
                'moves_evaluated': len(times)
            }
        else: 
             results[depth] = {
                'avg_time': 0, 'avg_nodes': 0, 'avg_q_nodes': 0, 'avg_tt_hits': 0, 'moves_evaluated': 0
            }

        print(f"--- Depth {depth} Summary ---")
        print(f"  Moves Evaluated: {results[depth]['moves_evaluated']}")
        if results[depth]['moves_evaluated'] > 0:
             print(f"  Avg Time: {results[depth]['avg_time']:.3f}s")
             print(f"  Avg Nodes: {results[depth]['avg_nodes']:.1f}")
             print(f"  Avg QNodes: {results[depth]['avg_q_nodes']:.1f}")
             print(f"  Avg TT Hits: {results[depth]['avg_tt_hits']:.1f}")
        print("-" * 25)
    print("\n--- Overall Performance Results ---")
    print("| Depth | Avg Time (s) | Avg Nodes    | Avg QNodes   | Avg TT Hits  | Moves Eval |")
    print("|-------|--------------|--------------|--------------|--------------|------------|")
    # Body
    for depth in sorted(results.keys()):
        r = results[depth]
        print(f"| {depth:<5} | {r['avg_time']:<12.3f} | {r['avg_nodes']:<12.1f} | "
              f"{r['avg_q_nodes']:<12.1f} | {r['avg_tt_hits']:<12.1f} | {r['moves_evaluated']:<10} |")

    print("\n--- Evaluation Complete ---")
    return results 

def evaluate_vs_random(ai_depth, num_games=10, max_time_per_move=5.0, max_game_ply=300):
    print(f"\n--- Starting Evaluation: AI Depth {ai_depth} vs Random ({num_games} games) ---")

    win_times = []
    win_ply_counts = []
    ai_wins = 0
    draws = 0

    for game_idx in range(num_games):
        game = GameState()
        ai_color = 'w' if game_idx % 2 == 0 else 'b'
        ai = ChessAI(game, max_depth=ai_depth, color=ai_color)
        use_id = True

        print(f"  Starting Game {game_idx + 1}/{num_games} (AI plays {'White' if ai_color == 'w' else 'Black'})")
        start_game_time = time.time()
        game_over = False
        outcome = None

        while len(game.move_log) <= max_game_ply:
            if game.checkmate or game.stalemate:
                game_over = True
                break

            is_ai_turn = (game.white_to_move and ai_color == 'w') or \
                         (not game.white_to_move and ai_color == 'b')

            move = None
            if is_ai_turn:
                move = ai.get_best_move(use_iterative_deepening=use_id,
                                        max_time_seconds=max_time_per_move)
            else: 
                move = random_move(game)

            if move:
                game.make_move(move)
            else:
                game_over = True
                break

        end_game_time = time.time()
        game_duration = end_game_time - start_game_time
        ply_count = len(game.move_log)

        if game.checkmate:
         
            winner_color = 'b' if game.white_to_move else 'w'
            if winner_color == ai_color:
                outcome = 'ai_win'
                ai_wins += 1
                win_times.append(game_duration)
                win_ply_counts.append(ply_count)
                print(f"  Game {game_idx + 1}: AI Wins in {ply_count} ply ({game_duration:.2f}s)")
            else:
                outcome = 'random_win'
                print(f"  Game {game_idx + 1}: Random Wins in {ply_count} ply ({game_duration:.2f}s)")
        elif game.stalemate:
            outcome = 'draw'
            draws += 1
            print(f"  Game {game_idx + 1}: Draw (Stalemate) in {ply_count} ply ({game_duration:.2f}s)")
        elif ply_count > max_game_ply:
            outcome = 'draw'
            draws += 1
            print(f"  Game {game_idx + 1}: Draw (Max Ply Exceeded) after {ply_count} ply ({game_duration:.2f}s)")
        else:

            print(f"  Game {game_idx + 1}: Unknown outcome after {ply_count} ply ?!")
            outcome = 'draw' 
            draws += 1

    avg_win_time = sum(win_times) / len(win_times) if win_times else 0
    avg_win_ply = sum(win_ply_counts) / len(win_ply_counts) if win_ply_counts else 0

    print("\n--- Evaluation Summary ---")
    print(f"AI Depth: {ai_depth}")
    print(f"Total Games: {num_games}")
    print(f"AI Wins: {ai_wins} ({ai_wins / num_games * 100:.1f}%)")
    print(f"Draws: {draws}")
    print(f"Random Wins: {num_games - ai_wins - draws}")
    if ai_wins > 0:
        print(f"Average Time per AI Win: {avg_win_time:.2f} seconds")
        print(f"Average Ply Count per AI Win: {avg_win_ply:.1f}")
    else:
         print("AI did not win any games.")

    print("-" * 28)

    return {
        'ai_wins': ai_wins,
        'avg_win_time': avg_win_time,
        'avg_win_ply': avg_win_ply,
        'draws': draws,
        'total_games': num_games
    }

   

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--eval-random':
        target_depth = 2 
        num_sim_games = 10
        if len(sys.argv) > 2:
            try: target_depth = int(sys.argv[2])
            except ValueError: print(f"Invalid depth, using {target_depth}.")
        if len(sys.argv) > 3:
            try: num_sim_games = int(sys.argv[3])
            except ValueError: print(f"Invalid number of games, using {num_sim_games}.")

        print(f"Running AI Depth {target_depth} vs Random for {num_sim_games} games...")
        results = evaluate_vs_random(ai_depth=target_depth, num_games=num_sim_games)
        print("Random evaluation finished. Exiting.")
        sys.exit()

    elif len(sys.argv) > 1 and sys.argv[1] == '--evaluate':
        print("Running Performance Evaluation...")
        # Defaults
        eval_depths = [2, 3, 4]
        eval_moves = 10
        if len(sys.argv) > 2:
            try:
                eval_depths = [int(d) for d in sys.argv[2].split(',')]
            except ValueError:
                print("Invalid depths format. Use comma-separated integers (e.g., 2,3,4). Using default.")
        if len(sys.argv) > 3:
             try:
                 eval_moves = int(sys.argv[3])
             except ValueError:
                 print("Invalid number of moves. Use an integer. Using default.")
        results = evaluate_performance(depths_to_test=eval_depths, num_moves_per_depth=eval_moves)
        print("Performance evaluation finished. Exiting.")
        sys.exit() 

    else:
        main()
        # print("Starting Interactive Game...")
        # visualizer = ChessVisualizer()
        # while True:
        #     mode = "player_vs_ai" 
        #     ai_depth = 3       
        #     player_wants_black_flag = False 

        #     if mode == "exit":
        #         break


        #     print(f"Starting Game: Mode={mode}, AI Depth={ai_depth}")
        #     result = play_game(mode, ai_depth, visualizer, player_wants_black=player_wants_black_flag)

        #     if result == 'quit':
        #         print("Game quit.")
        #         break
        #     elif result is not None:
        #         print(f"Game Result: {'White wins' if result == 'white' else 'Black wins' if result == 'black' else 'Draw'}")
        #         print("Returning to main menu...")
        #         time.sleep(1)
        #     else:
        #         print("Game ended unexpectedly. Returning to menu.")
        #         time.sleep(1)

        # visualizer.close()
        # print("Program exited.")