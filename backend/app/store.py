from dataclasses import dataclass
from enum import Enum
from uuid import uuid4

from app.domain.game import Game, Player
from app.domain.minimax import best_move


class GameMode(str, Enum):
    HUMAN_VS_HUMAN = "human_vs_human"
    HUMAN_VS_CPU = "human_vs_cpu"
    CPU_VS_CPU = "cpu_vs_cpu"
    AI_VS_CPU = "ai_vs_cpu"


class GameNotFoundError(LookupError):
    """Raised when a requested game id is not in the in-memory store."""


class CpuTurnUnavailableError(ValueError):
    """Raised when the current player is not controlled by the server CPU."""


@dataclass
class GameRecord:
    game: Game
    mode: GameMode


class GameStore:
    def __init__(self) -> None:
        self._games: dict[str, GameRecord] = {}

    def create(self, mode: GameMode) -> tuple[str, GameRecord]:
        game_id = uuid4().hex
        record = GameRecord(game=Game.new(), mode=mode)
        self._games[game_id] = record
        return game_id, record

    def get(self, game_id: str) -> GameRecord:
        try:
            return self._games[game_id]
        except KeyError as exc:
            raise GameNotFoundError(game_id) from exc

    def make_move(self, game_id: str, index: int) -> GameRecord:
        record = self.get(game_id)
        record.game = record.game.move(index)
        return record

    def reset(self, game_id: str) -> GameRecord:
        record = self.get(game_id)
        record.game = record.game.reset()
        return record

    def advance_cpu(self, game_id: str) -> GameRecord:
        record = self.get(game_id)
        if not self._is_cpu_turn(record):
            raise CpuTurnUnavailableError("current turn is not server-controlled")

        record.game = record.game.move(best_move(record.game))
        return record

    @staticmethod
    def _is_cpu_turn(record: GameRecord) -> bool:
        current_player = record.game.current_player
        if current_player is None:
            return False
        if record.mode is GameMode.CPU_VS_CPU:
            return True
        return record.mode in {GameMode.HUMAN_VS_CPU, GameMode.AI_VS_CPU} and current_player is Player.O
