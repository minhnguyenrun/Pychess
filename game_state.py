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
        self.white_king_location = (7, 4) #if not player_wants_black else (0, 4)
        self.black_king_location = (0, 4) #if not player_wants_black else (7, 4)
        self.in_check = False
        self.pins = []
        self.checks = []
        self.checkmate = False
        self.stalemate = False
        self.en_passant_possible = ()
        self.en_passant_log = [self.en_passant_possible]
        self.castle_rights = CastleRights(True, True, True, True)
        self.castle_rights_log = [deepcopy(self.castle_rights)]
        self.position_history = {}  # For threefold repetition

    def make_move(self, move):
        self.board[move.start_row][move.start_col] = "--"
        if move.is_pawn_promotion:
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + 'q'  # Promote to queen
        else:
            self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move)
        self.white_to_move = not self.white_to_move

        # Update king location
        if move.piece_moved == 'wk':
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_moved == 'bk':
            self.black_king_location = (move.end_row, move.end_col)

        # Check if a king was captured
        if move.piece_captured == 'wk' or move.piece_captured == 'bk':
            # This should never happen - log an error
            print("ERROR: Attempted to capture a king, which is illegal")
            return False

        if move.is_en_passant:
            self.board[move.start_row][move.end_col] = '--'

        if move.piece_moved[1] == 'p' and abs(move.start_row - move.end_row) == 2:
            self.en_passant_possible = ((move.start_row + move.end_row) // 2, move.start_col)
        else:
            self.en_passant_possible = ()

        if move.is_castle:
            if move.end_col - move.start_col == 2:  # Kingside
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][move.end_col + 1]
                self.board[move.end_row][move.end_col + 1] = "--"
            else:  # Queenside
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 2]
                self.board[move.end_row][move.end_col - 2] = "--"

        self.update_castle_rights(move)
        self.castle_rights_log.append(deepcopy(self.castle_rights))
        self.en_passant_log.append(self.en_passant_possible)
        self.update_position_history()

    def undo_move(self):
        if not self.move_log:
            return
        move = self.move_log.pop()
        self.board[move.start_row][move.start_col] = move.piece_moved
        self.board[move.end_row][move.end_col] = move.piece_captured
        self.white_to_move = not self.white_to_move

        if move.piece_moved == 'wk':
            self.white_king_location = (move.start_row, move.start_col)
        elif move.piece_moved == 'bk':
            self.black_king_location = (move.start_row, move.start_col)

        # Restore king location if it was captured
        if move.piece_captured == 'wk':
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_captured == 'bk':
            self.black_king_location = (move.end_row, move.end_col)

        if move.is_en_passant:
            self.board[move.end_row][move.end_col] = "--"
            self.board[move.start_row][move.end_col] = move.piece_captured

        if move.is_castle:
            if move.end_col - move.start_col == 2:
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                self.board[move.end_row][move.end_col - 1] = "--"
            else:
                self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                self.board[move.end_row][move.end_col + 1] = "--"

        self.en_passant_log.pop()
        self.en_passant_possible = self.en_passant_log[-1]
        self.castle_rights_log.pop()
        self.castle_rights = deepcopy(self.castle_rights_log[-1])
        self.checkmate = self.stalemate = False
        self.position_history.pop(self.get_position_key(), None)

    def get_all_possible_moves_who(self, who_move):
        moves = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if (piece[0] == who_move):
                    self.move_functions[piece[1]](r, c, moves)
        return moves
   

    def get_all_possible_moves(self):
        moves = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if (piece[0] == 'w' and self.white_to_move) or (piece[0] == 'b' and not self.white_to_move):
                    self.move_functions[piece[1]](r, c, moves)
        return moves
    
    def get_valid_moves(self):
        moves = []
        self.in_check, self.pins, self.checks = self.check_for_pins_and_checks()
        king_row, king_col = self.white_king_location if self.white_to_move else self.black_king_location
        if self.in_check:
            print(f"DEBUG: King is in check, filtering {len(self.get_all_possible_moves())} initial moves")
        if self.in_check:
            if len(self.checks) == 1:
                # One check - can block, capture, or move king
                moves = self.get_all_possible_moves()
                check = self.checks[0]
                check_row, check_col = check[0], check[1]
                piece_checking = self.board[check_row][check_col]
    
                # Prioritize capturing the threatening piece
                capturing_moves = [m for m in moves if (m.end_row, m.end_col) == (check_row, check_col)]
                other_moves = [m for m in moves if (m.end_row, m.end_col) != (check_row, check_col)]
                moves = capturing_moves + other_moves
    
                # Filter moves that don't resolve the check
                valid_squares = [(check_row, check_col)]  # Already includes the checking piece's position
                if piece_checking[1] != 'n':  # If not a knight, calculate blocking squares
                    dr = 1 if check_row > king_row else -1 if check_row < king_row else 0
                    dc = 1 if check_col > king_col else -1 if check_col < king_col else 0
                    r, c = king_row + dr, king_col + dc
                    while (r, c) != (check_row, check_col):
                        valid_squares.append((r, c))
                        r, c = r + dr, c + dc
                
                # For debugging: Print all valid moves when in check (especially for knight checks)
                if piece_checking[1] == 'n':
                    print(f"Knight check at {check_row},{check_col} - valid squares: {valid_squares}")
                    print(f"Capturing moves: {[(m.piece_moved, m.start_row, m.start_col, m.end_row, m.end_col) for m in capturing_moves]}")
                
                for i in range(len(moves) - 1, -1, -1):
                    if moves[i].piece_moved[1] != 'k' and (moves[i].end_row, moves[i].end_col) not in valid_squares:
                        moves.pop(i)
                    else:
                        self.make_move(moves[i])
                        self.white_to_move = not self.white_to_move
                        in_check_after_move, _, _ = self.check_for_pins_and_checks()
                        if in_check_after_move:
                            moves.pop(i)
                        self.white_to_move = not self.white_to_move
                        self.undo_move()
            else:
                # Multiple checks - king must move
                self.get_king_moves(king_row, king_col, moves)
    
                # Filter moves that don't resolve the check
                for i in range(len(moves) - 1, -1, -1):
                    self.make_move(moves[i])
                    self.white_to_move = not self.white_to_move
                    in_check_after_move, _, _ = self.check_for_pins_and_checks()
                    if in_check_after_move:
                        moves.pop(i)
                    self.white_to_move = not self.white_to_move
                    self.undo_move()
        else:
            moves = self.get_all_possible_moves()
    
            # Prioritize moves that capture threatening pieces or escape threats
            prioritized_moves = []
            for move in moves:
                self.make_move(move)
                self.white_to_move = not self.white_to_move
                in_check_after_move, _, _ = self.check_for_pins_and_checks()
                if not in_check_after_move:
                    if move.piece_captured != '--':  # Capturing a piece
                        prioritized_moves.append((1, move))  # High priority for captures
                    else:
                        prioritized_moves.append((2, move))  # Lower priority for non-captures
                self.white_to_move = not self.white_to_move
                self.undo_move()
    
            # Sort moves by priority (captures first)
            prioritized_moves.sort(key=lambda x: x[0])
            moves = [m[1] for m in prioritized_moves]
        if self.in_check:
            if len(moves) == 0:
                print(f"DEBUG: No moves found that resolve check - potential checkmate for {'White' if not self.white_to_move else 'Black'}")
                print(f"CHECKMATE: {'Black' if self.white_to_move else 'White'} wins")
            else:
                print(f"DEBUG: {len(moves)} moves found that resolve check")
                for move in moves[:5]:  # Print first few moves only
                    print(f"  - {move.piece_moved} from {chr(97+move.start_col)}{8-move.start_row} to {chr(97+move.end_col)}{8-move.end_row}")
        
        if len(moves) == 0:
            if self.in_check:
                self.checkmate = True
                winner = "Black" if self.white_to_move else "White"
                print(f"CHECKMATE: {winner} wins")
                # Important: return empty moves list to prevent further play
                return []
            else:
                self.stalemate = True
                print("STALEMATE")
        
        return moves
        
    def check_for_pins_and_checks(self):
        pins, checks = [], []
        in_check = False
        ally_color = 'w' if self.white_to_move else 'b'
        king_row, king_col = self.white_king_location if self.white_to_move else self.black_king_location

        if king_row is None or king_col is None:
            return in_check, pins, checks

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

        for j, (dr, dc) in enumerate(directions):
            possible_pin = ()
            for i in range(1, 8):
                r, c = king_row + dr * i, king_col + dc * i
                if not (0 <= r < 8 and 0 <= c < 8):
                    break
                piece = self.board[r][c]
                if piece[0] == ally_color and piece[1] != 'k':
                    if not possible_pin:
                        possible_pin = (r, c, dr, dc)
                    else:
                        break
                elif piece[0] != ally_color and piece != '--':
                    if piece[1] == 'k' and i == 1:  # Adjacent king check
                        in_check = True
                        checks.append((r, c, dr, dc))
                        #print(f"King check detected at ({r}, {c})")  # Debug
                        break
                    if (0 <= j <= 3 and piece[1] == 'r') or (4 <= j <= 7 and piece[1] == 'b') or \
                    (piece[1] == 'q') or (i == 1 and piece[1] == 'k') or \
                    (i == 1 and piece[1] == 'p' and ((ally_color == 'b' and 4 <= j <= 5) or (ally_color == 'w' and 6 <= j <= 7))):
                        if possible_pin:
                            pins.append(possible_pin)
                        else:
                            in_check = True
                            checks.append((r, c, dr, dc))
                        break
                    break

        knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        for dr, dc in knight_moves:
            r, c = king_row + dr, king_col + dc
            if 0 <= r < 8 and 0 <= c < 8 and self.board[r][c] != '--' and self.board[r][c][0] != ally_color and self.board[r][c][1] == 'n':
                in_check = True
                checks.append((r, c, dr, dc))

        return in_check, pins, checks

    def square_under_attack(self, r, c, ally_color):
        enemy_color = 'b' if ally_color == 'w' else 'w'
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for j, (dr, dc) in enumerate(directions):
            for i in range(1, 8):
                nr, nc = r + dr * i, c + dc * i
                if not (0 <= nr < 8 and 0 <= nc < 8):
                    break
                piece = self.board[nr][nc]
                if piece[0] == ally_color:
                    break
                elif piece[0] == enemy_color:
                    if (0 <= j <= 3 and piece[1] == 'r') or (4 <= j <= 7 and piece[1] == 'b') or \
                       (piece[1] == 'q') or (i == 1 and piece[1] == 'k') or \
                       (i == 1 and piece[1] == 'p' and ((enemy_color == 'w' and 6 <= j <= 7) or (enemy_color == 'b' and 4 <= j <= 5))):
                        return True
                    break
        for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and self.board[nr][nc] != '--' and self.board[nr][nc][0] == enemy_color and self.board[nr][nc][1] == 'n':
                return True
        return False

    # def get_pawn_moves(self, r, c, moves):
    #     piece_pinned = False
    #     pin_dir = None
    #     for i in range(len(self.pins) - 1, -1, -1):
    #         if self.pins[i][0] == r and self.pins[i][1] == c:
    #             piece_pinned = True
    #             pin_dir = (self.pins[i][2], self.pins[i][3])
    #             self.pins.pop(i)
    #             break

    #     direction = -1 if self.white_to_move else 1
    #     start_row = 6 if self.white_to_move else 1
    #     enemy_color = 'b' if self.white_to_move else 'w'
    #     promotion_row = 0 if self.white_to_move else 7

    #     if 0 <= r + direction < 8 and self.board[r + direction][c] == '--' and (not piece_pinned or pin_dir == (direction, 0)):
    #         if r + direction == promotion_row:
    #             moves.append(Move((r, c), (r + direction, c), self.board, is_pawn_promotion=True))
    #         else:
    #             moves.append(Move((r, c), (r + direction, c), self.board))
    #         if r == start_row and self.board[r + 2 * direction][c] == '--':
    #             moves.append(Move((r, c), (r + 2 * direction, c), self.board))

    #     for dc in [-1, 1]:
    #         if 0 <= c + dc < 8 and 0 <= r + direction < 8 and (not piece_pinned or pin_dir == (direction, dc)):
    #             target = self.board[r + direction][c + dc]
    #             if target != '--' and target[0] == enemy_color:
    #                 if r + direction == promotion_row:
    #                     moves.append(Move((r, c), (r + direction, c + dc), self.board, is_pawn_promotion=True))
    #                 else:
    #                     moves.append(Move((r, c), (r + direction, c + dc), self.board))
    #             elif (r + direction, c + dc) == self.en_passant_possible:
    #                 moves.append(Move((r, c), (r + direction, c + dc), self.board, is_en_passant=True))

    def get_pawn_moves(self, r, c, moves):
        piece_pinned = False
        pin_dir = None
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piece_pinned = True
                pin_dir = (self.pins[i][2], self.pins[i][3])
                self.pins.pop(i)
                break

        direction = -1 if self.white_to_move else 1
        start_row = 6 if self.white_to_move else 1
        enemy_color = 'b' if self.white_to_move else 'w'
        promotion_row = 0 if self.white_to_move else 7

        # Only generate moves if the pawn is not pinned or can move along the pin direction
        if 0 <= r + direction < 8 and self.board[r + direction][c] == '--' and (not piece_pinned or pin_dir == (direction, 0)):
            if r + direction == promotion_row:
                moves.append(Move((r, c), (r + direction, c), self.board, is_pawn_promotion=True))
            else:
                moves.append(Move((r, c), (r + direction, c), self.board))
            if r == start_row and self.board[r + 2 * direction][c] == '--':
                moves.append(Move((r, c), (r + 2 * direction, c), self.board))

        for dc in [-1, 1]:
            if 0 <= c + dc < 8 and 0 <= r + direction < 8 and (not piece_pinned or pin_dir == (direction, dc)):
                target = self.board[r + direction][c + dc]
                if target != '--' and target[0] == enemy_color:
                    if r + direction == promotion_row:
                        moves.append(Move((r, c), (r + direction, c + dc), self.board, is_pawn_promotion=True))
                    else:
                        moves.append(Move((r, c), (r + direction, c + dc), self.board))
                elif (r + direction, c + dc) == self.en_passant_possible:
                    moves.append(Move((r, c), (r + direction, c + dc), self.board, is_en_passant=True))

    def get_rook_moves(self, r, c, moves):
        piece_pinned = False
        pin_dir = None
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piece_pinned = True
                pin_dir = (self.pins[i][2], self.pins[i][3])
                if self.board[r][c][1] != 'q':
                    self.pins.pop(i)
                break

        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        enemy_color = 'b' if self.white_to_move else 'w'
        for dr, dc in directions:
            for i in range(1, 8):
                nr, nc = r + dr * i, c + dc * i
                if not (0 <= nr < 8 and 0 <= nc < 8):
                    break
                if not piece_pinned or pin_dir == (dr, dc) or pin_dir == (-dr, -dc):
                    target = self.board[nr][nc]
                    if target == '--':
                        moves.append(Move((r, c), (nr, nc), self.board))
                    elif target[0] == enemy_color:
                        moves.append(Move((r, c), (nr, nc), self.board))
                        break
                    else:
                        break

    def get_knight_moves(self, r, c, moves):
        piece_pinned = False
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piece_pinned = True
                self.pins.pop(i)
                break

        knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        enemy_color = 'b' if self.white_to_move else 'w'
        if not piece_pinned:
            for dr, dc in knight_moves:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    target = self.board[nr][nc]
                    if target == '--' or target[0] == enemy_color:
                        moves.append(Move((r, c), (nr, nc), self.board))

    def get_bishop_moves(self, r, c, moves):
        piece_pinned = False
        pin_dir = None
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piece_pinned = True
                pin_dir = (self.pins[i][2], self.pins[i][3])
                self.pins.pop(i)
                break

        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        enemy_color = 'b' if self.white_to_move else 'w'
        for dr, dc in directions:
            for i in range(1, 8):
                nr, nc = r + dr * i, c + dc * i
                if not (0 <= nr < 8 and 0 <= nc < 8):
                    break
                if not piece_pinned or pin_dir == (dr, dc) or pin_dir == (-dr, -dc):
                    target = self.board[nr][nc]
                    if target == '--':
                        moves.append(Move((r, c), (nr, nc), self.board))
                    elif target[0] == enemy_color:
                        moves.append(Move((r, c), (nr, nc), self.board))
                        break
                    else:
                        break

    def get_queen_moves(self, r, c, moves):
        self.get_rook_moves(r, c, moves)
        self.get_bishop_moves(r, c, moves)

    def get_king_moves(self, r, c, moves):
        ally_color = 'w' if self.white_to_move else 'b'
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        original_king_loc = self.white_king_location if ally_color == 'w' else self.black_king_location

        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                target = self.board[nr][nc]
                if target[0] != ally_color:  # Not an ally piece
                    # Check if the destination square is under attack
                    if not self.square_under_attack(nr, nc, ally_color):
                        if ally_color == 'w':
                            self.white_king_location = (nr, nc)
                        else:
                            self.black_king_location = (nr, nc)
                        in_check, _, _ = self.check_for_pins_and_checks()
                        if not in_check:
                            moves.append(Move((r, c), (nr, nc), self.board))
                        if ally_color == 'w':
                            self.white_king_location = original_king_loc
                        else:
                            self.black_king_location = original_king_loc

        if not self.in_check:
            if (self.white_to_move and self.castle_rights.wks) or (not self.white_to_move and self.castle_rights.bks):
                if self.board[r][c + 1] == "--" and self.board[r][c + 2] == "--" and \
                   not self.square_under_attack(r, c + 1, ally_color) and not self.square_under_attack(r, c + 2, ally_color):
                    moves.append(Move((r, c), (r, c + 2), self.board, is_castle=True))
            if (self.white_to_move and self.castle_rights.wqs) or (not self.white_to_move and self.castle_rights.bqs):
                if self.board[r][c - 1] == "--" and self.board[r][c - 2] == "--" and self.board[r][c - 3] == "--" and \
                   not self.square_under_attack(r, c - 1, ally_color) and not self.square_under_attack(r, c - 2, ally_color):
                    moves.append(Move((r, c), (r, c - 2), self.board, is_castle=True))

    def update_castle_rights(self, move):
        if move.piece_moved == 'wk':
            self.castle_rights.wks = self.castle_rights.wqs = False
        elif move.piece_moved == 'bk':
            self.castle_rights.bks = self.castle_rights.bqs = False
        if move.piece_captured == 'wr' and move.end_row == 7:
            self.castle_rights.wqs = False if move.end_col == 0 else self.castle_rights.wqs
            self.castle_rights.wks = False if move.end_col == 7 else self.castle_rights.wks
        elif move.piece_captured == 'br' and move.end_row == 0:
            self.castle_rights.bqs = False if move.end_col == 0 else self.castle_rights.bqs
            self.castle_rights.bks = False if move.end_col == 7 else self.castle_rights.bks

    def update_position_history(self):
        key = self.get_position_key()
        self.position_history[key] = self.position_history.get(key, 0) + 1

    def get_position_key(self):
        return ''.join(''.join(row) for row in self.board) + str(self.white_to_move) + str(self.castle_rights.wks) + \
               str(self.castle_rights.wqs) + str(self.castle_rights.bks) + str(self.castle_rights.bqs) + str(self.en_passant_possible)

    def is_threefold_repetition(self):
        return False#any(count >= 3 for count in self.position_history.values())

    def is_insufficient_material(self):
        pieces = [self.board[r][c] for r in range(8) for c in range(8) if self.board[r][c] != '--']
        piece_counts = Counter(piece[1] for piece in pieces)
        if len(pieces) == 2:  # Only kings
            return True
        if len(pieces) == 3 and (piece_counts['n'] == 1 or piece_counts['b'] == 1):  # King + Knight or King + Bishop
            return True
        return False

class CastleRights:
    def __init__(self, wks, wqs, bks, bqs):
        self.wks, self.wqs, self.bks, self.bqs = wks, wqs, bks, bqs

class Move:
    def __init__(self, start_sq, end_sq, board, is_en_passant=False, is_castle=False, is_pawn_promotion=False):
        self.start_row, self.start_col = start_sq
        self.end_row, self.end_col = end_sq
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col] if not is_en_passant else board[self.start_row][self.end_col]
        self.is_en_passant = is_en_passant
        self.is_castle = is_castle
        self.is_pawn_promotion = is_pawn_promotion
        self.move_id = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col

    def __eq__(self, other):
        return isinstance(other, Move) and self.move_id == other.move_id

    def get_notation(self):
        ranks = "87654321"
        files = "abcdefgh"
        return f"{files[self.start_col]}{ranks[self.start_row]}{files[self.end_col]}{ranks[self.end_row]}"