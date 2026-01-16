# Cross-User Isolation Testing Guide

## Purpose
Verify that the Windows-native identity system correctly isolates user data and maintains per-user profiles when multiple Windows accounts access the same DataLogicEngine installation.

---

## Test Environment Setup

### Prerequisites
- DataLogicEngine installed on Windows 10/11
- **Minimum 2 Windows user accounts**:
  - `UserA` (will become Owner)
  - `UserB` (will become standard User)
- Both accounts must have local login access
- Services running: `UKG-Backend`, `UKG-Frontend`, `UKG-Postgres`, `UKG-Redis`

### Initial State
- Fresh installation (no existing users in database)
- Database empty: `SELECT COUNT(*) FROM users;` should return `0`

---

## Test Cases

### Test 1: First User Becomes Owner

**Objective**: Verify the first Windows user to access the system is assigned the `owner` role.

**Steps**:
1. Log in to Windows as **UserA**
2. Navigate to `http://localhost:3000`
3. System should auto-login without credentials

**Expected Results**:
- ✅ UserA auto-registered with role `owner`
- ✅ Navigation bar shows "Owner" badge
- ✅ Admin panel accessible
- ✅ Database record: `SELECT role, windows_sid FROM users WHERE username='UserA';` shows `owner`
- ✅ Audit log entry: `FIRST_RUN_REGISTRATION` with UserA's SID

**SQL Verification**:
```sql
-- Connect as ukg_app
psql -U ukg_app -h localhost -p 5433 -d ukg_local

-- Check user
SELECT id, username, role, windows_sid, created_at 
FROM users 
ORDER BY created_at;

-- Expected: 1 row, role='owner'
```

---

### Test 2: Subsequent User Gets Standard Role

**Objective**: Verify second Windows user receives `user` role, not `owner`.

**Steps**:
1. Log out of Windows (or use "Switch User")
2. Log in as **UserB**
3. Navigate to `http://localhost:3000`

**Expected Results**:
- ✅ UserB auto-registered with role `user`
- ✅ Navigation bar shows "User" badge (not "Owner")
- ✅ Admin panel **not accessible** (403 or hidden)
- ✅ Database record: `SELECT role FROM users WHERE username='UserB';` shows `user`
- ✅ Audit log entry: `USER_AUTO_REGISTRATION` with UserB's SID

---

### Test 3: Username Deconfliction

**Objective**: Verify that users with identical Windows usernames get unique application usernames.

**Setup**:
1. Create Windows user `john` on domain A
2. Create Windows user `john` on domain B (or local account)

**Steps**:
1. Log in as first `john`, access application
2. Log in as second `john`, access application

**Expected Results**:
- ✅ First user: `username='john'`
- ✅ Second user: `username='john_1'`
- ✅ Both have unique `windows_sid` values
- ✅ No username conflicts in database

**SQL Verification**:
```sql
SELECT username, windows_sid FROM users WHERE username LIKE 'john%';
-- Expected: john, john_1 (or john_2, john_3, etc.)
```

---

### Test 4: LLM Key Isolation (DPAPI)

**Objective**: Verify LLM API keys are stored per-user and not visible across accounts.

**Steps**:
1. **As UserA**:
   - Navigate to **Settings** → **LLM Keys**
   - Add OpenAI key: `sk-test-key-userA`
   - Verify key saved

2. **Switch to UserB**:
   - Navigate to **Settings** → **LLM Keys**
   - Check if UserA's key is visible

**Expected Results**:
- ✅ UserA sees their key (`sk-test-key-userA`)
- ✅ UserB sees **no keys** (empty list)
- ✅ Keys stored in `HKEY_CURRENT_USER\Software\DataLogicEngine` (per-user registry)
- ✅ Database does **not** contain API keys

**Registry Verification** (as each user):
```powershell
# Run as UserA
Get-ItemProperty "HKCU:\Software\DataLogicEngine\LLMKeys" -ErrorAction SilentlyContinue

# Run as UserB (should be empty or different)
Get-ItemProperty "HKCU:\Software\DataLogicEngine\LLMKeys" -ErrorAction SilentlyContinue
```

---

### Test 5: Session Persistence

**Objective**: Verify sessions don't leak between Windows users.

**Steps**:
1. **As UserA**:
   - Log in to application
   - Note session (cookie in browser)
   - Create a simulation run

2. **Switch to UserB** (same browser, different Windows session):
   - Navigate to `http://localhost:3000`
   - Check if UserA's session is active

**Expected Results**:
- ✅ UserB gets **new session** (not UserA's)
- ✅ UserB does not see UserA's simulation runs
- ✅ Each user has separate `flask_login` cookie
- ✅ No cross-session contamination

---

### Test 6: Knowledge Graph Sharing

**Objective**: Verify knowledge graph data is **shared** across users (not isolated).

**Setup**:
1. **As UserA**: Create a knowledge graph with nodes/edges
2. **Switch to UserB**: Access knowledge graph interface

**Expected Results**:
- ✅ UserB can see knowledge graph created by UserA
- ✅ Shared database tables (`kg_nodes`, `kg_edges`)
- ✅ Both users can contribute to same graph
- ✅ Audit logs track who modified what

> **Note**: Knowledge graphs are **shared resources**, not per-user isolated.

---

### Test 7: Audit Log SID Tracking

**Objective**: Verify all administrative actions log the correct Windows SID.

**Steps**:
1. **As UserA (Owner)**:
   - Promote UserB to `admin` role
   - Transfer ownership to UserB

2. **Check audit logs**:
   ```sql
   SELECT timestamp, action, windows_sid, details 
   FROM audit_logs 
   WHERE action IN ('ROLE_UPDATE', 'OWNER_PROMOTED')
   ORDER BY timestamp DESC;
   ```

**Expected Results**:
- ✅ `ROLE_UPDATE` entry has UserA's SID (who performed action)
- ✅ Details include UserB's SID (target user)
- ✅ `OWNER_PROMOTED` shows UserA → UserB transition
- ✅ All SIDs match actual Windows account SIDs

**Get Windows SID**:
```powershell
# Run as each user
whoami /user
```

---

### Test 8: Profile Deletion Isolation

**Objective**: Verify profile deletion only removes own user data, not others.

**Steps**:
1. **As UserB**:
   - Navigate to **Settings** → **Privacy**
   - Click "Delete My Profile"
   - Confirm with `DELETE`

2. **Check database**:
   ```sql
   SELECT username, role FROM users;
   ```

**Expected Results**:
- ✅ UserB record removed from database
- ✅ UserA record **still exists**
- ✅ Audit log shows `PROFILE_WIPE` with UserB's SID
- ✅ UserB's DPAPI credentials removed from registry
- ✅ Knowledge graph data **preserved** (shared resource)

---

## Failure Scenarios

### Scenario 1: Second User Becomes Owner

**Symptom**: UserB (second user) has `owner` role instead of `user`.

**Likely Cause**:
- Database was reset/cleared between UserA and UserB logins
- First-run detection logic broken

**Debug**:
```sql
SELECT id, username, role, created_at FROM users ORDER BY created_at;
-- Check if UserA record exists and predates UserB
```

**Fix**:
- Manually update roles if needed
- Investigate why database was cleared

---

### Scenario 2: LLM Keys Visible Across Users

**Symptom**: UserB can see UserA's API keys.

**Likely Cause**:
- Keys stored in database instead of DPAPI
- Incorrect credential isolation

**Debug**:
1. Check if API keys in database:
   ```sql
   SELECT column_name FROM information_schema.columns 
   WHERE table_name='users' AND column_name LIKE '%api%';
   ```

2. Verify DPAPI storage:
   ```powershell
   Get-ItemProperty "HKCU:\Software\DataLogicEngine\LLMKeys"
   ```

**Fix**:
- Ensure `backend/auth/dpapi_store.py` is used for LLM keys
- Remove any API key columns from `users` table

---

### Scenario 3: Session Leakage

**Symptom**: UserB sees UserA's session/data without logging in.

**Likely Cause**:
- SID-based authentication broken
- Browser cookie persisting across OS users

**Debug**:
1. Check Flask-Login configuration
2. Verify `windows_sid` lookup in `desktop_auto_login`
3. Clear browser cookies and retry

---

## Verification Checklist

Use this checklist to confirm all tests pass:

- [ ] **Test 1**: First user is Owner ✅
- [ ] **Test 2**: Second user is standard User ✅
- [ ] **Test 3**: Username deconfliction works ✅
- [ ] **Test 4**: LLM keys isolated per user ✅
- [ ] **Test 5**: Sessions don't leak ✅
- [ ] **Test 6**: Knowledge graph is shared ✅
- [ ] **Test 7**: Audit logs track SIDs ✅
- [ ] **Test 8**: Profile deletion is isolated ✅

---

## Reporting Results

If any tests fail, document:
1. Test case number/name
2. Expected vs. actual behavior
3. Database state (`SELECT * FROM users;`)
4. Audit log entries
5. Windows SID of affected users (`whoami /user`)

Include this information when reporting issues or requesting fixes.
