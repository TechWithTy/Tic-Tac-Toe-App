import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

const initialResponse = {
  game_id: "game-1",
  mode: "human_vs_human",
  players: { x: "human", o: "human" },
  board: [null, null, null, null, null, null, null, null, null],
  current_player: "X",
  status: "in_progress",
  winner: null,
  turn: 0,
};

const capabilitiesResponse = {
  ai_agent_available: true,
};

const unavailableCapabilitiesResponse = {
  ai_agent_available: false,
};

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("player pairing setup", () => {
  it("renders independent X and O controller selectors", () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => unavailableCapabilitiesResponse }));
    render(<App />);

    expect(screen.getByRole("heading", { name: /choose your players/i })).toBeInTheDocument();
    expect(screen.getByRole("group", { name: /player x/i })).toBeInTheDocument();
    expect(screen.getByRole("group", { name: /player o/i })).toBeInTheDocument();
    expect(screen.getAllByRole("radio", { name: "Human" })).toHaveLength(2);
    expect(screen.getAllByRole("radio", { name: "CPU" })).toHaveLength(2);
    expect(screen.getAllByRole("radio", { name: "AI Agent" })).toHaveLength(2);
    expect(screen.getAllByRole("radio", { name: "AI Agent" }).every((radio) => radio.hasAttribute("disabled"))).toBe(true);
    expect(screen.getByRole("button", { name: /start game/i })).toBeInTheDocument();
  });

  it("does not create a game until Start game is pressed", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => capabilitiesResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => initialResponse });
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    const playerX = screen.getByRole("group", { name: /player x/i });
    fireEvent.click(within(playerX).getByRole("radio", { name: "CPU" }));
    expect(fetchMock).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: /start game/i }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(fetchMock).toHaveBeenLastCalledWith(
      "http://localhost:8000/games",
      expect.objectContaining({
        body: JSON.stringify({ players: { x: "cpu", o: "human" } }),
        method: "POST",
      }),
    );
  });

  it("shows Game Started and disables the start button after the server accepts the game", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => capabilitiesResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => initialResponse });
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    const startButton = screen.getByRole("button", { name: /start game/i });
    fireEvent.click(startButton);

    await waitFor(() => expect(screen.getByRole("button", { name: /game started/i })).toBeDisabled());
    expect(screen.getByText(/fastapi connected/i)).toBeInTheDocument();
    expect(screen.getByText("Current Turn")).toBeInTheDocument();
    const turnPanel = screen.getByText("Current Turn").closest("[aria-live='polite']");
    expect(turnPanel).toHaveTextContent("X To Move · Server State");
    expect(turnPanel).toHaveClass("items-center", "text-center");
  });

  it("renders one crisp hover indicator without a placeholder glyph in empty cells", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => capabilitiesResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => initialResponse });
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /start game/i }));
    const emptyCell = await screen.findByRole("button", { name: "Cell 1" });

    expect(emptyCell).not.toHaveTextContent("·");
  });

  it("disables player selections while the game is active and re-enables them after restart", async () => {
    const resetResponse = { ...initialResponse, turn: 0 };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => capabilitiesResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => initialResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => resetResponse });
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /start game/i }));
    await waitFor(() => expect(screen.getByRole("button", { name: /game started/i })).toBeDisabled());
    expect(screen.getAllByRole("radio", { name: "Human" }).every((radio) => radio.hasAttribute("disabled"))).toBe(true);
    expect(screen.getAllByRole("radio", { name: "CPU" }).every((radio) => radio.hasAttribute("disabled"))).toBe(true);

    fireEvent.click(screen.getByRole("button", { name: /reset game/i }));
    await waitFor(() => expect(screen.getByRole("button", { name: /start game/i })).toBeEnabled());
    expect(screen.getAllByRole("radio", { name: "Human" }).every((radio) => !radio.hasAttribute("disabled"))).toBe(true);
  });

  it("shows an actionable message when the game server cannot be reached", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce({ ok: true, json: async () => unavailableCapabilitiesResponse })
        .mockRejectedValueOnce(new TypeError("Failed to fetch")),
    );
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /start game/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/unable to connect to the game server/i);
    await waitFor(() => expect(screen.getByText("Disconnected")).toBeInTheDocument());
  });

  it("shows Disconnected when the initial FastAPI capability check fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    render(<App />);

    expect(await screen.findByText("Disconnected")).toBeInTheDocument();
  });

  it("submits a human move only after a game has started", async () => {
    const moveResponse = {
      ...initialResponse,
      board: ["X", null, null, null, null, null, null, null, null],
      current_player: "O",
      turn: 1,
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => unavailableCapabilitiesResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => initialResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => moveResponse });
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /start game/i }));
    await waitFor(() => expect(screen.getByRole("button", { name: /cell 1/i })).not.toBeDisabled());
    fireEvent.click(screen.getByRole("button", { name: /cell 1/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    expect(fetchMock).toHaveBeenLastCalledWith(
      "http://localhost:8000/games/game-1/moves",
      expect.objectContaining({ body: JSON.stringify({ actor: "human", index: 0 }), method: "POST" }),
    );
  });

  it("keeps board cells on the same plane when hovered", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => unavailableCapabilitiesResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => initialResponse });
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /start game/i }));

    const cell = await screen.findByRole("button", { name: "Cell 1" });
    expect(cell.className).not.toContain("hover:-translate-y-0.5");
  });

  it("shows the human move before the AI response finishes", async () => {
    const aiGameStartResponse = {
      ...initialResponse,
      mode: "human_vs_ai",
      players: { x: "human", o: "ai-agent" },
    };
    const humanMoveResponse = {
      ...aiGameStartResponse,
      board: ["X", null, null, null, null, null, null, null, null],
      current_player: "O",
      turn: 1,
    };
    const aiMoveResponse = {
      ...humanMoveResponse,
      board: ["X", null, null, null, "O", null, null, null, null],
      current_player: "X",
      turn: 2,
    };
    let releaseAgentTurn: (() => void) | undefined;
    const pendingAgentResponse = new Promise<{ ok: boolean; json: () => Promise<typeof aiMoveResponse> }>((resolve) => {
      releaseAgentTurn = () => resolve({ ok: true, json: async () => aiMoveResponse });
    });
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => capabilitiesResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => aiGameStartResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => humanMoveResponse })
      .mockReturnValueOnce(pendingAgentResponse);
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await waitFor(() => expect(screen.getAllByRole("radio", { name: "AI Agent" })).toHaveLength(2));
    fireEvent.click(within(screen.getByRole("group", { name: /player o/i })).getByRole("radio", { name: "AI Agent" }));
    fireEvent.click(screen.getByRole("button", { name: /start game/i }));
    await waitFor(() => expect(screen.getByRole("button", { name: /cell 1/i })).not.toBeDisabled());

    fireEvent.click(screen.getByRole("button", { name: /cell 1/i }));

    await waitFor(() => expect(screen.getByRole("button", { name: "Cell 1, X" })).toHaveTextContent("X"));
    expect(fetchMock).toHaveBeenCalledTimes(4);
    expect(screen.getByText(/syncing with the game server/i)).toBeInTheDocument();
    const thinkingStatus = screen.getByRole("status", { name: /ai agent is thinking/i });
    expect(thinkingStatus).toHaveTextContent("AI Agent Is Thinking");
    expect(thinkingStatus).toHaveClass("w-full", "flex-wrap", "text-xs");

    releaseAgentTurn?.();
    await waitFor(() => expect(screen.getByRole("button", { name: "Cell 5, O" })).toHaveTextContent("O"));
  });

  it("keeps an AI-controlled turn out of the human board controls", async () => {
    const aiGameStartResponse = {
      ...initialResponse,
      mode: "ai_vs_human",
      players: { x: "ai-agent", o: "human" },
    };
    const afterAgentTurnResponse = {
      ...aiGameStartResponse,
      board: ["X", null, null, null, null, null, null, null, null],
      current_player: "O",
      turn: 1,
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => capabilitiesResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => aiGameStartResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => afterAgentTurnResponse });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await waitFor(() => expect(screen.getAllByRole("radio", { name: "AI Agent" })).toHaveLength(2));
    fireEvent.click(within(screen.getByRole("group", { name: /player x/i })).getByRole("radio", { name: "AI Agent" }));
    fireEvent.click(screen.getByRole("button", { name: /start game/i }));

    await waitFor(() => expect(screen.getByRole("button", { name: /cell 2/i })).not.toBeDisabled());
    expect(fetchMock).toHaveBeenLastCalledWith(
      "http://localhost:8000/games/game-1/agent-turn",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("advances both AI-controlled turns through the agent endpoint", async () => {
    const aiVsAiStart = {
      ...initialResponse,
      mode: "ai_vs_ai",
      players: { x: "ai-agent", o: "ai-agent" },
    };
    const afterXAgentTurn = {
      ...aiVsAiStart,
      board: ["X", null, null, null, null, null, null, null, null],
      current_player: "O",
      turn: 1,
    };
    const afterOAgentTurn = {
      ...afterXAgentTurn,
      board: ["X", "O", null, null, null, null, null, null, null],
      current_player: null,
      status: "draw",
      turn: 9,
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => capabilitiesResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => aiVsAiStart })
      .mockResolvedValueOnce({ ok: true, json: async () => afterXAgentTurn })
      .mockResolvedValueOnce({ ok: true, json: async () => afterOAgentTurn });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await waitFor(() => expect(screen.getAllByRole("radio", { name: "AI Agent" })).toHaveLength(2));
    fireEvent.click(within(screen.getByRole("group", { name: /player x/i })).getByRole("radio", { name: "AI Agent" }));
    fireEvent.click(within(screen.getByRole("group", { name: /player o/i })).getByRole("radio", { name: "AI Agent" }));
    fireEvent.click(screen.getByRole("button", { name: /start game/i }));

    await waitFor(() => expect(screen.getByRole("dialog", { name: /draw game/i })).toBeInTheDocument());
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      "http://localhost:8000/games/game-1/agent-turn",
      expect.objectContaining({ method: "POST" }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      4,
      "http://localhost:8000/games/game-1/agent-turn",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("shows each CPU-vs-AI move as it arrives", async () => {
    const cpuVsAiStart = {
      ...initialResponse,
      mode: "cpu_vs_ai",
      players: { x: "cpu", o: "ai-agent" },
    };
    const afterCpuTurn = {
      ...cpuVsAiStart,
      board: ["X", null, null, null, null, null, null, null, null],
      current_player: "O",
      turn: 1,
    };
    const afterAgentTurn = {
      ...afterCpuTurn,
      board: ["X", null, null, null, "O", null, null, null, null],
      current_player: "X",
      turn: 2,
    };
    let releaseAgentTurn: (() => void) | undefined;
    const pendingAgentResponse = new Promise<{ ok: boolean; json: () => Promise<typeof afterAgentTurn> }>((resolve) => {
      releaseAgentTurn = () => resolve({ ok: true, json: async () => afterAgentTurn });
    });
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => capabilitiesResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => cpuVsAiStart })
      .mockResolvedValueOnce({ ok: true, json: async () => afterCpuTurn })
      .mockReturnValueOnce(pendingAgentResponse);
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await waitFor(() => expect(screen.getAllByRole("radio", { name: "AI Agent" })).toHaveLength(2));
    fireEvent.click(within(screen.getByRole("group", { name: /player x/i })).getByRole("radio", { name: "CPU" }));
    fireEvent.click(within(screen.getByRole("group", { name: /player o/i })).getByRole("radio", { name: "AI Agent" }));
    fireEvent.click(screen.getByRole("button", { name: /start game/i }));

    await waitFor(() => expect(screen.getByRole("button", { name: "Cell 1, X" })).toHaveTextContent("X"));
    expect(fetchMock).toHaveBeenCalledTimes(4);
    expect(screen.getByText(/syncing with the game server/i)).toBeInTheDocument();

    releaseAgentTurn?.();
    await waitFor(() => expect(screen.getByRole("button", { name: "Cell 5, O" })).toHaveTextContent("O"));
  });

  it("returns to setup after reset and requires starting a new game", async () => {
    const resetResponse = { ...initialResponse, turn: 0 };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => capabilitiesResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => initialResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => resetResponse });
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /start game/i }));
    await waitFor(() => expect(screen.getByRole("button", { name: /game started/i })).toBeDisabled());

    fireEvent.click(screen.getByRole("button", { name: /reset game/i }));

    await waitFor(() => expect(screen.getByRole("button", { name: /start game/i })).toBeEnabled());
    expect(screen.getByRole("button", { name: /cell 1/i })).toBeDisabled();
  });

  it("shows a winner animation with confetti and restarts from the result state", async () => {
    const terminalResponse = {
      ...initialResponse,
      board: ["X", null, null, "O", null, null, null, null, null],
      current_player: null,
      status: "x_won",
      winner: "X",
      turn: 5,
    };
    const resetResponse = { ...initialResponse, turn: 0 };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => capabilitiesResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => initialResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => terminalResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => resetResponse });
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /start game/i }));
    await waitFor(() => expect(screen.getByRole("button", { name: /cell 1/i })).not.toBeDisabled());
    fireEvent.click(screen.getByRole("button", { name: /cell 1/i }));

    const resultDialog = await screen.findByRole("dialog", { name: /winner: x/i });
    expect(resultDialog).toHaveAttribute("aria-modal", "true");
    expect(screen.getByRole("img", { name: /winner confetti/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /restart game/i }));

    await waitFor(() => expect(screen.getByRole("button", { name: /start game/i })).toBeEnabled());
    expect(screen.queryByRole("heading", { name: /winner: x/i })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /cell 1/i })).toBeDisabled();
    expect(fetchMock).toHaveBeenLastCalledWith(
      "http://localhost:8000/games/game-1/reset",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("shows a draw animation without confetti", async () => {
    const terminalResponse = {
      ...initialResponse,
      board: ["X", "O", "X", "X", "O", "O", "O", "X", "X"],
      current_player: null,
      status: "draw",
      winner: null,
      turn: 9,
    };
    const resetResponse = { ...initialResponse, turn: 0 };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => capabilitiesResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => initialResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => terminalResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => resetResponse });
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /start game/i }));
    await waitFor(() => expect(screen.getByRole("button", { name: /cell 1/i })).not.toBeDisabled());
    fireEvent.click(screen.getByRole("button", { name: /cell 1/i }));

    const resultDialog = await screen.findByRole("dialog", { name: /draw game/i });
    expect(resultDialog).toHaveAttribute("aria-modal", "true");
    expect(screen.queryByRole("img", { name: /winner confetti/i })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /restart game/i }));
    await waitFor(() => expect(screen.getByRole("button", { name: /start game/i })).toBeEnabled());
  });
});
