import json
import logging
from enum import Enum
from typing import NoReturn

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, StrictInt

from app.domain.game import GameStatus, InvalidMoveError, Player
from app.store import (
    CpuTurnUnavailableError,
    GameMode,
    GameNotFoundError,
    GameRecord,
    GameStore,
)


class CreateGameRequest(BaseModel):
    mode: GameMode = GameMode.HUMAN_VS_HUMAN


class MoveActor(str, Enum):
    HUMAN = "human"
    AI_AGENT = "ai-agent"


class MoveRequest(BaseModel):
    index: StrictInt
    actor: MoveActor = MoveActor.HUMAN


class GameStateResponse(BaseModel):
    game_id: str
    mode: GameMode
    board: list[Player | None]
    current_player: Player | None
    status: GameStatus
    winner: Player | None
    turn: int


router = APIRouter(prefix="/games", tags=["games"])
store = GameStore()
audit_logger = logging.getLogger("tic_tac_toe.audit")


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
        board=list(game.board),
        current_player=game.current_player,
        status=game.status,
        winner=game.winner,
        turn=game.turn,
    )


def _move_rejection(record: GameRecord, actor: MoveActor) -> tuple[str, str] | None:
    if record.mode is GameMode.CPU_VS_CPU:
        return "cpu_turn_unavailable", "current turn is server-controlled"

    if record.mode is GameMode.HUMAN_VS_CPU:
        if record.game.current_player is Player.O:
            return "cpu_turn_unavailable", "current turn is server-controlled"
        if actor is not MoveActor.HUMAN:
            return "move_actor_unavailable", "human-vs-cpu moves must be submitted by human"

    if record.mode is GameMode.AI_VS_CPU:
        if record.game.current_player is Player.O:
            return "cpu_turn_unavailable", "current turn is server-controlled"
        if actor is not MoveActor.AI_AGENT:
            return "move_actor_unavailable", "ai-vs-cpu moves must be submitted by ai-agent"

    if record.mode is GameMode.HUMAN_VS_HUMAN and actor is not MoveActor.HUMAN:
        return "move_actor_unavailable", "human-vs-human moves must be submitted by human"

    return None


@router.post("", response_model=GameStateResponse, status_code=201, operation_id="create_game")
def create_game(request: CreateGameRequest = Body(default=CreateGameRequest())) -> GameStateResponse:
    game_id, record = store.create(request.mode)
    return _state(game_id, record)


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


@router.post("/{game_id}/reset", response_model=GameStateResponse, operation_id="reset_game")
def reset_game(game_id: str) -> GameStateResponse:
    _get_record(game_id)
    return _state(game_id, store.reset(game_id))
