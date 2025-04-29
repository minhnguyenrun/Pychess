import math
from copy import deepcopy
from my_character import Queen, Pawn, King, Knight, Bishop, Rook
import random

# Piece values for evaluation
PIECE_VALUES = {"p": 1, "n": 3, "b": 3, "r": 5, "q": 9, "k": 0}

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

    def deep_evaluate(self, ai):
        score = 0
        for r in range(8):
            for c in range(8):
                chess_man = self.board[r][c]
                if chess_man is not None:
                    score += chess_man.value + len(chess_man.move) / 10000 * chess_man.player
        return ai * score

    def evaluate(self, ai):
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
    def __init__(self, game, max_depth):
        self.max_depth = max_depth
        self.game = game

    def generate_state(self, ai):
        move = []
        b = 0
        for r in range(8):
            for c in range(8):
                if self.game.board[r][c] is not None and self.game.board[r][c].player == ai:
                    for i, j in self.game.board[r][c].get_move():
                        move.append((r, c, i, j))
        return move

    def alphabeta(self, depth, alpha = -1000000, beta = 1000000, bonus = 0):
        ai = -1 if depth % 2 == 0 else 1
        if depth == self.max_depth:
            return self.game.deep_evaluate(ai) - bonus * ai, []
        i1, j1, i2, j2 = 0, 0, 0, 0
        move = self.generate_state(ai)
        #if (depth == 0):
            #for r, c, i, j in move:
                #print(self.game.board[r][c].value, ":", i, j)
        random.shuffle(move)
        best_path = []
        for r, c, i, j in move:
            if self.game.board[i][j] is not None and self.game.board[i][j].value == 0:
                result = ai * 10000
                path = []
            else:
                self.game.goto(r, c, i, j)
                if depth == 0:
                    ok = False
                    for a, b in self.game.board[i][j].get_move():
                        if self.game.board[a][b] is not None and self.game.board[a][b].value == 0: 
                            ok = True
                    if ok:
                        result, path = self.alphabeta(depth + 1, -beta, -alpha, 0.5)
                    else:
                        result, path = self.alphabeta(depth + 1, -beta, -alpha)
                else: result, path = self.alphabeta(depth + 1, -beta, -alpha, bonus)
                result = -result
                self.game.backto()
            if result > alpha:
                alpha = result
                i1, j1, i2, j2 = r, c, i ,j
                best_path = path
            if alpha >= beta:
                return alpha, [(i1, j1, i2, j2)] +  best_path
        return alpha, [(i1, j1, i2, j2)] + best_path
        

    def get_best_move(self):
        best_value, best_move = self.alphabeta(0)
        #print(best_value,":", best_move)
        i1, j1, i2, j2 = best_move[0]
        for m in self.game.game_adaptee.get_valid_moves():
            if i1 == m.start_row and i2 == m.end_row and j1 == m.start_col and j2 == m.end_col:
                return m
        return None
