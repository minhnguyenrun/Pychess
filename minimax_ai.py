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

    def quiescence_search(self, alpha, beta, depth=0):
        """Quiescence search to evaluate tactical positions"""
        standing_pat = self.game.evaluate(self.player if depth % 2 == 0 else -self.player)
        
        if depth >= 4:  # Limit quiescence depth
            return standing_pat, []
            
        if standing_pat >= beta:
            return beta, []
            
        if alpha < standing_pat:
            alpha = standing_pat
            
        # Only consider captures for quiescence search
        captures = []
        ai = self.player if depth % 2 == 0 else -self.player
        
        for r in range(8):
            for c in range(8):
                if self.game.board[r][c] is not None and self.game.board[r][c].player == ai:
                    for i, j in self.game.board[r][c].get_move():
                        if self.game.board[i][j] is not None:  # Only captures
                            victim_value = abs(self.game.board[i][j].value)
                            attacker_value = abs(self.game.board[r][c].value)
                            score = victim_value - (attacker_value / 10.0)
                            captures.append((score, r, c, i, j))
                            
        # Sort captures by MVA-LVA
        captures.sort(reverse=True)
        
        i1, j1, i2, j2 = 0, 0, 0, 0
        for _, r, c, i, j in captures:
            self.game.goto(r, c, i, j)
            score, _ = self.quiescence_search(-beta, -alpha, depth + 1)
            score = -score
            self.game.backto()
            
            if score > alpha:
                alpha = score
                i1, j1, i2, j2 = r, c, i, j
                
            if alpha >= beta:
                break
                
        return alpha, (i1, j1, i2, j2)

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
            alpha, best_move = self.quiescence_search(alpha, beta)
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
        """Check if a piece is under threat from opponent pieces"""
        piece_player = piece.player
        for i in range(8):
            for j in range(8):
                if (self.game.board[i][j] is not None and 
                    self.game.board[i][j].player == -piece_player):
                    for move_i, move_j in self.game.board[i][j].get_move():
                        if move_i == r and move_j == c:
                            # Check if attacker is less valuable than target
                            attacker_value = abs(self.game.board[i][j].value)
                            target_value = abs(piece.value)
                            if attacker_value < target_value:
                                return True, attacker_value
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
            
            # Track position history to avoid repetition
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
                        if distance == 2:  # Knight's move away - ideal distance
                            king_restriction_moves.append((1, move))
                    elif move.piece_moved[1] == 'k':
                        # Move our king toward enemy king in endgame
                        curr_distance = max(abs(move.start_row - enemy_king_pos[0]), 
                                           abs(move.start_col - enemy_king_pos[1]))
                        new_distance = max(abs(move.end_row - enemy_king_pos[0]), 
                                          abs(move.end_col - enemy_king_pos[1]))
                        if new_distance < curr_distance:
                            king_restriction_moves.append((2, move))
            
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
        
        # First check for high-value captures
        capture_moves = [m for m in valid_moves if m.piece_captured != '--']
        if capture_moves:
            print("Using fallback capture move selection:")
            # Sort by value of captured piece
            queen_captures = [m for m in capture_moves if m.piece_captured[1] == 'q']
            if queen_captures:
                print(f"Selected queen capture: {queen_captures[0].piece_moved} {chr(97+queen_captures[0].start_col)}{8-queen_captures[0].start_row}->{chr(97+queen_captures[0].end_col)}{8-queen_captures[0].end_row}")
                print("=== AI MOVE SELECTION END ===\n")
                return queen_captures[0]  # Return first move that captures queen
                
            rook_captures = [m for m in capture_moves if m.piece_captured[1] == 'r']
            if rook_captures:
                print(f"Selected rook capture: {rook_captures[0].piece_moved} {chr(97+rook_captures[0].start_col)}{8-rook_captures[0].start_row}->{chr(97+rook_captures[0].end_col)}{8-rook_captures[0].end_row}")
                print("=== AI MOVE SELECTION END ===\n")
                return rook_captures[0]  # Return first move that captures rook
                
            minor_captures = [m for m in capture_moves if m.piece_captured[1] in ['b', 'n']]
            if minor_captures:
                print(f"Selected minor piece capture: {minor_captures[0].piece_moved} {chr(97+minor_captures[0].start_col)}{8-minor_captures[0].start_row}->{chr(97+minor_captures[0].end_col)}{8-minor_captures[0].end_row}")
                print("=== AI MOVE SELECTION END ===\n")
                return minor_captures[0]  # Return first move that captures bishop/knight
                
            # Any capture is better than no capture
            print(f"Selected any capture: {capture_moves[0].piece_moved} {chr(97+capture_moves[0].start_col)}{8-capture_moves[0].start_row}->{chr(97+capture_moves[0].end_col)}{8-capture_moves[0].end_row}")
            print("=== AI MOVE SELECTION END ===\n")
            return capture_moves[0]
            
        # If no captures, prioritize different move types and use randomization
        if valid_moves:
            
            
            # Categorize moves by type for better selection
            pawn_moves = [m for m in valid_moves if m.piece_moved[1] == 'p']
            developing_moves = [m for m in valid_moves if m.piece_moved[1] in ['n', 'b'] and 
                              ((m.piece_moved[0] == 'w' and m.start_row == 7) or 
                               (m.piece_moved[0] == 'b' and m.start_row == 0))]
            center_control_moves = [m for m in valid_moves if m.end_row in [3, 4] and m.end_col in [3, 4]]
            
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