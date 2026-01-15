# Persona Editor Walkthrough

This walkthrough explains how to create, update, and validate Quad Persona profiles.
Personas are stored in `data/personas_db.json` and loaded by the Quad Persona engine.

---

## ✅ Prerequisites

- Backend dependencies installed (Python 3.11+).
- The repository `data/` directory present (default storage path).

---

## 1) List Available Personas

```bash
python scripts/persona_manager.py list
```

List only a specific persona type (Axes 8–11):

```bash
python scripts/persona_manager.py list --persona-type knowledge
```

---

## 2) Add a Persona

### Create a components file

Save the following JSON as `persona_components.json`:

```json
{
  "job_role": { "title": "Regulatory Analyst", "focus": "Healthcare" },
  "education": { "degree": "MPH", "school": "Example University" },
  "certifications": { "certs": ["CIPP/US"] },
  "skills": { "core": ["HIPAA", "GDPR", "Risk Analysis"] },
  "training": { "programs": ["AI Governance"] },
  "career_path": { "stages": ["Analyst", "Lead", "Director"] },
  "related_jobs": { "roles": ["Compliance Officer"] }
}
```

### Add the persona

```bash
python scripts/persona_manager.py add \
  --persona-type regulatory \
  --name "Regulatory Analyst" \
  --description "Healthcare-focused regulatory specialist" \
  --components-file persona_components.json
```

---

## 3) Update a Persona

```bash
python scripts/persona_manager.py update \
  --persona-id <persona_id> \
  --name "Senior Regulatory Analyst" \
  --description "Updated description"
```

---

## 4) Delete a Persona

```bash
python scripts/persona_manager.py delete --persona-id <persona_id>
```

---

## 5) Validate Through the API

Once the backend is running, you can verify available personas:

```bash
curl http://localhost:5000/api/v1/persona/personas
```

If you edited `data/personas_db.json` directly or via the CLI, restart the backend
process to reload the updated persona storage.

---

## 6) Storage Notes

- Default storage file: `data/personas_db.json`
- Override storage path with `PERSONA_STORAGE_PATH` when needed:

```bash
PERSONA_STORAGE_PATH=/tmp/personas_db.json python scripts/persona_manager.py list
```

---

## 7) Related References

- Persona loader: `quad_persona/persona_loader.py`
- Persona profile schema: `quad_persona/quad_engine.py`
- Persona API: `backend/persona_api.py`
