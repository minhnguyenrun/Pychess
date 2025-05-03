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
    
    # def get_valid_moves(self):
    #     moves = []
    #     self.in_check, self.pins, self.checks = self.check_for_pins_and_checks()
    #     king_row, king_col = self.white_king_location if self.white_to_move else self.black_king_location
    #     if self.in_check:
    #         print(f"DEBUG: King is in check, filtering {len(self.get_all_possible_moves())} initial moves")
    #     if self.in_check:
    #         if len(self.checks) == 1:
    #             # One check - can block, capture, or move king
    #             moves = self.get_all_possible_moves()
    #             check = self.checks[0]
    #             check_row, check_col = check[0], check[1]
    #             piece_checking = self.board[check_row][check_col]
    
    #             # Prioritize capturing the threatening piece
    #             capturing_moves = [m for m in moves if (m.end_row, m.end_col) == (check_row, check_col)]
    #             other_moves = [m for m in moves if (m.end_row, m.end_col) != (check_row, check_col)]
    #             moves = capturing_moves + other_moves
    
    #             # Filter moves that don't resolve the check
    #             valid_squares = [(check_row, check_col)]  # Already includes the checking piece's position
    #             if piece_checking[1] != 'n':  # If not a knight, calculate blocking squares
    #                 dr = 1 if check_row > king_row else -1 if check_row < king_row else 0
    #                 dc = 1 if check_col > king_col else -1 if check_col < king_col else 0
    #                 r, c = king_row + dr, king_col + dc
    #                 while (r, c) != (check_row, check_col):
    #                     valid_squares.append((r, c))
    #                     r, c = r + dr, c + dc
                
    #             # For debugging: Print all valid moves when in check (especially for knight checks)
    #             if piece_checking[1] == 'n':
    #                 print(f"Knight check at {check_row},{check_col} - valid squares: {valid_squares}")
    #                 print(f"Capturing moves: {[(m.piece_moved, m.start_row, m.start_col, m.end_row, m.end_col) for m in capturing_moves]}")
                
    #             for i in range(len(moves) - 1, -1, -1):
    #                 if moves[i].piece_moved[1] != 'k' and (moves[i].end_row, moves[i].end_col) not in valid_squares:
    #                     moves.pop(i)
    #                 else:
    #                     self.make_move(moves[i])
    #                     self.white_to_move = not self.white_to_move
    #                     in_check_after_move, _, _ = self.check_for_pins_and_checks()
    #                     if in_check_after_move:
    #                         moves.pop(i)
    #                     self.white_to_move = not self.white_to_move
    #                     self.undo_move()
    #         else:
    #             # Multiple checks - king must move
    #             self.get_king_moves(king_row, king_col, moves)
    
    #             # Filter moves that don't resolve the check
    #             for i in range(len(moves) - 1, -1, -1):
    #                 self.make_move(moves[i])
    #                 self.white_to_move = not self.white_to_move
    #                 in_check_after_move, _, _ = self.check_for_pins_and_checks()
    #                 if in_check_after_move:
    #                     moves.pop(i)
    #                 self.white_to_move = not self.white_to_move
    #                 self.undo_move()
    #     else:
    #         moves = self.get_all_possible_moves()
    
    #         # Prioritize moves that capture threatening pieces or escape threats
    #         prioritized_moves = []
    #         for move in moves:
    #             self.make_move(move)
    #             self.white_to_move = not self.white_to_move
    #             in_check_after_move, _, _ = self.check_for_pins_and_checks()
    #             if not in_check_after_move:
    #                 if move.piece_captured != '--':  # Capturing a piece
    #                     prioritized_moves.append((1, move))  # High priority for captures
    #                 else:
    #                     prioritized_moves.append((2, move))  # Lower priority for non-captures
    #             self.white_to_move = not self.white_to_move
    #             self.undo_move()
    
    #         # Sort moves by priority (captures first)
    #         prioritized_moves.sort(key=lambda x: x[0])
    #         moves = [m[1] for m in prioritized_moves]
    #     if self.in_check:
    #         if len(moves) == 0:
    #             print(f"DEBUG: No moves found that resolve check - potential checkmate for {'White' if not self.white_to_move else 'Black'}")
    #             print(f"CHECKMATE: {'Black' if self.white_to_move else 'White'} wins")
    #         else:
    #             print(f"DEBUG: {len(moves)} moves found that resolve check")
    #             for move in moves[:5]:  # Print first few moves only
    #                 print(f"  - {move.piece_moved} from {chr(97+move.start_col)}{8-move.start_row} to {chr(97+move.end_col)}{8-move.end_row}")
        
    #     if len(moves) == 0:
    #         if self.in_check:
    #             self.checkmate = True
    #             winner = "Black" if self.white_to_move else "White"
    #             print(f"CHECKMATE: {winner} wins")
    #             # Important: return empty moves list to prevent further play
    #             return []
    #         else:
    #             self.stalemate = True
    #             print("STALEMATE")
        
    #     return moves
        
    def get_valid_moves(self):
        # <<< DEBUG POINT 1: Start of function >>>
        print(f"\n--- DEBUG: get_valid_moves called for {'White' if self.white_to_move else 'Black'} ---")

        moves = [] # Initialize here, might be overwritten later depending on logic path
        self.in_check, self.pins, self.checks = self.check_for_pins_and_checks()

        # <<< DEBUG POINT 2: After checking for pins/checks >>>
        print(f"DEBUG: Initial state: In Check={self.in_check}, Pins={len(self.pins)}, Checks={len(self.checks)}")

        king_row, king_col = self.white_king_location if self.white_to_move else self.black_king_location

        # --- Logic Path: King is IN CHECK ---
        if self.in_check:
            # <<< DEBUG POINT 3a: Entering 'in_check' block >>>
            print(f"DEBUG: King is in check.")

            # --- Sub-Logic: SINGLE CHECK ---
            if len(self.checks) == 1:
                # <<< DEBUG POINT 4a: Entering 'single check' block >>>
                print(f"DEBUG: Single check detected.")
                moves = self.get_all_possible_moves() # Generate all moves for filtering
                # <<< DEBUG POINT 5a: Moves generated for single check filtering >>>
                print(f"DEBUG: Generated {len(moves)} possible moves for single check filtering.")

                check = self.checks[0]
                check_row, check_col = check[0], check[1]
                piece_checking = self.board[check_row][check_col]

                # Prioritize capturing the threatening piece (Your existing logic)
                capturing_moves = [m for m in moves if (m.end_row, m.end_col) == (check_row, check_col)]
                other_moves = [m for m in moves if (m.end_row, m.end_col) != (check_row, check_col)]
                moves = capturing_moves + other_moves # Reassign moves with captures first

                # Filter moves that don't resolve the check
                valid_squares = [(check_row, check_col)]
                if piece_checking[1] != 'n':
                    dr = 1 if check_row > king_row else -1 if check_row < king_row else 0
                    dc = 1 if check_col > king_col else -1 if check_col < king_col else 0
                    r, c = king_row + dr, king_col + dc
                    while (r, c) != (check_row, check_col):
                        valid_squares.append((r, c))
                        r, c = r + dr, c + dc
                # <<< DEBUG POINT 6a: Valid blocking/capturing squares >>>
                print(f"DEBUG: Valid blocking/capture squares for single check: {valid_squares}")

                # Iterate backwards for safe removal
                for i in range(len(moves) - 1, -1, -1):
                    move_to_check = moves[i]
                    # <<< DEBUG POINT 7a: Checking move in single check filter >>>
                    # print(f"DEBUG: Single Check - Validating move {move_to_check.get_notation()}...")

                    # Filter 1: Non-king moves must end on a valid square
                    if move_to_check.piece_moved[1] != 'k' and (move_to_check.end_row, move_to_check.end_col) not in valid_squares:
                        # <<< DEBUG POINT 8a: Removing move (doesn't block/capture) >>>
                        print(f"DEBUG: Single Check - Removing {move_to_check.get_notation()} (doesn't block/capture).")
                        moves.pop(i)
                        continue # Skip to next move

                    # Filter 2: Move must not leave king in check (handles pins, king moves into attack)
                    self.make_move(move_to_check)
                    self.white_to_move = not self.white_to_move # Temporarily switch turn
                    in_check_after_move, _, _ = self.check_for_pins_and_checks()
                    if in_check_after_move:
                        # <<< DEBUG POINT 9a: Removing move (still in check after move) >>>
                        print(f"DEBUG: Single Check - Removing {move_to_check.get_notation()} (still in check after move).")
                        moves.pop(i)
                    else:
                        # <<< DEBUG POINT 10a: Keeping move (resolves check) >>>
                        # print(f"DEBUG: Single Check - Keeping {move_to_check.get_notation()} (resolves check).")
                        pass # Keep the move
                    # Undo temporary changes
                    self.white_to_move = not self.white_to_move
                    self.undo_move()

            # --- Sub-Logic: DOUBLE CHECK ---
            else: # len(self.checks) > 1
                # <<< DEBUG POINT 4b: Entering 'double check' block >>>
                print(f"DEBUG: Double (or more) check detected.")
                moves = [] # Start with empty list, only add valid king moves
                self.get_king_moves(king_row, king_col, moves) # Generate only king moves
                # <<< DEBUG POINT 5b: King moves generated for double check filtering >>>
                print(f"DEBUG: Generated {len(moves)} king moves for double check filtering.")

                # Filter moves that don't resolve the check
                for i in range(len(moves) - 1, -1, -1):
                    move_to_check = moves[i]
                    # <<< DEBUG POINT 7b: Checking move in double check filter >>>
                    # print(f"DEBUG: Double Check - Validating king move {move_to_check.get_notation()}...")

                    self.make_move(move_to_check)
                    self.white_to_move = not self.white_to_move
                    in_check_after_move, _, _ = self.check_for_pins_and_checks()
                    if in_check_after_move:
                        # <<< DEBUG POINT 9b: Removing king move (still in check after move) >>>
                        print(f"DEBUG: Double Check - Removing king move {move_to_check.get_notation()} (still in check after move).")
                        moves.pop(i)
                    else:
                        # <<< DEBUG POINT 10b: Keeping king move (resolves check) >>>
                        # print(f"DEBUG: Double Check - Keeping king move {move_to_check.get_notation()} (resolves check).")
                        pass # Keep the move
                    self.white_to_move = not self.white_to_move
                    self.undo_move()

        # --- Logic Path: King is NOT IN CHECK ---
        else:
            # <<< DEBUG POINT 3c: Entering 'not in check' block >>>
            print(f"DEBUG: King is not initially in check.")
            all_possible_moves = self.get_all_possible_moves()
            # <<< DEBUG POINT 5c: Moves generated for 'not in check' filtering >>>
            print(f"DEBUG: Generated {len(all_possible_moves)} possible moves for 'not in check' filtering.")

            prioritized_moves = [] # Use your prioritization logic
            for move in all_possible_moves:
                # <<< DEBUG POINT 7c: Checking move in 'not in check' filter >>>
                # print(f"DEBUG: Not In Check - Validating move {move.get_notation()}...")

                self.make_move(move)
                self.white_to_move = not self.white_to_move
                in_check_after_move, _, _ = self.check_for_pins_and_checks()
                if not in_check_after_move:
                    # <<< DEBUG POINT 10c: Keeping move (doesn't result in check) >>>
                    # print(f"DEBUG: Not In Check - Keeping {move.get_notation()} (doesn't result in check).")
                    if move.piece_captured != '--':
                        prioritized_moves.append((1, move)) # High priority
                    else:
                        prioritized_moves.append((2, move)) # Lower priority
                else:
                    # <<< DEBUG POINT 9c: Removing move (results in check) >>>
                    print(f"DEBUG: Not In Check - Removing {move.get_notation()} (results in check).")
                    pass # Discard move
                self.white_to_move = not self.white_to_move
                self.undo_move()

            # Sort moves by priority (Your existing logic)
            prioritized_moves.sort(key=lambda x: x[0])
            moves = [m[1] for m in prioritized_moves] # Final moves list for 'not in check' case

        # --- Final Checkmate/Stalemate Logic ---
        # <<< DEBUG POINT 11: Before final checkmate/stalemate check >>>
        print(f"DEBUG: After filtering, {len(moves)} valid moves remain.")

        # Your existing checkmate/stalemate print statements are good here
        if len(moves) == 0:
            if self.in_check:
                self.checkmate = True
                winner = "Black" if self.white_to_move else "White"
                # <<< DEBUG POINT 12a: Checkmate detected >>>
                print(f"DEBUG: CHECKMATE detected for {'White' if self.white_to_move else 'Black'}. Winner: {winner}")
                # Important: return empty moves list to prevent further play
                # <<< DEBUG POINT 13a: Returning empty list for checkmate >>>
                print(f"--- DEBUG: get_valid_moves returning [] (Checkmate) ---\n")
                return [] # Explicitly return empty list on checkmate
            else:
                self.stalemate = True
                # <<< DEBUG POINT 12b: Stalemate detected >>>
                print(f"DEBUG: STALEMATE detected for {'White' if self.white_to_move else 'Black'}.")
                # <<< DEBUG POINT 13b: Returning empty list for stalemate >>>
                print(f"--- DEBUG: get_valid_moves returning [] (Stalemate) ---\n")
                # Return empty list for stalemate as well, as per standard chess engines
                return []
        else:
             # Reset flags if moves exist
             self.checkmate = False
             self.stalemate = False
             # Optional: Print some valid moves found
             # print(f"DEBUG: {len(moves)} valid moves found. First few:")
             # for m in moves[:3]: print(f"  - {m.get_notation()}")


        # <<< DEBUG POINT 14: Final return value (if not checkmate/stalemate) >>>
        print(f"--- DEBUG: get_valid_moves returning {len(moves)} moves. Checkmate={self.checkmate}, Stalemate={self.stalemate} ---\n")
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

    #     # Only generate moves if the pawn is not pinned or can move along the pin direction
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

    # def get_rook_moves(self, r, c, moves):
    #     piece_pinned = False
    #     pin_dir = None
    #     for i in range(len(self.pins) - 1, -1, -1):
    #         if self.pins[i][0] == r and self.pins[i][1] == c:
    #             piece_pinned = True
    #             pin_dir = (self.pins[i][2], self.pins[i][3])
    #             if self.board[r][c][1] != 'q':
    #                 self.pins.pop(i)
    #             break

    #     directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    #     enemy_color = 'b' if self.white_to_move else 'w'
    #     for dr, dc in directions:
    #         for i in range(1, 8):
    #             nr, nc = r + dr * i, c + dc * i
    #             if not (0 <= nr < 8 and 0 <= nc < 8):
    #                 break
    #             if not piece_pinned or pin_dir == (dr, dc) or pin_dir == (-dr, -dc):
    #                 target = self.board[nr][nc]
    #                 if target == '--':
    #                     moves.append(Move((r, c), (nr, nc), self.board))
    #                 elif target[0] == enemy_color:
    #                     moves.append(Move((r, c), (nr, nc), self.board))
    #                     break
    #                 else:
    #                     break

    # def get_knight_moves(self, r, c, moves):
    #     piece_pinned = False
    #     for i in range(len(self.pins) - 1, -1, -1):
    #         if self.pins[i][0] == r and self.pins[i][1] == c:
    #             piece_pinned = True
    #             self.pins.pop(i)
    #             break

    #     knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
    #     enemy_color = 'b' if self.white_to_move else 'w'
    #     if not piece_pinned:
    #         for dr, dc in knight_moves:
    #             nr, nc = r + dr, c + dc
    #             if 0 <= nr < 8 and 0 <= nc < 8:
    #                 target = self.board[nr][nc]
    #                 if target == '--' or target[0] == enemy_color:
    #                     moves.append(Move((r, c), (nr, nc), self.board))

    # def get_bishop_moves(self, r, c, moves):
    #     piece_pinned = False
    #     pin_dir = None
    #     for i in range(len(self.pins) - 1, -1, -1):
    #         if self.pins[i][0] == r and self.pins[i][1] == c:
    #             piece_pinned = True
    #             pin_dir = (self.pins[i][2], self.pins[i][3])
    #             self.pins.pop(i)
    #             break

    #     directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    #     enemy_color = 'b' if self.white_to_move else 'w'
    #     for dr, dc in directions:
    #         for i in range(1, 8):
    #             nr, nc = r + dr * i, c + dc * i
    #             if not (0 <= nr < 8 and 0 <= nc < 8):
    #                 break
    #             if not piece_pinned or pin_dir == (dr, dc) or pin_dir == (-dr, -dc):
    #                 target = self.board[nr][nc]
    #                 if target == '--':
    #                     moves.append(Move((r, c), (nr, nc), self.board))
    #                 elif target[0] == enemy_color:
    #                     moves.append(Move((r, c), (nr, nc), self.board))
    #                     break
    #                 else:
    #                     break
    def get_pawn_moves(self, r, c, moves):
        piece_pinned = False
        pin_dir = None
        # Read from self.pins without modifying it
        for pin_info in self.pins:
            if pin_info[0] == r and pin_info[1] == c:
                piece_pinned = True
                pin_dir = (pin_info[2], pin_info[3])
                break # Found the pin status for this piece

        direction = -1 if self.white_to_move else 1
        start_row = 6 if self.white_to_move else 1
        enemy_color = 'b' if self.white_to_move else 'w'
        promotion_row = 0 if self.white_to_move else 7

        # Forward move (1 square)
        if 0 <= r + direction < 8 and self.board[r + direction][c] == '--':
            # Can move if not pinned, or pinned along the vertical axis
            if not piece_pinned or pin_dir == (direction, 0):
                if r + direction == promotion_row:
                    moves.append(Move((r, c), (r + direction, c), self.board, is_pawn_promotion=True))
                else:
                    moves.append(Move((r, c), (r + direction, c), self.board))
                # Forward move (2 squares) - only possible if 1 square move is possible
                if r == start_row and self.board[r + 2 * direction][c] == '--':
                     # Check pin again for the 2-square move (must also be along vertical axis)
                     if not piece_pinned or pin_dir == (direction, 0):
                        moves.append(Move((r, c), (r + 2 * direction, c), self.board))

        # Captures
        for dc in [-1, 1]:
            if 0 <= c + dc < 8 and 0 <= r + direction < 8:
                # Can capture if not pinned, or pinned along the capture diagonal
                if not piece_pinned or pin_dir == (direction, dc):
                    target = self.board[r + direction][c + dc]
                    # Normal capture
                    if target != '--' and target[0] == enemy_color:
                        if r + direction == promotion_row:
                            moves.append(Move((r, c), (r + direction, c + dc), self.board, is_pawn_promotion=True))
                        else:
                            moves.append(Move((r, c), (r + direction, c + dc), self.board))
                    # En passant capture
                    elif (r + direction, c + dc) == self.en_passant_possible:
                        # The get_valid_moves function will later verify if this en passant leaves the king in check
                        moves.append(Move((r, c), (r + direction, c + dc), self.board, is_en_passant=True))

    def get_rook_moves(self, r, c, moves):
        piece_pinned = False
        pin_dir = None
        # Read from self.pins without modifying it
        for pin_info in self.pins:
            if pin_info[0] == r and pin_info[1] == c:
                piece_pinned = True
                pin_dir = (pin_info[2], pin_info[3])
                break # Found the pin status for this piece

        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)] # Vertical and Horizontal
        enemy_color = 'b' if self.white_to_move else 'w'
        for dr, dc in directions:
            # If pinned, can only move along the pin axis (forward or backward in that direction)
            if piece_pinned and pin_dir != (dr, dc) and pin_dir != (-dr, -dc):
                continue # Skip this direction if pinned and not along the pin axis

            for i in range(1, 8):
                nr, nc = r + dr * i, c + dc * i
                if not (0 <= nr < 8 and 0 <= nc < 8):
                    break # Off board
                target = self.board[nr][nc]
                if target == '--': # Empty square
                    moves.append(Move((r, c), (nr, nc), self.board))
                elif target[0] == enemy_color: # Enemy piece
                    moves.append(Move((r, c), (nr, nc), self.board))
                    break # Cannot move past captured piece
                else: # Ally piece
                    break # Blocked by ally

    def get_knight_moves(self, r, c, moves):
        piece_pinned = False
        # Read from self.pins without modifying it
        for pin_info in self.pins:
            if pin_info[0] == r and pin_info[1] == c:
                piece_pinned = True
                break # Found the pin status for this piece

        # If the knight is pinned, it cannot move at all.
        if piece_pinned:
            return # Exit early

        knight_moves_offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        ally_color = 'w' if self.white_to_move else 'b'
        for dr, dc in knight_moves_offsets:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                target = self.board[nr][nc]
                if target[0] != ally_color: # Empty square or enemy piece
                    moves.append(Move((r, c), (nr, nc), self.board))

    def get_bishop_moves(self, r, c, moves):
        piece_pinned = False
        pin_dir = None
        # Read from self.pins without modifying it
        for pin_info in self.pins:
            if pin_info[0] == r and pin_info[1] == c:
                piece_pinned = True
                pin_dir = (pin_info[2], pin_info[3])
                break # Found the pin status for this piece

        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)] # Diagonals
        enemy_color = 'b' if self.white_to_move else 'w'
        for dr, dc in directions:
            # If pinned, can only move along the pin axis (forward or backward in that direction)
            if piece_pinned and pin_dir != (dr, dc) and pin_dir != (-dr, -dc):
                continue # Skip this direction if pinned and not along the pin axis

            for i in range(1, 8):
                nr, nc = r + dr * i, c + dc * i
                if not (0 <= nr < 8 and 0 <= nc < 8):
                    break # Off board
                target = self.board[nr][nc]
                if target == '--': # Empty square
                    moves.append(Move((r, c), (nr, nc), self.board))
                elif target[0] == enemy_color: # Enemy piece
                    moves.append(Move((r, c), (nr, nc), self.board))
                    break # Cannot move past captured piece
                else: # Ally piece
                    break # Blocked by ally
                
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