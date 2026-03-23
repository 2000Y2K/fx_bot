# Audiovisual Asset Manager — API

FastAPI backend para gestión de assets y asignaciones en proyectos audiovisuales.

## Arrancar en desarrollo

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Docs interactivas: http://localhost:8000/docs

## Estructura

```
app/
  main.py              # entry point, routers registrados
  db/database.py       # conexión SQLAlchemy, get_db()
  models/models.py     # tablas: Project, Team, Person, Asset, Assignment, AssignmentLog
  schemas/schemas.py   # Pydantic: request/response shapes
  routers/
    projects.py        # CRUD proyectos
    teams.py           # CRUD equipos
    persons.py         # CRUD personas + query por whatsapp
    assets.py          # CRUD assets + update versión/url
    assignments.py     # asignaciones + cambio de estado + log
```

## Endpoints clave para el bot

| Método | Ruta | Uso |
|--------|------|-----|
| GET | `/persons/by-whatsapp/{number}` | Identificar quién escribe |
| GET | `/persons/{id}/assignments` | "¿Qué tengo yo?" |
| GET | `/assignments/team/{team_id}` | "¿Qué tiene mi equipo?" |
| GET | `/assets/{id}/assignments` | "¿Quién está en este archivo?" |
| PATCH | `/assignments/{id}/status` | "Terminé / empecé a trabajar" |

## Pasar a producción

1. Cambiar `DATABASE_URL` en `.env` a PostgreSQL
2. Correr migraciones (agregar Alembic cuando el esquema estabilice)
3. Configurar autenticación (recomendado: API key simple para el bot, JWT para el panel admin)
