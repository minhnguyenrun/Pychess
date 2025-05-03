# --- START OF FILE minimax_ai.py ---

import math
import random
import time
import sys
from game_state import GameState, Move # Import necessary classes from game_state

# --- Constants ---
# Game Phases (approximate, based on number of pieces left besides kings)
MIDDLEGAME_THRESHOLD = 20 # e.g., less than 20 pieces total means likely endgame
ENDGAME_THRESHOLD = 10   # e.g., less than 10 pieces

# Piece values
PIECE_VALUES = {"p": 100, "n": 320, "b": 330, "r": 500, "q": 900, "k": 20000}

# Transposition Table Flags
TT_EXACT = 0
TT_LOWERBOUND = 1 # Alpha cutoff
TT_UPPERBOUND = 2 # Beta cutoff

# --- Piece-Square Tables (Add tables for all pieces) ---
# Values represent centipawns bonus/penalty for piece placement
PAWN_TABLE = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [50, 50, 50, 50, 50, 50, 50, 50], # Strong incentive to advance
    [10, 10, 20, 30, 30, 20, 10, 10],
    [ 5,  5, 10, 25, 25, 10,  5,  5], # Center control
    [ 0,  0,  0, 20, 20,  0,  0,  0],
    [ 5, -5,-10,  0,  0,-10, -5,  5],
    [ 5, 10, 10,-25,-25, 10, 10,  5], # Penalty for blocked c/f pawns early?
    [ 0,  0,  0,  0,  0,  0,  0,  0]
]
KNIGHT_TABLE = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30], # Knights strong in center
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50] # Penalty for corners/back rank
]
BISHOP_TABLE = [
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10], # Good on long diagonals
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  5,  0,  0,  0,  0,  5,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20] # Penalty for corners
]
ROOK_TABLE = [
    [  0,  0,  0,  0,  0,  0,  0,  0],
    [  5, 10, 10, 10, 10, 10, 10,  5], # Good on 7th rank
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [  0,  0,  0,  5,  5,  0,  0,  0] # Bonus for center files, castling potential
]
QUEEN_TABLE = [
    [-20,-10,-10, -5, -5,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5,  5,  5,  5,  0,-10],
    [ -5,  0,  5,  5,  5,  5,  0, -5], # Slight center preference
    [  0,  0,  5,  5,  5,  5,  0, -5],
    [-10,  5,  5,  5,  5,  5,  0,-10],
    [-10,  0,  5,  0,  0,  0,  0,-10], # Avoid bringing out too early
    [-20,-10,-10, -5, -5,-10,-10,-20]
]
KING_MIDDLE_TABLE = [ # King safety focus in middlegame
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-20,-30,-30,-40,-40,-30,-30,-20],
    [-10,-20,-20,-20,-20,-20,-20,-10],
    [ 20, 20,  0,  0,  0,  0, 20, 20], # Encourage castling
    [ 20, 30, 10,  0,  0, 10, 30, 20]  # King tucked away
]
KING_END_TABLE = [ # King activity focus in endgame
    [-50,-40,-30,-20,-20,-30,-40,-50],
    [-30,-20,-10,  0,  0,-10,-20,-30],
    [-30,-10, 20, 30, 30, 20,-10,-30], # Centralize the king
    [-30,-10, 30, 40, 40, 30,-10,-30],
    [-30,-10, 30, 40, 40, 30,-10,-30],
    [-30,-10, 20, 30, 30, 20,-10,-30],
    [-30,-30,  0,  0,  0,  0,-30,-30],
    [-50,-30,-30,-30,-30,-30,-30,-50]
]

# Mirrored tables for Black (Precompute for efficiency)
def mirror_table(table):
    return table[::-1]

PAWN_TABLE_BLACK = mirror_table(PAWN_TABLE)
KNIGHT_TABLE_BLACK = mirror_table(KNIGHT_TABLE)
BISHOP_TABLE_BLACK = mirror_table(BISHOP_TABLE)
ROOK_TABLE_BLACK = mirror_table(ROOK_TABLE)
QUEEN_TABLE_BLACK = mirror_table(QUEEN_TABLE)
KING_MIDDLE_TABLE_BLACK = mirror_table(KING_MIDDLE_TABLE)
KING_END_TABLE_BLACK = mirror_table(KING_END_TABLE)

# Piece-to-Table mapping
PIECE_POSITION_TABLES = {
    'p': {'w': PAWN_TABLE, 'b': PAWN_TABLE_BLACK},
    'n': {'w': KNIGHT_TABLE, 'b': KNIGHT_TABLE_BLACK},
    'b': {'w': BISHOP_TABLE, 'b': BISHOP_TABLE_BLACK},
    'r': {'w': ROOK_TABLE, 'b': ROOK_TABLE_BLACK},
    'q': {'w': QUEEN_TABLE, 'b': QUEEN_TABLE_BLACK},
    'k': {'w': {'middle': KING_MIDDLE_TABLE, 'end': KING_END_TABLE},
          'b': {'middle': KING_MIDDLE_TABLE_BLACK, 'end': KING_END_TABLE_BLACK}}
}

# Evaluation Constants
CENTER_SQUARES = [(3,3), (3,4), (4,3), (4,4)] # d4, e4, d5, e5
CENTER_CONTROL_BONUS = 10 # Bonus per piece attacking center
PASSED_PAWN_BONUS = [0, 5, 15, 30, 50, 75, 100, 0] # Bonus based on rank (rank 8 is promotion)
ISOLATED_PAWN_PENALTY = -15
DOUBLED_PAWN_PENALTY = -10
KING_SAFETY_PAWN_SHIELD_BONUS = 5 # Bonus per pawn near king
KING_SAFETY_ATTACK_PENALTY = -50 # Penalty if enemy queen/rook has line of sight


class ChessAI:
    def __init__(self, game: GameState, max_depth: int, color: str):
        self.game = game # Operates directly on the GameState object
        self.max_depth = max_depth
        self.ai_player_color = color # 'w' or 'b'
        self.ai_player_sign = 1 if color == 'w' else -1 # 1 for white, -1 for black
        self.move_count = len(game.move_log) # Track game progress for evaluation phases
        self.start_time = 0 # For iterative deepening timeout
        self.max_time = 0   # For iterative deepening timeout
        self.nodes_visited = 0 # For performance tracking
        self.q_nodes_visited = 0 # Quiescence nodes
        self.tt_hits = 0       # Transposition table hits
        self.transposition_table = {} # Store evaluated positions {position_key: (score, depth, flag, best_move)}
        self.timeout_occurred = False # Flag to signal timeout across recursion

    def get_best_move(self, use_iterative_deepening=True, max_time_seconds=10.0):
        """Finds the best move using iterative deepening or fixed depth alpha-beta."""
        print(f"\n=== AI ({self.ai_player_color.upper()}) MOVE SELECTION START ===")
        self.move_count = len(self.game.move_log)
        self.nodes_visited = 0
        self.q_nodes_visited = 0
        self.tt_hits = 0
        self.timeout_occurred = False # Reset timeout flag
        best_move = None
        start_search_time = time.time()

        # --- Check for immediate game end conditions ---
        current_valid_moves = self.game.get_valid_moves() # This also updates game.checkmate/stalemate
        if self.game.checkmate or self.game.stalemate:
            print("AI recognizes Game Over condition - no moves possible.")
            print("=== AI MOVE SELECTION END ===\n")
            return None
        if not current_valid_moves:
             print("ERROR: No valid moves but not checkmate/stalemate?")
             print("=== AI MOVE SELECTION END ===\n")
             return None

        try:
            if use_iterative_deepening:
                print(f"Using iterative deepening search (max_time={max_time_seconds}s)")
                best_move = self.iterative_deepening(max_time=max_time_seconds)
            else:
                print(f"Using fixed depth alpha-beta search (depth={self.max_depth})")
                _, best_move = self.alphabeta_root(self.max_depth)

        except TimeoutError:
            print("Search timed out externally. Using best move found so far (if any).")
            # Best move should be stored by iterative_deepening
        except Exception as e:
            print(f"An unexpected error occurred during search: {e}")
            import traceback
            traceback.print_exc()
            best_move = None # Discard potentially corrupt results

        # --- Fallback Logic (if search failed completely or timed out early) ---
        if best_move is None:
            print("WARNING: Search failed or timed out without a valid move. Executing fallback.")
            fallback_valid_moves = self.game.get_valid_moves() # Re-check just in case
            if not fallback_valid_moves:
                 print("CRITICAL ERROR: Fallback could not generate any valid moves!")
                 return None

            # Simple fallback: prioritize captures (MVV-LVA), then random
            best_move = self.fallback_move_selection(fallback_valid_moves)

        # --- Final Output ---
        search_duration = time.time() - start_search_time
        if best_move:
            move_notation = best_move.get_notation()
            piece_name = self._get_piece_name(best_move.piece_moved)
            print(f"Selected move: {piece_name} {move_notation}")
            print(f"Nodes visited: {self.nodes_visited} (Q: {self.q_nodes_visited}) | TT Hits: {self.tt_hits}")
            print(f"Search time: {search_duration:.3f} seconds")
        else:
            print("ERROR: No move selected even after fallback.")

        print("=== AI MOVE SELECTION END ===\n")
        return best_move

    def iterative_deepening(self, max_time=5.0):
        """Performs alpha-beta search with increasing depth until time runs out."""
        self.start_time = time.time()
        self.max_time = max_time
        best_score_overall = -float('inf') * self.ai_player_sign # Initialize for AI's perspective
        best_move_overall = None
        last_completed_depth = 0
        # Clear TT at start of new move search (optional, could keep between moves)
        self.transposition_table.clear()

        # Generate initial moves once
        initial_moves = self.game.get_valid_moves()
        if not initial_moves: return None # No moves possible

        for depth in range(1, self.max_depth + 1):
            print(f"--- Starting Depth {depth} Search ---")
            self.nodes_visited = 0 # Reset counters per depth
            self.q_nodes_visited = 0
            self.tt_hits = 0
            self.timeout_occurred = False # Reset timeout flag for this depth

            try:
                # Pass the ordered moves from the previous iteration if available?
                # For now, re-order at each depth's root.
                current_score, current_best_move_this_depth = self.alphabeta_root(depth, initial_moves)

                # Check for timeout *during* the search (via self.timeout_occurred flag)
                if self.timeout_occurred:
                    print(f"Timeout detected during depth {depth} search.")
                    break # Stop searching, use results from last completed depth

                # If search completed without timeout, update results
                last_completed_depth = depth
                score_perspective = current_score * self.ai_player_sign # Score from AI's view

                if current_best_move_this_depth:
                    best_move_overall = current_best_move_this_depth
                    best_score_overall = current_score # Store score from white's perspective for TT consistency
                    move_notation = best_move_overall.get_notation()
                    print(f"Depth {depth} complete. Score: {current_score:.0f}, Move: {move_notation}, Nodes: {self.nodes_visited}(Q:{self.q_nodes_visited}), TT Hits: {self.tt_hits}")

                    # Optional: If mate is found, stop early
                    if abs(current_score) > PIECE_VALUES['k']: # If score indicates mate
                         print(f"Checkmate found at depth {depth}. Stopping search.")
                         break
                else:
                    # This could happen if alphabeta_root returns None move (e.g., immediate mate/stalemate)
                     print(f"Depth {depth} search returned no best move (likely game end state).")
                     if not best_move_overall: # If this is the first depth and game ends
                         best_move_overall = random.choice(initial_moves) if initial_moves else None # Failsafe needed? Game should end before this.
                     break # Stop searching


                # Check time *after* completing a depth for clean exit
                if time.time() - self.start_time > self.max_time * 0.9: # Check slightly early
                    print(f"Approaching time limit ({self.max_time}s) after depth {depth}. Stopping.")
                    break

            except TimeoutError: # Catch timeout specifically from alphabeta
                print(f"Timeout occurred during depth {depth} search.")
                break # Stop searching, use results from last completed depth
            except Exception as e:
                 print(f"ERROR during search at depth {depth}: {e}")
                 import traceback
                 traceback.print_exc()
                 break # Stop on unexpected errors

        if best_move_overall:
            print(f"\nSearch finished. Best move from depth {last_completed_depth}: {best_move_overall.get_notation()}")
        else:
             print("WARNING: Iterative deepening did not find any valid move.")
             # Implement fallback if no move found after all depths
             best_move_overall = self.fallback_move_selection(initial_moves)


        # Clean up time attributes
        self.start_time = 0
        self.max_time = 0

        return best_move_overall

    def fallback_move_selection(self, valid_moves):
        """Selects a move when the main search fails."""
        if not valid_moves: return None
        capture_moves = []
        other_moves = []
        for m in valid_moves:
            if m.piece_captured != '--':
                score = PIECE_VALUES.get(m.piece_captured[1], 0) * 10 - PIECE_VALUES.get(m.piece_moved[1], 0) # MVV-LVA
                capture_moves.append((score, m))
            else:
                other_moves.append(m)
        capture_moves.sort(key=lambda x: x[0], reverse=True)

        if capture_moves:
            selected = capture_moves[0][1]
            print(f"Fallback selected capture: {selected.get_notation()}")
            return selected
        else:
            selected = random.choice(other_moves)
            print(f"Fallback selected random move: {selected.get_notation()}")
            return selected

    def order_moves(self, moves):
        """Orders moves: MVV-LVA captures, Promotions, Checks, Others."""
        move_scores = []
        for move in moves:
            score = 0
            # 1. MVV-LVA Captures
            if move.piece_captured != '--':
                 # Prioritize capturing high value with low value
                 score += 10 * PIECE_VALUES.get(move.piece_captured[1], 0) - PIECE_VALUES.get(move.piece_moved[1], 0)
                 score += 1000 # Big bonus for any capture

            # 2. Promotions
            if move.is_pawn_promotion:
                 score += PIECE_VALUES['q'] # Bonus equal to queen value

            # 3. Checks (Estimate by checking if move puts opponent in check)
            # This requires simulating the move briefly, might be slow here.
            # Alternative: simpler estimate - does the move attack the opponent king's square?
            # Let's skip check ordering for now for simplicity/speed in Phase 2 ordering
            # To add it:
            # self.game.make_move(move)
            # if self.game.is_in_check():
            #    score += 50 # Bonus for giving check
            # self.game.undo_move()

            # Add other heuristics later (e.g., killer moves, history heuristic)

            move_scores.append((score, move))

        # Sort by score descending
        move_scores.sort(key=lambda x: x[0], reverse=True)
        return [move for score, move in move_scores]

    def alphabeta_root(self, depth, initial_moves=None):
        """Root node search, slightly different as it needs to return the best move object."""
        if initial_moves is None:
             initial_moves = self.game.get_valid_moves()

        if not initial_moves: return (-float('inf') if self.game.white_to_move else float('inf')), None # Checkmate
        if self.game.stalemate: return 0, None

        ordered_moves = self.order_moves(initial_moves)
        best_move_found = ordered_moves[0] # Default to first move
        alpha = -float('inf')
        beta = float('inf')

        if self.game.white_to_move: # Maximizing player at root
            max_eval = -float('inf')
            for move in ordered_moves:
                self.game.make_move(move)
                current_eval = self.alphabeta(depth - 1, alpha, beta)
                self.game.undo_move()

                if self.timeout_occurred: raise TimeoutError("Timeout") # Propagate timeout

                if current_eval > max_eval:
                    max_eval = current_eval
                    best_move_found = move
                alpha = max(alpha, current_eval)
                # No beta cutoff at root for the maximizing player comparing against initial -inf beta

            return max_eval, best_move_found
        else: # Minimizing player at root
            min_eval = float('inf')
            for move in ordered_moves:
                self.game.make_move(move)
                current_eval = self.alphabeta(depth - 1, alpha, beta)
                self.game.undo_move()

                if self.timeout_occurred: raise TimeoutError("Timeout") # Propagate timeout

                if current_eval < min_eval:
                    min_eval = current_eval
                    best_move_found = move
                beta = min(beta, current_eval)
                 # No alpha cutoff at root for the minimizing player comparing against initial +inf alpha

            return min_eval, best_move_found

    def alphabeta(self, depth, alpha, beta):
        """Recursive alpha-beta search function. Returns score (always from White's perspective)."""
        self.nodes_visited += 1

        # --- Timeout Check ---
        # Check more frequently in deeper searches? Check every N nodes?
        if self.nodes_visited % 2048 == 0: # Check every ~2k nodes
            if self.start_time > 0 and time.time() - self.start_time > self.max_time:
                self.timeout_occurred = True
                return 0 # Return neutral score on timeout

        if self.timeout_occurred: return 0 # Stop calculation if timeout signalled


        # --- Transposition Table Lookup ---
        position_key = self.game._get_position_key() # Use the existing key generation
        tt_entry = self.transposition_table.get(position_key)
        if tt_entry and tt_entry[1] >= depth: # Check if stored depth is sufficient
             self.tt_hits += 1
             score, stored_depth, flag, _ = tt_entry # Don't need stored move here
             if flag == TT_EXACT:
                 return score
             elif flag == TT_LOWERBOUND: # Previously caused beta cutoff (score >= beta)
                 alpha = max(alpha, score) # Improve alpha
             elif flag == TT_UPPERBOUND: # Previously caused alpha cutoff (score <= alpha)
                 beta = min(beta, score)  # Improve beta

             if alpha >= beta: # Can we prune based on improved bounds?
                 return score # Return the bound score that caused the cutoff

        # --- Base Case: Depth Limit or Game Over ---
        if depth <= 0:
            return self.quiescence_search(alpha, beta) # Enter quiescence search

        valid_moves = self.game.get_valid_moves()
        if not valid_moves:
            if self.game.checkmate:
                 # Score checkmate based on whose turn it *would* be (higher score further from root)
                 mate_score = float('inf') if not self.game.white_to_move else -float('inf')
                 return mate_score
            else: # Stalemate
                 # Use adjusted stalemate score based on material
                 return self.evaluate_stalemate()


        # --- Move Ordering ---
        ordered_moves = self.order_moves(valid_moves)
        best_move_for_tt = ordered_moves[0] # Default best move for TT storage


        # --- Recursive Search ---
        original_alpha = alpha # Store original alpha for TT flag
        if self.game.white_to_move: # Maximizing Player
            max_eval = -float('inf')
            for move in ordered_moves:
                self.game.make_move(move)
                current_eval = self.alphabeta(depth - 1, alpha, beta)
                self.game.undo_move()

                if self.timeout_occurred: return 0 # Check after undo

                if current_eval > max_eval:
                     max_eval = current_eval
                     best_move_for_tt = move # Update best move found at this node

                alpha = max(alpha, current_eval)
                if beta <= alpha:
                    break # Beta cut-off
            # --- Transposition Table Store ---
            flag = TT_EXACT if max_eval > original_alpha and max_eval < beta else \
                   TT_LOWERBOUND if max_eval >= beta else TT_UPPERBOUND # Must have been <= original_alpha
            self.transposition_table[position_key] = (max_eval, depth, flag, best_move_for_tt)
            return max_eval
        else: # Minimizing Player
            min_eval = float('inf')
            for move in ordered_moves:
                self.game.make_move(move)
                current_eval = self.alphabeta(depth - 1, alpha, beta)
                self.game.undo_move()

                if self.timeout_occurred: return 0 # Check after undo

                if current_eval < min_eval:
                    min_eval = current_eval
                    best_move_for_tt = move # Update best move found at this node

                beta = min(beta, current_eval)
                if beta <= alpha:
                    break # Alpha cut-off
            # --- Transposition Table Store ---
            flag = TT_EXACT if min_eval > original_alpha and min_eval < beta else \
                   TT_UPPERBOUND if min_eval <= original_alpha else TT_LOWERBOUND # Must have been >= beta
            self.transposition_table[position_key] = (min_eval, depth, flag, best_move_for_tt)
            return min_eval

    def quiescence_search(self, alpha, beta, depth_limit=4): # Limit quiescence depth
        """Search only captures and potentially checks until a 'quiet' position is reached."""
        self.q_nodes_visited += 1

        # --- Timeout Check (less frequent in Q-search?) ---
        if self.q_nodes_visited % 1024 == 0:
             if self.start_time > 0 and time.time() - self.start_time > self.max_time:
                 self.timeout_occurred = True
                 return 0
        if self.timeout_occurred: return 0

        # Use static evaluation as the baseline
        stand_pat_score = self.evaluate_board() # Evaluate the current "quiet" position

        if depth_limit <= 0:
            return stand_pat_score # Reached quiescence depth limit

        # Delta Pruning (Optional but recommended): If stand_pat + Big_Piece < alpha, prune.
        # if stand_pat_score < alpha - PIECE_VALUES['q'] - 200: # If even capturing queen isn't enough
        #      return alpha

        # --- Maximize/Minimize based on whose turn ---
        if self.game.white_to_move: # Maximizing player
            alpha = max(alpha, stand_pat_score) # Update alpha with the score of not making a capture
        else: # Minimizing player
            beta = min(beta, stand_pat_score) # Update beta with the score of not making a capture

        if alpha >= beta:
             return stand_pat_score # Pruning based on stand-pat score

        # --- Generate only captures (and maybe checks) ---
        # Need a way to get *only* captures/checks efficiently.
        # For now, get all moves and filter. This is slow.
        # TODO: Optimize move generation for quiescence (e.g., GameState.get_capture_moves())
        all_moves = self.game.get_valid_moves()
        capture_moves = [m for m in all_moves if m.piece_captured != '--' or m.is_pawn_promotion]
        # Add checks later if needed: or self.is_check_move(m)
        ordered_captures = self.order_moves(capture_moves) # Order captures too

        # --- Recursive Quiescence Search ---
        if self.game.white_to_move: # Maximizing Player
            for move in ordered_captures:
                self.game.make_move(move)
                score = self.quiescence_search(alpha, beta, depth_limit - 1)
                self.game.undo_move()

                if self.timeout_occurred: return 0

                alpha = max(alpha, score)
                if beta <= alpha:
                    break # Beta cut-off
            return alpha # Return the best score found (could be stand_pat or from a capture sequence)

        else: # Minimizing Player
            for move in ordered_captures:
                self.game.make_move(move)
                score = self.quiescence_search(alpha, beta, depth_limit - 1)
                self.game.undo_move()

                if self.timeout_occurred: return 0

                beta = min(beta, score)
                if beta <= alpha:
                    break # Alpha cut-off
            return beta # Return the best score found (could be stand_pat or from a capture sequence)


    def get_piece_counts_and_material(self, board):
        """ Helper to get piece counts and total material for evaluation """
        white_material = 0
        black_material = 0
        piece_count = 0
        white_pawns = [] # Store column index for structure eval
        black_pawns = []

        for r in range(8):
            for c in range(8):
                piece = board[r][c]
                if piece != '--':
                    piece_count += 1
                    piece_type = piece[1]
                    value = PIECE_VALUES.get(piece_type, 0)
                    if piece[0] == 'w':
                        white_material += value
                        if piece_type == 'p': white_pawns.append(c)
                    else:
                        black_material += value
                        if piece_type == 'p': black_pawns.append(c)
        return white_material, black_material, piece_count, sorted(white_pawns), sorted(black_pawns)


    def evaluate_stalemate(self):
        """ Returns 0 for stalemate, potentially adjusted based on material balance. """
        # If AI is winning significantly, stalemate is bad (-ve score).
        # If AI is losing significantly, stalemate is good (0 or slightly +ve score).
        white_mat, black_mat, _, _, _ = self.get_piece_counts_and_material(self.game.board)
        material_diff = white_mat - black_mat # From White's perspective

        ai_perspective_diff = material_diff * self.ai_player_sign

        if ai_perspective_diff > 300: # AI thinks it's winning significantly
            return -50 * self.ai_player_sign # Return small penalty (from AI perspective) -> translates to -50 for white, +50 for black
        elif ai_perspective_diff < -300: # AI thinks it's losing significantly
             return 50 * self.ai_player_sign # Return small bonus (from AI perspective) -> translates to +50 for white, -50 for black
        else:
             return 0 # Neutral if roughly even


    def evaluate_board(self):
        """
        Enhanced evaluation function. Returns score from White's perspective.
        Includes: Material, Piece-Square Tables, Basic Pawn Structure, King Safety, Center Control.
        """
        # --- 1. Material and Piece Counts ---
        white_material, black_material, piece_count, white_pawns, black_pawns = \
            self.get_piece_counts_and_material(self.game.board)
        material_score = white_material - black_material

        # --- 2. Determine Game Phase ---
        if piece_count > MIDDLEGAME_THRESHOLD: game_phase = 'middle'
        elif piece_count > ENDGAME_THRESHOLD: game_phase = 'middle' # Treat early endgame more like middlegame for king safety
        else: game_phase = 'end'

        # --- 3. Initialize Scores ---
        position_score = 0
        pawn_structure_score = 0
        king_safety_score = 0
        center_control_score = 0
        # Add other scores like mobility, connectivity later if needed

        # --- 4. Iterate Board for Positional Features ---
        white_king_pos = self.game.white_king_location
        black_king_pos = self.game.black_king_location

        for r in range(8):
            for c in range(8):
                piece = self.game.board[r][c]
                if piece != '--':
                    piece_type = piece[1]
                    piece_color = piece[0]
                    color_sign = 1 if piece_color == 'w' else -1

                    # --- 4a. Piece-Square Tables ---
                    try:
                        if piece_type == 'k':
                             table = PIECE_POSITION_TABLES['k'][piece_color][game_phase]
                             position_score += table[r][c] * color_sign
                        else:
                             table = PIECE_POSITION_TABLES[piece_type][piece_color]
                             position_score += table[r][c] * color_sign
                    except KeyError: pass # Should not happen if tables are defined
                    except IndexError: print(f"Index Error PSTable: P={piece} R={r} C={c}"); pass

                    # --- 4b. Center Control (Simple version: piece attacks center) ---
                    # TODO: A better way is to generate attacks from each piece to center squares.
                    # Simple proxy: bonus if piece is near center or bishop/rook controls diagonal/file through center
                    if (r, c) in [(2,2),(2,3),(2,4),(2,5), (3,2),(3,3),(3,4),(3,5), (4,2),(4,3),(4,4),(4,5), (5,2),(5,3),(5,4),(5,5)]: # Expanded center area
                        if piece_type in 'nbp': # Pawns, Knights, Bishops in/near center
                           center_control_score += (CENTER_CONTROL_BONUS / 2) * color_sign
                    if (r,c) in CENTER_SQUARES:
                         if piece_type in 'nbp':
                             center_control_score += (CENTER_CONTROL_BONUS / 2) * color_sign


                    # --- 4c. Passed Pawns (Simple Check) ---
                    if piece_type == 'p':
                        is_passed = True
                        # Check squares directly ahead and diagonally ahead in the same file and adjacent files
                        for check_r in range(r + color_sign, 8 if color_sign == 1 else -1, color_sign):
                            if not (0 <= check_r < 8): break # Off board
                            for check_c_offset in [-1, 0, 1]:
                                check_c = c + check_c_offset
                                if 0 <= check_c < 8:
                                    opp_piece = self.game.board[check_r][check_c]
                                    if opp_piece != '--' and opp_piece[0] != piece_color and opp_piece[1] == 'p':
                                        is_passed = False
                                        break
                            if not is_passed: break
                        if is_passed:
                            rank_index = r if piece_color == 'b' else 7 - r # 0=start, 7=promotion
                            pawn_structure_score += PASSED_PAWN_BONUS[rank_index] * color_sign


        # --- 5. Pawn Structure (Doubled, Isolated - using collected pawn columns) ---
        wp_counts = {col: white_pawns.count(col) for col in white_pawns}
        bp_counts = {col: black_pawns.count(col) for col in black_pawns}

        for col, count in wp_counts.items():
            if count > 1: pawn_structure_score += DOUBLED_PAWN_PENALTY * (count - 1) # Penalize each extra pawn
            is_isolated = True
            if col > 0 and (col - 1) in wp_counts: is_isolated = False
            if col < 7 and (col + 1) in wp_counts: is_isolated = False
            if is_isolated: pawn_structure_score += ISOLATED_PAWN_PENALTY

        for col, count in bp_counts.items():
            if count > 1: pawn_structure_score -= DOUBLED_PAWN_PENALTY * (count - 1)
            is_isolated = True
            if col > 0 and (col - 1) in bp_counts: is_isolated = False
            if col < 7 and (col + 1) in bp_counts: is_isolated = False
            if is_isolated: pawn_structure_score -= ISOLATED_PAWN_PENALTY


        # --- 6. King Safety (Simple Pawn Shield, Basic Attack Check) ---
        if game_phase == 'middle': # Only apply in middle game
             # White King Safety
             wk_r, wk_c = white_king_pos
             for dr, dc in [( -1, -1), ( -1, 0), ( -1, 1)]: # Pawns in front
                 pr, pc = wk_r + dr, wk_c + dc
                 if 0 <= pr < 8 and 0 <= pc < 8 and self.game.board[pr][pc] == 'wp':
                     king_safety_score += KING_SAFETY_PAWN_SHIELD_BONUS
             # TODO: Add checks for open files near king, enemy pieces pointing at king

             # Black King Safety
             bk_r, bk_c = black_king_pos
             for dr, dc in [( 1, -1), ( 1, 0), ( 1, 1)]: # Pawns in front
                  pr, pc = bk_r + dr, bk_c + dc
                  if 0 <= pr < 8 and 0 <= pc < 8 and self.game.board[pr][pc] == 'bp':
                      king_safety_score -= KING_SAFETY_PAWN_SHIELD_BONUS
             # TODO: Add checks for open files near king, enemy pieces pointing at king


        # --- 7. Combine Scores ---
        # Weights can be tuned
        final_score = (material_score +
                       position_score * 0.5 +      # Positional less important than material
                       pawn_structure_score * 0.8 + # Structure is quite important
                       king_safety_score * 1.0 +    # Safety is very important
                       center_control_score * 0.7)  # Center control important

        # Return score from White's perspective
        return final_score


    def _print_board(self): # Kept from Phase 1 for debugging
        """Prints the current board state to the console for debugging."""
        print("  a b c d e f g h")
        print(" +-----------------+")
        for r in range(8):
            print(f"{8-r}|", end=" ")
            for c in range(8):
                piece = self.game.board[r][c]
                if piece == '--':
                    print(".", end=" ")
                else:
                    char = piece[1]
                    print(char.upper() if piece[0] == 'w' else char.lower(), end=" ")
            print(f"|{8-r}")
        print(" +-----------------+")
        print("  a b c d e f g h")
        print(f"Turn: {'White' if self.game.white_to_move else 'Black'}")

    def _get_piece_name(self, piece_code): # Kept from Phase 1
        """Helper to get full piece name from code (e.g., 'wp' -> 'Pawn')."""
        names = {'p': 'Pawn', 'n': 'Knight', 'b': 'Bishop', 'r': 'Rook', 'q': 'Queen', 'k': 'King'}
        return names.get(piece_code[1], 'Unknown')
