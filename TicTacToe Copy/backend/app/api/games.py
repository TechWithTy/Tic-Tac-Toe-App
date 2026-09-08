import json
import logging
from enum import Enum
from typing import Annotated, NoReturn

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, StrictInt

from app.agent_service import (
    AgentConfigurationError,
    AgentTurnError,
    AgentTurnService,
    AgentTurnUnavailableError,
)
from app.domain.game import GameStatus, InvalidMoveError, Player
from app.settings import Settings
from app.store import (
    CpuTurnUnavailableError,
    GameMode,
    GameNotFoundError,
    GameRecord,
    GameStore,
    PlayerAssignments,
    PlayerType,
)


class PlayerAssignmentsRequest(BaseModel):
    x: PlayerType
    o: PlayerType


class CreateGameRequest(BaseModel):
    mode: GameMode = GameMode.HUMAN_VS_HUMAN
    players: PlayerAssignmentsRequest | None = None


DEFAULT_CREATE_GAME_REQUEST = CreateGameRequest()


class MoveActor(str, Enum):
    HUMAN = "human"
    AI_AGENT = "ai-agent"


class MoveRequest(BaseModel):
    index: StrictInt
    actor: MoveActor = MoveActor.HUMAN


class GameStateResponse(BaseModel):
    game_id: str
    mode: GameMode
    players: PlayerAssignmentsRequest
    board: list[Player | None]
    current_player: Player | None
    status: GameStatus
    winner: Player | None
    turn: int


class GameCapabilitiesResponse(BaseModel):
    ai_agent_available: bool


router = APIRouter(prefix="/games", tags=["games"])
store = GameStore()
audit_logger = logging.getLogger("tic_tac_toe.audit")
agent_turn_service = AgentTurnService(settings=Settings(), store=store)


def _error(status_code: int, code: str, message: str) -> NoReturn:
    raise HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
    )


def _audit(
    *,
    actor: str,
    tool: str,
    game_id: str,
    requested_move: int | None,
    accepted: bool,
    turn: int,
) -> None:
    audit_logger.info(
        json.dumps(
            {
                "accepted": accepted,
                "actor": actor,
                "game_id": game_id,
                "requested_move": requested_move,
                "tool": tool,
                "turn": turn,
            },
            sort_keys=True,
        )
    )


def _get_record(game_id: str) -> GameRecord:
    try:
        return store.get(game_id)
    except GameNotFoundError:
        _error(404, "game_not_found", "game was not found")


def _state(game_id: str, record: GameRecord) -> GameStateResponse:
    game = record.game
    return GameStateResponse(
        game_id=game_id,
        mode=record.mode,
        players=PlayerAssignmentsRequest(x=record.players.x, o=record.players.o),
        board=list(game.board),
        current_player=game.current_player,
        status=game.status,
        winner=game.winner,
        turn=game.turn,
    )


def _move_rejection(record: GameRecord, actor: MoveActor) -> tuple[str, str] | None:
    current_player = record.game.current_player
    if current_player is None:
        return "invalid_move", "game is completed"

    controller = record.players.for_player(current_player)
    if controller is PlayerType.CPU:
        return "cpu_turn_unavailable", "current turn is server-controlled"

    expected_actor = MoveActor.HUMAN if controller is PlayerType.HUMAN else MoveActor.AI_AGENT
    if actor is not expected_actor:
        return "move_actor_unavailable", f"current turn must be submitted by {expected_actor.value}"

    return None


@router.post("", response_model=GameStateResponse, status_code=201, operation_id="create_game")
def create_game(
    request: Annotated[CreateGameRequest, Body()] = DEFAULT_CREATE_GAME_REQUEST,
) -> GameStateResponse:
    assignments = (
        PlayerAssignments(x=request.players.x, o=request.players.o)
        if request.players is not None
        else PlayerAssignments.from_mode(request.mode)
    )
    game_id, record = store.create(players=assignments)
    return _state(game_id, record)


@router.get(
    "/capabilities",
    response_model=GameCapabilitiesResponse,
    operation_id="get_game_capabilities",
)
def get_game_capabilities() -> GameCapabilitiesResponse:
    api_key = agent_turn_service.settings.openai_api_key
    return GameCapabilitiesResponse(
        ai_agent_available=bool(api_key and api_key.get_secret_value().strip())
    )


@router.get("/{game_id}", response_model=GameStateResponse, operation_id="get_game_state")
def get_game_state(game_id: str) -> GameStateResponse:
    return _state(game_id, _get_record(game_id))


@router.post("/{game_id}/moves", response_model=GameStateResponse, operation_id="make_move")
def make_move(game_id: str, request: MoveRequest) -> GameStateResponse:
    before = _get_record(game_id)
    rejection = _move_rejection(before, request.actor)
    if rejection is not None:
        code, message = rejection
        _audit(
            actor=request.actor.value,
            tool="make_move",
            game_id=game_id,
            requested_move=request.index,
            accepted=False,
            turn=before.game.turn,
        )
        _error(409, code, message)
    try:
        record = store.make_move(game_id, request.index)
    except InvalidMoveError as exc:
        _audit(
            actor=request.actor.value,
            tool="make_move",
            game_id=game_id,
            requested_move=request.index,
            accepted=False,
            turn=before.game.turn,
        )
        _error(409, "invalid_move", str(exc))
    _audit(
        actor=request.actor.value,
        tool="make_move",
        game_id=game_id,
        requested_move=request.index,
        accepted=True,
        turn=record.game.turn,
    )
    return _state(game_id, record)


@router.post("/{game_id}/cpu-move", response_model=GameStateResponse, operation_id="advance_cpu_turn")
def advance_cpu_turn(game_id: str) -> GameStateResponse:
    before = _get_record(game_id)
    before_board = before.game.board
    before_turn = before.game.turn
    try:
        record = store.advance_cpu(game_id)
    except CpuTurnUnavailableError as exc:
        _audit(
            actor="cpu",
            tool="advance_cpu_turn",
            game_id=game_id,
            requested_move=None,
            accepted=False,
            turn=before_turn,
        )
        _error(409, "cpu_turn_unavailable", str(exc))
    except InvalidMoveError as exc:
        _audit(
            actor="cpu",
            tool="advance_cpu_turn",
            game_id=game_id,
            requested_move=None,
            accepted=False,
            turn=before_turn,
        )
        _error(409, "invalid_move", str(exc))
    requested_move = next(
        index
        for index, (before_cell, after_cell) in enumerate(
            zip(before_board, record.game.board)
        )
        if before_cell is None and after_cell is not None
    )
    _audit(
        actor="cpu",
        tool="advance_cpu_turn",
        game_id=game_id,
        requested_move=requested_move,
        accepted=True,
        turn=record.game.turn,
    )
    return _state(game_id, record)


@router.post(
    "/{game_id}/agent-turn",
    response_model=GameStateResponse,
    operation_id="run_agent_turn",
)
async def run_agent_turn(game_id: str) -> GameStateResponse:
    before = _get_record(game_id)
    try:
        record = await agent_turn_service.run(game_id)
    except AgentTurnUnavailableError as exc:
        _audit(
            actor="ai-agent",
            tool="agent_turn",
            game_id=game_id,
            requested_move=None,
            accepted=False,
            turn=before.game.turn,
        )
        _error(409, "agent_turn_unavailable", str(exc))
    except AgentConfigurationError:
        _audit(
            actor="ai-agent",
            tool="agent_turn",
            game_id=game_id,
            requested_move=None,
            accepted=False,
            turn=before.game.turn,
        )
        _error(503, "agent_configuration_missing", "agent runtime is not configured")
    except AgentTurnError:
        _audit(
            actor="ai-agent",
            tool="agent_turn",
            game_id=game_id,
            requested_move=None,
            accepted=False,
            turn=before.game.turn,
        )
        _error(502, "agent_turn_failed", "agent did not complete a legal turn")
    return _state(game_id, record)


@router.post("/{game_id}/reset", response_model=GameStateResponse, operation_id="reset_game")
def reset_game(game_id: str) -> GameStateResponse:
    _get_record(game_id)
    return _state(game_id, store.reset(game_id))
