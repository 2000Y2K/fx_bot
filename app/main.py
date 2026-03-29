import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import projects, teams, persons, assets, assignments
from app.db.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Audiovisual Asset Manager API", version="0.1.0", redirect_slashes=False)

_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
origins = [o.strip() for o in _origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(teams.router, prefix="/teams", tags=["teams"])
app.include_router(persons.router, prefix="/persons", tags=["persons"])
app.include_router(assets.router, prefix="/assets", tags=["assets"])
app.include_router(assignments.router, prefix="/assignments", tags=["assignments"])


@app.get("/health")
def health():
    return {"status": "ok"}
