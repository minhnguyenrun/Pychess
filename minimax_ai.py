import math
import random
from copy import deepcopy
from my_character import Queen, Pawn, King, Knight, Bishop, Rook

# Enhanced piece values for evaluation
PIECE_VALUES = {"p": 100, "n": 320, "b": 330, "r": 500, "q": 900, "k": 20000}

# Opening book - simplified version
OPENING_BOOK = {
    # Format: board_hash -> [(from_square, to_square), ...]
    "start": [
        # e4 openings
        ((6, 4), (4, 4)),  # e4
        # d4 openings
        ((6, 3), (4, 3)),  # d4
        # Sicilian defense as black
        ((1, 2), (3, 2)),  # c5 after e4
        # Queen's gambit
        ((6, 3), (4, 3)),  # d4
        ((6, 2), (4, 2)),  # c4
    ],
    # Add more openings as needed
}

# Piece-square tables for positional evaluation
PAWN_TABLE = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5,  5, 10, 25, 25, 10,  5,  5],
    [0,  0,  0, 20, 20,  0,  0,  0],
    [5, -5,-10,  0,  0,-10, -5,  5],
    [5, 10, 10,-20,-20, 10, 10,  5],
    [0,  0,  0,  0,  0,  0,  0,  0]
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
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10,  5,  5,  5,  5,  5,  5,-10],
    [-10,  0,  5,  0,  0,  5,  0,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20]
]

ROOK_TABLE = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [5, 10, 10, 10, 10, 10, 10,  5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [0,  0,  0,  5,  5,  0,  0,  0]
]

QUEEN_TABLE = [
    [-20,-10,-10, -5, -5,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5,  5,  5,  5,  0,-10],
    [-5,  0,  5,  5,  5,  5,  0, -5],
    [0,  0,  5,  5,  5,  5,  0, -5],
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
    [20, 20,  0,  0,  0,  0, 20, 20],
    [20, 30, 10,  0,  0, 10, 30, 20]
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

# Transposition table for storing evaluated positions
TRANSPOSITION_TABLE = {}

class Event:
    def __init__(self, state, i1, j1, i2, j2):
        self.i1, self.j1, self.i2, self.j2 = i1, j1, i2, j2
        self.chess_man_1 = state.board[i1][j1]
        self.chess_man_2 = state.board[i2][j2]
        self.state = state
        self.special_event = 'UP' if abs(self.chess_man_1.value) == 1 and (i2 == 0 or i2 == 7) else None

    def goto(self):
        self.state.board[self.i1][self.j1] = None
        self.state.board[self.i2][self.j2] = self.chess_man_1
        self.chess_man_1.make_a_move(self.i2, self.j2)
        if self.special_event is not None:
            self.chess_man_1.level = 2
            self.chess_man_1.value = self.chess_man_1.value * 9

    def backto(self):
        self.state.board[self.i1][self.j1] = self.chess_man_1
        self.state.board[self.i2][self.j2] = self.chess_man_2
        self.chess_man_1.make_a_move(self.i1, self.j1)
        if self.special_event is not None:
            self.chess_man_1.level = 1
            self.chess_man_1.value = self.chess_man_1.value // 9

class MinimaxGameState:
    def __init__(self, game_adaptee):
        self.board = []
        self.castle_right = game_adaptee.castle_rights
        self.en_passant_possible = game_adaptee.en_passant_possible
        self.history = []
        self.game_adaptee = game_adaptee
        self.move_count = len(game_adaptee.move_log)
        self.adapter(game_adaptee)

    def adapter(self, game):
        for r in range(8):
            row = []
            for c in range(8):
                name = game.board[r][c]
                if name != '--':
                    if name[1] == 'p': chessman = Pawn(self, name, r, c)
                    elif name[1] == 'n': chessman = Knight(self, name, r, c)
                    elif name[1] == 'b': chessman = Bishop(self, name, r, c)
                    elif name[1] == 'r': chessman = Rook(self, name, r, c)
                    elif name[1] == 'q': chessman = Queen(self, name, r, c)
                    elif name[1] == 'k': chessman = King(self, name, r, c)
                    row.append(chessman)
                else:
                    row.append(None)
            self.board.append(row)

    def get_position_hash(self):
        """Generate a simple hash representation of the current board position"""
        hash_val = ""
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece is None:
                    hash_val += "--"
                else:
                    hash_val += piece.name
        return hash_val

    def is_endgame(self):
        """Determine if the position is in the endgame phase"""
        piece_count = 0
        queen_count = 0
        for r in range(8):
            for c in range(8):
                if self.board[r][c] is not None:
                    piece_count += 1
                    if abs(self.board[r][c].value) > 800:  # Queen value
                        queen_count += 1
        # Consider endgame if fewer than 10 pieces or no queens
        return piece_count <= 10 or queen_count == 0

    def deep_evaluate(self, ai):
        """Enhanced evaluation function with positional understanding"""
        # Material score
        material_score = 0
        
        # Position score
        position_score = 0
        
        # Pawn structure and advancement
        pawn_structure_score = 0
        
        # Control of the center
        center_control = 0
        
        # King safety
        king_safety = 0
        
        # Piece mobility
        mobility_score = 0
        
        # Piece development (for opening)
        development_score = 0
        
        is_endgame = self.is_endgame()
        
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece is not None:
                    # Base material value
                    material_score += piece.value
                    
                    # Piece-specific positional evaluation
                    if piece.name[1] == 'p':
                        # Pawn positional value
                        if piece.player == 1:  # White
                            position_score += PAWN_TABLE[r][c]
                            # Passed pawn check
                            passed = True
                            for check_r in range(r-1, -1, -1):
                                if c > 0 and self.board[check_r][c-1] is not None and self.board[check_r][c-1].name[1] == 'p':
                                    passed = False
                                    break
                                if c < 7 and self.board[check_r][c+1] is not None and self.board[check_r][c+1].name[1] == 'p':
                                    passed = False
                                    break
                            if passed:
                                # Bonus for passed pawns (higher for more advanced pawns)
                                pawn_structure_score += (7 - r) * 10
                        else:  # Black
                            position_score += PAWN_TABLE[7-r][c]
                            # Passed pawn check for black
                            passed = True
                            for check_r in range(r+1, 8):
                                if c > 0 and self.board[check_r][c-1] is not None and self.board[check_r][c-1].name[1] == 'p':
                                    passed = False
                                    break
                                if c < 7 and self.board[check_r][c+1] is not None and self.board[check_r][c+1].name[1] == 'p':
                                    passed = False
                                    break
                            if passed:
                                pawn_structure_score += r * 10
                    
                    elif piece.name[1] == 'n':
                        # Knight positional value
                        position_score += KNIGHT_TABLE[r if piece.player == 1 else 7-r][c]
                        # Knights are better in closed positions
                        if not is_endgame:
                            position_score += 10
                    
                    elif piece.name[1] == 'b':
                        # Bishop positional value
                        position_score += BISHOP_TABLE[r if piece.player == 1 else 7-r][c]
                        # Bishop pair bonus
                        has_pair = False
                        for r2 in range(8):
                            for c2 in range(8):
                                if r != r2 and c != c2 and self.board[r2][c2] is not None and \
                                   self.board[r2][c2].name[1] == 'b' and self.board[r2][c2].player == piece.player:
                                    has_pair = True
                        if has_pair:
                            position_score += 50
                    
                    elif piece.name[1] == 'r':
                        # Rook positional value
                        position_score += ROOK_TABLE[r if piece.player == 1 else 7-r][c]
                        # Rook on open file bonus
                        open_file = True
                        for check_r in range(8):
                            if check_r != r and self.board[check_r][c] is not None and self.board[check_r][c].name[1] == 'p':
                                open_file = False
                                break
                        if open_file:
                            position_score += 20
                    
                    elif piece.name[1] == 'q':
                        # Queen positional value
                        position_score += QUEEN_TABLE[r if piece.player == 1 else 7-r][c]
                    
                    elif piece.name[1] == 'k':
                        # King positional value - different for middle game and endgame
                        if is_endgame:
                            position_score += KING_END_TABLE[r if piece.player == 1 else 7-r][c]
                        else:
                            position_score += KING_MIDDLE_TABLE[r if piece.player == 1 else 7-r][c]
                        
                        # King safety (pawn shield in midgame)
                        if not is_endgame:
                            if piece.player == 1:  # White
                                if r < 7:
                                    for offset in [-1, 0, 1]:
                                        if 0 <= c+offset < 8 and self.board[r+1][c+offset] is not None and \
                                           self.board[r+1][c+offset].name[1] == 'p' and self.board[r+1][c+offset].player == 1:
                                            king_safety += 10
                            else:  # Black
                                if r > 0:
                                    for offset in [-1, 0, 1]:
                                        if 0 <= c+offset < 8 and self.board[r-1][c+offset] is not None and \
                                           self.board[r-1][c+offset].name[1] == 'p' and self.board[r-1][c+offset].player == -1:
                                            king_safety += 10
                    
                    # Mobility (approximated by move count)
                    mobility_score += len(piece.get_move()) * piece.player * 0.1
                    
                    # Center control bonus
                    if (r, c) in [(3, 3), (3, 4), (4, 3), (4, 4)]:
                        center_control += piece.player * 10
                        
                    # Development bonus for minor pieces in opening
                    if self.move_count < 10 and piece.name[1] in ['n', 'b']:
                        if piece.player == 1 and r < 6:  # White piece moved from back rank
                            development_score += 10
                        elif piece.player == -1 and r > 1:  # Black piece moved from back rank
                            development_score += 10
        
        # Combine all evaluation factors
        total_score = material_score + position_score * 0.5 + pawn_structure_score + \
                     center_control + king_safety + mobility_score
                    
        # Development bonus is only significant in opening
        if self.move_count < 10:
            total_score += development_score
        
        return ai * total_score

    def evaluate(self, ai):
        """Simplified evaluation function for quiescence search"""
        score = 0
        for r in range(8):
            for c in range(8):
                chess_man = self.board[r][c]
                if chess_man is not None:
                    score += chess_man.value
        return ai * score

    def goto(self, i1, j1, i2, j2):
        event = Event(self, i1, j1, i2, j2)
        self.history.append(event)
        event.goto()

    def backto(self):
        event = self.history.pop()
        event.backto()

class ChessAI:
    def __init__(self, game, max_depth, color='b'):
        self.max_depth = max_depth
        self.game = game
        self.player = {'b': -1, 'w': 1}[color]
        self.bonus = 0
        self.move_count = len(game.game_adaptee.move_log)
        self.transposition_table = {}

    def generate_state(self, ai):
        """Generate moves with MVA-LVA ordering and improved prioritization"""
        moves = []  # Unused but kept for compatibility
        captures = []
        non_captures = []
        defensive_moves = []  # New category for king safety moves
        check_moves = []  # New category for moves that maintain check on opponent
        
        # First check if king is under threat
        king_threatened = self.is_check(ai)
        
        # Find if opponent's king is in check (new)
        opponent_king_in_check = self.is_check(-ai)
        opponent_king_pos = None
        
        # Find king positions
        king_pos = None
        for r in range(8):
            for c in range(8):
                if (self.game.board[r][c] is not None and 
                    self.game.board[r][c].name[1] == 'k'):
                    if self.game.board[r][c].player == ai:
                        king_pos = (r, c)
                    else:
                        opponent_king_pos = (r, c)
                if king_pos and opponent_king_pos:
                    break
        
        # Rest of existing code for queen_pos detection...
        
        # First, collect all possible moves
        for r in range(8):
            for c in range(8):
                if self.game.board[r][c] is not None and self.game.board[r][c].player == ai:
                    # Existing code for piece detection...
                    
                    for i, j in self.game.board[r][c].get_move():
                        # Existing king defense logic...
                        
                        # NEW: Prioritize moves that maintain check against opponent's king
                        if opponent_king_in_check:
                            self.game.goto(r, c, i, j)
                            still_in_check = self.is_check(-ai)
                            # Check if this move delivers checkmate
                            is_checkmate = still_in_check and self.is_opponent_checkmated(-ai)
                            self.game.backto()
                            
                            if is_checkmate:
                                # Highest priority for checkmate moves
                                check_moves.append((2000, r, c, i, j))
                                continue
                            elif still_in_check:
                                # High priority for moves that maintain check
                                check_moves.append((950, r, c, i, j))
                                continue
                        
                        # Rest of existing logic for queen defense, captures, etc...
        
        # Sort each category
        check_moves.sort(reverse=True)  # New category
        defensive_moves.sort(reverse=True)
        captures.sort(reverse=True)
        non_captures.sort(reverse=True)
        
        # Combine with check moves and defensive moves first (highest priority)
        move_data = [m[1:] for m in check_moves] + [m[1:] for m in defensive_moves] + [m[1:] for m in captures] + [m[1:] for m in non_captures]
        
        # Use opening book for early moves if available
        if self.move_count < 10:
            position_hash = self.game.get_position_hash()
            if position_hash in OPENING_BOOK:
                book_moves = []
                for book_from, book_to in OPENING_BOOK[position_hash]:
                    # Check if the book move is valid
                    for r, c, i, j in move_data:
                        if (r, c) == book_from and (i, j) == book_to:
                            book_moves.append((r, c, i, j))
                if book_moves:
                    # Return a book move with some randomness
                    return [random.choice(book_moves)]
            # If at start position, use general opening moves
            elif self.move_count < 2 and "start" in OPENING_BOOK:
                for book_from, book_to in OPENING_BOOK["start"]:
                    for r, c, i, j in move_data:
                        if (r, c) == book_from and (i, j) == book_to:
                            return [(r, c, i, j)]
                
        return move_data
    def is_opponent_checkmated(self, opponent):
        """Check if opponent has any legal moves to get out of check"""
        # Generate all possible moves for opponent
        for r in range(8):
            for c in range(8):
                if (self.game.board[r][c] is not None and 
                    self.game.board[r][c].player == opponent):
                    for i, j in self.game.board[r][c].get_move():
                        # Try the move
                        self.game.goto(r, c, i, j)
                        still_in_check = self.is_check(opponent)
                        self.game.backto()
                        
                        if not still_in_check:
                            return False  # Found at least one legal move
        return True  # No legal moves found

    def quiescence_search(self, alpha, beta, depth=0, include_checks=False):
        """Improved quiescence search to evaluate tactical positions"""
        # Get current static evaluation
        standing_pat = self.game.evaluate(self.player if depth % 2 == 0 else -self.player)
        
        if depth >= 4:  # Reasonable depth limit
            return standing_pat, []
            
        if standing_pat >= beta:
            return beta, []
            
        if alpha < standing_pat:
            alpha = standing_pat
            
        # Consider captures and checks
        ai = self.player if depth % 2 == 0 else -self.player
        captures = []
        
        # Collect all possible captures
        for r in range(8):
            for c in range(8):
                if self.game.board[r][c] is not None and self.game.board[r][c].player == ai:
                    for i, j in self.game.board[r][c].get_move():
                        # Only consider captures (not quiet moves)
                        if self.game.board[i][j] is not None and self.game.board[i][j].player == -ai:
                            captured_value = abs(self.game.board[i][j].value)
                            attacker_value = abs(self.game.board[r][c].value)
                            # Sort by MVV-LVA: Most Valuable Victim, Least Valuable Attacker
                            score = captured_value * 100 - attacker_value
                            captures.append((score, r, c, i, j))
        
        # Sort by MVV-LVA for better move ordering
        captures.sort(reverse=True)
        
        # Evaluate each capture
        for _, r, c, i, j in captures:
            # Check if the move doesn't lose material
            self.game.goto(r, c, i, j)
            
            # See if our piece would be recaptured
            is_threatened = self.is_piece_threatened(i, j, self.game.board[i][j])
            
            if not is_threatened[0] or abs(self.game.board[i][j].value) >= is_threatened[1]:
                # Only recurse if this isn't a losing capture
                score, _ = self.quiescence_search(-beta, -alpha, depth + 1)
                score = -score
                
                self.game.backto()
                
                if score > alpha:
                    alpha = score
                    
                if alpha >= beta:
                    break
            else:
                self.game.backto()
        
        return alpha, []

    def alphabeta(self, depth, alpha=-1000000, beta=1000000, iterative_deepening=True):
        """Enhanced alpha-beta pruning with iterative deepening and transposition table"""
        # Check transposition table
        position_hash = self.game.get_position_hash()
        if position_hash in self.transposition_table and self.transposition_table[position_hash][0] >= depth:
            stored_depth, stored_value, stored_move = self.transposition_table[position_hash]
            return stored_value, stored_move
            
        ai = self.player if depth % 2 == 0 else -self.player
        
        if depth == self.max_depth:
            # Switch to quiescence search at max depth
            alpha, best_move = self.quiescence_search(alpha, beta, depth=0, include_checks=True)
            return alpha + self.bonus * (1 if depth % 2 == 0 else -1), best_move
            
        i1, j1, i2, j2 = 0, 0, 0, 0
        move = self.generate_state(ai)
        
        # If no legal moves, might be checkmate or stalemate
        if not move:
            # Simple check for mate/stalemate - this is just a placeholder
            return -10000 * ai if self.is_check(ai) else 0, []
        
        for r, c, i, j in move:
            # Check for direct checkmate moves first
            # if self.game.board[i][j] is not None and self.game.board[i][j].value == 0:
            #     return 10000, (r, c, i, j)
                
            self.game.goto(r, c, i, j)
            
            # Increased bonus for checking the opponent's king
            if depth == 0 and self.is_check(-ai):
                self.bonus = 50
                result, _ = self.alphabeta(depth + 1, -beta, -alpha)
                result = -result
                self.bonus = 0
            # Track opportunities to promote pawns
            elif depth == 0 and self.game.board[i][j].name[1] == 'p' and ((ai == 1 and i <= 1) or (ai == -1 and i >= 6)):
                self.bonus = 100  # Bigger bonus for promotion opportunities
                result, _ = self.alphabeta(depth + 1, -beta, -alpha)
                result = -result
                self.bonus = 0
            # Regular move
            else:
                # Apply Late Move Reduction for non-capture moves at deeper levels
                if depth > 2 and self.game.board[i][j] is None and (r, c, i, j) != move[0]:
                    # Reduced depth search
                    result, _ = self.alphabeta(depth + 1 + 1, -alpha-1, -alpha)  # +1 for reduction
                    result = -result
                    
                    # If the reduced search indicates a good move, do a full search
                    if result > alpha:
                        result, _ = self.alphabeta(depth + 1, -beta, -alpha)
                        result = -result
                else:
                    result, _ = self.alphabeta(depth + 1, -beta, -alpha)
                    result = -result
                    
            self.game.backto()
            
            if result > alpha:
                alpha = result
                i1, j1, i2, j2 = r, c, i, j
                
            if alpha >= beta:
                # Store position in transposition table
                self.transposition_table[position_hash] = (depth, alpha, (i1, j1, i2, j2))
                return alpha, (i1, j1, i2, j2)
                
        # Store position in transposition table
        self.transposition_table[position_hash] = (depth, alpha, (i1, j1, i2, j2))
        return alpha, (i1, j1, i2, j2)
    
    def is_check(self, player):
        """Determine if the player's king is in check"""
        # Find king position
        king_pos = None
        for r in range(8):
            for c in range(8):
                if (self.game.board[r][c] is not None and 
                    self.game.board[r][c].name[1] == 'k' and 
                    self.game.board[r][c].player == player):
                    king_pos = (r, c)
                    break
            if king_pos:
                break
                
        if not king_pos:
            return False  # No king found (shouldn't happen in a valid game)
            
        # Check if any opponent's piece can attack the king
        for r in range(8):
            for c in range(8):
                if (self.game.board[r][c] is not None and 
                    self.game.board[r][c].player == -player):
                    for i, j in self.game.board[r][c].get_move():
                        if (i, j) == king_pos:
                            return True
        return False
    
       
    def is_piece_threatened(self, r, c, piece):
        """Enhanced check if a piece is under threat from opponent pieces"""
        piece_player = piece.player
        threats = []
        
        for i in range(8):
            for j in range(8):
                if (self.game.board[i][j] is not None and 
                    self.game.board[i][j].player == -piece_player):
                    for move_i, move_j in self.game.board[i][j].get_move():
                        if move_i == r and move_j == c:
                            # Calculate attack score: attacker value vs target value
                            attacker_value = abs(self.game.board[i][j].value)
                            target_value = abs(piece.value)
                            # Consider a piece threatened if attacked by equal or HIGHER value
                            if attacker_value >= target_value:
                                threats.append((attacker_value, i, j))
        
        # Return True if threatened, along with the highest value attacker
        if threats:
            threats.sort(reverse=True)  # Sort by attacker value (descending)
            return True, threats[0][0]
        return False, 0
    
    def iterative_deepening(self, max_time=5.0):
        """Implement iterative deepening for better time management"""
        import time
        start_time = time.time()
        best_move = None
        
        # Don't clear the table between depths - reuse previous calculations
        # self.transposition_table = {}
        
        for depth in range(1, min(self.max_depth, 4) + 1):  # Limit to depth 4 initially
            # Run alpha-beta search at current depth
            score, move = self.alphabeta(0, iterative_deepening=True)
            if move and len(move) == 4:  # Valid move check
                best_move = move
            
            # Check time - stop if more than 50% of allocated time used (more conservative)
            elapsed = time.time() - start_time
            if elapsed > max_time * 0.5:
                break
                
        return best_move
    
    def _print_board(self):
        """Print a text representation of the board for debugging"""
        print("  a b c d e f g h")
        print(" +-----------------+")
        for r in range(8):
            print(f"{8-r}|", end=" ")
            for c in range(8):
                piece = self.game.board[r][c]
                if piece is None:
                    print(".", end=" ")
                else:
                    # For white pieces use uppercase, for black lowercase
                    char = piece.name[1]
                    if piece.player == 1:  # White
                        char = char.upper()
                    print(char, end=" ")
            print(f"|{8-r}")
        print(" +-----------------+")
        print("  a b c d e f g h")

    def specialized_kq_endgame(self, board):
        """
        Specialized algorithm for King+Queen vs King endgame.
        Returns the best move for this specific endgame.
        """
        # Find positions of all pieces
        ai_king_pos = None
        ai_queen_pos = None
        enemy_king_pos = None
        
        for r in range(8):
            for c in range(8):
                piece = board[r][c]
                if piece is not None:
                    if piece.name[1] == 'k':
                        if piece.player == self.player:
                            ai_king_pos = (r, c)
                        else:
                            enemy_king_pos = (r, c)
                    elif piece.name[1] == 'q' and piece.player == self.player:
                        ai_queen_pos = (r, c)
        
        if not all([ai_king_pos, ai_queen_pos, enemy_king_pos]):
            # Not a K+Q vs K scenario
            return None
        
        # Calculate distances
        ek_r, ek_c = enemy_king_pos
        ak_r, ak_c = ai_king_pos
        q_r, q_c = ai_queen_pos
        
        # Distance from enemy king to edges
        edge_dist = min(ek_r, ek_c, 7-ek_r, 7-ek_c)
        
        # Distance between kings
        king_dist = max(abs(ek_r - ak_r), abs(ek_c - ak_c))
        
        # Possible queen moves
        queen = board[q_r][q_c]
        queen_moves = []
        for i, j in queen.get_move():
            # Check if the move gives check
            gives_check = False
            for di, dj in [(0,1), (1,0), (0,-1), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]:
                r, c = i + di, j + dj
                if 0 <= r < 8 and 0 <= c < 8 and (r, c) == enemy_king_pos:
                    gives_check = True
                    break
                    
            # Validate no pieces in between for sliding moves
            valid = True
            if abs(q_r - i) > 1 or abs(q_c - j) > 1:  # Not adjacent
                dr = 0 if q_r == i else (i - q_r) // abs(i - q_r)
                dc = 0 if q_c == j else (j - q_c) // abs(j - q_c)
                r, c = q_r + dr, q_c + dc
                while (r, c) != (i, j):
                    if board[r][c] is not None:
                        valid = False
                        break
                    r, c = r + dr, c + dc
                    
            if valid:
                # Calculate how good this move is
                new_q_dist = max(abs(i - ek_r), abs(j - ek_c))
                score = 0
                
                # Prefer moves that:
                # 1. Give check
                # 2. Push enemy king toward edge
                # 3. Keep queen at knight's distance from enemy king (2 squares)
                if gives_check:
                    score += 50
                    
                    # Extra points if the check forces the king toward the edge
                    if edge_dist > 0:  # Not already on edge
                        for escape_r, escape_c in [
                            (ek_r+1, ek_c), (ek_r-1, ek_c), 
                            (ek_r, ek_c+1), (ek_r, ek_c-1),
                            (ek_r+1, ek_c+1), (ek_r+1, ek_c-1),
                            (ek_r-1, ek_c+1), (ek_r-1, ek_c-1)
                        ]:
                            if 0 <= escape_r < 8 and 0 <= escape_c < 8:
                                # Check if this escape square is under attack
                                escape_edge_dist = min(escape_r, escape_c, 7-escape_r, 7-escape_c)
                                if escape_edge_dist < edge_dist:
                                    score += 20
                else:
                    # If not giving check, prioritize moves that:
                    # 1. Keep the queen close to the enemy king (but not too close)
                    # 2. Restrict enemy king's mobility
                    if 2 <= new_q_dist <= 3:
                        score += 30
                    
                    # Bonus for restricting king mobility by controlling nearby squares
                    mobility_control = 0
                    for dr, dc in [(0,1), (1,0), (0,-1), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]:
                        next_r, next_c = ek_r + dr, ek_c + dc
                        if 0 <= next_r < 8 and 0 <= next_c < 8:
                            # Check if queen attacks this square
                            if (abs(i - next_r) == abs(j - next_c)) or i == next_r or j == next_c:
                                mobility_control += 5
                    
                    score += mobility_control
                
                # Encourage our king to get closer to the enemy king
                # but not too close if we're already near
                if king_dist > 3:
                    king_approach = 15 - king_dist  # Higher score for getting closer
                    score += king_approach
                else:
                    # Maintain a distance of 2 for the optimal checkmate pattern
                    if king_dist == 2:
                        score += 15
                
                # Add this move with its score
                queen_moves.append((score, q_r, q_c, i, j))
        
        if queen_moves:
            # Pick the best move
            queen_moves.sort(reverse=True)
            _, qr, qc, i, j = queen_moves[0]
            return qr, qc, i, j
        
        # If no good queen move was found, try to move king closer to enemy king
        ai_king = board[ak_r][ak_c]
        king_moves = []
        for i, j in ai_king.get_move():
            if board[i][j] is None:  # Empty square
                new_king_dist = max(abs(i - ek_r), abs(j - ek_c))
                
                # Don't get too close to prevent stalemate
                if new_king_dist >= 2:
                    score = 10 - new_king_dist  # Higher score for getting closer
                    king_moves.append((score, ak_r, ak_c, i, j))
        
        if king_moves:
            king_moves.sort(reverse=True)
            _, kr, kc, i, j = king_moves[0]
            return kr, kc, i, j
        
        # Fallback to any legal queen move
        return q_r, q_c, q_r, q_c


    def evaluate_move_safety(self, r, c, i, j):
        """
        Evaluate if a move is safe by checking potential threats after the move
        Returns: (is_safe, threat_value, num_attackers)
        """
        # Make the move
        self.game.goto(r, c, i, j)
        
        # Check if the piece at destination will be under attack
        piece_at_dest = self.game.board[i][j]
        piece_value = abs(piece_at_dest.value)
        
        # Collect all attackers and defenders
        attackers = []
        defenders = []
        
        for r2 in range(8):
            for c2 in range(8):
                if self.game.board[r2][c2] is not None:
                    # Check if this piece can attack our moved piece
                    if self.game.board[r2][c2].player == -piece_at_dest.player:
                        for ar, ac in self.game.board[r2][c2].get_move():
                            if (ar, ac) == (i, j):
                                attacker_value = abs(self.game.board[r2][c2].value)
                                attackers.append((attacker_value, r2, c2))
                    # Check if our pieces can defend the moved piece
                    elif self.game.board[r2][c2].player == piece_at_dest.player and (r2, c2) != (i, j):
                        for dr, dc in self.game.board[r2][c2].get_move():
                            if (dr, dc) == (i, j):
                                defender_value = abs(self.game.board[r2][c2].value)
                                defenders.append((defender_value, r2, c2))
        
        # Undo the move
        self.game.backto()
        
        # Calculate safety score
        if not attackers:
            return True, 0, 0  # No attackers, completely safe
        
        # Find the smallest attacker
        attackers.sort()  # Sort by value (ascending)
        smallest_attacker = attackers[0][0]
        
        # If a valuable piece is attacked by a less valuable piece, it's unsafe
        if smallest_attacker < piece_value:
            # But check if it can be recaptured favorably
            if defenders:
                # Basic exchange evaluation
                defenders.sort()  # Sort by value (ascending)
                if defenders[0][0] <= smallest_attacker:
                    # We can recapture with an equal or less valuable piece
                    return True, smallest_attacker, len(attackers)
            return False, smallest_attacker, len(attackers)
        
        # If attacking piece is more valuable, might still be safe
        return True, smallest_attacker, len(attackers)
    def get_best_move(self, use_iterative_deepening=True):
        """Get the best move using iterative deepening within time constraints"""
        # Add logging - BOARD STATE AND CONTEXT
        print("\n=== AI MOVE SELECTION START ===")
        print(f"AI color: {'Black' if self.player == -1 else 'White'}")
        
        # Log current board position
        print("\nCurrent board state:")
        self._print_board()
        
        # Check if opponent's king is in check
        opponent_in_check = self.is_check(-self.player)
        if opponent_in_check:
            print(f"OPPONENT'S KING IS IN CHECK!")
            
            # Find opponent king position
            opponent_king_pos = None
            for r in range(8):
                for c in range(8):
                    if (self.game.board[r][c] is not None and 
                        self.game.board[r][c].name[1] == 'k' and 
                        self.game.board[r][c].player == -self.player):
                        opponent_king_pos = (r, c)
                        break
                if opponent_king_pos:
                    break
            
            # Log which pieces are delivering check
            checking_pieces = []
            for r in range(8):
                for c in range(8):
                    if (self.game.board[r][c] is not None and 
                        self.game.board[r][c].player == self.player):
                        for i, j in self.game.board[r][c].get_move():
                            if (i, j) == opponent_king_pos:
                                piece_type = {'p': 'Pawn', 'n': 'Knight', 'b': 'Bishop', 
                                             'r': 'Rook', 'q': 'Queen', 'k': 'King'}[self.game.board[r][c].name[1]]
                                checking_pieces.append((piece_type, r, c))
                                print(f"CHECK! {piece_type} at {chr(97+c)}{8-r} is checking opponent king at {chr(97+opponent_king_pos[1])}{8-opponent_king_pos[0]}")
            
            # Detailed analysis of check situation
            if checking_pieces:
                for piece_type, r, c in checking_pieces:
                    # Check if piece is threatened
                    threatened, attacker_value = self.is_piece_threatened(r, c, self.game.board[r][c])
                    if threatened:
                        print(f"WARNING: Checking {piece_type} at {chr(97+c)}{8-r} is threatened by opponent piece of value {attacker_value}")
        
        # First, check if king is in check and handle it explicitly
        king_in_check = self.is_check(self.player)
        
        # Special handling for check situations
        if king_in_check:
            print("AI king is in check - using defensive move selection")
            # Rest of the existing defensive code...
            
            # Find king position and add detailed logging
            king_pos = None
            for r in range(8):
                for c in range(8):
                    if (self.game.board[r][c] is not None and 
                        self.game.board[r][c].name[1] == 'k' and 
                        self.game.board[r][c].player == self.player):
                        king_pos = (r, c)
                        print(f"AI king is at {chr(97+c)}{8-r}")
                        break
                if king_pos:
                    break
            
            # Find pieces checking the king
            checking_pieces = []
            for r in range(8):
                for c in range(8):
                    if (self.game.board[r][c] is not None and 
                        self.game.board[r][c].player == -self.player):
                        for i, j in self.game.board[r][c].get_move():
                            if (i, j) == king_pos:
                                piece_type = {'p': 'Pawn', 'n': 'Knight', 'b': 'Bishop', 
                                             'r': 'Rook', 'q': 'Queen', 'k': 'King'}[self.game.board[r][c].name[1]]
                                checking_pieces.append((piece_type, r, c))
                                print(f"Under check from: {piece_type} at {chr(97+c)}{8-r}")
            
            # Get all possible moves
            defensive_moves = []
            
            # Look for all moves that get out of check
            for r in range(8):
                for c in range(8):
                    if self.game.board[r][c] is not None and self.game.board[r][c].player == self.player:
                        for i, j in self.game.board[r][c].get_move():
                            # Try the move
                            self.game.goto(r, c, i, j)
                            still_in_check = self.is_check(self.player)
                            self.game.backto()
                            
                            if not still_in_check:
                                piece_type = {'p': 'Pawn', 'n': 'Knight', 'b': 'Bishop', 
                                             'r': 'Rook', 'q': 'Queen', 'k': 'King'}[self.game.board[r][c].name[1]]
                                move_type = "capture" if self.game.board[i][j] is not None else "move"
                                defensive_moves.append((r, c, i, j))
                                print(f"Defensive option: {piece_type} {chr(97+c)}{8-r}->{chr(97+j)}{8-i} ({move_type})")
                
            # If we found defensive moves, use them
            if defensive_moves:
                print(f"Found {len(defensive_moves)} defensive moves")
                # Prioritize capturing the checking piece
                for move in defensive_moves:
                    r, c, i, j = move
                    # Check if this move captures a piece
                    if self.game.board[i][j] is not None:
                        piece_type = {'p': 'Pawn', 'n': 'Knight', 'b': 'Bishop', 
                                     'r': 'Rook', 'q': 'Queen', 'k': 'King'}[self.game.board[r][c].name[1]]
                        target_type = {'p': 'Pawn', 'n': 'Knight', 'b': 'Bishop', 
                                      'r': 'Rook', 'q': 'Queen', 'k': 'King'}[self.game.board[i][j].name[1]]
                        print(f"Selected defensive capture: {piece_type} {chr(97+c)}{8-r}->{chr(97+j)}{8-i} captures {target_type}")
                        # Check if destination matches a game move
                        for m in self.game.game_adaptee.get_valid_moves():
                            if r == m.start_row and i == m.end_row and c == m.start_col and j == m.end_col:
                                print("=== AI MOVE SELECTION END ===\n")
                                return m
                
                # Next priority is king moving away
                for move in defensive_moves:
                    r, c, i, j = move
                    # If this is a king move
                    if self.game.board[r][c].name[1] == 'k':
                        print(f"Selected defensive king move: {chr(97+c)}{8-r}->{chr(97+j)}{8-i}")
                        for m in self.game.game_adaptee.get_valid_moves():
                            if r == m.start_row and i == m.end_row and c == m.start_col and j == m.end_col:
                                print("=== AI MOVE SELECTION END ===\n")
                                return m
                
                # Last resort - any valid defensive move
                for move in defensive_moves:
                    r, c, i, j = move
                    piece_type = {'p': 'Pawn', 'n': 'Knight', 'b': 'Bishop', 
                                 'r': 'Rook', 'q': 'Queen', 'k': 'King'}[self.game.board[r][c].name[1]]
                    print(f"Selected defensive move (last resort): {piece_type} {chr(97+c)}{8-r}->{chr(97+j)}{8-i}")
                    for m in self.game.game_adaptee.get_valid_moves():
                        if r == m.start_row and i == m.end_row and c == m.start_col and j == m.end_col:
                            print("=== AI MOVE SELECTION END ===\n")
                            return m
        
        # If king is not in check or no defensive moves found, use normal search
        if use_iterative_deepening:
            print("Using iterative deepening search")
            best_move = self.iterative_deepening(5.0)  # 5 seconds max
        else:
            print("Using standard alpha-beta search")
            _, best_move = self.alphabeta(0)
            
        if best_move and len(best_move) == 4:
            i1, j1, i2, j2 = best_move
            piece = self.game.board[i1][j1]
            piece_type = {'p': 'Pawn', 'n': 'Knight', 'b': 'Bishop', 
                         'r': 'Rook', 'q': 'Queen', 'k': 'King'}[piece.name[1]]
            move_description = f"{piece_type} from {chr(97+j1)}{8-i1} to {chr(97+j2)}{8-i2}"
            
            if self.game.board[i2][j2] is not None:
                target = self.game.board[i2][j2]
                target_type = {'p': 'Pawn', 'n': 'Knight', 'b': 'Bishop', 
                              'r': 'Rook', 'q': 'Queen', 'k': 'King'}[target.name[1]]
                move_description += f", capturing {target_type}"
            
            # Check if move maintains check
            self.game.goto(i1, j1, i2, j2)
            still_in_check = self.is_check(-self.player)
            self.game.backto()
            
            if still_in_check:
                move_description += " (maintaining check)"
                
            print(f"Selected move from search: {move_description}")
            
            # Find the corresponding move in the game's valid moves list
            for m in self.game.game_adaptee.get_valid_moves():
                if i1 == m.start_row and i2 == m.end_row and j1 == m.start_col and j2 == m.end_col:
                    print("=== AI MOVE SELECTION END ===\n")
                    return m
        else:
            print("No move selected from search, using fallback")
            
        # ADD ENDGAME STRATEGY HERE - right at this indentation level
        # ENDGAME STRATEGY - CHECK FOR KING+MATERIAL vs LONE KING
        enemy_pieces = [self.game.board[r][c] for r in range(8) for c in range(8) 
                        if self.game.board[r][c] is not None and self.game.board[r][c].player == -self.player]

        if len(enemy_pieces) <= 3:  # Only enemy king remains or very few pieces
            print("Using specialized endgame strategy")
            valid_moves = self.game.game_adaptee.get_valid_moves()
            
            # NEW CODE: Check for King+Queen vs King endgame
            ai_pieces = {'king': 0, 'queen': 0, 'rook': 0, 'bishop': 0, 'knight': 0, 'pawn': 0}
            enemy_pieces_dict = {'king': 0, 'queen': 0, 'rook': 0, 'bishop': 0, 'knight': 0, 'pawn': 0}
            
            for r in range(8):
                for c in range(8):
                    piece = self.game.board[r][c]
                    if piece is not None:
                        piece_type = {'p': 'pawn', 'n': 'knight', 'b': 'bishop', 
                                    'r': 'rook', 'q': 'queen', 'k': 'king'}[piece.name[1]]
                        piece_dict = ai_pieces if piece.player == self.player else enemy_pieces_dict
                        piece_dict[piece_type] += 1
            
            # King + Queen vs King endgame
            if (ai_pieces['king'] == 1 and ai_pieces['queen'] == 1 and 
                sum(ai_pieces.values()) == 2 and
                enemy_pieces_dict['king'] == 1 and sum(enemy_pieces_dict.values()) == 1):
                
                print("Detected K+Q vs K endgame - using specialized algorithm")
                best_move = self.specialized_kq_endgame(self.game.board)
                
                if best_move:
                    qr, qc, i, j = best_move
                    for move in valid_moves:
                        if (qr == move.start_row and qc == move.start_col and 
                            i == move.end_row and j == move.end_col):
                            print(f"Selected K+Q vs K optimal move: {move.piece_moved} from {chr(97+qc)}{8-qr} to {chr(97+j)}{8-i}")
                            print("=== AI MOVE SELECTION END ===\n")
                            return move
            
            # EXISTING CODE - Track position history to avoid repetition
            current_position = self.game.game_adaptee.get_position_key()
            recent_positions = list(self.game.game_adaptee.position_history.keys())[-10:] if self.game.game_adaptee.position_history else []
            
            # Avoid moves that lead to positions we've seen before
            repetition_threshold = 1  # Avoid positions we've seen even once before
            repetitive_moves = []
            
            # First check if we can deliver checkmate
            checkmate_moves = []
            check_moves = []
            for move in valid_moves:
                self.game.goto(move.start_row, move.start_col, move.end_row, move.end_col)
                opponent_in_check = self.is_check(-self.player)
                if opponent_in_check:
                    is_checkmate = self.is_opponent_checkmated(-self.player)
                    if is_checkmate:
                        checkmate_moves.append(move)
                    else:
                        check_moves.append(move)
                self.game.backto()
            
            # When finding check moves, filter out repetitive ones
            if check_moves:
                non_repetitive_check_moves = []
                for move in check_moves:
                    # Test the move
                    self.game.goto(move.start_row, move.start_col, move.end_row, move.end_col)
                    test_position = self.game.game_adaptee.get_position_key()
                    self.game.backto()
                    
                    # If the resulting position isn't a repetition, keep it
                    if recent_positions.count(test_position) <= repetition_threshold:
                        non_repetitive_check_moves.append(move)
                    else:
                        repetitive_moves.append(move)
                
                # If we have non-repetitive checks, use those instead
                if non_repetitive_check_moves:
                    check_moves = non_repetitive_check_moves
            checkmate_moves = []
            check_moves = []
            for move in valid_moves:
                self.game.goto(move.start_row, move.start_col, move.end_row, move.end_col)
                opponent_in_check = self.is_check(-self.player)
                if opponent_in_check:
                    is_checkmate = self.is_opponent_checkmated(-self.player)
                    if is_checkmate:
                        checkmate_moves.append(move)
                    else:
                        check_moves.append(move)
                self.game.backto()
            
            if checkmate_moves:
                print("Found checkmate move!")
                selected_move = random.choice(checkmate_moves)
                return selected_move
            
            if check_moves:
                print("Found move that delivers check!")
                # Calculate the distance between kings for each move
                for move in check_moves:
                    # Test the move
                    self.game.goto(move.start_row, move.start_col, move.end_row, move.end_col)
                    
                    # Find king positions
                    enemy_king_pos = None
                    my_king_pos = None
                    for r in range(8):
                        for c in range(8):
                            piece = self.game.board[r][c]
                            if piece and piece.name[1] == 'k':
                                if piece.player == -self.player:
                                    enemy_king_pos = (r, c)
                                else:
                                    my_king_pos = (r, c)
                                    
                    # Calculate Manhattan distance between kings
                    if enemy_king_pos and my_king_pos:
                        move.king_distance = abs(enemy_king_pos[0] - my_king_pos[0]) + abs(enemy_king_pos[1] - my_king_pos[1])
                    else:
                        move.king_distance = 14  # Max possible distance
                        
                    # Also check if this is an edge check (better for cornering)
                    move.is_edge_check = (move.end_row in [0, 7] or move.end_col in [0, 7])
                    
                    self.game.backto()
                
                # Sort by: 1) Edge checks first, 2) Moves that bring kings closer together
                check_moves.sort(key=lambda m: (0 if m.is_edge_check else 1, m.king_distance))
                
                # Select the best check move
                selected_move = check_moves[0]
                print(f"Selected optimal check move: {selected_move.piece_moved} from {chr(97+selected_move.start_col)}{8-selected_move.start_row} to {chr(97+selected_move.end_col)}{8-selected_move.end_row}")
                print("=== AI MOVE SELECTION END ===\n")
                return selected_move
            
            # STRATEGY 1: Try to promote pawns
            promotion_moves = []
            for move in valid_moves:
                if move.piece_moved[1] == 'p':
                    # Find pawns close to promotion
                    promotion_rank = 1 if self.player == 1 else 6  # Target rank before promotion
                    if move.start_row == promotion_rank + self.player:
                        promotion_moves.append((1, move))  # High priority
                    elif move.start_row == promotion_rank + 2*self.player:
                        promotion_moves.append((2, move))  # Medium priority
            
            # STRATEGY 2: Restrict king's movement - move pieces closer to enemy king
            king_restriction_moves = []
            enemy_king_pos = None
            for r in range(8):
                for c in range(8):
                    if (self.game.board[r][c] is not None and 
                        self.game.board[r][c].name[1] == 'k' and 
                        self.game.board[r][c].player == -self.player):
                        enemy_king_pos = (r, c)
                        break
                if enemy_king_pos:
                    break
            
            if enemy_king_pos:
                for move in valid_moves:
                    if move.piece_moved[1] == 'q':
                        # Prioritize queen moves that get closer to the enemy king
                        distance = max(abs(move.end_row - enemy_king_pos[0]), 
                                      abs(move.end_col - enemy_king_pos[1]))
                        if 2 <= distance <= 3:  # Slightly safer distance from enemy king
                            # Higher priority for positions that control more squares
                            priority = 1
                            # Don't place queen where it can be captured
                            self.game.goto(move.start_row, move.start_col, move.end_row, move.end_col)
                            is_threatened = self.is_piece_threatened(move.end_row, move.end_col, self.game.board[move.end_row][move.end_col])
                            self.game.backto()
                            
                            if not is_threatened[0]:  # Only if the queen won't be captured
                                king_restriction_moves.append((priority, move))
                    elif move.piece_moved[1] == 'k':
                        # Move our king toward enemy king in endgame
                        curr_distance = max(abs(move.start_row - enemy_king_pos[0]), 
                        abs(move.start_col - enemy_king_pos[1]))
                        new_distance = max(abs(move.end_row - enemy_king_pos[0]), 
                                        abs(move.end_col - enemy_king_pos[1]))
                        
                        # Don't get too close in middle game, optimal distance is 2 squares in endgame
                        target_distance = 2 if len(enemy_pieces) <= 2 else 3
                        
                        # Check if the move is safe (not moving into check)
                        self.game.goto(move.start_row, move.start_col, move.end_row, move.end_col)
                        is_safe = not self.is_check(self.player)  # Make sure we're not moving into check
                        self.game.backto()
                        
                        if new_distance <= target_distance and new_distance < curr_distance and is_safe:
                            king_restriction_moves.append((2, move))  # Lower priority for king moves
            
            # Choose best strategy
            if promotion_moves:
                promotion_moves.sort(key=lambda x: x[0])
                selected_move = promotion_moves[0][1]
                print(f"Selected pawn promotion move: {selected_move.piece_moved} {chr(97+selected_move.start_col)}{8-selected_move.start_row}->{chr(97+selected_move.end_col)}{8-selected_move.end_row}")
                print("=== AI MOVE SELECTION END ===\n")
                return selected_move
            elif king_restriction_moves:
                king_restriction_moves.sort(key=lambda x: x[0])
                selected_move = king_restriction_moves[0][1]
                print(f"Selected king restriction move: {selected_move.piece_moved} {chr(97+selected_move.start_col)}{8-selected_move.start_row}->{chr(97+selected_move.end_col)}{8-selected_move.end_row}")
                print("=== AI MOVE SELECTION END ===\n")
                return selected_move
                
        # FALLBACK: If no move was found, choose any valid move
        valid_moves = self.game.game_adaptee.get_valid_moves()
        
       
        capture_moves = [m for m in valid_moves if m.piece_captured != '--']
        if capture_moves:
            print("Using fallback capture move selection:")
            # Calculate the value difference for each capture
            piece_values = {'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900, 'k': 20000}
            
            # Calculate whether captures are favorable
            for m in capture_moves:
                attacker_value = piece_values.get(m.piece_moved[1], 0)
                target_value = piece_values.get(m.piece_captured[1], 0)
                
                # Evaluate safety AFTER the capture
                is_safe, threat_value, num_attackers = self.evaluate_move_safety(
                    m.start_row, m.start_col, m.end_row, m.end_col)
                
                if is_safe:
                    # Safe capture - full value
                    m.value_difference = target_value
                else:
                    # Unsafe capture - consider the exchange
                    m.value_difference = target_value - attacker_value
                    
                    # Heavy penalty for putting valuable pieces at risk
                    if attacker_value > 300:  # Knight/Bishop or higher
                        m.value_difference -= 200
                    
                    # Extra penalty for multiple attackers
                    m.value_difference -= 50 * (num_attackers - 1)
            
            # Sort by value difference (highest first)
            capture_moves.sort(key=lambda m: m.value_difference, reverse=True)
            
            # Only consider favorable trades
            good_captures = [m for m in capture_moves if m.value_difference > 0]
            if good_captures:
                selected_move = good_captures[0]
                print(f"Selected favorable capture: {selected_move.piece_moved} captures {selected_move.piece_captured}")
                return selected_move
            
        # If no captures, prioritize different move types and use randomization
        if valid_moves:
            
            
            # Categorize moves by type for better selection
            pawn_moves = [m for m in valid_moves if m.piece_moved[1] == 'p']
            developing_moves = [m for m in valid_moves if m.piece_moved[1] in ['n', 'b'] and 
                              ((m.piece_moved[0] == 'w' and m.start_row == 7) or 
                               (m.piece_moved[0] == 'b' and m.start_row == 0))]
            center_control_moves = [m for m in valid_moves if m.end_row in [3, 4] and m.end_col in [3, 4]]
            pawn_moves = self.evaluate_and_filter_moves(pawn_moves)
            developing_moves = self.evaluate_and_filter_moves(developing_moves)
            center_control_moves = self.evaluate_and_filter_moves(center_control_moves)
            for move in center_control_moves:
                is_safe, _, _ = self.evaluate_move_safety(
                    move.start_row, move.start_col, move.end_row, move.end_col)
                move.is_safe = is_safe

            # Filter to only safe center control moves if possible
            safe_center_moves = [m for m in center_control_moves if m.is_safe]
            if safe_center_moves:
                center_control_moves = safe_center_moves
            # Filter out the repetitive rook moves
            rook_back_forth = [m for m in valid_moves if 
                             m.piece_moved[1] == 'r' and 
                             ((m.start_row == 0 and m.start_col == 0 and m.end_row == 0 and m.end_col == 1) or
                              (m.start_row == 0 and m.start_col == 1 and m.end_row == 0 and m.end_col == 0))]
            
            # Prioritize development in the opening
            if self.move_count < 10 and developing_moves:
                selected_move = random.choice(developing_moves)
                print(f"Selected developing move: {selected_move.piece_moved} {chr(97+selected_move.start_col)}{8-selected_move.start_row}->{chr(97+selected_move.end_col)}{8-selected_move.end_row}")
                print("=== AI MOVE SELECTION END ===\n")
                return selected_move
            
            # Prioritize center control
            if center_control_moves:
                # Get current position key and position history from game state
                current_position = self.game.game_adaptee.get_position_key()
                position_history = list(self.game.game_adaptee.position_history.keys())
                
                # Track last few moves to detect repetition
                previously_used_moves = self.game.game_adaptee.move_log[-5:] if len(self.game.game_adaptee.move_log) >= 5 else []
                
                # Check for repetition
                if len(position_history) > 4 and position_history.count(current_position) >= 2:
                    # If this position has occurred recently, avoid moves that lead to repetition
                    non_repetitive_moves = [m for m in valid_moves if m.piece_moved[1] != 'b' or
                                           (m.start_row, m.start_col, m.end_row, m.end_col) not in 
                                           [(prev.start_row, prev.start_col, prev.end_row, prev.end_col) for prev in previously_used_moves]]
                    
                    if non_repetitive_moves:
                        selected_move = random.choice(non_repetitive_moves)
                        print(f"Avoiding repetition - selected alternative move: {selected_move.piece_moved} {chr(97+selected_move.start_col)}{8-selected_move.start_row}->{chr(97+selected_move.end_col)}{8-selected_move.end_row}")
                        print("=== AI MOVE SELECTION END ===\n")
                        return selected_move
                
                # Default center control selection if no repetition detected
                selected_move = random.choice(center_control_moves)
                print(f"Selected center control move: {selected_move.piece_moved} {chr(97+selected_move.start_col)}{8-selected_move.start_row}->{chr(97+selected_move.end_col)}{8-selected_move.end_row}")
                print("=== AI MOVE SELECTION END ===\n")
                return selected_move
            
            if not center_control_moves and pawn_moves:
                # Prioritize pawns that are further advanced
                pawn_moves.sort(key=lambda m: 7-m.end_row if m.piece_moved[0] == 'w' else m.end_row)
                selected_move = pawn_moves[0]  # Select most advanced pawn
                print(f"Selected pawn advance: {selected_move.piece_moved} {chr(97+selected_move.start_col)}{8-selected_move.start_row}->{chr(97+selected_move.end_col)}{8-selected_move.end_row}")
                print("=== AI MOVE SELECTION END ===\n")
                return selected_move
            
            # Filter out the repetitive rook moves if there are other options
            filtered_moves = [m for m in valid_moves if m not in rook_back_forth]
            
            # If we have other moves besides the rook back and forth, use those
            if filtered_moves:
                selected_move = random.choice(filtered_moves)
                print(f"Selected random move (avoiding repetition): {selected_move.piece_moved} {chr(97+selected_move.start_col)}{8-selected_move.start_row}->{chr(97+selected_move.end_col)}{8-selected_move.end_row}")
                print("=== AI MOVE SELECTION END ===\n")
                return selected_move
            
            # Last resort - completely random move (including potential repetitions)
            selected_move = random.choice(valid_moves)
            print(f"Selected random move: {selected_move.piece_moved} {chr(97+selected_move.start_col)}{8-selected_move.start_row}->{chr(97+selected_move.end_col)}{8-selected_move.end_row}")
            print("=== AI MOVE SELECTION END ===\n")
            return selected_move
            
        print("No valid moves found!")
        print("=== AI MOVE SELECTION END ===\n")
        return None

    def evaluate_and_filter_moves(self, moves):
        """Evaluate safety of moves and filter unsafe ones"""
        safe_moves = []
        unsafe_moves = []
        
        for move in moves:
            is_safe, threat_value, num_attackers = self.evaluate_move_safety(
                move.start_row, move.start_col, move.end_row, move.end_col)
            
            # Store safety information on the move
            move.is_safe = is_safe
            move.threat_value = threat_value
            move.num_attackers = num_attackers
            
            # Consider piece value when determining if an "unsafe" move is actually worth it
            piece_value = {'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900, 'k': 20000}[move.piece_moved[1]]
            
            # Consider a move safe if:
            # 1. It's actually safe (no attackers)
            # 2. The piece being risked is less valuable than what it's attacking
            if is_safe or (move.piece_captured != '--' and 
                           piece_value < PIECE_VALUES.get(move.piece_captured[1], 0)):
                safe_moves.append(move)
            else:
                unsafe_moves.append(move)
        
        # Return safe moves if available, otherwise return all moves
        return safe_moves if safe_moves else moves