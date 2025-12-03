# Database Migration Guide

**DataLogicEngine - Production Database Migration Procedures**

This guide covers database migration procedures for Phase 1 security hardening and future schema changes.

---

## Table of Contents

- [Overview](#overview)
- [Migration Tools](#migration-tools)
- [Quick Start](#quick-start)
- [Development Workflow](#development-workflow)
- [Production Deployment](#production-deployment)
- [Rollback Procedures](#rollback-procedures)
- [Testing Migrations](#testing-migrations)
- [Troubleshooting](#troubleshooting)
- [Phase 1 Migration Details](#phase-1-migration-details)

---

## Overview

### What This Migration Does

**Phase 1: Security Hardening (Migration 001_phase1_security)**

This migration implements comprehensive security enhancements:

1. **Password History Tracking**
   - Creates `password_history` table
   - Prevents reuse of last 5 passwords
   - Tracks password change timestamps

2. **Password Expiration**
   - Adds `password_changed_at` and `password_expires_at` columns
   - Enforces 90-day password rotation policy
   - Supports forced password changes

3. **Account Lockout Protection**
   - Adds `failed_login_attempts` counter
   - Implements `locked_until` timestamp
   - Protects against brute force attacks (5 attempts = 30 min lockout)

4. **Multi-Factor Authentication Foundation**
   - Adds `mfa_enabled`, `mfa_secret`, `mfa_backup_codes` columns
   - Prepares for TOTP implementation

### Migration Strategy

- **Zero-downtime**: Migrations can run on live databases (additive changes only)
- **Backward compatible**: Existing code continues to work during migration
- **Rollback safe**: Full downgrade capability for emergency rollback
- **Data preserving**: Existing user accounts remain functional

---

## Migration Tools

### Flask-Migrate Commands

We use Flask-Migrate (built on Alembic) for database migrations:

```bash
# Show current migration status
flask db current

# Show migration history
flask db history

# Apply pending migrations
flask db upgrade

# Rollback one migration
flask db downgrade

# Show SQL that would be executed (dry run)
flask db upgrade --sql
```

### Direct Python Script

For environments without Flask CLI access:

```python
# run_migration.py
from app import app, db
from flask_migrate import upgrade, downgrade, current

with app.app_context():
    # Show current version
    print("Current migration:", current())

    # Apply migrations
    upgrade()
    print("Migration complete!")
```

---

## Quick Start

### Prerequisites

1. **Backup your database** (CRITICAL!)
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-phase1.txt
   ```
3. Set environment variables (see `.env.template`)

### Run Migration (Development)

```bash
# 1. Backup database
cp ukg_database.db ukg_database.db.backup

# 2. Run migration
flask db upgrade

# 3. Verify migration
flask db current
# Should show: 001_phase1_security

# 4. Test your application
python main.py
```

### Run Migration (Production)

See [Production Deployment](#production-deployment) section below.

---

## Development Workflow

### Step-by-Step Development Migration

1. **Backup Database**
   ```bash
   # SQLite
   cp ukg_database.db ukg_database.db.backup_$(date +%Y%m%d_%H%M%S)

   # PostgreSQL
   pg_dump -U postgres datalogicengine > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Review Migration Script**
   ```bash
   cat migrations/versions/001_phase1_security_hardening.py
   ```

3. **Test Migration (Dry Run)**
   ```bash
   # Generate SQL without executing
   flask db upgrade --sql > migration_preview.sql
   cat migration_preview.sql
   ```

4. **Apply Migration**
   ```bash
   flask db upgrade
   ```

5. **Verify Schema Changes**
   ```bash
   # SQLite
   sqlite3 ukg_database.db ".schema users"
   sqlite3 ukg_database.db ".schema password_history"

   # PostgreSQL
   psql -U postgres -d datalogicengine -c "\d users"
   psql -U postgres -d datalogicengine -c "\d password_history"
   ```

6. **Test Application**
   ```bash
   # Run tests
   pytest tests/test_auth.py -v

   # Start application
   python main.py

   # Test registration endpoint
   curl -X POST http://localhost:8080/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","email":"test@example.com","password":"SecurePass123!"}'
   ```

7. **Verify Data Migration**
   ```bash
   # Check that existing users have default values
   sqlite3 ukg_database.db "SELECT username, password_changed_at, password_expires_at FROM users LIMIT 5;"
   ```

### If Something Goes Wrong

```bash
# Rollback migration
flask db downgrade

# Restore from backup
cp ukg_database.db.backup ukg_database.db
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Migration tested in development environment
- [ ] Migration tested on production data snapshot
- [ ] Database backup completed and verified
- [ ] Rollback plan documented and tested
- [ ] Deployment window scheduled (off-peak hours recommended)
- [ ] Team notified of deployment
- [ ] Monitoring alerts configured

### Production Migration Procedure

**⚠️ CRITICAL: Always backup before migrating production!**

#### Step 1: Pre-Migration Backup

```bash
# PostgreSQL (Recommended for Production)
pg_dump -U $DB_USER -h $DB_HOST $DB_NAME > backup_pre_phase1_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh backup_pre_phase1_*.sql

# Test backup restore (on separate database)
createdb datalogicengine_test
psql -U $DB_USER datalogicengine_test < backup_pre_phase1_*.sql
```

#### Step 2: Enable Maintenance Mode (Optional)

```bash
# Add to app.py or use environment variable
export MAINTENANCE_MODE=true
```

#### Step 3: Run Migration

```bash
# Set production environment
export FLASK_ENV=production
export DATABASE_URL="postgresql://user:pass@host:5432/datalogicengine"

# Generate migration SQL for review
flask db upgrade --sql > phase1_migration.sql

# Review SQL
cat phase1_migration.sql

# Execute migration
time flask db upgrade

# Verify migration status
flask db current
```

#### Step 4: Verify Schema

```bash
# Check new tables exist
psql -U $DB_USER -d $DB_NAME -c "\dt password_history"

# Check new columns exist
psql -U $DB_USER -d $DB_NAME -c "\d users"

# Verify data migration
psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM users WHERE password_changed_at IS NOT NULL;"
```

#### Step 5: Application Deployment

```bash
# Pull latest code with migration support
git pull origin main

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-phase1.txt

# Restart application
systemctl restart datalogicengine

# Or for Docker
docker-compose restart app
```

#### Step 6: Post-Migration Verification

```bash
# Health check
curl https://your-domain.com/health

# Test authentication
curl -X POST https://your-domain.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"TestPass123!"}'

# Check logs for errors
tail -f /var/log/datalogicengine/app.log
```

#### Step 7: Disable Maintenance Mode

```bash
export MAINTENANCE_MODE=false
systemctl restart datalogicengine
```

### Zero-Downtime Migration (Advanced)

For critical production systems:

```bash
# 1. Deploy new code WITHOUT running migration
#    New code handles both old and new schema (backward compatible)

# 2. Run migration (additive changes only)
flask db upgrade

# 3. Code automatically uses new features
#    Old instances continue working with old schema

# 4. Rolling restart of application servers
for server in app1 app2 app3; do
    systemctl restart datalogicengine@$server
    sleep 30  # Wait for health check
done
```

---

## Rollback Procedures

### When to Rollback

- Migration fails during execution
- Application errors after migration
- Unexpected data corruption
- Performance issues

### Emergency Rollback (Database Restore)

**Fastest method - Use for critical failures:**

```bash
# 1. Stop application
systemctl stop datalogicengine

# 2. Drop current database
dropdb datalogicengine

# 3. Restore from backup
createdb datalogicengine
psql -U $DB_USER datalogicengine < backup_pre_phase1_*.sql

# 4. Deploy previous application version
git checkout <previous-commit>
pip install -r requirements.txt
systemctl start datalogicengine

# 5. Verify
curl https://your-domain.com/health
```

### Graceful Rollback (Migration Downgrade)

**Preferred method if migration completed successfully:**

```bash
# 1. Stop application
systemctl stop datalogicengine

# 2. Rollback migration
flask db downgrade

# 3. Verify schema
flask db current
# Should show: (empty) or previous migration

# 4. Deploy previous application version
git checkout <previous-commit>
pip install -r requirements.txt
systemctl start datalogicengine

# 5. Verify
curl https://your-domain.com/health
```

### Rollback Verification

```bash
# Check schema reverted
psql -U $DB_USER -d $DB_NAME -c "\d users"
# Should NOT show password_changed_at, etc.

psql -U $DB_USER -d $DB_NAME -c "\dt password_history"
# Should show: Did not find any relation named "password_history"

# Check application works
curl -X POST https://your-domain.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"TestPass123!"}'
```

---

## Testing Migrations

### Test Migration on Production Data Snapshot

```bash
# 1. Copy production database to test environment
pg_dump -U $PROD_USER -h $PROD_HOST $PROD_DB > prod_snapshot.sql
psql -U $TEST_USER -h $TEST_HOST $TEST_DB < prod_snapshot.sql

# 2. Run migration on test database
export DATABASE_URL="postgresql://test_user:test_pass@test_host:5432/test_db"
flask db upgrade

# 3. Test application against migrated data
pytest tests/ -v --db-url=$DATABASE_URL

# 4. Verify performance
python scripts/benchmark_auth.py

# 5. Test rollback
flask db downgrade
```

### Automated Migration Testing

```python
# tests/test_migration_001_phase1.py
import pytest
from app import app, db
from flask_migrate import upgrade, downgrade

def test_phase1_migration_upgrade():
    """Test Phase 1 migration upgrade"""
    with app.app_context():
        # Run migration
        upgrade()

        # Verify password_history table exists
        result = db.engine.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='password_history'"
        )
        assert result.fetchone() is not None

        # Verify users table has new columns
        result = db.engine.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in result.fetchall()]
        assert 'password_changed_at' in columns
        assert 'password_expires_at' in columns
        assert 'failed_login_attempts' in columns

def test_phase1_migration_downgrade():
    """Test Phase 1 migration rollback"""
    with app.app_context():
        # Rollback migration
        downgrade()

        # Verify password_history table removed
        result = db.engine.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='password_history'"
        )
        assert result.fetchone() is None
```

---

## Troubleshooting

### Common Issues

#### 1. "Table already exists"

**Cause**: Migration already run or tables created manually

**Solution**:
```bash
# Mark migration as complete without running it
flask db stamp 001_phase1_security
flask db current  # Verify
```

#### 2. "Column already exists"

**Cause**: Partial migration or schema drift

**Solution**:
```bash
# Check actual schema
sqlite3 ukg_database.db ".schema users"

# If columns exist, stamp migration as complete
flask db stamp 001_phase1_security

# If columns partially exist, manual cleanup needed:
sqlite3 ukg_database.db "ALTER TABLE users DROP COLUMN password_changed_at;"
# ... then re-run migration
flask db upgrade
```

#### 3. "Migration fails mid-execution"

**Cause**: Database lock, insufficient permissions, or constraint violation

**Solution**:
```bash
# 1. Check database locks
# SQLite: Close all connections
# PostgreSQL:
psql -U $DB_USER -d $DB_NAME -c "SELECT * FROM pg_stat_activity WHERE datname='datalogicengine';"

# 2. Restore from backup and retry
cp ukg_database.db.backup ukg_database.db
flask db upgrade

# 3. If persists, run migration SQL manually
flask db upgrade --sql > migration.sql
sqlite3 ukg_database.db < migration.sql
flask db stamp 001_phase1_security
```

#### 4. "Foreign key constraint failed"

**Cause**: Orphaned records or constraint issues

**Solution**:
```bash
# Check for orphaned password history records (shouldn't exist in fresh migration)
sqlite3 ukg_database.db "SELECT COUNT(*) FROM password_history WHERE user_id NOT IN (SELECT id FROM users);"

# Clean up if needed
sqlite3 ukg_database.db "DELETE FROM password_history WHERE user_id NOT IN (SELECT id FROM users);"

# Re-run migration
flask db upgrade
```

#### 5. "No migrations to apply"

**Cause**: Migration already applied or version mismatch

**Solution**:
```bash
# Check current version
flask db current

# Check migration history
flask db history

# If out of sync, stamp to correct version
flask db stamp 001_phase1_security
```

### Database-Specific Issues

#### SQLite

- **Limitation**: Cannot drop columns (ALTER TABLE DROP COLUMN not supported)
- **Workaround**: Downgrade creates new table without dropped columns and copies data

#### PostgreSQL

- **Connection pooling**: May need to close connections before migration
  ```bash
  psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='datalogicengine';"
  ```

- **Permissions**: Ensure migration user has CREATE, ALTER, DROP privileges
  ```sql
  GRANT ALL PRIVILEGES ON DATABASE datalogicengine TO migration_user;
  ```

### Getting Help

If you encounter issues not covered here:

1. Check migration logs: `migrations/versions/001_phase1_security_hardening.py`
2. Review Alembic documentation: https://alembic.sqlalchemy.org/
3. Check Flask-Migrate docs: https://flask-migrate.readthedocs.io/
4. File an issue with:
   - Database type and version
   - Migration output/error messages
   - Schema before migration (`flask db current`, table schema dumps)

---

## Phase 1 Migration Details

### Schema Changes

#### New Table: `password_history`

```sql
CREATE TABLE password_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX ix_password_history_user_id ON password_history(user_id);
CREATE INDEX ix_password_history_created_at ON password_history(created_at);
```

**Purpose**: Track last 5 passwords per user to prevent reuse

**Size estimate**: ~500 bytes per entry, 2.5KB per user (5 passwords)

#### Enhanced Table: `users`

```sql
-- Password expiration
ALTER TABLE users ADD COLUMN password_changed_at DATETIME;
ALTER TABLE users ADD COLUMN password_expires_at DATETIME;
ALTER TABLE users ADD COLUMN force_password_change BOOLEAN DEFAULT 0;

-- Account lockout
ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN locked_until DATETIME;

-- MFA foundation
ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN DEFAULT 0;
ALTER TABLE users ADD COLUMN mfa_secret VARCHAR(32);
ALTER TABLE users ADD COLUMN mfa_backup_codes JSON;

-- Indexes for performance
CREATE INDEX ix_users_password_expires_at ON users(password_expires_at);
CREATE INDEX ix_users_locked_until ON users(locked_until);
```

**Purpose**: Enhanced authentication security and MFA support

**Size estimate**: ~200 bytes per user for new columns

### Data Migration

**Existing Users**: Automatically assigned default values:
- `password_changed_at`: Current timestamp
- `password_expires_at`: Current timestamp + 90 days
- `force_password_change`: False
- `failed_login_attempts`: 0
- Other columns: NULL (defaults)

**Impact**: Existing users have 90 days before password expiration warning

### Performance Impact

- **Migration time**: ~0.1 seconds per 1000 users (SQLite), ~0.05 seconds (PostgreSQL)
- **Index creation**: ~0.5 seconds per index (negligible for < 1M users)
- **Application impact**: None (backward compatible)
- **Storage increase**: ~1KB per user (400 bytes for columns + 2.5KB for password history over time)

### Testing Checklist

- [ ] Migration completes without errors
- [ ] `password_history` table created
- [ ] Users table has 8 new columns
- [ ] Existing users have `password_changed_at` and `password_expires_at` set
- [ ] Indexes created successfully
- [ ] User registration works
- [ ] User login works
- [ ] Password change works
- [ ] Account lockout triggers after 5 failed attempts
- [ ] Password history prevents reuse
- [ ] Rollback works and removes all changes

---

## Next Steps

After migration:

1. **Monitor Application**: Check logs for errors related to new schema
2. **Test Security Features**: Verify password policies, account lockout, etc.
3. **Update Documentation**: Document any migration-specific issues encountered
4. **Plan Phase 2**: Review next phase requirements (MFA implementation, etc.)

---

## Quick Reference

```bash
# Development
flask db upgrade              # Apply migrations
flask db current              # Show current version
flask db downgrade            # Rollback one migration

# Production
flask db upgrade --sql        # Preview SQL
time flask db upgrade         # Run with timing
flask db history              # Show all migrations

# Emergency
cp ukg_database.db.backup ukg_database.db  # Restore from backup
flask db downgrade                          # Rollback migration
flask db stamp 001_phase1_security         # Mark migration as applied without running
```

---

**Phase 1 Migration Complete! 🔒**

Your database now includes comprehensive security hardening:
- ✅ Password expiration (90-day policy)
- ✅ Password history (prevents reuse of last 5)
- ✅ Account lockout (5 attempts = 30 min lock)
- ✅ MFA foundation (ready for TOTP implementation)

See [PHASE_1_STATUS.md](PHASE_1_STATUS.md) for next steps.
