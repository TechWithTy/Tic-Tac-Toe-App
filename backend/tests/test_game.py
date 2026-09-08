import pytest

from app.domain.game import Game, GameStatus, InvalidMoveError, Player


def play(game: Game, moves: list[int]) -> Game:
    for move in moves:
        game = game.move(move)
    return game


def test_new_game_starts_with_x_and_alternates_players():
    game = Game.new()

    assert game.current_player is Player.X
    assert game.status is GameStatus.IN_PROGRESS
    assert game.board == (None,) * 9

    next_game = game.move(4)

    assert next_game.board[4] is Player.X
    assert next_game.current_player is Player.O
    assert next_game.turn == 1
    assert game.board == (None,) * 9


def test_occupied_cell_is_rejected_without_mutating_state():
    game = Game.new().move(0)

    with pytest.raises(InvalidMoveError, match="occupied"):
        game.move(0)

    assert game.board == (Player.X,) + (None,) * 8
    assert game.current_player is Player.O
    assert game.turn == 1


@pytest.mark.parametrize(
    "moves",
    [
        [0, 3, 1, 4, 2],
        [3, 0, 4, 1, 5],
        [6, 0, 7, 1, 8],
        [0, 1, 3, 2, 6],
        [1, 0, 4, 2, 7],
        [2, 0, 5, 1, 8],
        [0, 1, 4, 2, 8],
        [2, 0, 4, 1, 6],
    ],
)
def test_all_rows_columns_and_diagonals_detect_an_x_win(moves: list[int]):
    game = play(Game.new(), moves)

    assert game.status is GameStatus.X_WON
    assert game.winner is Player.X
    assert game.current_player is None


def test_full_board_without_winner_is_a_draw():
    game = play(Game.new(), [0, 1, 2, 4, 3, 5, 7, 6, 8])

    assert game.status is GameStatus.DRAW
    assert game.winner is None
    assert game.current_player is None
    assert game.turn == 9


def test_completed_game_rejects_moves_without_mutating_state():
    game = play(Game.new(), [0, 3, 1, 4, 2])

    with pytest.raises(InvalidMoveError, match="completed"):
        game.move(5)

    assert game.status is GameStatus.X_WON
    assert game.turn == 5
    assert game.board[5] is None


@pytest.mark.parametrize("index", [-1, 9, 1.5, "0", None])
def test_invalid_cell_index_is_rejected_without_mutating_state(index: object):
    game = Game.new()

    with pytest.raises(InvalidMoveError, match="cell index"):
        game.move(index)  # type: ignore[arg-type]

    assert game == Game.new()


def test_reset_returns_a_fresh_x_turn_game():
    game = play(Game.new(), [0, 4, 1])

    reset_game = game.reset()

    assert reset_game == Game.new()
    assert reset_game is not game
