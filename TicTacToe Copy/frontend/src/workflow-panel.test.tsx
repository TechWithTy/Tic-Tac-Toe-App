import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { WorkflowPanel } from "./components/workflow-panel";

describe("workflow presentation panel", () => {
  it("shows the bounded agent flow and current task evidence", () => {
    render(<WorkflowPanel />);

    expect(screen.getByRole("heading", { name: /agent workflow/i })).toBeInTheDocument();
    expect(screen.getByText("OpenHands Tic-Tac-Toe Take-Home Delivery")).toBeInTheDocument();
    expect(screen.getByText("OpenHands Take-Home · 120-Minute Delivery")).toBeInTheDocument();
    expect(screen.getByText("Master-Orchestrator-Agent")).toBeInTheDocument();
    expect(screen.getByText(/one writer at a time/i)).toBeInTheDocument();
    expect(screen.getByText(/server-owned game engine/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /PR #1/i })).toHaveAttribute("href", "https://github.com/TechWithTy/Tic-Tac-Toe-App/pull/1");
  });

  it("centers the delivery trace heading and subtitle on mobile", () => {
    render(<WorkflowPanel />);

    expect(screen.getByText("The delivery trace")).toHaveClass("justify-center", "lg:justify-start");
    expect(screen.getByRole("heading", { name: /agent workflow/i }).parentElement).toHaveClass("text-center", "lg:text-left");
    expect(screen.getByText(/A presentation layer for the decisions/)).toHaveClass(
      "mx-auto",
      "text-center",
      "lg:mx-0",
      "lg:text-left",
    );
  });
});
