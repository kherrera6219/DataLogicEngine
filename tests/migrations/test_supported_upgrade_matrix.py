"""Phase 4 migration graph and supported-upgrade inventory tests."""

from __future__ import annotations

from pathlib import Path

from flask import Flask
from flask_migrate import upgrade
from sqlalchemy import inspect, text

import models
from backend.storage.migration_inventory import (
    MIGRATION_SURFACES,
    SUPPORTED_UPGRADE_SOURCES,
    build_migration_inventory,
    inventory_alembic_revisions,
)
from backend.storage.runtime_migrations import (
    BACKUP_REQUIRED_RUNTIME_MIGRATION_PATHS,
    POSTGRESQL_PROVIDER_DEFAULT_SOURCE_REVISION,
    POSTGRESQL_TARGET_REVISION,
    SUPPORTED_RUNTIME_MIGRATION_PATHS,
)
from extensions import db, migrate


ROOT = Path(__file__).resolve().parents[2]


def test_alembic_revision_graph_has_one_ordered_base_and_head():
    graph = inventory_alembic_revisions(ROOT / "migrations" / "versions")

    assert len(graph["revisions"]) == 27
    assert graph["bases"] == ["000000000001"]
    assert graph["heads"] == ["b2c3d4e5f6a7"]
    assert graph["errors"] == []
    assert graph["linear_order"][0] == "000000000001"
    assert graph["linear_order"][-1] == "b2c3d4e5f6a7"


def test_empty_database_upgrades_from_frozen_baseline(tmp_path):
    app = Flask("phase4-empty-migration")
    app.config.update(
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'empty.db'}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        upgrade(directory=str(ROOT / "migrations"), revision="head")
        inspector = inspect(db.engine)
        tables = set(inspector.get_table_names())
        ka_run_columns = {
            column["name"]
            for column in inspector.get_columns("ka_product_runs")
        }
        ka_run_constraints = {
            constraint["name"]
            for constraint in inspector.get_unique_constraints(
                "ka_product_runs"
            )
        }
        current = db.session.execute(text("SELECT version_num FROM alembic_version")).scalar_one()

    assert set(models.db.metadata.tables) <= tables
    assert {
        "principal_key",
        "request_ciphertext",
        "result_ciphertext",
        "confirmation_digest",
        "cancellation_requested",
    } <= ka_run_columns
    assert "uq_ka_product_run_principal_idempotency" in ka_run_constraints
    assert current == "b2c3d4e5f6a7"


def test_provider_default_migration_updates_only_known_retired_models(tmp_path):
    app = Flask("provider-model-default-migration")
    app.config.update(
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'provider-models.db'}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        upgrade(directory=str(ROOT / "migrations"), revision="0a1b2c3d4e5f")
        db.session.execute(text("""
            INSERT INTO llm_providers (id, name, provider_type, model_id)
            VALUES
              ('11111111-1111-1111-1111-111111111111', 'OpenAI', 'openai', 'gpt-5.5'),
              ('22222222-2222-2222-2222-222222222222', 'Google', 'google', 'gemini-3.1-pro-preview'),
              ('33333333-3333-3333-3333-333333333333', 'Custom', 'openai', 'owner-pinned-model')
        """))
        db.session.execute(text("""
            INSERT INTO users (id, username, email)
            VALUES
              (1, 'openai-owner', 'openai-owner@example.test'),
              (2, 'google-owner', 'google-owner@example.test')
        """))
        db.session.execute(text("""
            INSERT INTO user_ai_preferences
              (id, user_id, preferred_provider, preferred_model, ai_processing_enabled, store_chat_history)
            VALUES
              (1, 1, 'openai', 'gpt-5.5', true, true),
              (2, 2, 'google', 'gemini-3.1-pro-preview', true, true)
        """))
        db.session.commit()

        upgrade(directory=str(ROOT / "migrations"), revision="head")
        provider_models = dict(db.session.execute(text(
            "SELECT name, model_id FROM llm_providers ORDER BY name"
        )).all())
        preference_models = dict(db.session.execute(text(
            "SELECT preferred_provider, preferred_model FROM user_ai_preferences"
        )).all())

    assert provider_models == {
        "Custom": "owner-pinned-model",
        "Google": "gemini-3.7-flash",
        "OpenAI": "gpt-5.6-sol",
    }
    assert preference_models == {
        "google": "gemini-3.7-flash",
        "openai": "gpt-5.6-sol",
    }


def test_runtime_authorizes_only_the_lossless_provider_default_revision():
    assert SUPPORTED_RUNTIME_MIGRATION_PATHS == {
        (
            "postgresql",
            POSTGRESQL_PROVIDER_DEFAULT_SOURCE_REVISION,
            POSTGRESQL_TARGET_REVISION,
        )
    }
    assert BACKUP_REQUIRED_RUNTIME_MIGRATION_PATHS == set()


def test_every_retained_store_has_a_version_and_migration_disposition():
    required = {
        "postgresql",
        "redis",
        "neo4j",
        "chroma",
        "minio",
        "local_json_memory",
        "retained_configuration",
        "sqlite_development",
    }
    surfaces = {surface.key: surface for surface in MIGRATION_SURFACES}

    assert required == set(surfaces)
    assert all(surface.target_version for surface in surfaces.values())
    assert all(surface.version_probe for surface in surfaces.values())
    assert all(surface.forward_migration for surface in surfaces.values())
    assert all(surface.rollback_policy for surface in surfaces.values())


def test_inventory_reports_real_blockers_instead_of_authorizing_migration():
    inventory = build_migration_inventory(ROOT)

    assert inventory["production_migration_ready"] is False
    assert inventory["managed_backup_required_before_destructive_migration"] is True
    assert inventory["legacy_create_all_is_production_coordinator"] is False
    assert inventory["alembic"]["errors"] == []
    assert "0.1.1" in SUPPORTED_UPGRADE_SOURCES
    assert {
        "supported_0_1_1_upgrade_not_qualified",
        "supported_0_1_1_redis_adoption_not_qualified",
        "supported_0_1_1_neo4j_adoption_not_qualified",
        "supported_0_1_1_chroma_rebuild_not_qualified",
        "supported_0_1_1_minio_adoption_not_qualified",
        "released_sqlite_to_postgresql_import_not_implemented",
    } <= set(inventory["blockers"])
    assert inventory["release_constraints"]["coordinated_backup_available"] is True
    assert inventory["release_constraints"]["coordinated_restore_available"] is True
    assert "4.4.0" in SUPPORTED_UPGRADE_SOURCES
    assert "4.4.1" in SUPPORTED_UPGRADE_SOURCES
