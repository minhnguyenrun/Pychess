# --- START OF FILE game_state.py ---

from copy import deepcopy
from collections import Counter

class GameState:
    def __init__(self, player_wants_black=False):
        # Initial board setup
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
        # Mapping piece type to its move generation function
        self.move_functions = {'p': self.get_pawn_moves, 'r': self.get_rook_moves, 'n': self.get_knight_moves,
                              'b': self.get_bishop_moves, 'q': self.get_queen_moves, 'k': self.get_king_moves}
        self.white_to_move = True
        self.player_wants_black = player_wants_black # Keep track of player preference if needed elsewhere
        self.move_log = []
        # King locations are crucial for check detection and castling
        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)
        # State flags
        self.in_check = False
        self.pins = []      # List of pinned pieces and pin direction
        self.checks = []    # List of pieces delivering check and attack direction
        self.checkmate = False
        self.stalemate = False
        self.en_passant_possible = () # Coordinates (row, col) of the square where en passant capture is possible
        self.en_passant_log = [self.en_passant_possible] # Log for undoing moves
        # Castling rights (White KingSide, White QueenSide, Black KingSide, Black QueenSide)
        self.castle_rights = CastleRights(True, True, True, True)
        self.castle_rights_log = [deepcopy(self.castle_rights)] # Log for undoing moves
        # For threefold repetition detection
        self.position_history = {}
        self._update_position_history() # Log initial position

    def make_move(self, move):
        """Applies a move to the board and updates game state."""
        if self.board[move.start_row][move.start_col] == '--':
            print(f"ERROR: Attempting to move from empty square: {move.get_notation()}")
            return # Should not happen with valid moves

        self.board[move.start_row][move.start_col] = "--" # Remove piece from start square
        self.board[move.end_row][move.end_col] = move.piece_moved # Place piece on end square

        # Update king's location if moved
        if move.piece_moved == 'wk':
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_moved == 'bk':
            self.black_king_location = (move.end_row, move.end_col)

        # Pawn promotion (simplification: always promote to Queen)
        if move.is_pawn_promotion:
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + 'q'

        # En passant capture
        if move.is_en_passant:
            # The captured pawn is behind the moved pawn
            self.board[move.start_row][move.end_col] = '--'

        # Update en_passant_possible state
        if move.piece_moved[1] == 'p' and abs(move.start_row - move.end_row) == 2:
            # If a pawn moves two squares, en passant is possible on the square it skipped
            self.en_passant_possible = ((move.start_row + move.end_row) // 2, move.start_col)
        else:
            self.en_passant_possible = ()

        # Castle move - move the rook as well
        if move.is_castle:
            if move.end_col - move.start_col == 2:  # Kingside castle
                # Move the rook from h-file to f-file
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][move.end_col + 1]
                self.board[move.end_row][move.end_col + 1] = "--"
            else:  # Queenside castle (end_col - start_col == -2)
                # Move the rook from a-file to d-file
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 2]
                self.board[move.end_row][move.end_col - 2] = "--"

        # Update castling rights - rights are lost if king or rook moves
        self.update_castle_rights(move)
        self.castle_rights_log.append(deepcopy(self.castle_rights))

        # Log the en passant state for undo
        self.en_passant_log.append(self.en_passant_possible)

        # Add move to log and switch turn
        self.move_log.append(move)
        self.white_to_move = not self.white_to_move

        # Update position history for repetition detection
        self._update_position_history()

        # Reset check/stalemate flags - will be recalculated by get_valid_moves
        self.checkmate = False
        self.stalemate = False
        # Important: After making a move, we need to know if the *new* current player is in check
        # This is typically done implicitly when get_valid_moves is called for the next turn
        # Or you can explicitly call check_for_pins_and_checks here if needed immediately
    
    
    def undo_move(self):
        """Reverts the last move made."""
        if not self.move_log:
            return # No move to undo

        move = self.move_log.pop()

        # --- FIX: Get the key of the state we are *leaving* BEFORE reverting ---
        # This key represents the board state *after* the move 'move' was made,
        # including whose turn it was *after* the move.
        key_to_decrement = self._get_position_key()

        # --- Now, perform the state reversal ---

        # Switch turn back FIRST (so piece colors match the board state we are reverting TO)
        self.white_to_move = not self.white_to_move

        # Reverse the basic move
        self.board[move.start_row][move.start_col] = move.piece_moved
        self.board[move.end_row][move.end_col] = move.piece_captured # Put captured piece back

        # Update king location if king was moved
        if move.piece_moved == 'wk':
            self.white_king_location = (move.start_row, move.start_col)
        elif move.piece_moved == 'bk':
            self.black_king_location = (move.start_row, move.start_col)

        # Handle en passant undo
        if move.is_en_passant:
            self.board[move.end_row][move.end_col] = "--" # Landing square becomes empty
            # Put the captured pawn back (color determined by whose pawn was captured)
            # Since we already flipped the turn, the *current* player made the capture
            captured_pawn_color = 'b' if self.white_to_move else 'w' # Color of the pawn that WAS captured
            self.board[move.start_row][move.end_col] = captured_pawn_color + 'p'
            # Note: piece_captured on the move object already stores the correct captured piece 'bp' or 'wp'
            # self.board[move.start_row][move.end_col] = move.piece_captured # This might be simpler if piece_captured is reliable

        # Restore previous en passant state
        self.en_passant_log.pop()
        self.en_passant_possible = self.en_passant_log[-1]

        # Restore previous castling rights
        self.castle_rights_log.pop()
        self.castle_rights = deepcopy(self.castle_rights_log[-1]) # Use deepcopy here just to be safe, though CastleRights has only primitives

        # Handle castle undo - move the rook back
        if move.is_castle:
            if move.end_col - move.start_col == 2: # Kingside
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                self.board[move.end_row][move.end_col - 1] = "--"
            else: # Queenside
                self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                self.board[move.end_row][move.end_col + 1] = "--"

        # Reset check/mate/stalemate flags - they will be determined by the next call to get_valid_moves
        self.checkmate = False
        self.stalemate = False
        self.in_check = False # Resetting this might be needed too
        self.pins = []
        self.checks = []

        # --- FIX: Decrement the count for the key captured *before* undoing ---
        if key_to_decrement in self.position_history:
            self.position_history[key_to_decrement] -= 1
            if self.position_history[key_to_decrement] <= 0:
                # Remove the key if its count reaches zero
                 del self.position_history[key_to_decrement]
        else:
            # This case indicates a potential mismatch between make_move and undo_move logic
            print(f"WARNING: Attempted to decrement history count for an unknown key: {key_to_decrement}")
            # This might happen if the initial state logic differs from the make/undo cycle
            # Or if there's another bug in state management (e.g., castling/en passant affecting key unexpectedly)


    def get_valid_moves(self):
        """Generates all valid moves for the current player."""
        # print(f"\n--- DEBUG: get_valid_moves called for {'White' if self.white_to_move else 'Black'} ---") # Keep for debugging

        # For threefold repetition, check before generating moves
        if self.is_threefold_repetition():
            # print("DEBUG: Threefold repetition detected!")
            self.stalemate = True # Technically a draw claim, treat as stalemate for game end
            return []

        # Store current en passant state because get_pawn_moves might modify it temporarily in some implementations
        temp_en_passant = self.en_passant_possible
        # Store current castle rights because get_king_moves modifies them for generation
        temp_castle_rights = deepcopy(self.castle_rights)

        # 1. Generate all possible pseudo-legal moves (moves that ignore checks)
        moves = self.get_all_possible_moves()
        # print(f"DEBUG: Generated {len(moves)} pseudo-legal moves.")

        # Add castle moves specifically
        self.get_castle_moves(self.white_king_location[0], self.white_king_location[1], moves) if self.white_to_move else \
        self.get_castle_moves(self.black_king_location[0], self.black_king_location[1], moves)

        # Restore castle rights after potential modification during generation
        self.castle_rights = temp_castle_rights

        # 2. For each pseudo-legal move, check if it leaves the king in check
        # Iterate backwards to allow safe removal
        for i in range(len(moves) - 1, -1, -1):
            move = moves[i]
            # Simulate the move on the board
            self.make_move(move)
            # Switch turn back to check the original player's king
            self.white_to_move = not self.white_to_move
            if self.is_in_check():
                # print(f"DEBUG: Removing invalid move {move.get_notation()} (leaves king in check)")
                moves.pop(i) # If the king is in check after the move, it's invalid
            # Switch turn back again to restore state before undo
            self.white_to_move = not self.white_to_move
            # Undo the simulated move
            self.undo_move()

        # print(f"DEBUG: {len(moves)} valid moves remain after check validation.")

        # 3. Determine checkmate or stalemate
        if len(moves) == 0:
            # No valid moves left. Is the king currently in check?
            if self.is_in_check():
                self.checkmate = True
                # print(f"DEBUG: CHECKMATE detected for {'White' if self.white_to_move else 'Black'}")
            else:
                self.stalemate = True
                # print(f"DEBUG: STALEMATE detected for {'White' if self.white_to_move else 'Black'}")
        else:
            # If moves exist, it's not checkmate or stalemate
            self.checkmate = False
            self.stalemate = False

        # Restore en passant state just in case
        self.en_passant_possible = temp_en_passant

        # Check for insufficient material draw
        if not self.checkmate and not self.stalemate and self.is_insufficient_material():
            # print("DEBUG: Insufficient material detected!")
            self.stalemate = True # Treat as draw/stalemate for game end
            return []

        # print(f"--- DEBUG: get_valid_moves returning {len(moves)} moves. Checkmate={self.checkmate}, Stalemate={self.stalemate} ---\n")
        return moves

    def is_in_check(self):
        """Checks if the current player's king is under attack."""
        king_pos = self.white_king_location if self.white_to_move else self.black_king_location
        return self.square_under_attack(king_pos[0], king_pos[1])

    def square_under_attack(self, r, c):
        """Checks if the square (r, c) is under attack by the opponent."""
        # Temporarily switch turn to generate opponent's moves
        self.white_to_move = not self.white_to_move
        opponent_moves = self.get_all_possible_moves()
        # Switch turn back immediately
        self.white_to_move = not self.white_to_move

        # Check if any opponent move ends on the target square
        for move in opponent_moves:
            if move.end_row == r and move.end_col == c:
                return True
        return False

    def check_for_pins_and_checks(self):
        """
        Finds all pins and checks against the current player's king.
        This is kept separate as it might be useful for evaluation,
        but get_valid_moves now uses a simulation approach.
        """
        pins, checks = [], []
        in_check = False
        ally_color = 'w' if self.white_to_move else 'b'
        enemy_color = 'b' if self.white_to_move else 'w'
        king_row, king_col = self.white_king_location if self.white_to_move else self.black_king_location

        # Check outward from king for pins and checks
        directions = ((-1, 0), (1, 0), (0, -1), (0, 1), # Rook directions
                      (-1, -1), (-1, 1), (1, -1), (1, 1)) # Bishop directions
        for j, (dr, dc) in enumerate(directions):
            possible_pin = () # Reset possible pin for each direction
            for i in range(1, 8):
                end_row = king_row + dr * i
                end_col = king_col + dc * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] == ally_color and end_piece[1] != 'k':
                        if possible_pin == (): # First allied piece blocking
                            possible_pin = (end_row, end_col, dr, dc)
                        else: # Second allied piece, no pin possible in this direction
                            break
                    elif end_piece[0] == enemy_color:
                        piece_type = end_piece[1]
                        # Check if the piece type matches the attack direction
                        # 1. Rook/Queen on straight lines
                        # 2. Bishop/Queen on diagonals
                        # 3. Pawn on diagonal (only 1 step away)
                        # 4. King on any direction (only 1 step away - prevents kings moving next to each other)
                        if (0 <= j <= 3 and piece_type == 'r') or \
                           (4 <= j <= 7 and piece_type == 'b') or \
                           (piece_type == 'q') or \
                           (i == 1 and piece_type == 'k') or \
                           (i == 1 and piece_type == 'p' and (
                               (enemy_color == 'w' and ((dr == -1 and dc == -1) or (dr == -1 and dc == 1))) or
                               (enemy_color == 'b' and ((dr == 1 and dc == -1) or (dr == 1 and dc == 1)))
                           )):
                            if possible_pin == (): # No piece blocking, it's a check
                                in_check = True
                                checks.append((end_row, end_col, dr, dc))
                                break
                            else: # Piece is blocking, so it's a pin
                                pins.append(possible_pin)
                                break
                        else: # Enemy piece doesn't attack in this direction
                            break
                else: # Off board
                    break

        # Check for knight checks
        knight_moves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2),
                        (1, -2), (1, 2), (2, -1), (2, 1))
        for dr, dc in knight_moves:
            end_row = king_row + dr
            end_col = king_col + dc
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] == enemy_color and end_piece[1] == 'n':
                    in_check = True
                    checks.append((end_row, end_col, dr, dc))

        self.in_check = in_check # Update state flag
        self.pins = pins
        self.checks = checks
        # print(f"DEBUG pins/checks: In Check={in_check}, Pins={len(pins)}, Checks={len(checks)}")
        return in_check, pins, checks

    def get_all_possible_moves(self):
        """Generates all pseudo-legal moves (ignores checks)."""
        moves = []
        for r in range(8):
            for c in range(8):
                turn = self.board[r][c][0]
                if (turn == 'w' and self.white_to_move) or \
                   (turn == 'b' and not self.white_to_move):
                    piece = self.board[r][c][1]
                    self.move_functions[piece](r, c, moves) # Call the appropriate move function
        return moves

    # --- Piece Move Generation Functions (Pseudo-Legal) ---
    # These generate moves assuming the piece is not pinned and the move doesn't result in check.
    # The get_valid_moves function handles pin and check validation later via simulation.

    def get_pawn_moves(self, r, c, moves):
        """Generates pseudo-legal pawn moves."""
        piece_color = self.board[r][c][0]
        direction = -1 if piece_color == 'w' else 1
        enemy_color = 'b' if piece_color == 'w' else 'w'
        start_row = 6 if piece_color == 'w' else 1
        promotion_row = 0 if piece_color == 'w' else 7

        # 1. One square forward
        if 0 <= r + direction < 8 and self.board[r + direction][c] == "--":
            if r + direction == promotion_row: # Promotion
                 moves.append(Move((r, c), (r + direction, c), self.board, is_pawn_promotion=True))
            else: # Regular move
                 moves.append(Move((r, c), (r + direction, c), self.board))
            # 2. Two squares forward (only from start row and if one square is clear)
            if r == start_row and self.board[r + 2 * direction][c] == "--":
                moves.append(Move((r, c), (r + 2 * direction, c), self.board))

        # 3. Captures (diagonal)
        for dc in [-1, 1]:
            if 0 <= c + dc < 8 and 0 <= r + direction < 8:
                target_square = self.board[r + direction][c + dc]
                # Normal capture
                if target_square[0] == enemy_color:
                    if r + direction == promotion_row: # Promotion capture
                        moves.append(Move((r, c), (r + direction, c + dc), self.board, is_pawn_promotion=True))
                    else: # Regular capture
                        moves.append(Move((r, c), (r + direction, c + dc), self.board))
                # En passant capture
                elif (r + direction, c + dc) == self.en_passant_possible:
                    moves.append(Move((r, c), (r + direction, c + dc), self.board, is_en_passant=True))

    def get_rook_moves(self, r, c, moves):
        """Generates pseudo-legal rook moves."""
        ally_color = self.board[r][c][0]
        directions = ((1, 0), (-1, 0), (0, 1), (0, -1))
        for dr, dc in directions:
            for i in range(1, 8):
                end_row, end_col = r + dr * i, c + dc * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece == "--": # Empty square
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                    elif end_piece[0] != ally_color: # Enemy piece
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                        break # Cannot move past capture
                    else: # Ally piece
                        break # Blocked
                else: # Off board
                    break

    def get_knight_moves(self, r, c, moves):
        """Generates pseudo-legal knight moves."""
        ally_color = self.board[r][c][0]
        knight_moves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2),
                        (1, -2), (1, 2), (2, -1), (2, 1))
        for dr, dc in knight_moves:
            end_row, end_col = r + dr, c + dc
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color: # Empty square or enemy piece
                    moves.append(Move((r, c), (end_row, end_col), self.board))

    def get_bishop_moves(self, r, c, moves):
        """Generates pseudo-legal bishop moves."""
        ally_color = self.board[r][c][0]
        directions = ((1, 1), (1, -1), (-1, 1), (-1, -1))
        for dr, dc in directions:
            for i in range(1, 8):
                end_row, end_col = r + dr * i, c + dc * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece == "--": # Empty square
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                    elif end_piece[0] != ally_color: # Enemy piece
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                        break # Cannot move past capture
                    else: # Ally piece
                        break # Blocked
                else: # Off board
                    break

    def get_queen_moves(self, r, c, moves):
        """Generates pseudo-legal queen moves by combining rook and bishop moves."""
        self.get_rook_moves(r, c, moves)
        self.get_bishop_moves(r, c, moves)

    def get_king_moves(self, r, c, moves):
        """Generates pseudo-legal king moves (excluding castling)."""
        ally_color = self.board[r][c][0]
        king_moves = ((1, 0), (-1, 0), (0, 1), (0, -1),
                      (1, 1), (1, -1), (-1, 1), (-1, -1))
        for dr, dc in king_moves:
            end_row, end_col = r + dr, c + dc
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color: # Empty square or enemy piece
                    # Note: We don't check if the landing square is attacked here.
                    # get_valid_moves handles that via simulation.
                    moves.append(Move((r, c), (end_row, end_col), self.board))

    def get_castle_moves(self, r, c, moves):
         """Generates valid castle moves."""
         if self.square_under_attack(r, c):
             return # Can't castle while in check

         ally_color = 'w' if self.white_to_move else 'b'

         # Kingside castling
         if (self.white_to_move and self.castle_rights.wks) or \
            (not self.white_to_move and self.castle_rights.bks):
             # Check if squares between king and rook are empty
             if self.board[r][c + 1] == "--" and self.board[r][c + 2] == "--":
                 # Check if squares king passes over are not under attack
                 if not self.square_under_attack(r, c + 1) and \
                    not self.square_under_attack(r, c + 2):
                     moves.append(Move((r, c), (r, c + 2), self.board, is_castle=True))

         # Queenside castling
         if (self.white_to_move and self.castle_rights.wqs) or \
            (not self.white_to_move and self.castle_rights.bqs):
             # Check if squares between king and rook are empty
             if self.board[r][c - 1] == "--" and self.board[r][c - 2] == "--" and \
                self.board[r][c - 3] == "--":
                  # Check if squares king passes over are not under attack
                  if not self.square_under_attack(r, c - 1) and \
                     not self.square_under_attack(r, c - 2):
                      moves.append(Move((r, c), (r, c - 2), self.board, is_castle=True))


    def update_castle_rights(self, move):
        """Updates castling rights based on the move made."""
        # If a king moves, all its castling rights are lost
        if move.piece_moved == 'wk':
            self.castle_rights.wks = False
            self.castle_rights.wqs = False
        elif move.piece_moved == 'bk':
            self.castle_rights.bks = False
            self.castle_rights.bqs = False

        # If a rook moves or is captured, the corresponding side's castling right is lost
        if move.piece_moved == 'wr':
            if move.start_row == 7:
                if move.start_col == 0: # White Queenside rook
                    self.castle_rights.wqs = False
                elif move.start_col == 7: # White Kingside rook
                    self.castle_rights.wks = False
        elif move.piece_moved == 'br':
             if move.start_row == 0:
                if move.start_col == 0: # Black Queenside rook
                    self.castle_rights.bqs = False
                elif move.start_col == 7: # Black Kingside rook
                    self.castle_rights.bks = False

        # If a rook is captured
        if move.piece_captured == 'wr':
            if move.end_row == 7:
                if move.end_col == 0: # White Queenside rook captured
                    self.castle_rights.wqs = False
                elif move.end_col == 7: # White Kingside rook captured
                    self.castle_rights.wks = False
        elif move.piece_captured == 'br':
            if move.end_row == 0:
                if move.end_col == 0: # Black Queenside rook captured
                    self.castle_rights.bqs = False
                elif move.end_col == 7: # Black Kingside rook captured
                    self.castle_rights.bks = False

    def _update_position_history(self):
        """Updates the count for the current board position."""
        key = self._get_position_key()
        self.position_history[key] = self.position_history.get(key, 0) + 1

    def _get_position_key(self):
        """Creates a unique string representation of the current game state."""
        # Includes board state, whose turn, castling rights, and en passant target square
        return ''.join(''.join(row) for row in self.board) + \
               ('w' if self.white_to_move else 'b') + \
               ('K' if self.castle_rights.wks else '') + \
               ('Q' if self.castle_rights.wqs else '') + \
               ('k' if self.castle_rights.bks else '') + \
               ('q' if self.castle_rights.bqs else '') + \
               (str(self.en_passant_possible) if self.en_passant_possible else '-')

    def is_threefold_repetition(self):
        """Checks if the current position has occurred 3 or more times."""
        key = self._get_position_key()
        # print(f"DEBUG: Position key: {key}, Count: {self.position_history.get(key, 0)}") # Debug
        return self.position_history.get(key, 0) >= 3

    def is_insufficient_material(self):
        """Checks for draw conditions based on remaining material."""
        # Count pieces, excluding kings initially
        piece_counts = Counter()
        other_pieces = 0
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece != '--' and piece[1] != 'k':
                    piece_counts[piece] += 1
                    other_pieces += 1

        # King vs King
        if other_pieces == 0:
            return True
        # King + Knight vs King
        if other_pieces == 1 and (piece_counts['wn'] == 1 or piece_counts['bn'] == 1):
            return True
        # King + Bishop vs King
        if other_pieces == 1 and (piece_counts['wb'] == 1 or piece_counts['bb'] == 1):
            return True
        # King + Bishop vs King + Bishop (bishops on same color squares)
        if other_pieces == 2 and piece_counts['wb'] == 1 and piece_counts['bb'] == 1:
            wb_pos = None
            bb_pos = None
            for r in range(8):
                for c in range(8):
                    piece = self.board[r][c]
                    if piece == 'wb': wb_pos = (r, c)
                    if piece == 'bb': bb_pos = (r, c)
            if wb_pos and bb_pos:
                 # Check if bishops are on same colored squares
                 if (wb_pos[0] + wb_pos[1]) % 2 == (bb_pos[0] + bb_pos[1]) % 2:
                     return True

        # Add more insufficient material cases if needed (e.g., K+N vs K+N)

        return False

class CastleRights:
    """Helper class to store castling rights."""
    def __init__(self, wks, wqs, bks, bqs):
        self.wks = wks # White King Side
        self.wqs = wqs # White Queen Side
        self.bks = bks # Black King Side
        self.bqs = bqs # Black Queen Side

class Move:
    """Represents a move in the chess game."""
    # Using chess notation maps for easier understanding
    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4,
                     "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3,
                     "e": 4, "f": 5, "g": 6, "h": 7}
    cols_to_files = {v: k for k, v in files_to_cols.items()}

    def __init__(self, start_sq, end_sq, board, is_en_passant=False, is_castle=False, is_pawn_promotion=False):
        self.start_row, self.start_col = start_sq
        self.end_row, self.end_col = end_sq
        self.piece_moved = board[self.start_row][self.start_col]
        # Determine captured piece
        if is_en_passant:
            # Captured pawn is on start_row, end_col
             captured_pawn_color = 'b' if self.piece_moved[0] == 'w' else 'w'
             self.piece_captured = captured_pawn_color + 'p'
        elif is_castle:
            self.piece_captured = '--' # No capture in castling
        else:
             self.piece_captured = board[self.end_row][self.end_col]

        # Boolean flags for special moves
        self.is_en_passant = is_en_passant
        self.is_castle = is_castle
        self.is_pawn_promotion = is_pawn_promotion and (self.piece_moved[1] == 'p')

        # Simple unique ID for the move based on coordinates
        self.move_id = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col

    def __eq__(self, other):
        """Checks if two move objects represent the same move."""
        return isinstance(other, Move) and self.move_id == other.move_id

    def __str__(self):
        """String representation (like algebraic notation)."""
        return self.get_notation()

    def get_notation(self):
        """Returns the move in standard algebraic notation (e.g., 'e2e4')."""
        # Handle castling notation
        if self.is_castle:
            return "O-O" if self.end_col > self.start_col else "O-O-O"

        start = self.get_rank_file(self.start_row, self.start_col)
        end = self.get_rank_file(self.end_row, self.end_col)
        notation = start + end

        # Add promotion notation (defaulting to 'q' for Queen)
        if self.is_pawn_promotion:
            notation += 'q' # Simplification: always promote to Queen

        return notation

    def get_rank_file(self, r, c):
        """Converts row and column index to algebraic notation (e.g., 'e4')."""
        return self.cols_to_files[c] + self.rows_to_ranks[r]


# --- END OF FILE game_state.py ---