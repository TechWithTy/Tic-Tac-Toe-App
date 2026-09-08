from fastapi.middleware.cors import CORSMiddleware

from app.api.games import router as games_router
from app.mcp_server import build_mcp_server
from fastapi import FastAPI

app = FastAPI(title="Tic-Tac-Toe API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(games_router)
mcp_server = build_mcp_server(app)
mcp_app = mcp_server.http_app(path="/", transport="http")
app.state.mcp_server = mcp_server
app.state.mcp_app = mcp_app
app.router.lifespan_context = mcp_app.lifespan
app.mount("/mcp", mcp_app)
