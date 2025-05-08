import math
import random
import time
import sys
from game_state import GameState, Move
import traceback 

MIDDLEGAME_THRESHOLD = 20
ENDGAME_THRESHOLD = 10

PIECE_VALUES = {"p": 100, "n": 320, "b": 330, "r": 500, "q": 900, "k": 20000}

TT_EXACT = 0
TT_LOWERBOUND = 1
TT_UPPERBOUND = 2

PAWN_TABLE = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [ 5,  5, 10, 25, 25, 10,  5,  5],
    [ 0,  0,  0, 20, 20,  0,  0,  0],
    [ 5, -5,-10,  0,  0,-10, -5,  5],
    [ 5, 10, 10,-25,-25, 10, 10,  5],
    [ 0,  0,  0,  0,  0,  0,  0,  0]
]
KNIGHT_TABLE = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50]
]
BISHOP_TABLE = [
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  5,  0,  0,  0,  0,  5,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20]
]
ROOK_TABLE = [
    [  0,  0,  0,  0,  0,  0,  0,  0],
    [  5, 10, 10, 10, 10, 10, 10,  5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [  0,  0,  0,  5,  5,  0,  0,  0]
]
QUEEN_TABLE = [
    [-20,-10,-10, -5, -5,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5,  5,  5,  5,  0,-10],
    [ -5,  0,  5,  5,  5,  5,  0, -5],
    [  0,  0,  5,  5,  5,  5,  0, -5],
    [-10,  5,  5,  5,  5,  5,  0,-10],
    [-10,  0,  5,  0,  0,  0,  0,-10],
    [-20,-10,-10, -5, -5,-10,-10,-20]
]
KING_MIDDLE_TABLE = [
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-20,-30,-30,-40,-40,-30,-30,-20],
    [-10,-20,-20,-20,-20,-20,-20,-10],
    [ 20, 20,  0,  0,  0,  0, 20, 20],
    [ 20, 30, 10,  0,  0, 10, 30, 20]
]
KING_END_TABLE = [
    [-50,-40,-30,-20,-20,-30,-40,-50],
    [-30,-20,-10,  0,  0,-10,-20,-30],
    [-30,-10, 20, 30, 30, 20,-10,-30],
    [-30,-10, 30, 40, 40, 30,-10,-30],
    [-30,-10, 30, 40, 40, 30,-10,-30],
    [-30,-10, 20, 30, 30, 20,-10,-30],
    [-30,-30,  0,  0,  0,  0,-30,-30],
    [-50,-30,-30,-30,-30,-30,-30,-50]
]

def mirror_table(table):
    return table[::-1]

PAWN_TABLE_BLACK = mirror_table(PAWN_TABLE)
KNIGHT_TABLE_BLACK = mirror_table(KNIGHT_TABLE)
BISHOP_TABLE_BLACK = mirror_table(BISHOP_TABLE)
ROOK_TABLE_BLACK = mirror_table(ROOK_TABLE)
QUEEN_TABLE_BLACK = mirror_table(QUEEN_TABLE)
KING_MIDDLE_TABLE_BLACK = mirror_table(KING_MIDDLE_TABLE)
KING_END_TABLE_BLACK = mirror_table(KING_END_TABLE)

PIECE_POSITION_TABLES = {
    'p': {'w': PAWN_TABLE, 'b': PAWN_TABLE_BLACK},
    'n': {'w': KNIGHT_TABLE, 'b': KNIGHT_TABLE_BLACK},
    'b': {'w': BISHOP_TABLE, 'b': BISHOP_TABLE_BLACK},
    'r': {'w': ROOK_TABLE, 'b': ROOK_TABLE_BLACK},
    'q': {'w': QUEEN_TABLE, 'b': QUEEN_TABLE_BLACK},
    'k': {'w': {'middle': KING_MIDDLE_TABLE, 'end': KING_END_TABLE},
          'b': {'middle': KING_MIDDLE_TABLE_BLACK, 'end': KING_END_TABLE_BLACK}}
}

CENTER_SQUARES = [(3,3), (3,4), (4,3), (4,4)]
CENTER_CONTROL_BONUS = 10
PASSED_PAWN_BONUS = [0, 5, 15, 30, 50, 75, 100, 0]
ISOLATED_PAWN_PENALTY = -15
DOUBLED_PAWN_PENALTY = -10
KING_SAFETY_PAWN_SHIELD_BONUS = 5
KING_SAFETY_ATTACK_PENALTY = -50


class ChessAI:
    def __init__(self, game: GameState, max_depth: int, color: str):
        self.game = game
        self.max_depth = max_depth
        self.ai_player_color = color
        self.ai_player_sign = 1 if color == 'w' else -1
        self.move_count = len(game.move_log)
        self.start_time = 0
        self.max_time = 0
        self.nodes_visited = 0
        self.q_nodes_visited = 0
        self.tt_hits = 0
        self.transposition_table = {}
        self.timeout_occurred = False

    def get_best_move(self, use_iterative_deepening=True, max_time_seconds=10.0):
        self.move_count = len(self.game.move_log)
        self.nodes_visited = 0
        self.q_nodes_visited = 0
        self.tt_hits = 0
        self.timeout_occurred = False
        best_move = None

        current_valid_moves = self.game.get_valid_moves()
        if self.game.checkmate or self.game.stalemate:
            return None
        if not current_valid_moves:
             return None

        try:
            if use_iterative_deepening:
                best_move = self.iterative_deepening(max_time=max_time_seconds)
            else:
                _, best_move = self.alphabeta_root(self.max_depth)

        except TimeoutError:
            pass
        except Exception as e:
            print(f"An unexpected error occurred during search: {e}") 
            traceback.print_exc()
            best_move = None

        if best_move is None:
            fallback_valid_moves = self.game.get_valid_moves()
            if not fallback_valid_moves:
                 return None
            best_move = self.fallback_move_selection(fallback_valid_moves)

        return best_move

    def iterative_deepening(self, max_time=5.0):
        self.start_time = time.time()
        self.max_time = max_time
       
        best_move_overall = None
        self.transposition_table.clear()

        initial_moves = self.game.get_valid_moves()
        if not initial_moves: return None

        for depth in range(1, self.max_depth + 1):
            self.nodes_visited = 0
            self.q_nodes_visited = 0
            self.tt_hits = 0
            self.timeout_occurred = False

            try:
                current_score, current_best_move_this_depth = self.alphabeta_root(depth, initial_moves)

                if self.timeout_occurred:
                    break

                if current_best_move_this_depth:
                    best_move_overall = current_best_move_this_depth
                   
                    if abs(current_score) > PIECE_VALUES['k']:
                         break
                else:
                     if not best_move_overall:
                         best_move_overall = random.choice(initial_moves) if initial_moves else None
                     break

                if time.time() - self.start_time > self.max_time * 0.95: 
                    break

            except TimeoutError:
                break
            except Exception as e:
                 print(f"ERROR during search at depth {depth}: {e}") 
                 traceback.print_exc()
                 break

        if not best_move_overall:
             best_move_overall = self.fallback_move_selection(initial_moves)

        self.start_time = 0
        self.max_time = 0

        return best_move_overall

    def fallback_move_selection(self, valid_moves):
        if not valid_moves: return None
        capture_moves = []
        other_moves = []
        for m in valid_moves:
            if m.piece_captured != '--':
                score = PIECE_VALUES.get(m.piece_captured[1], 0) * 10 - PIECE_VALUES.get(m.piece_moved[1], 0)
                capture_moves.append((score, m))
            else:
                other_moves.append(m)
        capture_moves.sort(key=lambda x: x[0], reverse=True)

        if capture_moves:
            selected = capture_moves[0][1]
            return selected
        else:
            selected = random.choice(other_moves)
            return selected

    def order_moves(self, moves):
        move_scores = []
        for move in moves:
            score = 0
            if move.piece_captured != '--':
                 score += 10 * PIECE_VALUES.get(move.piece_captured[1], 0) - PIECE_VALUES.get(move.piece_moved[1], 0)
                 score += 1000

            if move.is_pawn_promotion:
                 score += PIECE_VALUES['q']


            move_scores.append((score, move))

        move_scores.sort(key=lambda x: x[0], reverse=True)
        return [move for score, move in move_scores]

    def alphabeta_root(self, depth, initial_moves=None):
        if initial_moves is None:
             initial_moves = self.game.get_valid_moves()

        if not initial_moves: return (-float('inf') if self.game.white_to_move else float('inf')), None
        if self.game.stalemate: return 0, None

        ordered_moves = self.order_moves(initial_moves)
        best_move_found = ordered_moves[0]
        alpha = -float('inf')
        beta = float('inf')

        if self.game.white_to_move:
            max_eval = -float('inf')
            for move in ordered_moves:
                self.game.make_move(move)
                current_eval = self.alphabeta(depth - 1, alpha, beta)
                self.game.undo_move()

                if self.timeout_occurred: raise TimeoutError("Timeout")

                if current_eval > max_eval:
                    max_eval = current_eval
                    best_move_found = move
                alpha = max(alpha, current_eval)

            return max_eval, best_move_found
        else:
            min_eval = float('inf')
            for move in ordered_moves:
                self.game.make_move(move)
                current_eval = self.alphabeta(depth - 1, alpha, beta)
                self.game.undo_move()

                if self.timeout_occurred: raise TimeoutError("Timeout")

                if current_eval < min_eval:
                    min_eval = current_eval
                    best_move_found = move
                beta = min(beta, current_eval)

            return min_eval, best_move_found

    def alphabeta(self, depth, alpha, beta):
        self.nodes_visited += 1

        if self.nodes_visited % 2048 == 0:
            if self.start_time > 0 and time.time() - self.start_time > self.max_time:
                self.timeout_occurred = True
                return 0

        if self.timeout_occurred: return 0

        position_key = self.game._get_position_key()
        tt_entry = self.transposition_table.get(position_key)
        if tt_entry and tt_entry[1] >= depth:
             self.tt_hits += 1
             score, stored_depth, flag, _ = tt_entry
             if flag == TT_EXACT:
                 return score
             elif flag == TT_LOWERBOUND:
                 alpha = max(alpha, score)
             elif flag == TT_UPPERBOUND:
                 beta = min(beta, score)

             if alpha >= beta:
                 return score

        if depth <= 0:
            return self.quiescence_search(alpha, beta)

        valid_moves = self.game.get_valid_moves()
        if not valid_moves:
            if self.game.checkmate:
                 mate_score = float('inf') if not self.game.white_to_move else -float('inf')
                 return mate_score
            else:
                 return self.evaluate_stalemate()

        ordered_moves = self.order_moves(valid_moves)
        best_move_for_tt = ordered_moves[0]

        original_alpha = alpha
        if self.game.white_to_move:
            max_eval = -float('inf')
            for move in ordered_moves:
                self.game.make_move(move)
                current_eval = self.alphabeta(depth - 1, alpha, beta)
                self.game.undo_move()

                if self.timeout_occurred: return 0

                if current_eval > max_eval:
                     max_eval = current_eval
                     best_move_for_tt = move

                alpha = max(alpha, current_eval)
                if beta <= alpha:
                    break
            flag = TT_EXACT if max_eval > original_alpha and max_eval < beta else \
                   TT_LOWERBOUND if max_eval >= beta else TT_UPPERBOUND
            self.transposition_table[position_key] = (max_eval, depth, flag, best_move_for_tt)
            return max_eval
        else:
            min_eval = float('inf')
            for move in ordered_moves:
                self.game.make_move(move)
                current_eval = self.alphabeta(depth - 1, alpha, beta)
                self.game.undo_move()

                if self.timeout_occurred: return 0

                if current_eval < min_eval:
                    min_eval = current_eval
                    best_move_for_tt = move

                beta = min(beta, current_eval)
                if beta <= alpha:
                    break
            flag = TT_EXACT if min_eval > original_alpha and min_eval < beta else \
                   TT_UPPERBOUND if min_eval <= original_alpha else TT_LOWERBOUND
            self.transposition_table[position_key] = (min_eval, depth, flag, best_move_for_tt)
            return min_eval

    def quiescence_search(self, alpha, beta, depth_limit=4):
        self.q_nodes_visited += 1

        if self.q_nodes_visited % 1024 == 0:
             if self.start_time > 0 and time.time() - self.start_time > self.max_time:
                 self.timeout_occurred = True
                 return 0
        if self.timeout_occurred: return 0

        stand_pat_score = self.evaluate_board()

        if depth_limit <= 0:
            return stand_pat_score

        if self.game.white_to_move:
            alpha = max(alpha, stand_pat_score)
        else:
            beta = min(beta, stand_pat_score)

        if alpha >= beta:
             return stand_pat_score

        all_moves = self.game.get_valid_moves()
        capture_moves = [m for m in all_moves if m.piece_captured != '--' or m.is_pawn_promotion]
        ordered_captures = self.order_moves(capture_moves)

        if self.game.white_to_move:
            for move in ordered_captures:
                self.game.make_move(move)
                score = self.quiescence_search(alpha, beta, depth_limit - 1)
                self.game.undo_move()

                if self.timeout_occurred: return 0

                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return alpha

        else:
            for move in ordered_captures:
                self.game.make_move(move)
                score = self.quiescence_search(alpha, beta, depth_limit - 1)
                self.game.undo_move()

                if self.timeout_occurred: return 0

                beta = min(beta, score)
                if beta <= alpha:
                    break
            return beta


    def get_piece_counts_and_material(self, board):
        white_material = 0
        black_material = 0
        piece_count = 0
        white_pawns = []
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
        white_mat, black_mat, _, _, _ = self.get_piece_counts_and_material(self.game.board)
        material_diff = white_mat - black_mat

        ai_perspective_diff = material_diff * self.ai_player_sign

        if ai_perspective_diff > 300:
            return -50 * self.ai_player_sign
        elif ai_perspective_diff < -300:
             return 50 * self.ai_player_sign
        else:
             return 0


    def evaluate_board(self):
        white_material, black_material, piece_count, white_pawns, black_pawns = \
            self.get_piece_counts_and_material(self.game.board)
        material_score = white_material - black_material

        if piece_count > MIDDLEGAME_THRESHOLD: game_phase = 'middle'
        elif piece_count > ENDGAME_THRESHOLD: game_phase = 'middle'
        else: game_phase = 'end'

        position_score = 0
        pawn_structure_score = 0
        king_safety_score = 0
        center_control_score = 0

        white_king_pos = self.game.white_king_location
        black_king_pos = self.game.black_king_location

        for r in range(8):
            for c in range(8):
                piece = self.game.board[r][c]
                if piece != '--':
                    piece_type = piece[1]
                    piece_color = piece[0]
                    color_sign = 1 if piece_color == 'w' else -1

                    try:
                        if piece_type == 'k':
                             table = PIECE_POSITION_TABLES['k'][piece_color][game_phase]
                             position_score += table[r][c] * color_sign
                        else:
                             table = PIECE_POSITION_TABLES[piece_type][piece_color]
                             position_score += table[r][c] * color_sign
                    except KeyError: pass
                    except IndexError: pass  

                    if (r, c) in [(2,2),(2,3),(2,4),(2,5), (3,2),(3,3),(3,4),(3,5), (4,2),(4,3),(4,4),(4,5), (5,2),(5,3),(5,4),(5,5)]:
                        if piece_type in 'nbp':
                           center_control_score += (CENTER_CONTROL_BONUS / 2) * color_sign
                    if (r,c) in CENTER_SQUARES:
                         if piece_type in 'nbp':
                             center_control_score += (CENTER_CONTROL_BONUS / 2) * color_sign

                    if piece_type == 'p':
                        is_passed = True
                        for check_r in range(r + color_sign, 8 if color_sign == 1 else -1, color_sign):
                            if not (0 <= check_r < 8): break
                            for check_c_offset in [-1, 0, 1]:
                                check_c = c + check_c_offset
                                if 0 <= check_c < 8:
                                    opp_piece = self.game.board[check_r][check_c]
                                    if opp_piece != '--' and opp_piece[0] != piece_color and opp_piece[1] == 'p':
                                        is_passed = False
                                        break
                            if not is_passed: break
                        if is_passed:
                            rank_index = r if piece_color == 'b' else 7 - r
                            pawn_structure_score += PASSED_PAWN_BONUS[rank_index] * color_sign

        wp_counts = {col: white_pawns.count(col) for col in white_pawns}
        bp_counts = {col: black_pawns.count(col) for col in black_pawns}

        for col, count in wp_counts.items():
            if count > 1: pawn_structure_score += DOUBLED_PAWN_PENALTY * (count - 1)
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

        if game_phase == 'middle':
             wk_r, wk_c = white_king_pos
             for dr, dc in [( -1, -1), ( -1, 0), ( -1, 1)]:
                 pr, pc = wk_r + dr, wk_c + dc
                 if 0 <= pr < 8 and 0 <= pc < 8 and self.game.board[pr][pc] == 'wp':
                     king_safety_score += KING_SAFETY_PAWN_SHIELD_BONUS

             bk_r, bk_c = black_king_pos
             for dr, dc in [( 1, -1), ( 1, 0), ( 1, 1)]:
                  pr, pc = bk_r + dr, bk_c + dc
                  if 0 <= pr < 8 and 0 <= pc < 8 and self.game.board[pr][pc] == 'bp':
                      king_safety_score -= KING_SAFETY_PAWN_SHIELD_BONUS

        final_score = (material_score +
                       position_score * 0.5 +
                       pawn_structure_score * 0.8 +
                       king_safety_score * 1.0 +
                       center_control_score * 0.7)

        return final_score


    def _print_board(self): 
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

    def _get_piece_name(self, piece_code):  
        """Helper to get full piece name from code (e.g., 'wp' -> 'Pawn')."""
        names = {'p': 'Pawn', 'n': 'Knight', 'b': 'Bishop', 'r': 'Rook', 'q': 'Queen', 'k': 'King'}
        return names.get(piece_code[1], 'Unknown')