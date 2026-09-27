# OCPI 2.2.1-d2 Simulator Frontend

React + Vite + TypeScript operator console for the FastAPI simulator. The UI follows the approved mockup direction and is wired to the current Versions, Credentials and Locations APIs.

## Demo scope

- Dashboard shell with CPO / eMSP / CPO + eMSP role selector.
- Versions page wired to:
  - GET /ocpi/cpo/versions
  - GET /ocpi/cpo/2.2.1
  - GET /ocpi/emsp/versions
  - GET /ocpi/emsp/2.2.1
- Credentials page wired to:
  - GET /ocpi/cpo/2.2.1/credentials
  - GET /ocpi/emsp/2.2.1/credentials
  - POST /ocpi/emsp/handshake
- Locations page wired to CPO GET Locations with search, status filter, date_from/date_to, limit and offset.
- Location detail view showing Location -> EVSE -> Connector.
- Simulation screen for a visual Credential Registration / Location Sync demo.
- Communication log for requests triggered by the UI.

## Run

Open a new terminal in the frontend folder:

```powershell
npm install
npm run dev
```

Then open the Vite URL shown in the terminal (normally http://localhost:5173).

Start the FastAPI backend in your existing project first:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The Vite development server proxies `/ocpi/*` requests to `http://127.0.0.1:8000`, so you do not need to add CORS just for local development.

### Optional API base

Copy `.env.example` to `.env` only if you want to call a different API host. For the local FastAPI + Vite demo, leave it blank.

Keep backend secrets such as `.env` tokens out of the frontend.
