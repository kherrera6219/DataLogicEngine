"""Phase 4 migration graph and supported-upgrade inventory tests."""

from __future__ import annotations

from pathlib import Path

from flask import Flask
from flask_migrate import upgrade
from sqlalchemy import inspect, text

from extensions import db, migrate
import models
from backend.storage.migration_inventory import (
    MIGRATION_SURFACES,
    SUPPORTED_UPGRADE_SOURCES,
    build_migration_inventory,
    inventory_alembic_revisions,
)


ROOT = Path(__file__).resolve().parents[2]


def test_alembic_revision_graph_has_one_ordered_base_and_head():
    graph = inventory_alembic_revisions(ROOT / "migrations" / "versions")

    assert len(graph["revisions"]) == 17
    assert graph["bases"] == ["000000000001"]
    assert graph["heads"] == ["d3e4f5a6b7c8"]
    assert graph["errors"] == []
    assert graph["linear_order"][0] == "000000000001"
    assert graph["linear_order"][-1] == "d3e4f5a6b7c8"


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
        tables = set(inspect(db.engine).get_table_names())
        current = db.session.execute(text("SELECT version_num FROM alembic_version")).scalar_one()

    assert set(models.db.metadata.tables) <= tables
    assert current == "d3e4f5a6b7c8"


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
