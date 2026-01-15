# Simulation Walkthrough (UI + API)

This walkthrough shows how to run a simulation through the web UI and the REST API.
It aligns with the current simulation endpoints and the Simulation Monitor UI.

---

## ✅ Prerequisites

- Backend running (`python run.py` or your standard app entrypoint).
- Frontend running (`npm run dev` from `frontend/`).
- A configured database with the `SimulationSession` table.

---

## 1) Run a Simulation from the UI

1. Open the **Simulation Monitor** page at:
   - `http://localhost:3000/simulations`
2. Click **New Simulation** to create a run.
3. The list updates with live progress; the UI subscribes to WebSocket events for the active simulation.
4. Use the action buttons to advance steps or stop the simulation if your environment allows it.

**Notes**
- The UI uses `/api/v1/simulations` for listing and creation.
- Step progress is driven by `/api/v1/simulations/{uid}/step`.

---

## 2) Run a Simulation via REST API

### Create a simulation session

```bash
curl -X POST http://localhost:5000/api/v1/simulations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Simulation Run - Demo",
    "parameters": {
      "mode": "standard",
      "trace_enabled": true
    }
  }'
```

**Response** (truncated):
```json
{
  "success": true,
  "data": {
    "uid": "...",
    "name": "Simulation Run - Demo",
    "status": "pending",
    "current_step": 0
  }
}
```

### Advance a simulation step

```bash
curl -X POST http://localhost:5000/api/v1/simulations/<uid>/step
```

### Fetch a simulation session

```bash
curl http://localhost:5000/api/v1/simulations/<uid>
```

---

## 3) Export or Inspect Results

When a simulation completes, the backend stores results in the `SimulationSession` record.
You can inspect results via the REST response or export with the export service.

---

## 4) Troubleshooting

- If a simulation stays in `pending`, ensure your database migrations are up to date.
- If step progression fails, confirm the simulation is in `active` status.
- For real-time progress, confirm WebSocket connectivity to the backend.

---

## 5) Related References

- API definitions: `backend/ukg_api.py`, `backend/rest_api.py`
- UI view: `frontend/app/simulations/page.tsx`
- WebSocket events: `backend/websocket.py`, `frontend/lib/socket.ts`
