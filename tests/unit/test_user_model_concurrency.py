"""
User Model Concurrency Testing Suite

Tests for thread-safe operations in the User model, specifically:
- Concurrent failed login attempts
- Account lockout race conditions
- Atomic counter increments
- Session isolation

These tests verify that concurrent requests can't bypass security
mechanisms like account lockout thresholds.
"""

import pytest
import threading
import time
from datetime import datetime, timedelta
from unittest.mock import patch
from models import User, db
from sqlalchemy.exc import SQLAlchemyError

from tests._helpers import is_sqlite_test_db

# These suites exercise concurrent writes (atomic failed-login increments,
# lockout race conditions). SQLite cannot run them reliably, so they are gated
# to run only when TEST_DATABASE_URL selects PostgreSQL (dual-engine coverage);
# they skip on the SQLite desktop default. See A18.
_skip_on_sqlite = pytest.mark.skipif(
    is_sqlite_test_db(),
    reason="SQLite cannot run concurrent-write tests reliably; "
    "runs on PostgreSQL (set TEST_DATABASE_URL)",
)



@_skip_on_sqlite
class TestFailedLoginConcurrency:
    """Test concurrent failed login attempts"""

    def test_record_failed_login_atomic_increment(self, app, client):
        """Test that failed login increments are atomic"""
        with app.app_context():
            # Create test user
            user = User(
                username="testuser",
                email="test@example.com"
            )
            user.set_password("Tr0ub4dor&3xtra!")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            # Record initial state
            initial_attempts = user.failed_login_attempts

            # Record a failed login
            user.record_failed_login()
            db.session.commit()

            # Refresh from database
            db.session.expire(user)
            user = db.session.get(User, user_id)

            assert user.failed_login_attempts == initial_attempts + 1

            # Cleanup
            db.session.delete(user)
            db.session.commit()

    def test_concurrent_failed_logins_all_counted(self, app, client):
        """Test that concurrent failed logins are all counted correctly"""
        with app.app_context():
            # Create test user
            user = User(
                username="concurrenttest",
                email="concurrent@example.com"
            )
            user.set_password("Tr0ub4dor&3xtra!")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            # Number of concurrent attempts
            num_attempts = 5
            results = []
            errors = []

            def record_failed_attempt():
                """Record a failed login in a thread"""
                try:
                    with app.app_context():
                        # Get fresh user instance for this thread
                        thread_user = db.session.get(User, user_id)
                        thread_user.record_failed_login()
                        db.session.commit()
                        results.append(True)
                except Exception as e:
                    errors.append(str(e))

            # Create and start threads
            threads = []
            for _ in range(num_attempts):
                thread = threading.Thread(target=record_failed_attempt)
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # Verify all increments were successful
            assert len(errors) == 0, f"Errors occurred: {errors}"

            # Refresh user and check final count
            db.session.expire_all()
            final_user = db.session.get(User, user_id)

            # All attempts should be recorded
            assert final_user.failed_login_attempts == num_attempts

            # Cleanup
            db.session.delete(final_user)
            db.session.commit()

    def test_lockout_triggered_at_threshold(self, app, client):
        """Test that account locks at threshold during concurrent attempts"""
        with app.app_context():
            # Create test user
            user = User(
                username="lockouttest",
                email="lockout@example.com"
            )
            user.set_password("Tr0ub4dor&3xtra!")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            # Get lockout threshold from settings
            from backend.config.settings import settings
            threshold = getattr(settings, 'MAX_FAILED_LOGIN_ATTEMPTS', 5)

            # Attempt threshold + 2 failed logins concurrently
            num_attempts = threshold + 2
            errors = []

            def record_failed_attempt():
                """Record a failed login"""
                try:
                    with app.app_context():
                        thread_user = db.session.get(User, user_id)
                        thread_user.record_failed_login()
                        db.session.commit()
                except Exception as e:
                    errors.append(str(e))

            # Execute concurrent attempts
            threads = []
            for _ in range(num_attempts):
                thread = threading.Thread(target=record_failed_attempt)
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            # Verify account is locked
            db.session.expire_all()
            final_user = db.session.get(User, user_id)

            assert final_user.is_account_locked() is True
            assert final_user.locked_until is not None
            assert final_user.failed_login_attempts >= threshold

            # Cleanup
            db.session.delete(final_user)
            db.session.commit()

    def test_no_race_condition_lockout_bypass(self, app, client):
        """Test that race conditions can't bypass lockout"""
        with app.app_context():
            # Create user
            user = User(
                username="racetest",
                email="race@example.com"
            )
            user.set_password("Tr0ub4dor&3xtra!")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            from backend.config.settings import settings
            threshold = getattr(settings, 'MAX_FAILED_LOGIN_ATTEMPTS', 5)

            # Set user to threshold - 1
            user.failed_login_attempts = threshold - 1
            db.session.commit()

            # Two concurrent attempts (simulating race condition)
            results = []

            def attempt_login():
                with app.app_context():
                    thread_user = db.session.get(User, user_id)
                    thread_user.record_failed_login()
                    db.session.commit()
                    results.append(thread_user.is_account_locked())

            thread1 = threading.Thread(target=attempt_login)
            thread2 = threading.Thread(target=attempt_login)

            thread1.start()
            thread2.start()

            thread1.join()
            thread2.join()

            # At least one should have locked the account
            db.session.expire_all()
            final_user = db.session.get(User, user_id)
            assert final_user.is_account_locked() is True

            # Cleanup
            db.session.delete(final_user)
            db.session.commit()


@_skip_on_sqlite
class TestSuccessfulLoginConcurrency:
    """Test concurrent successful login handling"""

    def test_successful_login_resets_counter(self, app, client):
        """Test successful login resets failed attempts"""
        with app.app_context():
            # Create user with failed attempts
            user = User(
                username="resettest",
                email="reset@example.com"
            )
            user.set_password("Tr0ub4dor&3xtra!")
            user.failed_login_attempts = 3
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            # Record successful login
            user.record_successful_login()
            db.session.commit()

            # Verify reset
            db.session.expire(user)
            user = db.session.get(User, user_id)

            assert user.failed_login_attempts == 0
            assert user.locked_until is None
            assert user.last_successful_login is not None

            # Cleanup
            db.session.delete(user)
            db.session.commit()

    def test_concurrent_success_and_failure(self, app, client):
        """Test handling concurrent successful and failed logins"""
        with app.app_context():
            # Create user
            user = User(
                username="mixedtest",
                email="mixed@example.com"
            )
            user.set_password("Tr0ub4dor&3xtra!")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            # Concurrent operations
            def record_failure():
                with app.app_context():
                    thread_user = db.session.get(User, user_id)
                    thread_user.record_failed_login()
                    db.session.commit()

            def record_success():
                with app.app_context():
                    thread_user = db.session.get(User, user_id)
                    thread_user.record_successful_login()
                    db.session.commit()

            # Interleave failures and success
            threads = []
            for i in range(6):
                if i == 3:  # Success in middle
                    thread = threading.Thread(target=record_success)
                else:
                    thread = threading.Thread(target=record_failure)
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            # Final state should be consistent
            db.session.expire_all()
            final_user = db.session.get(User, user_id)

            # State should be valid (not corrupted)
            assert final_user.failed_login_attempts >= 0

            # Cleanup
            db.session.delete(final_user)
            db.session.commit()


@_skip_on_sqlite
class TestAccountLockoutConcurrency:
    """Test account lockout checking with concurrent access"""

    def test_is_account_locked_thread_safe(self, app, client):
        """Test is_account_locked is thread-safe"""
        with app.app_context():
            # Create locked user
            user = User(
                username="lockeduser",
                email="locked@example.com"
            )
            user.set_password("Tr0ub4dor&3xtra!")
            user.locked_until = datetime.utcnow() + timedelta(minutes=15)
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            # Check from multiple threads
            results = []

            def check_locked():
                with app.app_context():
                    thread_user = db.session.get(User, user_id)
                    results.append(thread_user.is_account_locked())

            threads = [threading.Thread(target=check_locked) for _ in range(10)]

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            # All should return True
            assert all(results)
            assert len(results) == 10

            # Cleanup
            db.session.delete(db.session.get(User, user_id))
            db.session.commit()

    def test_lockout_expiration_race_condition(self, app, client):
        """Test lockout expiration boundary condition"""
        with app.app_context():
            # Create user locked until very soon
            user = User(
                username="expiringuser",
                email="expiring@example.com"
            )
            user.set_password("Tr0ub4dor&3xtra!")
            # Lock expires in 100ms
            user.locked_until = datetime.utcnow() + timedelta(milliseconds=100)
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            # Check if locked
            locked_before = user.is_account_locked()

            # Wait for expiration
            time.sleep(0.15)

            # Refresh and check again
            db.session.expire(user)
            user = db.session.get(User, user_id)
            locked_after = user.is_account_locked()

            assert locked_before is True
            assert locked_after is False

            # Cleanup
            db.session.delete(user)
            db.session.commit()


@_skip_on_sqlite
class TestDatabaseIsolation:
    """Test database transaction isolation"""

    def test_concurrent_reads_isolated(self, app, client):
        """Test concurrent reads see consistent data"""
        with app.app_context():
            # Create user
            user = User(
                username="isolationtest",
                email="isolation@example.com"
            )
            user.set_password("Tr0ub4dor&3xtra!")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            initial_attempts = user.failed_login_attempts

            # Read from multiple threads
            results = []

            def read_attempts():
                with app.app_context():
                    thread_user = db.session.get(User, user_id)
                    results.append(thread_user.failed_login_attempts)

            threads = [threading.Thread(target=read_attempts) for _ in range(5)]

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            # All reads should see same initial value
            assert all(attempt == initial_attempts for attempt in results)

            # Cleanup
            db.session.delete(db.session.get(User, user_id))
            db.session.commit()

    def test_write_read_consistency(self, app, client):
        """Test that writes are immediately visible after commit"""
        with app.app_context():
            # Create user
            user = User(
                username="consistencytest",
                email="consistency@example.com"
            )
            user.set_password("Tr0ub4dor&3xtra!")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            # Write
            user.record_failed_login()
            db.session.commit()

            # Read from new session
            db.session.expire(user)
            refreshed_user = db.session.get(User, user_id)

            assert refreshed_user.failed_login_attempts == 1

            # Cleanup
            db.session.delete(refreshed_user)
            db.session.commit()


@_skip_on_sqlite
class TestErrorHandling:
    """Test error handling in concurrent scenarios"""

    def test_database_error_handling(self, app, client):
        """Test that database errors are handled properly"""
        with app.app_context():
            # Create user
            user = User(
                username="errortest",
                email="error@example.com"
            )
            user.set_password("Tr0ub4dor&3xtra!")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            # Mock database error
            with patch('models.db.session.execute') as mock_execute:
                mock_execute.side_effect = SQLAlchemyError("Database error")

                # Should raise error
                with pytest.raises(SQLAlchemyError):
                    user.record_failed_login()

            # Cleanup
            db.session.delete(db.session.get(User, user_id))
            db.session.commit()

    def test_concurrent_error_recovery(self, app, client):
        """Test system recovers from concurrent errors"""
        with app.app_context():
            # Create user
            user = User(
                username="recoverytest",
                email="recovery@example.com"
            )
            user.set_password("Tr0ub4dor&3xtra!")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            errors = []
            successes = []

            def attempt_with_potential_error(should_error=False):
                try:
                    with app.app_context():
                        thread_user = db.session.get(User, user_id)
                        if should_error:
                            raise Exception("Simulated error")
                        thread_user.record_failed_login()
                        db.session.commit()
                        successes.append(True)
                except Exception as e:
                    errors.append(str(e))

            # Mix of successful and failed attempts
            threads = []
            for i in range(10):
                should_error = (i % 3 == 0)  # Error every 3rd attempt
                thread = threading.Thread(target=attempt_with_potential_error, args=(should_error,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            # Some should succeed
            assert len(successes) > 0
            # Some should have errors
            assert len(errors) > 0

            # System should still be functional
            db.session.expire_all()
            final_user = db.session.get(User, user_id)
            assert final_user is not None

            # Cleanup
            db.session.delete(final_user)
            db.session.commit()


@_skip_on_sqlite
class TestEdgeCases:
    """Test edge cases in concurrent operations"""

    def test_rapid_sequential_operations(self, app, client):
        """Test rapid sequential failed login attempts"""
        with app.app_context():
            # Create user
            user = User(
                username="rapidtest",
                email="rapid@example.com"
            )
            user.set_password("Tr0ub4dor&3xtra!")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            # Rapid sequential attempts (not concurrent)
            for _ in range(10):
                user.record_failed_login()
                db.session.commit()
                db.session.expire(user)
                user = db.session.get(User, user_id)

            # All should be counted
            assert user.failed_login_attempts == 10

            # Cleanup
            db.session.delete(user)
            db.session.commit()

    def test_lockout_then_unlock_then_lock_again(self, app, client):
        """Test locking, unlocking, and locking again"""
        with app.app_context():
            # Create user
            user = User(
                username="cycletest",
                email="cycle@example.com"
            )
            user.set_password("Tr0ub4dor&3xtra!")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            from backend.config.settings import settings
            threshold = getattr(settings, 'MAX_FAILED_LOGIN_ATTEMPTS', 5)

            # Lock account
            for _ in range(threshold):
                user.record_failed_login()
                db.session.commit()
                db.session.expire(user)
                user = db.session.get(User, user_id)

            assert user.is_account_locked() is True

            # Unlock via successful login
            user.record_successful_login()
            db.session.commit()
            db.session.expire(user)
            user = db.session.get(User, user_id)

            assert user.is_account_locked() is False
            assert user.failed_login_attempts == 0

            # Lock again
            for _ in range(threshold):
                user.record_failed_login()
                db.session.commit()
                db.session.expire(user)
                user = db.session.get(User, user_id)

            assert user.is_account_locked() is True

            # Cleanup
            db.session.delete(user)
            db.session.commit()

    def test_max_attempts_boundary(self, app, client):
        """Test exact boundary at max attempts"""
        with app.app_context():
            # Create user
            user = User(
                username="boundarytest",
                email="boundary@example.com"
            )
            user.set_password("Tr0ub4dor&3xtra!")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            from backend.config.settings import settings
            threshold = getattr(settings, 'MAX_FAILED_LOGIN_ATTEMPTS', 5)

            # Go to threshold - 1
            for _ in range(threshold - 1):
                user.record_failed_login()
                db.session.commit()
                db.session.expire(user)
                user = db.session.get(User, user_id)

            # Should not be locked yet
            assert user.is_account_locked() is False

            # One more should lock
            user.record_failed_login()
            db.session.commit()
            db.session.expire(user)
            user = db.session.get(User, user_id)

            assert user.is_account_locked() is True

            # Cleanup
            db.session.delete(user)
            db.session.commit()


@_skip_on_sqlite
class TestPerformance:
    """Test performance of concurrent operations"""

    def test_many_concurrent_attempts_complete_quickly(self, app, client):
        """Test that many concurrent attempts complete in reasonable time"""
        with app.app_context():
            # Create user
            user = User(
                username="perftest",
                email="perf@example.com"
            )
            user.set_password("Tr0ub4dor&3xtra!")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            start_time = time.time()

            # 50 concurrent attempts
            def record_attempt():
                with app.app_context():
                    thread_user = db.session.get(User, user_id)
                    thread_user.record_failed_login()
                    db.session.commit()

            threads = [threading.Thread(target=record_attempt) for _ in range(50)]

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            elapsed = time.time() - start_time

            # Should complete in under 10 seconds
            assert elapsed < 10

            # Verify all were recorded
            db.session.expire_all()
            final_user = db.session.get(User, user_id)
            assert final_user.failed_login_attempts == 50

            # Cleanup
            db.session.delete(final_user)
            db.session.commit()
