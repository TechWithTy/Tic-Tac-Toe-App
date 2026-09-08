from functools import lru_cache

from .game import Game, GameStatus, InvalidMoveError, Player


def best_move(game: Game) -> int:
    """Return the deterministic optimal move for the current player."""
    if game.status is not GameStatus.IN_PROGRESS:
        raise InvalidMoveError("game is completed")

    player = game.current_player
    if player is None:
        raise InvalidMoveError("game is completed")

    moves = [index for index, cell in enumerate(game.board) if cell is None]
    if not moves:
        raise InvalidMoveError("game is completed")

    scored_moves = [
        (index, _minimax(game.move(index), player, depth=1)) for index in moves
    ]
    return max(scored_moves, key=lambda item: item[1])[0]


@lru_cache(maxsize=100_000)
def _minimax(game: Game, maximizing_player: Player, depth: int) -> int:
    terminal_score = _terminal_score(game, maximizing_player, depth)
    if terminal_score is not None:
        return terminal_score

    moves = [index for index, cell in enumerate(game.board) if cell is None]
    scores = [_minimax(game.move(index), maximizing_player, depth + 1) for index in moves]

    if game.current_player is maximizing_player:
        return max(scores)
    return min(scores)


def _terminal_score(game: Game, maximizing_player: Player, depth: int) -> int | None:
    if game.status is GameStatus.DRAW:
        return 0
    if game.status is GameStatus.IN_PROGRESS:
        return None
    if game.winner is maximizing_player:
        return 10 - depth
    return depth - 10
