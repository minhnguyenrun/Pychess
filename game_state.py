from copy import deepcopy
from collections import Counter

class GameState:
    def __init__(self, player_wants_black=False):
        self.board = [
            ['br', 'bn', 'bb', 'bq', 'bk', 'bb', 'bn', 'br'],
            ['bp', 'bp', 'bp', 'bp', 'bp', 'bp', 'bp', 'bp'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['wp', 'wp', 'wp', 'wp', 'wp', 'wp', 'wp', 'wp'],
            ['wr', 'wn', 'wb', 'wq', 'wk', 'wb', 'wn', 'wr']
        ]

        self.move_functions = {'p': self.get_pawn_moves, 'r': self.get_rook_moves, 'n': self.get_knight_moves,
                              'b': self.get_bishop_moves, 'q': self.get_queen_moves, 'k': self.get_king_moves}
        self.white_to_move = True
        self.player_wants_black = player_wants_black
        self.move_log = []
        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)
        self.in_check = False
        self.pins = []
        self.checks = []
        self.checkmate = False
        self.stalemate = False
        self.en_passant_possible = ()
        self.en_passant_log = [self.en_passant_possible]

        self.castle_rights = CastleRights(True, True, True, True)
        self.castle_rights_log = [deepcopy(self.castle_rights)]

        self.position_history = {}
        self._update_position_history()

    def make_move(self, move):
        if self.board[move.start_row][move.start_col] == '--':
            print(f"ERROR: Attempting to move from empty square: {move.get_notation()}")
            return

        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_moved

        if move.piece_moved == 'wk':
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_moved == 'bk':
            self.black_king_location = (move.end_row, move.end_col)

        if move.is_pawn_promotion:
            promote_to = move.promotion_choice if move.promotion_choice in ['q', 'r', 'b', 'n'] else 'q'
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + promote_to

        if move.is_en_passant:
            self.board[move.start_row][move.end_col] = '--'

        if move.piece_moved[1] == 'p' and abs(move.start_row - move.end_row) == 2:
            self.en_passant_possible = ((move.start_row + move.end_row) // 2, move.start_col)
        else:
            self.en_passant_possible = ()

        if move.is_castle:
            if move.end_col - move.start_col == 2:
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][move.end_col + 1]
                self.board[move.end_row][move.end_col + 1] = "--"
            else:
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 2]
                self.board[move.end_row][move.end_col - 2] = "--"


        self.update_castle_rights(move)
        self.castle_rights_log.append(deepcopy(self.castle_rights))
        self.en_passant_log.append(self.en_passant_possible)

        self.move_log.append(move)
        self.white_to_move = not self.white_to_move

        self._update_position_history()
        self.checkmate = False
        self.stalemate = False


    def undo_move(self):
        if not self.move_log:
            return

        move = self.move_log.pop()

        key_to_decrement = self._get_position_key()

        self.white_to_move = not self.white_to_move

        self.board[move.start_row][move.start_col] = move.piece_moved
        self.board[move.end_row][move.end_col] = move.piece_captured

        if move.piece_moved == 'wk':
            self.white_king_location = (move.start_row, move.start_col)
        elif move.piece_moved == 'bk':
            self.black_king_location = (move.start_row, move.start_col)

        if move.is_en_passant:
            self.board[move.end_row][move.end_col] = "--"
            captured_pawn_color = 'b' if self.white_to_move else 'w'
            self.board[move.start_row][move.end_col] = captured_pawn_color + 'p'

        self.en_passant_log.pop()
        self.en_passant_possible = self.en_passant_log[-1]
        self.castle_rights_log.pop()
        self.castle_rights = deepcopy(self.castle_rights_log[-1])
        if move.is_castle:
            if move.end_col - move.start_col == 2:
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                self.board[move.end_row][move.end_col - 1] = "--"
            else:
                self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                self.board[move.end_row][move.end_col + 1] = "--"

        self.checkmate = False
        self.stalemate = False
        self.in_check = False
        self.pins = []
        self.checks = []

        if key_to_decrement in self.position_history:
            self.position_history[key_to_decrement] -= 1
            if self.position_history[key_to_decrement] <= 0:
                 del self.position_history[key_to_decrement]
        else:
            print(f"WARNING: Attempted to decrement history count for an unknown key: {key_to_decrement}")



    def get_valid_moves(self):
        if self.is_threefold_repetition():
            self.stalemate = True
            return []

        temp_en_passant = self.en_passant_possible
        temp_castle_rights = deepcopy(self.castle_rights)

        moves = self.get_all_possible_moves()

        self.get_castle_moves(self.white_king_location[0], self.white_king_location[1], moves) if self.white_to_move else \
        self.get_castle_moves(self.black_king_location[0], self.black_king_location[1], moves)

        self.castle_rights = temp_castle_rights

        for i in range(len(moves) - 1, -1, -1):
            move = moves[i]
            self.make_move(move)
            self.white_to_move = not self.white_to_move
            if self.is_in_check():
                moves.pop(i)

            self.white_to_move = not self.white_to_move
            self.undo_move()

        if len(moves) == 0:
            if self.is_in_check():
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

        self.en_passant_possible = temp_en_passant

        if not self.checkmate and not self.stalemate and self.is_insufficient_material():
            self.stalemate = True
            return []
        return moves

    def is_in_check(self):
        king_pos = self.white_king_location if self.white_to_move else self.black_king_location
        return self.square_under_attack(king_pos[0], king_pos[1])

    def square_under_attack(self, r, c):
        self.white_to_move = not self.white_to_move
        opponent_moves = self.get_all_possible_moves()
        self.white_to_move = not self.white_to_move

        for move in opponent_moves:
            if move.end_row == r and move.end_col == c:
                return True
        return False

    def get_all_possible_moves(self):
        moves = []
        for r in range(8):
            for c in range(8):
                turn = self.board[r][c][0]
                if (turn == 'w' and self.white_to_move) or \
                   (turn == 'b' and not self.white_to_move):
                    piece = self.board[r][c][1]
                    self.move_functions[piece](r, c, moves)
        return moves

    def get_pawn_moves(self, r, c, moves):
        piece_color = self.board[r][c][0]
        direction = -1 if piece_color == 'w' else 1
        enemy_color = 'b' if piece_color == 'w' else 'w'
        start_row = 6 if piece_color == 'w' else 1
        promotion_row = 0 if piece_color == 'w' else 7

        if 0 <= r + direction < 8 and self.board[r + direction][c] == "--":
            if r + direction == promotion_row:
                 moves.append(Move((r, c), (r + direction, c), self.board, is_pawn_promotion=True))
            else:
                 moves.append(Move((r, c), (r + direction, c), self.board))
            if r == start_row and self.board[r + 2 * direction][c] == "--":
                moves.append(Move((r, c), (r + 2 * direction, c), self.board))

        for dc in [-1, 1]:
            if 0 <= c + dc < 8 and 0 <= r + direction < 8:
                target_square = self.board[r + direction][c + dc]
                if target_square[0] == enemy_color:
                    if r + direction == promotion_row:
                        moves.append(Move((r, c), (r + direction, c + dc), self.board, is_pawn_promotion=True))
                    else:
                        moves.append(Move((r, c), (r + direction, c + dc), self.board))
                elif (r + direction, c + dc) == self.en_passant_possible:
                    moves.append(Move((r, c), (r + direction, c + dc), self.board, is_en_passant=True))

    def get_rook_moves(self, r, c, moves):
        ally_color = self.board[r][c][0]
        directions = ((1, 0), (-1, 0), (0, 1), (0, -1))
        for dr, dc in directions:
            for i in range(1, 8):
                end_row, end_col = r + dr * i, c + dc * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece == "--":
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                    elif end_piece[0] != ally_color:
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                        break
                    else:
                        break
                else:
                    break

    def get_knight_moves(self, r, c, moves):
        ally_color = self.board[r][c][0]
        knight_moves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2),
                        (1, -2), (1, 2), (2, -1), (2, 1))
        for dr, dc in knight_moves:
            end_row, end_col = r + dr, c + dc
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:
                    moves.append(Move((r, c), (end_row, end_col), self.board))

    def get_bishop_moves(self, r, c, moves):
        ally_color = self.board[r][c][0]
        directions = ((1, 1), (1, -1), (-1, 1), (-1, -1))
        for dr, dc in directions:
            for i in range(1, 8):
                end_row, end_col = r + dr * i, c + dc * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece == "--":
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                    elif end_piece[0] != ally_color:
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                        break
                    else:
                        break
                else:
                    break

    def get_queen_moves(self, r, c, moves):
        self.get_rook_moves(r, c, moves)
        self.get_bishop_moves(r, c, moves)

    def get_king_moves(self, r, c, moves):
        ally_color = self.board[r][c][0]
        king_moves = ((1, 0), (-1, 0), (0, 1), (0, -1),
                      (1, 1), (1, -1), (-1, 1), (-1, -1))
        for dr, dc in king_moves:
            end_row, end_col = r + dr, c + dc
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:
                    moves.append(Move((r, c), (end_row, end_col), self.board))

    def get_castle_moves(self, r, c, moves):
         if self.square_under_attack(r, c):
             return

         ally_color = 'w' if self.white_to_move else 'b'

         if (self.white_to_move and self.castle_rights.wks) or \
            (not self.white_to_move and self.castle_rights.bks):
             if self.board[r][c + 1] == "--" and self.board[r][c + 2] == "--":
                 if not self.square_under_attack(r, c + 1) and \
                    not self.square_under_attack(r, c + 2):
                     moves.append(Move((r, c), (r, c + 2), self.board, is_castle=True))

         if (self.white_to_move and self.castle_rights.wqs) or \
            (not self.white_to_move and self.castle_rights.bqs):
             if self.board[r][c - 1] == "--" and self.board[r][c - 2] == "--" and \
                self.board[r][c - 3] == "--":
                  if not self.square_under_attack(r, c - 1) and \
                     not self.square_under_attack(r, c - 2):
                      moves.append(Move((r, c), (r, c - 2), self.board, is_castle=True))


    def update_castle_rights(self, move):
        if move.piece_moved == 'wk':
            self.castle_rights.wks = False
            self.castle_rights.wqs = False
        elif move.piece_moved == 'bk':
            self.castle_rights.bks = False
            self.castle_rights.bqs = False

        if move.piece_moved == 'wr':
            if move.start_row == 7:
                if move.start_col == 0:
                    self.castle_rights.wqs = False
                elif move.start_col == 7:
                    self.castle_rights.wks = False
        elif move.piece_moved == 'br':
             if move.start_row == 0:
                if move.start_col == 0:
                    self.castle_rights.bqs = False
                elif move.start_col == 7:
                    self.castle_rights.bks = False

        if move.piece_captured == 'wr':
            if move.end_row == 7:
                if move.end_col == 0:
                    self.castle_rights.wqs = False
                elif move.end_col == 7:
                    self.castle_rights.wks = False
        elif move.piece_captured == 'br':
            if move.end_row == 0:
                if move.end_col == 0:
                    self.castle_rights.bqs = False
                elif move.end_col == 7:
                    self.castle_rights.bks = False

    def _update_position_history(self):
        key = self._get_position_key()
        self.position_history[key] = self.position_history.get(key, 0) + 1

    def _get_position_key(self):
        return ''.join(''.join(row) for row in self.board) + \
               ('w' if self.white_to_move else 'b') + \
               ('K' if self.castle_rights.wks else '') + \
               ('Q' if self.castle_rights.wqs else '') + \
               ('k' if self.castle_rights.bks else '') + \
               ('q' if self.castle_rights.bqs else '') + \
               (str(self.en_passant_possible) if self.en_passant_possible else '-')

    def is_threefold_repetition(self):
        key = self._get_position_key()
        return self.position_history.get(key, 0) >= 3

    def is_insufficient_material(self):
        piece_counts = Counter()
        other_pieces = 0
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece != '--' and piece[1] != 'k':
                    piece_counts[piece] += 1
                    other_pieces += 1

        if other_pieces == 0:
            return True
        if other_pieces == 1 and (piece_counts['wn'] == 1 or piece_counts['bn'] == 1):
            return True
        if other_pieces == 1 and (piece_counts['wb'] == 1 or piece_counts['bb'] == 1):
            return True
        if other_pieces == 2 and piece_counts['wb'] == 1 and piece_counts['bb'] == 1:
            wb_pos = None
            bb_pos = None
            for r in range(8):
                for c in range(8):
                    piece = self.board[r][c]
                    if piece == 'wb': wb_pos = (r, c)
                    if piece == 'bb': bb_pos = (r, c)
            if wb_pos and bb_pos:
                 if (wb_pos[0] + wb_pos[1]) % 2 == (bb_pos[0] + bb_pos[1]) % 2:
                     return True

        return False

class CastleRights:
    def __init__(self, wks, wqs, bks, bqs):
        self.wks = wks
        self.wqs = wqs
        self.bks = bks
        self.bqs = bqs

class Move:
    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4,
                     "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3,
                     "e": 4, "f": 5, "g": 6, "h": 7}
    cols_to_files = {v: k for k, v in files_to_cols.items()}

    def __init__(self, start_sq, end_sq, board, is_en_passant=False, is_castle=False, is_pawn_promotion=False, promotion_choice='q'):
        self.start_row, self.start_col = start_sq
        self.end_row, self.end_col = end_sq
        self.piece_moved = board[self.start_row][self.start_col]

        if is_en_passant:
             captured_pawn_color = 'b' if self.piece_moved[0] == 'w' else 'w'
             self.piece_captured = captured_pawn_color + 'p'
        elif is_castle:
            self.piece_captured = '--'
        else:
             self.piece_captured = board[self.end_row][self.end_col]

        self.is_en_passant = is_en_passant
        self.is_castle = is_castle
        self.is_pawn_promotion = is_pawn_promotion and (self.piece_moved[1] == 'p') and (self.end_row == 0 or self.end_row == 7)
        self.promotion_choice = promotion_choice if self.is_pawn_promotion else None
        self.move_id = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col

    def __eq__(self, other):
        return isinstance(other, Move) and self.move_id == other.move_id

    def __str__(self):
        return self.get_notation()

    def get_notation(self):
        if self.is_castle:
            return "O-O" if self.end_col > self.start_col else "O-O-O"

        start = self.get_rank_file(self.start_row, self.start_col)
        end = self.get_rank_file(self.end_row, self.end_col)
        notation = start + end

        if self.is_pawn_promotion:
            notation += 'q'

        return notation

    def get_rank_file(self, r, c):
        return self.cols_to_files[c] + self.rows_to_ranks[r]