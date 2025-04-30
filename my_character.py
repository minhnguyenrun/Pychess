from functools import partial

# Piece values for evaluation
PIECE_VALUES = {"p": 1, "n": 3, "b": 3, "r": 5, "q": 9, "k": 0}

class Character:
    def __init__(self, state, name, i, j):
        self.state, self.i, self.j, self.value = state, i, j, PIECE_VALUES[name[1]]
        self.player = {'b': -1, 'w': 1}[name[0]]
        self.move = []
        self.value = self.value * self.player

    def get_move(self):
        self.move = []
        self.func()
        return self.move

    def get_normal_move(self, func):
        for di, dj in self.dir_set: 
            func(di, dj)

    def check_valid(self, i, j):
        return i > -1 and j > -1 and i < 8 and j < 8

    def walk(self, di, dj):
        i = self.i + di
        j = self.j + dj
        while self.check_valid(i, j):
            cell = self.state.board[i][j]
            if cell is not None:
                if cell.player != self.player:
                    self.move.append((i, j))
                break
            self.move.append((i, j))
            i += di
            j += dj

    def jump(self, di, dj):
        i = self.i + di
        j = self.j + dj
        if self.check_valid(i, j) and (self.state.board[i][j] is None or self.state.board[i][j].player != self.player):
            self.move.append((i, j))

    def make_a_move(self, i, j):
        self.i = i
        self.j = j

class Queen(Character):
    def __init__(self, state, name, i, j):
        super().__init__(state, name, i, j)
        self.dir_set = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
        self.func = partial(self.get_normal_move, func = self.walk)
        self.special_move = None

class Pawn(Character):
    def __init__(self, state, name, i, j):
        super().__init__(state, name, i, j)
        self.dir_set = []
        self.func = self.my_special_move
        self.level = 1
        self.queen_dir_set = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
        self.queen_func = self.walk

    def pawn_move(self, di, dj):
        i = self.i + di
        j = self.j + dj
        if self.check_valid(i, j) and self.state.board[i][j] is None:
            self.move.append((i, j))
            return True
        return False

    def pawn_attack(self, di, dj):
        i = self.i + di
        j = self.j + dj
        if self.check_valid(i, j) and self.state.board[i][j] is not None and self.state.board[i][j].player != self.player:
            self.move.append((i, j))

    def my_special_move(self):
        if self.level == 1:
            if self.pawn_move(-self.player, 0) and ((self.player == -1 and self.i == 1) or (self.player == 1 and self.i == 6)):
                self.pawn_move(-self.player * 2, 0)
            self.pawn_attack(-self.player, 1)
            self.pawn_attack(-self.player, -1)
        else:
            for di, dj in self.queen_dir_set: 
                self.queen_func(di, dj)

class King(Character):
    def __init__(self, state, name, i, j):
        super().__init__(state, name, i, j)
        self.dir_set = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
        self.func = partial(self.get_normal_move, func = self.jump)
        self.special_move = None

class Rook(Character):
    def __init__(self, state, name, i, j):
        super().__init__(state, name, i, j)
        self.dir_set = ((1, 0), (-1, 0), (0, 1), (0, -1))
        self.func = partial(self.get_normal_move, func = self.walk)

class Bishop(Character):
    def __init__(self, state, name, i, j):
        super().__init__(state, name, i, j)
        self.dir_set = ((1, 1), (1, -1), (-1, 1), (-1, -1))
        self.func = partial(self.get_normal_move, func = self.walk)

class Knight(Character):
    def __init__(self, state, name, i, j):
        super().__init__(state, name, i, j)
        self.dir_set = ((2, 1), (-2, 1), (2, -1), (-2, -1), (1, 2), (-1, 2), (1, -2), (-1, -2))
        self.func = partial(self.get_normal_move, func = self.jump)