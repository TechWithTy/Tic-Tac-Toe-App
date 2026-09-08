from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.games import router as games_router


app = FastAPI(title="Tic-Tac-Toe API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(games_router)
