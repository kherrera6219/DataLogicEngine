# Phase 1 Migration Checklist

**Quick reference for deploying Phase 1 security hardening migration**

---

## Pre-Migration

### Development Environment

- [ ] Dependencies installed: `pip install -r requirements.txt requirements-phase1.txt`
- [ ] Database backup created: `cp ukg_database.db ukg_database.db.backup`
- [ ] Migration tested locally: `python run_migration.py upgrade`
- [ ] Application tested: `python main.py` (verify auth endpoints work)
- [ ] Migration rollback tested: `python run_migration.py downgrade`
- [ ] Code committed: `git add . && git commit -m "feat: Phase 1 migration ready"`

### Production Environment (Before Deployment)

- [ ] **CRITICAL: Full database backup created and verified**
- [ ] Backup tested (restore to test database successful)
- [ ] Migration tested on production data snapshot
- [ ] Rollback procedure documented and tested
- [ ] Deployment window scheduled (recommend off-peak hours)
- [ ] Team notified of deployment timeline
- [ ] Monitoring/alerting configured for deployment
- [ ] Emergency contacts available during deployment

---

## Migration Execution

### Step 1: Backup (CRITICAL)

```bash
# SQLite
cp ukg_database.db ukg_database.db.backup_$(date +%Y%m%d_%H%M%S)

# PostgreSQL
pg_dump -U $DB_USER -h $DB_HOST $DB_NAME > backup_phase1_$(date +%Y%m%d_%H%M%S).sql

# Verify backup size
ls -lh ukg_database.db*
# OR
ls -lh backup_phase1_*.sql
```

- [ ] Backup created
- [ ] Backup size verified (should match or be close to database size)
- [ ] Backup location recorded: `___________________________`

### Step 2: Deploy Code

```bash
# Pull latest code
git pull origin main

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-phase1.txt

# Verify installation
python -c "from flask_migrate import Migrate; print('✓ Flask-Migrate installed')"
python -c "from backend.security.password_security import PasswordSecurity; print('✓ Password security module available')"
```

- [ ] Code deployed
- [ ] Dependencies installed
- [ ] Import tests passed

### Step 3: Run Migration

```bash
# Option 1: Using migration script (recommended)
python run_migration.py current   # Check current state
python run_migration.py upgrade   # Apply migration

# Option 2: Using Flask CLI
flask db current
flask db upgrade

# Verify migration applied
python run_migration.py current
# Should show: 001_phase1_security
```

- [ ] Migration command executed
- [ ] Migration completed without errors
- [ ] Current version verified: `001_phase1_security`

### Step 4: Verify Schema

```bash
# SQLite
sqlite3 ukg_database.db ".schema password_history"
sqlite3 ukg_database.db ".schema users" | grep -E "(password_changed_at|failed_login_attempts|mfa_enabled)"

# PostgreSQL
psql -U $DB_USER -d $DB_NAME -c "\d password_history"
psql -U $DB_USER -d $DB_NAME -c "\d users"
```

- [ ] `password_history` table exists
- [ ] `users` table has new columns (8 new columns)
- [ ] Indexes created (4 new indexes)

### Step 5: Verify Data

```bash
# Check existing users have default values
sqlite3 ukg_database.db "SELECT username, password_changed_at, password_expires_at, failed_login_attempts FROM users LIMIT 5;"

# OR for PostgreSQL
psql -U $DB_USER -d $DB_NAME -c "SELECT username, password_changed_at, password_expires_at, failed_login_attempts FROM users LIMIT 5;"
```

- [ ] Existing users have `password_changed_at` set
- [ ] Existing users have `password_expires_at` set (90 days from now)
- [ ] Existing users have `failed_login_attempts` = 0

---

## Post-Migration

### Application Verification

```bash
# Start application
python main.py
# OR
systemctl restart datalogicengine
# OR
docker-compose restart app

# Wait for startup
sleep 5
```

- [ ] Application started without errors
- [ ] No migration-related errors in logs

### Endpoint Testing

```bash
# Test registration (should enforce 12-char password minimum)
curl -X POST http://localhost:8080/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser1","email":"test1@example.com","password":"Short1!"}'
# Expected: 400 error (password too short)

curl -X POST http://localhost:8080/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser2","email":"test2@example.com","password":"SecurePass123!"}'
# Expected: 201 success

# Test login
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser2","password":"SecurePass123!"}'
# Expected: 200 with access token

# Test account lockout (5 failed attempts)
for i in {1..5}; do
  curl -X POST http://localhost:8080/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"testuser2","password":"WrongPassword"}'
  echo "Attempt $i"
done
# Expected: 403 locked after 5 attempts
```

- [ ] Registration enforces password strength (min 12 chars)
- [ ] Login works with valid credentials
- [ ] Account lockout works after 5 failed attempts
- [ ] Password history prevents reuse (test by changing password twice to same value)

### Production Health Checks

```bash
# Check application health
curl https://your-domain.com/health

# Monitor error logs
tail -f /var/log/datalogicengine/app.log | grep -i error

# Check database connections
# SQLite: Should see .db file in use
lsof ukg_database.db

# PostgreSQL: Check active connections
psql -U $DB_USER -d $DB_NAME -c "SELECT count(*) FROM pg_stat_activity WHERE datname='datalogicengine';"
```

- [ ] Health endpoint returns 200
- [ ] No errors in application logs
- [ ] Database connections normal
- [ ] Response times normal

### Security Feature Verification

- [ ] Password strength validation working
- [ ] Password expiration policy active (90 days)
- [ ] Account lockout working (5 attempts = 30 min lock)
- [ ] Failed login attempts being tracked
- [ ] Password history preventing reuse

---

## Rollback (If Needed)

### When to Rollback

- [ ] Migration failed during execution
- [ ] Application won't start after migration
- [ ] Critical errors in logs related to new schema
- [ ] Data corruption detected
- [ ] Performance severely degraded

### Rollback Procedure

```bash
# Method 1: Migration downgrade (preferred if migration completed)
python run_migration.py downgrade

# Method 2: Database restore (use if critical failure)
# Stop application first!
systemctl stop datalogicengine

# Restore backup
cp ukg_database.db.backup ukg_database.db
# OR for PostgreSQL
dropdb datalogicengine && createdb datalogicengine
psql -U $DB_USER datalogicengine < backup_phase1_*.sql

# Deploy previous code version
git checkout <previous-commit>
pip install -r requirements.txt

# Restart application
systemctl start datalogicengine
```

- [ ] Rollback method chosen: `___________________________`
- [ ] Rollback executed successfully
- [ ] Schema verified (new columns/tables removed)
- [ ] Application working with old schema
- [ ] Team notified of rollback

---

## Post-Deployment

### Documentation

- [ ] Migration completion recorded in changelog
- [ ] Any issues encountered documented
- [ ] Performance metrics recorded (migration time, etc.)
- [ ] Team notified of successful deployment

### Monitoring (First 24 Hours)

- [ ] Error rates normal
- [ ] Response times normal
- [ ] Database performance normal
- [ ] No user-reported issues
- [ ] Authentication success rate normal

### Cleanup

- [ ] Old database backups archived (if migration successful)
- [ ] Migration logs saved
- [ ] Documentation updated with any migration-specific notes

---

## Quick Reference Commands

```bash
# Check migration status
python run_migration.py current

# Apply migration
python run_migration.py upgrade

# Rollback migration
python run_migration.py downgrade

# Show migration history
python run_migration.py history

# Backup database (SQLite)
cp ukg_database.db ukg_database.db.backup_$(date +%Y%m%d_%H%M%S)

# Backup database (PostgreSQL)
pg_dump -U $DB_USER -h $DB_HOST $DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database (SQLite)
cp ukg_database.db.backup ukg_database.db

# Restore database (PostgreSQL)
dropdb datalogicengine && createdb datalogicengine
psql -U $DB_USER datalogicengine < backup_*.sql
```

---

## Support

For detailed migration documentation, see:
- **docs/MIGRATION_GUIDE.md** - Comprehensive migration guide
- **PHASE_1_STATUS.md** - Phase 1 implementation status
- **migrations/versions/001_phase1_security_hardening.py** - Migration source code

For issues:
1. Check application logs
2. Review MIGRATION_GUIDE.md troubleshooting section
3. Restore from backup if critical
4. Contact team lead

---

**Migration Completion Sign-Off**

- Deployed by: `___________________________`
- Date: `___________________________`
- Environment: `___________________________`
- Migration version: `001_phase1_security`
- Status: `✅ Success` / `❌ Rolled Back`
- Notes: `___________________________`

---

✅ **Phase 1 Migration Complete!**

Your database now includes:
- Password expiration (90-day policy)
- Password history (last 5 passwords)
- Account lockout (5 failed attempts)
- MFA foundation

Next: Continue with Phase 1 implementation (MFA, session security, etc.)
