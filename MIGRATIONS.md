# Database Migrations Guide

## Overview

This application uses **Alembic** (via Flask-Migrate) for database schema management. Database migrations provide version control for your database schema and enable safe schema changes in production.

## ⚠️ IMPORTANT

**Never use `db.create_all()` in production code.** All database schema changes must go through migrations.

## Quick Start

### First-Time Setup

1. **Initialize the database** (already done if you have a `migrations/` directory):
   ```bash
   python -m flask db init
   ```

2. **Create initial migration** (if starting fresh):
   ```bash
   python -m flask db migrate -m "Initial database schema"
   ```

3. **Apply migrations to database**:
   ```bash
   python -m flask db upgrade
   ```

### Making Schema Changes

1. **Modify your models** in `models.py` or other model files

2. **Generate migration**:
   ```bash
   python -m flask db migrate -m "Descriptive message about changes"
   ```

3. **Review the migration** in `migrations/versions/` - ensure it looks correct

4. **Apply migration**:
   ```bash
   python -m flask db upgrade
   ```

## Common Commands

### Create a Migration

After modifying your SQLAlchemy models:

```bash
python -m flask db migrate -m "Add user preferences table"
```

This generates a new migration script in `migrations/versions/`.

### Apply Migrations

Apply all pending migrations:

```bash
python -m flask db upgrade
```

Apply migrations up to a specific revision:

```bash
python -m flask db upgrade <revision>
```

### Rollback Migrations

Downgrade to previous migration:

```bash
python -m flask db downgrade
```

Downgrade to specific revision:

```bash
python -m flask db downgrade <revision>
```

### Check Migration Status

Show current revision:

```bash
python -m flask db current
```

Show migration history:

```bash
python -m flask db history
```

### Other Useful Commands

Show all available commands:

```bash
python -m flask db --help
```

Show SQL that would be executed (without running it):

```bash
python -m flask db upgrade --sql
```

## Migration Best Practices

### 1. Always Review Generated Migrations

Flask-Migrate auto-generates migrations, but they may need manual adjustment:

```bash
# After running 'flask db migrate', check the generated file
ls -la migrations/versions/
# Edit if necessary
nano migrations/versions/<generated_file>.py
```

### 2. Test Migrations Locally First

```bash
# Create a backup of your database
cp ukg_database.db ukg_database.db.backup

# Test the migration
python -m flask db upgrade

# Test rollback
python -m flask db downgrade

# If successful, apply to staging/production
```

### 3. Never Edit Applied Migrations

Once a migration is applied to production, **never modify it**. Instead:
- Create a new migration to fix issues
- Roll back, modify, and re-apply only in development

### 4. Use Descriptive Migration Messages

```bash
# Good
python -m flask db migrate -m "Add email verification fields to User model"

# Bad
python -m flask db migrate -m "Update models"
```

### 5. Handle Data Migrations Carefully

For migrations involving data transformations:

```python
# Example: Manually edit migration to include data migration
def upgrade():
    # Schema changes
    op.add_column('users', sa.Column('full_name', sa.String(200)))

    # Data migration
    connection = op.get_bind()
    connection.execute("""
        UPDATE users
        SET full_name = first_name || ' ' || last_name
    """)

    # Remove old columns
    op.drop_column('users', 'first_name')
    op.drop_column('users', 'last_name')
```

## Production Deployment

### Pre-Deployment Checklist

- [ ] All migrations tested in development
- [ ] All migrations tested in staging
- [ ] Database backup created
- [ ] Downgrade path tested
- [ ] Rollback plan documented
- [ ] Maintenance window scheduled (if needed)

### Deployment Process

1. **Backup production database**:
   ```bash
   # PostgreSQL
   pg_dump -U username dbname > backup_$(date +%Y%m%d_%H%M%S).sql

   # SQLite
   cp production.db production.db.backup_$(date +%Y%m%d_%H%M%S)
   ```

2. **Apply migrations**:
   ```bash
   python -m flask db upgrade
   ```

3. **Verify application**:
   - Check application logs
   - Test critical user flows
   - Monitor error rates

4. **Rollback if needed**:
   ```bash
   python -m flask db downgrade
   # Restore from backup if necessary
   ```

### Zero-Downtime Migrations

For high-availability systems:

1. **Backward-compatible migrations first**:
   - Add new columns as nullable
   - Don't remove columns immediately
   - Use multi-step migrations

2. **Example multi-step migration**:

   **Step 1**: Add new column (nullable)
   ```python
   op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=True))
   ```

   **Step 2**: Populate data, make non-nullable
   ```python
   # Update existing records
   op.execute("UPDATE users SET email_verified = false WHERE email_verified IS NULL")
   # Make non-nullable
   op.alter_column('users', 'email_verified', nullable=False)
   ```

## Troubleshooting

### Migration Conflict

**Error**: `Target database is not up to date`

```bash
# Check current version
python -m flask db current

# Check migration history
python -m flask db history

# Force stamp to specific version (DANGER - only in development)
python -m flask db stamp head
```

### Migration Failed Mid-Way

```bash
# Manually mark as failed
python -m flask db stamp <previous_revision>

# Fix the migration script
# Re-run
python -m flask db upgrade
```

### Can't Generate Migrations

**Issue**: `flask db migrate` creates empty migration

**Solutions**:
1. Ensure all models are imported before migration runs
2. Check that models inherit from `db.Model`
3. Verify models are in files imported by app.py

```python
# In app.py - ensure all models are imported
from models import User, SimulationSession, KnowledgeGraphNode  # etc.
```

### Alembic Version Mismatch

```bash
# Reset migrations (DEVELOPMENT ONLY)
rm -rf migrations/
python -m flask db init
python -m flask db migrate -m "Initial schema"
python -m flask db upgrade
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Database Migrations

on:
  push:
    branches: [main]

jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run migrations
        run: python -m flask db upgrade
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

## Migration Directory Structure

```
migrations/
├── alembic.ini          # Alembic configuration
├── env.py               # Migration environment setup
├── README               # Alembic readme
├── script.py.mako       # Migration template
└── versions/            # Migration scripts
    ├── 001_initial.py
    ├── 002_add_user_preferences.py
    └── ...
```

## References

- [Flask-Migrate Documentation](https://flask-migrate.readthedocs.io/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

## Support

For migration issues:
1. Check this guide
2. Review Alembic documentation
3. Check application logs
4. Open an issue on GitHub

---

**Last Updated**: December 9, 2025
**Version**: 1.0.0
