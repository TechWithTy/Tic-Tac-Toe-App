from dataclasses import dataclass
from enum import Enum
from uuid import uuid4

from app.domain.game import Game, Player
from app.domain.minimax import best_move


class GameMode(str, Enum):
    HUMAN_VS_HUMAN = "human_vs_human"
    HUMAN_VS_CPU = "human_vs_cpu"
    HUMAN_VS_AI = "human_vs_ai"
    CPU_VS_HUMAN = "cpu_vs_human"
    CPU_VS_CPU = "cpu_vs_cpu"
    CPU_VS_AI = "cpu_vs_ai"
    AI_VS_HUMAN = "ai_vs_human"
    AI_VS_CPU = "ai_vs_cpu"
    AI_VS_AI = "ai_vs_ai"


class PlayerType(str, Enum):
    HUMAN = "human"
    CPU = "cpu"
    AI_AGENT = "ai-agent"


@dataclass(frozen=True)
class PlayerAssignments:
    x: PlayerType
    o: PlayerType

    @classmethod
    def from_mode(cls, mode: GameMode) -> "PlayerAssignments":
        x, o = mode.value.split("_vs_")
        type_by_name = {"human": PlayerType.HUMAN, "cpu": PlayerType.CPU, "ai": PlayerType.AI_AGENT}
        return cls(type_by_name[x], type_by_name[o])

    def for_player(self, player: Player) -> PlayerType:
        return self.x if player is Player.X else self.o

    def mode(self) -> GameMode:
        name_by_type = {
            PlayerType.HUMAN: "human",
            PlayerType.CPU: "cpu",
            PlayerType.AI_AGENT: "ai",
        }
        return GameMode(f"{name_by_type[self.x]}_vs_{name_by_type[self.o]}")


class GameNotFoundError(LookupError):
    """Raised when a requested game id is not in the in-memory store."""


class CpuTurnUnavailableError(ValueError):
    """Raised when the current player is not controlled by the server CPU."""


@dataclass
class GameRecord:
    game: Game
    mode: GameMode
    players: PlayerAssignments


class GameStore:
    def __init__(self) -> None:
        self._games: dict[str, GameRecord] = {}

    def create(
        self,
        mode: GameMode = GameMode.HUMAN_VS_HUMAN,
        players: PlayerAssignments | None = None,
    ) -> tuple[str, GameRecord]:
        game_id = uuid4().hex
        assignments = players or PlayerAssignments.from_mode(mode)
        record = GameRecord(game=Game.new(), mode=assignments.mode(), players=assignments)
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
        return record.players.for_player(current_player) is PlayerType.CPU
