from time import perf_counter

import pytest

from app.domain.game import Game, GameStatus, InvalidMoveError, Player
from app.domain.minimax import best_move


def play(game: Game, moves: list[int]) -> Game:
    for move in moves:
        game = game.move(move)
    return game


def test_cpu_returns_an_empty_cell_for_the_current_player():
    game = Game.new().move(4)

    move = best_move(game)

    assert game.board[move] is None


def test_cpu_takes_an_immediate_winning_move():
    game = play(Game.new(), [0, 3, 1, 4])

    assert game.current_player is Player.X
    assert best_move(game) == 2


def test_cpu_blocks_an_immediate_opponent_win():
    game = play(Game.new(), [0, 4, 1])

    assert game.current_player is Player.O
    assert best_move(game) == 2


def test_cpu_is_deterministic_for_the_same_state():
    game = play(Game.new(), [0, 4])

    assert best_move(game) == best_move(game)


def test_cpu_moves_from_an_empty_board_within_an_interactive_budget():
    started = perf_counter()

    best_move(Game.new())

    assert perf_counter() - started < 1.0


def test_perfect_cpu_against_perfect_cpu_finishes_in_a_draw():
    game = Game.new()

    while game.status is GameStatus.IN_PROGRESS:
        game = game.move(best_move(game))

    assert game.status is GameStatus.DRAW
    assert game.turn == 9


def test_cpu_rejects_terminal_games():
    game = play(Game.new(), [0, 3, 1, 4, 2])

    with pytest.raises(InvalidMoveError, match="completed"):
        best_move(game)
