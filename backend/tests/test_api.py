import json
import logging

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_game(mode: str = "human_vs_human") -> dict:
    response = client.post("/games", json={"mode": mode})
    assert response.status_code == 201
    return response.json()


def create_game_with_players(x: str, o: str) -> dict:
    response = client.post("/games", json={"players": {"x": x, "o": o}})
    assert response.status_code == 201
    return response.json()


def test_create_and_get_game_return_canonical_initial_state():
    created = create_game()

    assert created["game_id"]
    assert created["mode"] == "human_vs_human"
    assert created["board"] == [None] * 9
    assert created["current_player"] == "X"
    assert created["status"] == "in_progress"
    assert created["winner"] is None
    assert created["turn"] == 0

    response = client.get(f"/games/{created['game_id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_create_game_accepts_explicit_independent_player_assignments():
    created = create_game_with_players("human", "ai-agent")

    assert created["players"] == {"x": "human", "o": "ai-agent"}
    assert created["mode"] == "human_vs_ai"
    assert created["current_player"] == "X"


def test_cpu_and_human_pairing_uses_current_player_controller_for_validation():
    created = create_game_with_players("cpu", "human")
    game_id = created["game_id"]

    rejected = client.post(f"/games/{game_id}/moves", json={"index": 0, "actor": "human"})
    assert rejected.status_code == 409
    assert rejected.json()["detail"]["code"] == "cpu_turn_unavailable"

    cpu_move = client.post(f"/games/{game_id}/cpu-move")
    assert cpu_move.status_code == 200
    assert cpu_move.json()["current_player"] == "O"

    human_move = client.post(f"/games/{game_id}/moves", json={"index": 1, "actor": "human"})
    assert human_move.status_code == 200
    assert human_move.json()["board"][1] == "O"


def test_human_and_ai_pairing_accepts_only_the_controller_for_each_turn():
    created = create_game_with_players("human", "ai-agent")
    game_id = created["game_id"]

    human_move = client.post(f"/games/{game_id}/moves", json={"index": 0, "actor": "human"})
    assert human_move.status_code == 200
    assert human_move.json()["current_player"] == "O"

    rejected = client.post(f"/games/{game_id}/moves", json={"index": 1, "actor": "human"})
    assert rejected.status_code == 409
    assert rejected.json()["detail"]["code"] == "move_actor_unavailable"

    agent_move = client.post(f"/games/{game_id}/moves", json={"index": 1, "actor": "ai-agent"})
    assert agent_move.status_code == 200
    assert agent_move.json()["board"][1] == "O"


def test_valid_move_returns_new_canonical_state():
    created = create_game()

    response = client.post(
        f"/games/{created['game_id']}/moves",
        json={"index": 4},
    )

    assert response.status_code == 200
    assert response.json()["board"][4] == "X"
    assert response.json()["current_player"] == "O"
    assert response.json()["turn"] == 1


def test_valid_move_emits_a_structured_audit_event(caplog):
    created = create_game()
    caplog.set_level(logging.INFO, logger="tic_tac_toe.audit")

    response = client.post(
        f"/games/{created['game_id']}/moves",
        json={"index": 4},
    )

    assert response.status_code == 200
    event = json.loads(caplog.records[-1].message)
    assert event == {
        "accepted": True,
        "actor": "human",
        "game_id": created["game_id"],
        "requested_move": 4,
        "tool": "make_move",
        "turn": 1,
    }


def test_invalid_move_returns_structured_error_and_preserves_state():
    created = create_game()
    game_id = created["game_id"]
    client.post(f"/games/{game_id}/moves", json={"index": 0})

    response = client.post(f"/games/{game_id}/moves", json={"index": 0})

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "invalid_move"
    assert response.json()["detail"]["message"] == "cell is occupied"
    assert client.get(f"/games/{game_id}").json()["turn"] == 1


def test_move_index_rejects_type_coercion_without_mutating_state():
    created = create_game()
    game_id = created["game_id"]

    response = client.post(f"/games/{game_id}/moves", json={"index": "0"})

    assert response.status_code == 422
    assert response.json()["detail"]
    assert client.get(f"/games/{game_id}").json()["turn"] == 0


def test_terminal_game_rejects_moves_and_preserves_completed_state():
    created = create_game()
    game_id = created["game_id"]
    for index in [0, 3, 1, 4, 2]:
        assert client.post(f"/games/{game_id}/moves", json={"index": index}).status_code == 200

    response = client.post(f"/games/{game_id}/moves", json={"index": 5})

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "invalid_move"
    state = client.get(f"/games/{game_id}").json()
    assert state["status"] == "x_won"
    assert state["winner"] == "X"
    assert state["turn"] == 5
    assert state["board"][5] is None


def test_cpu_advance_is_server_owned_and_mode_aware():
    created = create_game("human_vs_cpu")
    game_id = created["game_id"]

    rejected = client.post(f"/games/{game_id}/cpu-move")

    assert rejected.status_code == 409
    assert rejected.json()["detail"]["code"] == "cpu_turn_unavailable"

    client.post(f"/games/{game_id}/moves", json={"index": 4})
    response = client.post(f"/games/{game_id}/cpu-move")

    assert response.status_code == 200
    state = response.json()
    assert state["board"].count("O") == 1
    assert state["turn"] == 2


def test_human_vs_cpu_rejects_direct_moves_on_cpu_turn_without_mutating_state():
    created = create_game("human_vs_cpu")
    game_id = created["game_id"]
    client.post(f"/games/{game_id}/moves", json={"index": 4})
    before = client.get(f"/games/{game_id}").json()

    response = client.post(f"/games/{game_id}/moves", json={"index": 0})

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "cpu_turn_unavailable"
    assert client.get(f"/games/{game_id}").json() == before


def test_cpu_vs_cpu_rejects_direct_moves_without_mutating_state():
    created = create_game("cpu_vs_cpu")
    game_id = created["game_id"]

    response = client.post(f"/games/{game_id}/moves", json={"index": 0})

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "cpu_turn_unavailable"
    assert client.get(f"/games/{game_id}").json() == created


def test_ai_vs_cpu_accepts_only_ai_agent_moves_on_the_ai_turn():
    created = create_game("ai_vs_cpu")
    game_id = created["game_id"]

    rejected = client.post(
        f"/games/{game_id}/moves",
        json={"index": 0, "actor": "human"},
    )

    assert rejected.status_code == 409
    assert rejected.json()["detail"]["code"] == "move_actor_unavailable"
    assert client.get(f"/games/{game_id}").json() == created

    accepted = client.post(
        f"/games/{game_id}/moves",
        json={"index": 0, "actor": "ai-agent"},
    )

    assert accepted.status_code == 200
    assert accepted.json()["board"][0] == "X"


def test_cpu_vs_cpu_can_finish_as_a_draw_through_the_api():
    created = create_game("cpu_vs_cpu")
    game_id = created["game_id"]
    state = created

    while state["status"] == "in_progress":
        response = client.post(f"/games/{game_id}/cpu-move")
        assert response.status_code == 200
        state = response.json()

    assert state["status"] == "draw"
    assert state["winner"] is None
    assert state["turn"] == 9


def test_reset_returns_a_fresh_game_state():
    created = create_game()
    game_id = created["game_id"]
    client.post(f"/games/{game_id}/moves", json={"index": 0})

    response = client.post(f"/games/{game_id}/reset")

    assert response.status_code == 200
    assert response.json()["game_id"] == game_id
    assert response.json()["board"] == [None] * 9
    assert response.json()["current_player"] == "X"
    assert response.json()["turn"] == 0


def test_unknown_game_returns_structured_not_found_error():
    response = client.get("/games/not-a-real-game")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "game_not_found"


def test_cors_allows_only_the_vite_origin():
    allowed = client.options(
        "/games",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    denied = client.options(
        "/games",
        headers={
            "Origin": "http://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-origin" not in denied.headers
