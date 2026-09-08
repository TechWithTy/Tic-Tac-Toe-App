from dataclasses import dataclass
from enum import Enum


class Player(str, Enum):
    X = "X"
    O = "O"


class GameStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    X_WON = "x_won"
    O_WON = "o_won"
    DRAW = "draw"


class InvalidMoveError(ValueError):
    """Raised when a move cannot be applied to a game state."""


WINNING_LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


@dataclass(frozen=True)
class Game:
    board: tuple[Player | None, ...]
    current_player: Player | None
    status: GameStatus
    winner: Player | None
    turn: int

    @classmethod
    def new(cls) -> "Game":
        return cls(
            board=(None,) * 9,
            current_player=Player.X,
            status=GameStatus.IN_PROGRESS,
            winner=None,
            turn=0,
        )

    def move(self, index: int) -> "Game":
        if self.status is not GameStatus.IN_PROGRESS:
            raise InvalidMoveError("game is completed")
        if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < 9:
            raise InvalidMoveError("cell index must be an integer from 0 to 8")
        if self.board[index] is not None:
            raise InvalidMoveError("cell is occupied")

        board = list(self.board)
        player = self.current_player
        board[index] = player
        board_tuple = tuple(board)

        if self._has_winning_line(board_tuple, player):
            status = GameStatus.X_WON if player is Player.X else GameStatus.O_WON
            return Game(board_tuple, None, status, player, self.turn + 1)

        if all(cell is not None for cell in board_tuple):
            return Game(board_tuple, None, GameStatus.DRAW, None, self.turn + 1)

        next_player = Player.O if player is Player.X else Player.X
        return Game(board_tuple, next_player, GameStatus.IN_PROGRESS, None, self.turn + 1)

    def reset(self) -> "Game":
        return Game.new()

    @staticmethod
    def _has_winning_line(board: tuple[Player | None, ...], player: Player | None) -> bool:
        return player is not None and any(
            all(board[index] is player for index in line) for line in WINNING_LINES
        )
