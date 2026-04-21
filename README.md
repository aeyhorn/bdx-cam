# BDXPostOffice

Internes MVP zur strukturierten Erfassung von CAM-/NC-/Maschinen-Feedback, technischen Analysen, Change Requests, Tests, Regressionen und Wissensdatenbank — mit rollenbasierter API, Audit-Log und Docker-Start.

## Voraussetzungen

- Docker & Docker Compose **oder**
- Python 3.11+, Node.js 20+, PostgreSQL 16+

## Start mit Docker Compose

```bash
docker compose up --build
```

- **Frontend:** http://localhost:8080 (Nginx, `/api` → Backend)
- **Backend API:** http://localhost:8000 — OpenAPI: http://localhost:8000/docs
- **PostgreSQL:** Port 5432 (User/Pass/DB: `postgres` / `postgres` / `cam_feedback`)

**Zugriff über andere Rechner / LAN-IP:** Die Oberfläche unter `http://<deine-ip>:8080` öffnen (nicht nur „localhost“). API-Aufrufe laufen dann über denselben Host (Nginx-Proxy `/api`). Wenn du beim Frontend-Build `VITE_API_URL=http://localhost:8000` gesetzt hast, würde der Browser von anderen PCs fälschlich `localhost` auf dem **eigenen** Rechner ansprechen — Anmeldung schlägt fehl (häufig **404 Not Found**). Entweder `VITE_API_URL` weglassen/leer lassen oder die echte URL zum Backend setzen und `CORS_ORIGINS` in Compose um `http://<deine-ip>:8080` ergänzen.

Nach dem Start werden Migrationen ausgeführt, **Seed-Daten** und der **Initial-Admin** angelegt (siehe unten).

## Start lokal ohne Docker

### Datenbank

PostgreSQL anlegen, z. B. `cam_feedback`. `DATABASE_URL` in `backend/.env` setzen (siehe `backend/.env.example`).

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env     # anpassen
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite proxy leitet `/api` auf `http://localhost:8000` (siehe `frontend/vite.config.ts`).

## Seed / Initial-Admin

Standard (über `app.core.config.Settings`, per Umgebungsvariablen überschreibbar):

| Variable | Standard |
|----------|----------|
| `INITIAL_ADMIN_EMAIL` | `admin@example.com` |
| `INITIAL_ADMIN_PASSWORD` | `ChangeMe123!` |

Der Seed legt Rollen, Severities, Priorities, Status, Fehlerkategorien, Demo-Maschine, Demo-Steuerung und eine produktive Demo-Post-Version an.

## Migrationen

```bash
cd backend
alembic upgrade head
```

Neue Revision (bei laufender/erreichbarer DB):

```bash
alembic revision --autogenerate -m "beschreibung"
```

## Wichtige Umgebungsvariablen (Backend)

| Variable | Beschreibung |
|----------|----------------|
| `DATABASE_URL` | SQLAlchemy-URL (PostgreSQL) |
| `SECRET_KEY` | JWT-Signing |
| `RELEASE_ID` | Gemeinsame Release-ID für Frontend/Backend-Match (z. B. Git-SHA) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS` | Token-Laufzeiten |
| `UPLOAD_DIR` | Verzeichnis für Anhänge |
| `MAX_UPLOAD_MB` | max. Uploadgröße (Default 100) |
| `STEP_VIEWER_CACHE_DIR` | Cache-Verzeichnis für konvertierte STEP-Modelle (GLB) |
| `STEP_CONVERTER_COMMAND` | Kommando-Template zur STEP→GLB-Konvertierung (`{input}`, `{output}`) |
| `CORS_ORIGINS` | Komma-separierte Origins |
| `INITIAL_ADMIN_EMAIL` / `INITIAL_ADMIN_PASSWORD` | erster Admin |

## Architektur (Kurz)

- **Backend:** `backend/app` — `api/v1`, `core`, `db`, `models`, `schemas`, `services`
- **Frontend:** `frontend/src` — `api`, `context`, `components`, `pages`
- **Audit:** Feld `case_id` an `audit_logs` für schnelle Fall-Historie (Erweiterung für Nachvollziehbarkeit)

## API-Überblick

Basis: `/api/v1` — Auth (`/auth/login`, `/auth/refresh`, `/auth/me`), Benutzer, Rollen, Stammdaten, Fälle, Kommentare, Anhänge, Root Cause, Change Requests, Testfälle, Regressionen, Knowledge, Dashboards.

Zusätzlich: `GET /health/version` liefert den aktuellen Backend-Release-Stand (`release_id`), damit das Frontend Versionsabweichungen anzeigen kann.

Hinweis 3D-Viewer: Wenn beim Öffnen einer STEP-Datei eine Fehlermeldung erscheint, fehlt meist `STEP_CONVERTER_COMMAND` im Backend-Deployment oder der Konverter ist im Container/Server nicht installiert. Das Frontend zeigt die konkrete Backend-Fehlermeldung an.

## Deploy ohne manuelle RELEASE_ID

Für konsistente Frontend/Backend-Stände bei jedem Build sind Deploy-Skripte enthalten, die `RELEASE_ID` automatisch aus Git setzen (Tag bevorzugt, sonst Commit-SHA):

- Linux/macOS: `./scripts/deploy.sh` (optional Branch: `./scripts/deploy.sh main`)
- Windows PowerShell: `./scripts/deploy.ps1` (optional Branch: `.\scripts\deploy.ps1 -Branch main`)

### Verbindliche Deploy-Checkliste

- Nur über `scripts/deploy.sh` bzw. `scripts/deploy.ps1` deployen.
- Keine manuellen `docker compose up -d --build` Aufrufe ohne gesetzte `RELEASE_ID`.
- Nach Deploy kurz prüfen: UI-Warnung zur Versionsabweichung darf nicht erscheinen.

## Lizenz / intern

Internes Engineering-Tool — weiterentwickeln nach Bedarf.
