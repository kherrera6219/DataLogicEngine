# Git Hook Setup

Enable repository-managed hooks:

```powershell
git config core.hooksPath .githooks
```

Current hook coverage:

1. `pre-commit`: runs `scripts/dev/run_precommit_checks.py` (Python lint + frontend lint + frontend typecheck).
