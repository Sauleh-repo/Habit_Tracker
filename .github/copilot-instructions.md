<!-- Short, focused instructions for AI coding assistants working on this repo -->
# Copilot / AI Agent Instructions

This repository contains a small FastAPI backend (`sql_app/`) and a Create-React-App frontend (`habit-tracker-frontend/`). The goal of these instructions is to help an AI agent become productive quickly by highlighting architecture, conventions, and exact commands/files to touch.

- **Big picture**: `habit-tracker-frontend` (React) talks to the FastAPI backend at `http://127.0.0.1:8000` (see `src/services/api.js`). The backend stores data in a local SQLite file `./sql_app.db` (see `sql_app/database.py`). The backend exposes auth endpoints (`/token`, `/users/register`) and habit CRUD under `/habits/` (see `sql_app/main.py`).

- **Run & debug (local)**:
  - Backend (dev): `uvicorn sql_app.main:app --reload --host 127.0.0.1 --port 8000`
  - Frontend (dev): from `habit-tracker-frontend/`: `npm install` then `npm start` (runs at `http://localhost:3000`).
  - Docker (backend): `docker build -t habit-backend .` then `docker run -p 8000:8000 habit-backend` (Dockerfile runs `uvicorn sql_app.main:app ...`).

- **Key files to read first**:
  - `sql_app/main.py` — API routes, CORS, Auth dependency (`get_current_user`).
  - `sql_app/crud.py` — DB access patterns (create/commit/refresh). Use these helpers for business logic.
  - `sql_app/models.py` & `sql_app/schemas.py` — SQLAlchemy models and Pydantic schemas. Note: response models are configured to read model attributes (`from_attributes = True`).
  - `sql_app/security.py` — JWT creation, `SECRET_KEY`, hashing helpers.
  - `sql_app/database.py` — `SessionLocal`, `engine`, and SQLite URL.
  - `habit-tracker-frontend/src/services/api.js` — Axios client, auth token storage (`localStorage` key `token`) and automatic `Authorization` header.

- **Auth & tokens**:
  - The API uses OAuth2 password flow (`/token`) and returns a JWT. Tokens are expected in `Authorization: Bearer <token>` headers. See `sql_app/security.py` for `SECRET_KEY`, `ALGORITHM`, and `ACCESS_TOKEN_EXPIRE_MINUTES`.
  - Frontend stores token in `localStorage` and axios attaches it automatically (see `api.js`). 401 responses clear token and reload the page.

- **Database & migrations**:
  - The project uses SQLite (`sqlite:///./sql_app.db`) and does not include Alembic. Model creation code is commented out in `main.py` (`models.Base.metadata.create_all(bind=engine)`), so if you add new models either enable that call or run a create step manually.

- **Patterns & conventions to follow when editing/adding code**:
  - Use `get_db()` dependency in `sql_app/main.py` to obtain a `SessionLocal()` and `yield` it, then `close()` in `finally`.
  - Use functions in `sql_app/crud.py` for DB operations; they `add()`, `commit()`, and `refresh()` ORM objects — match this workflow to keep consistency.
  - Response models are Pydantic schemas declared in `sql_app/schemas.py`. Keep naming consistent (`User`, `UserCreate`, `Habit`, `HabitCreate`, `HabitUpdate`).
  - Respect ownership checks: habit endpoints check `owner_id` against `current_user.id` (see `main.py`) — follow same authorization pattern for new resources.

- **Endpoints worth referencing** (examples in `sql_app/main.py`):
  - `POST /users/register` — register new user (uses `crud.create_user`).
  - `POST /token` — OAuth2 token endpoint (form data `username` & `password`).
  - `GET /habits/`, `POST /habits/`, `PUT /habits/{id}`, `PUT /habits/{id}/toggle`, `DELETE /habits/{id}`.

- **Frontend integration notes**:
  - `habit-tracker-frontend/src/services/api.js` sets `baseURL: 'http://127.0.0.1:8000'`. If you run backend on another host/port, update this file.
  - Axios interceptors automatically attach token and handle 401 by clearing `localStorage` and reloading — tests or scripts should mock `localStorage` accordingly.

- **Dev dependencies & install**:
  - Backend: `requirements.txt` lists `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `passlib[bcrypt]`, `python-jose[cryptography]`.
  - Frontend: use `npm install` in `habit-tracker-frontend` and `npm start`.

- **Production and safety notes (do not change without review)**:
  - `SECRET_KEY` in `sql_app/security.py` is hardcoded for dev. For production, load from env var/secret store.
  - CORS in `main.py` is restricted to `http://localhost:3000`. Update CORS origins when deploying.
  - `.ebignore` excludes local files like `sql_app.db` and the frontend folder — Elastic Beanstalk was used historically.

If anything above is unclear or you'd like me to include small code snippets/examples for common edits (adding a new model, endpoint, or upgrading DB), tell me which area to expand and I'll iterate.
