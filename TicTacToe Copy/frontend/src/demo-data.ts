export type AgentSummary = {
  name: string;
  domain: string;
  owns: string;
  writeZone: string;
  approval: string;
};

export type TaskSummary = {
  id: string;
  title: string;
  epic: string;
  sprint: string;
  owner: string;
  status: string;
  acceptance: string;
  evidence: string;
  sourceUrl: string;
  prUrl: string;
  prLabel: string;
};

export const deliveryContext = {
  epic: {
    title: "OpenHands Tic-Tac-Toe Take-Home Delivery",
    detail: "A tested, playable vertical slice with FastAPI as the authority.",
    url: "https://app.notion.com/3d5e9c25ecb08117a9f1fa328294c794",
  },
  sprint: {
    title: "OpenHands Take-Home · 120-Minute Delivery",
    detail: "Core game by minute 72; MCP proof by minute 100; browser evidence by minute 120.",
    url: "https://app.notion.com/3d5e9c25ecb08158a77ee5e5bff7704d",
  },
  source: "https://app.notion.com/p/3b4e9c25ecb0835b8cfe81d557c905f5",
};

export const agents: AgentSummary[] = [
  { name: "Master-Orchestrator-Agent", domain: "Orchestration", owns: "routing, dependencies, handoffs, audit trail", writeZone: "agent runtime + delegated Notion metadata", approval: "Privileged changes: required" },
  { name: "BE-Engineer-Agent", domain: "Backend", owns: "domain rules, FastAPI, MCP adapters", writeZone: "/backend + backend tests", approval: "Privileged changes: required" },
  { name: "FE-Engineer-Agent", domain: "Frontend", owns: "React UI, states, accessibility", writeZone: "/frontend + frontend tests", approval: "Conditional" },
  { name: "QA-Agent", domain: "Quality", owns: "acceptance, regression, Playwright evidence", writeZone: "tests, fixtures, QA reports", approval: "Normal changes: no" },
  { name: "Safety-Agent", domain: "Safety / Security", owns: "tool scope, secrets, dangerous operations", writeZone: "security policy + audit metadata", approval: "Destructive/security-sensitive: always" },
  { name: "Git-Agent", domain: "Git / Release", owns: "branches, commits, PRs, merge policy", writeZone: "Git metadata + PRs", approval: "Conditional" },
];

export const taskCards: TaskSummary[] = [
  { id: "TASK-01", title: "Server-owned game engine", epic: deliveryContext.epic.title, sprint: deliveryContext.sprint.title, owner: "BE-Engineer-Agent", status: "Done", acceptance: "FastAPI validates turns, occupied cells, wins, draws, terminal moves, and reset.", evidence: "18 focused domain tests passed", sourceUrl: "https://app.notion.com/3d5e9c25ecb081169bcaf4e810fd6eaf", prUrl: "https://github.com/TechWithTy/Tic-Tac-Toe-App/pull/1", prLabel: "PR #1" },
  { id: "TASK-02", title: "React game interface", epic: deliveryContext.epic.title, sprint: deliveryContext.sprint.title, owner: "FE-Engineer-Agent", status: "Done", acceptance: "The client renders server state and never owns legality or turn rules.", evidence: "frontend tests, typecheck, lint, production build", sourceUrl: "https://app.notion.com/3d5e9c25ecb0814cb08eed2c5877c715", prUrl: "https://github.com/TechWithTy/Tic-Tac-Toe-App/pull/6", prLabel: "PR #6" },
  { id: "TASK-03", title: "Constrained MCP game tools", epic: deliveryContext.epic.title, sprint: deliveryContext.sprint.title, owner: "BE-Engineer-Agent", status: "Done", acceptance: "Only create, read, move, and reset are exposed through the unified FastAPI runtime.", evidence: "43 focused backend tests + mounted transport check", sourceUrl: "https://app.notion.com/3d5e9c25ecb0817e886defa1b1530dca", prUrl: "https://github.com/TechWithTy/Tic-Tac-Toe-App/pull/4", prLabel: "PR #4" },
  { id: "TASK-04", title: "Independent browser proof", epic: deliveryContext.epic.title, sprint: deliveryContext.sprint.title, owner: "QA-Agent", status: "Done", acceptance: "Playwright covers load, selection, start, turns, errors, reset, CPU, and AI handoff.", evidence: "critical-flow matrix with environment notes", sourceUrl: "https://app.notion.com/3d5e9c25ecb081998912fae4403d6be0", prUrl: "https://github.com/TechWithTy/Tic-Tac-Toe-App/pull/8", prLabel: "PR #8" },
];

export const decisions = [
  { title: "FastAPI owns canonical state", detail: "Human, CPU, and AI are controllers over one validated game state.", consequence: "The client presents state; it does not duplicate legality rules." },
  { title: "One writer at a time", detail: "Specialists can review or supply inputs, but only one agent owns a mutation surface.", consequence: "Conflicts become explicit handoffs instead of overlapping edits." },
  { title: "Evidence before score", detail: "Acceptance criteria, tests, QA, Safety, and branch policy outrank an aggregate model score.", consequence: "A high score cannot hide a blocker or bypass approval." },
];
