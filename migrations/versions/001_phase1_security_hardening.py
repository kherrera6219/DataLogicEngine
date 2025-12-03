"""Phase 1: Security Hardening - Enhanced Authentication & Password Security

This migration implements comprehensive security enhancements including:
- Password security (expiration, history, strength validation)
- Account lockout protection (brute force prevention)
- Multi-factor authentication foundation
- Enhanced audit logging

Revision ID: 001_phase1_security
Revises:
Create Date: 2025-12-03 02:21:00

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timedelta


# revision identifiers, used by Alembic.
revision = '001_phase1_security'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    Apply Phase 1 security hardening changes to the database schema.

    Creates:
    - password_history table for tracking password reuse

    Enhances users table with:
    - Password expiration tracking
    - Account lockout protection
    - MFA foundation
    """

    # ========================================
    # 1. Create password_history table
    # ========================================
    op.create_table(
        'password_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('password_hash', sa.String(length=256), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )

    # Add index for efficient lookups
    op.create_index('ix_password_history_user_id', 'password_history', ['user_id'])
    op.create_index('ix_password_history_created_at', 'password_history', ['created_at'])

    # ========================================
    # 2. Add password security columns to users table
    # ========================================

    # Password expiration tracking
    op.add_column('users', sa.Column('password_changed_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('password_expires_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('force_password_change', sa.Boolean(), nullable=False, server_default='0'))

    # Account lockout protection (brute force prevention)
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(), nullable=True))

    # Multi-factor authentication foundation
    op.add_column('users', sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('mfa_secret', sa.String(length=32), nullable=True))
    op.add_column('users', sa.Column('mfa_backup_codes', sa.JSON(), nullable=True))

    # ========================================
    # 3. Set default values for existing users
    # ========================================

    # Set password_changed_at to current time for existing users
    # Set password_expires_at to 90 days from now
    op.execute("""
        UPDATE users
        SET password_changed_at = CURRENT_TIMESTAMP,
            password_expires_at = datetime(CURRENT_TIMESTAMP, '+90 days')
        WHERE password_changed_at IS NULL
    """)

    # ========================================
    # 4. Add indexes for performance
    # ========================================

    # Index for checking expired passwords
    op.create_index('ix_users_password_expires_at', 'users', ['password_expires_at'])

    # Index for checking locked accounts
    op.create_index('ix_users_locked_until', 'users', ['locked_until'])

    print("✓ Phase 1 Security Hardening migration completed successfully")
    print("  - Created password_history table")
    print("  - Added password security columns to users table")
    print("  - Added account lockout protection")
    print("  - Added MFA foundation columns")
    print("  - Set default values for existing users")


def downgrade():
    """
    Rollback Phase 1 security hardening changes.

    WARNING: This will remove security features and delete password history.
    Only use this in development or if absolutely necessary.
    """

    # Drop indexes from users table
    op.drop_index('ix_users_locked_until', 'users')
    op.drop_index('ix_users_password_expires_at', 'users')

    # Drop password security columns from users table
    op.drop_column('users', 'mfa_backup_codes')
    op.drop_column('users', 'mfa_secret')
    op.drop_column('users', 'mfa_enabled')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'force_password_change')
    op.drop_column('users', 'password_expires_at')
    op.drop_column('users', 'password_changed_at')

    # Drop password_history table (including indexes)
    op.drop_index('ix_password_history_created_at', 'password_history')
    op.drop_index('ix_password_history_user_id', 'password_history')
    op.drop_table('password_history')

    print("✓ Phase 1 Security Hardening migration rolled back")
    print("  WARNING: Security features have been removed")
