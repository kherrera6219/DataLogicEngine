"""Seed Neo4j with UKG pillar taxonomy and Honeycomb crosswalk edges.

Usage:
    python scripts/seed_neo4j.py [--wipe]

Reads PillarLevel rows from the local SQLite database and merges them into Neo4j
as Pillar nodes with HAS_CHILD relationships. Also seeds a representative set of
HONEYCOMB_BRIDGE edges between cross-domain pillar pairs.

Pass --wipe to delete all Pillar and KnowledgeNode data before seeding.
"""

import argparse
import sys
import os
import uuid

import yaml

# Make repo root importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv  # noqa: E402
load_dotenv()

from app import app  # noqa: E402
from models import PillarLevel  # noqa: E402
from backend.storage.graph_store import get_graph_store  # noqa: E402

_PILLAR_YAML = os.path.join(os.path.dirname(__file__), "..", "data", "ukg", "pillar_levels.yaml")

# --- Representative starter pillar data ---
# Used when the SQLite DB has no PillarLevel rows yet.
STARTER_PILLARS = [
    # (pillar_id, name, description, parent_pillar_id)
    ("PL01", "Fundamental Science", "Core scientific principles and natural laws", None),
    ("PL02", "Applied Science & Engineering", "Applied scientific disciplines", "PL01"),
    ("PL03", "Mathematics & Computation", "Formal mathematical systems and algorithms", "PL01"),
    ("PL04", "Life Sciences", "Biology, medicine, ecology", "PL01"),
    ("PL05", "Social Sciences", "Human behaviour, psychology, sociology", None),
    ("PL06", "Law & Regulatory Frameworks", "Legal systems and compliance", None),
    ("PL07", "Finance & Economics", "Financial markets, economics, accounting", None),
    ("PL08", "Healthcare & Clinical Practice", "Clinical medicine and patient care", "PL04"),
    ("PL09", "Artificial Intelligence", "Machine learning, LLMs, autonomous systems", "PL03"),
    ("PL10", "Cybersecurity", "Information security, threat analysis", "PL02"),
    ("PL11", "Environmental Science", "Climate, ecology, sustainability", "PL04"),
    ("PL12", "Education & Pedagogy", "Teaching methods, curriculum design", "PL05"),
]

# Honeycomb crosswalk pairs (source_pillar_id, target_pillar_id)
# Represents meaningful cross-domain knowledge bridges
HONEYCOMB_BRIDGES = [
    ("PL09", "PL08"),  # AI ↔ Healthcare
    ("PL09", "PL06"),  # AI ↔ Law
    ("PL06", "PL07"),  # Law ↔ Finance
    ("PL10", "PL09"),  # Cybersecurity ↔ AI
    ("PL10", "PL06"),  # Cybersecurity ↔ Law
    ("PL11", "PL07"),  # Environmental ↔ Finance (ESG)
    ("PL04", "PL08"),  # Life Sciences ↔ Healthcare
    ("PL03", "PL09"),  # Math ↔ AI
    ("PL05", "PL06"),  # Social Sciences ↔ Law
    ("PL02", "PL10"),  # Engineering ↔ Cybersecurity
]


def _load_yaml_pillars() -> list:
    """Parse data/ukg/pillar_levels.yaml into a flat pillar list."""
    path = os.path.abspath(_PILLAR_YAML)
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        rows = []
        for item in raw.get("PillarLevels", []):
            pillar_id = item.get("id", "")
            rows.append({
                "uid": item.get("uid") or str(uuid.uuid4()),
                "pillar_id": pillar_id,
                "name": item.get("label", pillar_id),
                "description": item.get("description", ""),
                "children": [],  # top-level YAML doesn't encode parent→child
            })
        return rows
    except Exception as exc:
        print(f"  Warning: could not load pillar_levels.yaml: {exc}")
        return []


def _merge_pillar(session, uid: str, pillar_id: str, name: str, description: str) -> None:
    session.run(
        """
        MERGE (p:Pillar {uid: $uid})
        SET p.code = $pillar_id,
            p.name = $name,
            p.description = $description
        """,
        uid=uid,
        pillar_id=pillar_id,
        name=name,
        description=description or "",
    )


def _merge_has_child(session, parent_uid: str, child_uid: str) -> None:
    session.run(
        """
        MATCH (parent:Pillar {uid: $parent_uid}), (child:Pillar {uid: $child_uid})
        MERGE (parent)-[:HAS_CHILD]->(child)
        """,
        parent_uid=parent_uid,
        child_uid=child_uid,
    )


def _merge_honeycomb(session, source_uid: str, target_uid: str) -> None:
    session.run(
        """
        MATCH (a:Pillar {uid: $source_uid}), (b:Pillar {uid: $target_uid})
        MERGE (a)-[:HONEYCOMB_BRIDGE]->(b)
        MERGE (b)-[:HONEYCOMB_BRIDGE]->(a)
        """,
        source_uid=source_uid,
        target_uid=target_uid,
    )


def seed(wipe: bool = False) -> None:
    store = get_graph_store()
    store.connect()

    if not store.driver:
        print("ERROR: Could not connect to Neo4j. Is it running?")
        sys.exit(1)

    with app.app_context():
        pillar_rows = PillarLevel.query.all()

    # Build pillar list: prefer YAML file > DB rows > starter data
    yaml_pillars = _load_yaml_pillars()

    if yaml_pillars:
        print(f"  Loading {len(yaml_pillars)} pillar levels from data/ukg/pillar_levels.yaml")
        uid_by_code = {p["pillar_id"]: p["uid"] for p in yaml_pillars}
        pillars = [(p["uid"], p["pillar_id"], p["name"], p["description"]) for p in yaml_pillars]
        child_pairs = [(p["uid"], uid_by_code[c]) for p in yaml_pillars for c in p.get("children", []) if c in uid_by_code]
    elif pillar_rows:
        print(f"  Loading {len(pillar_rows)} pillar levels from SQLite database")
        pillars = [(p.uid, p.pillar_id, p.name, p.description or "") for p in pillar_rows]
        uid_by_code = {p.pillar_id: p.uid for p in pillar_rows}
        child_pairs = []
    else:
        print("  No pillar data found — seeding from starter dataset")
        uid_map = {pid: str(uuid.uuid4()) for pid, *_ in STARTER_PILLARS}
        pillars = [(uid_map[pid], pid, name, desc) for pid, name, desc, _ in STARTER_PILLARS]
        uid_by_code = uid_map
        child_pairs = []
        for pid, name, desc, parent_pid in STARTER_PILLARS:
            if parent_pid and parent_pid in uid_map:
                child_pairs.append((uid_map[parent_pid], uid_map[pid]))

    with store.driver.session() as session:
        if wipe:
            print("  Wiping existing Pillar and KnowledgeNode data...")
            session.run("MATCH (p:Pillar) DETACH DELETE p")
            session.run("MATCH (n:KnowledgeNode) DETACH DELETE n")

        print(f"  Merging {len(pillars)} Pillar nodes...")
        for uid, pillar_id, name, description in pillars:
            _merge_pillar(session, uid, pillar_id, name, description)

        print(f"  Merging {len(child_pairs)} HAS_CHILD edges...")
        for parent_uid, child_uid in child_pairs:
            _merge_has_child(session, parent_uid, child_uid)

        # Honeycomb bridges — map from pillar code to uid
        print(f"  Merging {len(HONEYCOMB_BRIDGES)} HONEYCOMB_BRIDGE edge pairs...")
        for src_code, tgt_code in HONEYCOMB_BRIDGES:
            src_uid = uid_by_code.get(src_code)
            tgt_uid = uid_by_code.get(tgt_code)
            if src_uid and tgt_uid:
                _merge_honeycomb(session, src_uid, tgt_uid)
            else:
                print(f"    Skipped bridge {src_code} <-> {tgt_code} (pillar not in seed set)")

    pillar_count = store.run_query("MATCH (p:Pillar) RETURN count(p) AS n")[0]["n"]
    edge_count = store.run_query("MATCH ()-[r:HAS_CHILD|HONEYCOMB_BRIDGE]->() RETURN count(r) AS n")[0]["n"]
    print(f"  Done. Neo4j: {pillar_count} Pillar nodes, {edge_count} edges total.")
    store.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Neo4j with UKG pillar taxonomy")
    parser.add_argument("--wipe", action="store_true", help="Delete existing Pillar data before seeding")
    args = parser.parse_args()
    print("Seeding Neo4j...")
    seed(wipe=args.wipe)
