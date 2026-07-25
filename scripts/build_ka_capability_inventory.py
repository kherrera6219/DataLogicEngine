"""Build the Phase 18 lossless Knowledge Algorithm capability inventory.

This is an evidence generator, not the production KA manifest. It reconciles the
currently executable registry, Layer 9/10 implementations, the original design
registry, expanded historical metadata, SDK data, runtime callers, and tests.
The output stays read-only with respect to runtime identity until CP18-A review
approves the canonical manifest migration.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "production-readiness" / "2026" / "phase-18"
LIVE_REGISTRY_PATH = ROOT / "backend" / "knowledge_algorithms" / "ka_registry.yaml"
ORIGINAL_REGISTRY_PATH = ROOT / "data" / "registries" / "ka_registry.yaml"
CORE_METADATA_PATH = ROOT / "core" / "data" / "ka_registry.json"
SDK_REGISTRY_PATH = (
    ROOT / "sdk" / "UKG_Python_SDK" / "ukg_sdk" / "data" / "ka_registry_by_id.json"
)

SCHEMA_VERSION = "dle.ka-capability-inventory.v1"
CROSSWALK_SCHEMA_VERSION = "dle.ka-capability-crosswalk.v1"
GENERIC_SCAFFOLD_RE = re.compile(
    r"^Advanced (Security|Data|Synthesis|Reasoning|Analysis|Compliance|Optimization) "
    r"Module \d+$"
)
KA_ID_RE = re.compile(r"\b(?:L(?:9|10)-)?KA-(?:MASTER|\d{1,4})\b", re.IGNORECASE)
IMPLEMENTATION_PREFIX_RE = re.compile(r"^(?:ka_\d+_|l(?:9|10)_ka_\d+_)")
RISK_EFFECT_WORDS = {
    "access",
    "archive",
    "backup",
    "broker",
    "cache",
    "deployment",
    "encryption",
    "environment",
    "gateway",
    "incident",
    "ingestion",
    "inbox",
    "injection",
    "integration",
    "key",
    "mesh",
    "notification",
    "outbox",
    "policy",
    "pruner",
    "recovery",
    "release",
    "rollback",
    "scheduler",
    "training",
}

L9_DEFINITIONS = {
    "L9-KA-001": (
        "Trace Analyzer",
        "backend.knowledge_algorithms.l9.l9_ka_001_trace_analyzer",
    ),
    "L9-KA-002": (
        "Belief Drift Detector",
        "backend.knowledge_algorithms.l9.l9_ka_002_belief_drift",
    ),
    "L9-KA-003": (
        "Persona Agreement Auditor",
        "backend.knowledge_algorithms.l9.l9_ka_003_persona_auditor",
    ),
    "L9-KA-004": (
        "Meta-Cognitive Evaluator",
        "backend.knowledge_algorithms.l9.l9_ka_004_meta_evaluator",
    ),
    "L9-KA-005": (
        "Recursion Trigger",
        "backend.knowledge_algorithms.l9.l9_ka_005_recursion_trigger",
    ),
    "L9-KA-006": (
        "Readiness Scorer",
        "backend.knowledge_algorithms.l9.l9_ka_006_confidence_calc",
    ),
    "L9-KA-007": (
        "Loop Controller",
        "backend.knowledge_algorithms.l9.l9_ka_007_loop_controller",
    ),
}

DELETED_STUB_ALIASES = {
    "KA-278": ("Input Validation and Normalization", "KA-004"),
    "KA-279": ("Self Critique and Reflection", "KA-008"),
    "KA-280": ("Interactive Clarification and Learning", "KA-058"),
    "KA-281": ("Cross-Instance Consensus Engine", "KA-1084"),
}

# These are reviewed semantic-equivalence decisions whose implementation names
# are intentionally shorter than the original design-catalog titles. Keep this
# map exact: approximate/fuzzy title matching is not allowed to decide runtime
# identity.
ORIGINAL_CAPABILITY_ALIASES = {
    ("KA-113", "queryanalysiscomplexityrouter"): "KA-113",
}

# A generated named row is an alias only when review proves that it adds no
# distinct inputs, outputs, side effects, or decision semantics.
GENERATED_CAPABILITY_ALIASES = {
    ("KA-133", "chaosinjection"): "KA-1101",
}

CANONICAL_NAME_OVERRIDES = {
    "L10-KA-006": "Layer-10 Belief-Decay Trust Gate",
}

# Candidate pairs are intentionally broad. Each retained pair needs an explicit
# semantic boundary so a similar title cannot silently create two copies of the
# same production algorithm.
REVIEWED_DISTINCT_CAPABILITY_PAIRS = {
    ("KA-001", "KA-002"): (
        "Sequential task decomposition is distinct from parallel branch "
        "generation and scoring."
    ),
    ("KA-024", "L10-KA-006"): (
        "The general confidence/risk policy veto is distinct from the terminal "
        "Layer-10 belief-decay threshold."
    ),
    ("KA-031", "KA-1047"): (
        "Selection among registered algorithms is distinct from bounded "
        "meta-selection or algorithm invention."
    ),
    ("KA-039", "KA-1085"): (
        "Numeric data-stream outlier detection is distinct from reasoning and "
        "output-pattern anomaly detection."
    ),
    ("KA-042", "KA-070"): (
        "Local baseline-state counterfactual projection is distinct from "
        "bounded downstream graph-ripple simulation."
    ),
    ("KA-043", "KA-066"): (
        "Candidate-cause ranking is distinct from causal graph-fragment "
        "construction over events and dependencies."
    ),
    ("KA-056", "KA-168"): (
        "Narrative explanation presentation is distinct from general "
        "explanation derivation and evidence binding."
    ),
    ("KA-100", "KA-1036"): (
        "Runtime resource optimization is distinct from multi-objective Pareto "
        "trade-off optimization."
    ),
    ("KA-109", "KA-138"): (
        "Current health aggregation is distinct from predictive health forecasting."
    ),
    ("KA-1099", "KA-117"): (
        "Knowledge-record integrity validation is distinct from a full-system "
        "consistency and health audit."
    ),
    ("KA-1087", "KA-168"): (
        "Producing an explanation is distinct from checking whether an "
        "explanation covers all critical reasoning steps."
    ),
    ("KA-1109", "L10-KA-005"): (
        "Persistence-safety classification is distinct from applying the "
        "Layer-10 runtime containment decision."
    ),
}
HISTORICAL_RESEARCH_SOURCES = [
    "docs/archive/phase-16/KNOWLEDGE_ALGORITHM_CATALOG.md",
    "docs/archive/whitepapers/Integration of Knowledge Algorithms (KAs) into the UKG_USKD Architecture.pdf",
    "docs/archive/whitepapers/Universal Knowledge Algorithm (KA) System – Technical Report.pdf",
    "docs/archive/whitepapers/UKG_Workflow_Architecture__active-through-2026-07-15.md",
]


@dataclass(frozen=True)
class SourceDefinition:
    source: str
    source_id: str
    name: str
    purpose: str | None
    disposition: str
    canonical_id: str | None
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "source_id": self.source_id,
            "name": self.name,
            "purpose": self.purpose,
            "disposition": self.disposition,
            "canonical_id": self.canonical_id,
            "rationale": self.rationale,
        }


def normalize_name(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def normalize_ka_id(value: str) -> str:
    clean = str(value).strip().upper()
    if clean == "KA-MASTER":
        return "KA-Master"
    match = re.fullmatch(r"(L(?:9|10)-KA-)(\d+)", clean)
    if match:
        return f"{match.group(1)}{int(match.group(2)):03d}"
    match = re.fullmatch(r"KA-(\d+)", clean)
    if match:
        number = int(match.group(1))
        width = 3 if number < 1000 else 4
        return f"KA-{number:0{width}d}"
    return clean


def implementation_file(module_or_callable: str) -> Path:
    module = module_or_callable
    if module.endswith(".run"):
        module = module.rsplit(".", 1)[0]
    return ROOT.joinpath(*module.split(".")).with_suffix(".py")


def restored_implementation_module(canonical_id: str) -> str | None:
    """Resolve one reviewed restored-capability source by canonical ID."""
    number = canonical_id.removeprefix("KA-")
    candidates = sorted(
        (ROOT / "backend" / "knowledge_algorithms").glob(f"ka_{number}_*.py")
    )
    if len(candidates) > 1:
        paths = ", ".join(path.name for path in candidates)
        raise ValueError(
            f"{canonical_id}: multiple restored implementation owners: {paths}"
        )
    if not candidates:
        return None
    return f"backend.knowledge_algorithms.{candidates[0].stem}.run"


def implementation_name(module_or_callable: str, ka_id: str) -> str:
    module = (
        module_or_callable.rsplit(".", 1)[0]
        if module_or_callable.endswith(".run")
        else module_or_callable
    )
    stem = module.rsplit(".", 1)[-1]
    stem = IMPLEMENTATION_PREFIX_RE.sub("", stem)
    if ka_id == "KA-Master":
        return "KA Master Controller"
    words = stem.replace("__", "_").replace("_", " ").strip()
    replacements = {
        "ab testing": "A/B Testing",
        "api gateway": "API Gateway",
        "pii redactor": "PII Redactor",
    }
    return replacements.get(words, words.title())


def source_input_sha256(extra_paths: Iterable[Path] = ()) -> str:
    """Hash all live inputs used to classify KA capability and integration state."""

    paths = {
        Path(__file__).resolve(),
        LIVE_REGISTRY_PATH,
        ORIGINAL_REGISTRY_PATH,
        CORE_METADATA_PATH,
        SDK_REGISTRY_PATH,
        ROOT / "backend" / "routes" / "ka_routes.py",
        ROOT / "backend" / "knowledge_algorithms" / "production_catalog.py",
        ROOT / "core" / "engine" / "ka_engine.py",
        ROOT / "core" / "knowledge_algorithm" / "ka_loader.py",
        ROOT / "scripts" / "build_ka_runtime_manifest.py",
        ROOT / "scripts" / "verify_ka_runtime_authority.py",
        ROOT / "scripts" / "verify_ka_capability_inventory.py",
    }
    paths.update(path for path in extra_paths if path.exists())
    for scan_root, patterns in (
        (ROOT / "backend" / "knowledge_algorithms", ("*.py", "*.yaml", "*.json")),
        (ROOT / "sdk" / "UKG_Python_SDK" / "ukg_sdk" / "ka", ("*.py",)),
        (ROOT / "frontend" / "app" / "algorithms", ("*.tsx", "*.ts")),
        (ROOT / "tests" / "knowledge_algorithms", ("*.py",)),
    ):
        if not scan_root.exists():
            continue
        for pattern in patterns:
            paths.update(
                path
                for path in scan_root.rglob(pattern)
                if ".generated." not in path.name
            )

    digest = hashlib.sha256()
    paths = {path for path in paths if path.exists()}
    for path in sorted(paths, key=lambda item: item.relative_to(ROOT).as_posix()):
        relative = path.relative_to(ROOT).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def load_live_registry() -> dict[str, str]:
    payload = yaml.safe_load(LIVE_REGISTRY_PATH.read_text(encoding="utf-8")) or {}
    return {
        normalize_ka_id(str(ka_id)): str(implementation)
        for ka_id, implementation in payload.get("ka_registry", {}).items()
    }


def load_original_registry() -> list[dict[str, Any]]:
    rows = yaml.safe_load(ORIGINAL_REGISTRY_PATH.read_text(encoding="utf-8")) or []
    if not isinstance(rows, list):
        raise TypeError("Original KA registry must be a list")
    return [dict(row) for row in rows if isinstance(row, dict)]


def load_core_metadata() -> list[dict[str, Any]]:
    rows = json.loads(CORE_METADATA_PATH.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise TypeError("Core KA metadata must be a list")
    return [dict(row) for row in rows if isinstance(row, dict)]


def load_sdk_registry() -> dict[str, dict[str, Any]]:
    rows = json.loads(SDK_REGISTRY_PATH.read_text(encoding="utf-8"))
    if not isinstance(rows, dict):
        raise TypeError("SDK KA registry must be an object keyed by ID")
    return {normalize_ka_id(str(key)): dict(value) for key, value in rows.items()}


def production_metadata() -> dict[str, dict[str, Any]]:
    from backend.knowledge_algorithms.production_catalog import load_production_catalog

    return {key: value.to_dict() for key, value in load_production_catalog().items()}


def analyze_implementation(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": path.relative_to(ROOT).as_posix(),
            "exists": False,
            "has_run": False,
            "has_execution_entry_point": False,
            "nonblank_noncomment_loc": 0,
            "signals": ["missing_implementation"],
        }
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    functions = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )
    classes = sorted(
        node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    )
    lines = [
        line
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    lowered = text.lower()
    signals = []
    signal_patterns = {
        "contains_mock_language": r"\bmock(?:ed|ing)?\b",
        "contains_stub_language": r"\bstub(?:bed|s)?\b",
        "contains_placeholder_language": r"\bplaceholder\b",
        "uses_randomness": r"\b(?:random\.|secrets\.|os\.urandom)",
        "contains_todo": r"\bTODO\b",
    }
    for label, pattern in signal_patterns.items():
        if re.search(pattern, text, flags=re.IGNORECASE):
            signals.append(label)
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "exists": True,
        "has_run": "run" in functions,
        "has_execution_entry_point": bool({"run", "execute"} & set(functions)),
        "functions": functions,
        "classes": classes,
        "nonblank_noncomment_loc": len(lines),
        "signals": sorted(signals),
        "imports_celery": "from celery" in lowered or "import celery" in lowered,
    }


def iter_python_files(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if any(
                part in {".venv", "node_modules", "__pycache__"} for part in path.parts
            ):
                continue
            yield path


def scan_references(
    canonical_ids: Iterable[str], implementations: dict[str, Path]
) -> dict[str, Any]:
    all_ids = sorted(set(canonical_ids))
    runtime_files = list(
        iter_python_files([ROOT / "backend", ROOT / "core", ROOT / "sdk"])
    )
    test_files = list(iter_python_files([ROOT / "tests"]))
    execution_call_sites: dict[str, set[str]] = {ka_id: set() for ka_id in all_ids}
    runtime_references: dict[str, set[str]] = {ka_id: set() for ka_id in all_ids}
    test_references: dict[str, set[str]] = {ka_id: set() for ka_id in all_ids}
    named_test_functions: dict[str, set[str]] = {ka_id: set() for ka_id in all_ids}

    def literal_ids(text: str) -> set[str]:
        return {normalize_ka_id(match.group(0)) for match in KA_ID_RE.finditer(text)}

    for path in runtime_files:
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT).as_posix()
        own_ids = {
            ka_id
            for ka_id, implementation in implementations.items()
            if implementation.resolve() == path.resolve()
        }
        for ka_id in literal_ids(text):
            if ka_id in runtime_references and ka_id not in own_ids:
                runtime_references[ka_id].add(relative)
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            func_name = ""
            if isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                func_name = node.func.id
            if func_name not in {
                "execute_algorithm",
                "execute_ka",
                "execute",
                "run_ka_task",
            }:
                continue
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                ka_id = normalize_ka_id(first.value)
                if ka_id in execution_call_sites and ka_id not in own_ids:
                    execution_call_sites[ka_id].add(
                        f"{relative}:{getattr(node, 'lineno', 0)}"
                    )

    for path in test_files:
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT).as_posix()
        mentioned = literal_ids(text)
        for ka_id, implementation in implementations.items():
            if implementation.stem in text:
                mentioned.add(ka_id)
        for ka_id in mentioned:
            if ka_id in test_references:
                test_references[ka_id].add(relative)
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test_"):
                continue
            function_text = ast.get_source_segment(text, node) or ""
            function_ids = literal_ids(function_text)
            normalized_function_name = normalize_name(node.name)
            for ka_id in all_ids:
                digits = re.sub(r"\D", "", ka_id)
                if ka_id in function_ids or (
                    digits
                    and (
                        f"ka{digits}" in normalized_function_name
                        or f"ka{int(digits)}" in normalized_function_name
                    )
                ):
                    named_test_functions[ka_id].add(f"{relative}::{node.name}")

    return {
        ka_id: {
            "runtime_references": sorted(runtime_references[ka_id]),
            "execution_call_sites": sorted(execution_call_sites[ka_id]),
            "test_references": sorted(test_references[ka_id]),
            "named_test_functions": sorted(named_test_functions[ka_id]),
        }
        for ka_id in all_ids
    }


def classify_implementation_surfaces(
    implementations: dict[str, Path],
) -> list[dict[str, Any]]:
    ids_by_path: dict[str, list[str]] = {}
    for ka_id, path in implementations.items():
        relative = path.relative_to(ROOT).as_posix()
        ids_by_path.setdefault(relative, []).append(ka_id)

    discovered = {
        path
        for pattern_root, pattern in (
            (ROOT / "backend" / "knowledge_algorithms", "ka_[0-9]*.py"),
            (ROOT / "backend" / "knowledge_algorithms" / "l9", "l9_ka_[0-9]*.py"),
            (ROOT / "backend" / "knowledge_algorithms" / "l10", "l10_ka_[0-9]*.py"),
        )
        for path in pattern_root.glob(pattern)
    }
    discovered.add(
        ROOT / "backend" / "knowledge_algorithms" / "ka_master_controller.py"
    )
    rows = []
    for path in sorted(discovered | set(implementations.values())):
        relative = path.relative_to(ROOT).as_posix()
        canonical_ids = sorted(ids_by_path.get(relative, []))
        rows.append(
            {
                "path": relative,
                "canonical_ids": canonical_ids,
                "exists": path.exists(),
                "disposition": (
                    "canonical_implementation_requires_phase18_qualification"
                    if canonical_ids and path.exists()
                    else "unclassified_implementation"
                ),
            }
        )
    return rows


def classify_integration_surfaces(
    implementation_paths: dict[str, Path],
) -> list[dict[str, Any]]:
    implementation_files = {path.resolve() for path in implementation_paths.values()}
    roots = [ROOT / "backend", ROOT / "core", ROOT / "sdk", ROOT / "frontend"]
    candidates: set[Path] = {
        ROOT / "backend" / "routes" / "ka_routes.py",
        ROOT / "frontend" / "app" / "algorithms" / "page.tsx",
        ROOT / "frontend" / "app" / "algorithms" / "page.test.tsx",
        ROOT / "frontend" / "app" / "algorithms" / "error.tsx",
    }
    for owned_surface_root in (
        ROOT / "core" / "knowledge_algorithm",
        ROOT / "sdk" / "UKG_Python_SDK" / "ukg_sdk" / "ka",
    ):
        if owned_surface_root.exists():
            candidates.update(owned_surface_root.glob("*.py"))
    signal = re.compile(
        r"knowledge algorithm|ka_registry|execute_algorithm|execute_ka|/algorithms",
        re.IGNORECASE,
    )
    allowed_suffixes = {".py", ".ts", ".tsx", ".json", ".yaml", ".yml"}
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if (
                not path.is_file()
                or path.suffix.lower() not in allowed_suffixes
                or ".generated." in path.name
                or any(part in {"node_modules", "__pycache__"} for part in path.parts)
                or path.resolve() in implementation_files
            ):
                continue
            try:
                if signal.search(path.read_text(encoding="utf-8")):
                    candidates.add(path)
            except (OSError, UnicodeDecodeError):
                continue

    rows = []
    for path in sorted(candidates):
        relative = path.relative_to(ROOT).as_posix()
        if relative == "backend/knowledge_algorithms/ka_registry.yaml":
            kind = "current_executable_registry"
            disposition = "source_for_cp18_b_manifest_migration"
            checkpoint = "CP18-B"
        elif relative.startswith("backend/knowledge_algorithms/"):
            kind = "backend_ka_governance_or_package_surface"
            disposition = "merge_into_canonical_manifest_and_controller"
            checkpoint = "CP18-B"
        elif relative in {
            "core/engine/ka_engine.py",
            "core/knowledge_algorithm/ka_loader.py",
        }:
            kind = "duplicate_runtime"
            disposition = "convert_to_canonical_controller_adapter"
            checkpoint = "CP18-B"
        elif relative.startswith("core/knowledge_algorithm/"):
            kind = "legacy_runtime_contract_surface"
            disposition = "retain_only_as_canonical_contract_or_compatibility_adapter"
            checkpoint = "CP18-B"
        elif relative.startswith("core/"):
            kind = "application_caller"
            disposition = "route_through_canonical_controller"
            checkpoint = "CP18-D"
        elif relative.startswith("backend/routes/") or relative in {
            "backend/graphql_schema.py",
            "backend/api/specs/ukg_api_v3_2.yaml",
        }:
            kind = "backend_api_surface"
            disposition = "generate_or_migrate_to_versioned_ka_api"
            checkpoint = "CP18-E"
        elif relative.startswith("backend/"):
            kind = "backend_application_caller"
            disposition = "route_through_canonical_controller"
            checkpoint = "CP18-D"
        elif "/ukg_sdk/ka/" in f"/{relative}":
            kind = "private_sdk_runtime"
            disposition = "replace_with_generated_canonical_api_client"
            checkpoint = "CP18-B"
        elif relative.startswith("sdk/"):
            kind = "sdk_contract_or_catalog_surface"
            disposition = "generate_from_canonical_manifest"
            checkpoint = "CP18-B"
        elif relative.startswith("frontend/app/algorithms/"):
            kind = "algorithms_desktop_workflow"
            disposition = "complete_against_versioned_real_backend_api"
            checkpoint = "CP18-E"
        elif relative.startswith("frontend/"):
            kind = "frontend_reference_surface"
            disposition = "align_to_canonical_manifest_and_trace_contract"
            checkpoint = "CP18-E"
        else:
            kind = "unclassified"
            disposition = "unclassified_integration_surface"
            checkpoint = None
        rows.append(
            {
                "path": relative,
                "exists": path.exists(),
                "kind": kind,
                "disposition": disposition,
                "target_checkpoint": checkpoint,
            }
        )
    return rows


def choose_name_match(
    *,
    source_id: str,
    name: str,
    canonical_by_name: dict[str, list[str]],
) -> str | None:
    candidates = list(canonical_by_name.get(normalize_name(name), []))
    if source_id in candidates:
        return source_id
    if len(candidates) == 1:
        return candidates[0]
    numeric = [
        candidate for candidate in candidates if re.fullmatch(r"KA-\d+", candidate)
    ]
    if len(numeric) == 1:
        return numeric[0]
    return None


def is_effect_oriented(name: str) -> bool:
    tokens = set(re.findall(r"[a-z0-9]+", name.lower()))
    return bool(tokens & RISK_EFFECT_WORDS)


def semantic_name_tokens(value: str) -> set[str]:
    generic = {
        "algorithm",
        "analysis",
        "analyzer",
        "and",
        "checker",
        "controller",
        "engine",
        "for",
        "knowledge",
        "manager",
        "module",
        "of",
        "system",
        "the",
        "validator",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if token not in generic
    }


def semantic_duplicate_candidates(
    entries: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = sorted(entries, key=lambda row: row["canonical_id"])
    candidates = []
    for index, left in enumerate(rows):
        left_tokens = semantic_name_tokens(left["name"])
        for right in rows[index + 1 :]:
            right_tokens = semantic_name_tokens(right["name"])
            union = left_tokens | right_tokens
            similarity = len(left_tokens & right_tokens) / len(union) if union else 1.0
            if similarity < 0.5:
                continue
            pair = (left["canonical_id"], right["canonical_id"])
            rationale = REVIEWED_DISTINCT_CAPABILITY_PAIRS.get(pair)
            candidates.append(
                {
                    "canonical_ids": list(pair),
                    "names": [left["name"], right["name"]],
                    "token_similarity": round(similarity, 4),
                    "disposition": (
                        "reviewed_materially_distinct"
                        if rationale
                        else "unresolved_semantic_duplicate_candidate"
                    ),
                    "rationale": rationale,
                }
            )
    return candidates


def split_catalog_values(value: Any) -> list[str]:
    if value is None:
        return []
    return [
        item.strip() for item in re.split(r"[,;]", str(value)) if item and item.strip()
    ]


def catalog_yes(value: Any) -> bool:
    return str(value or "").strip().lower() in {"yes", "true", "1"}


@lru_cache(maxsize=1)
def build_inventory() -> tuple[dict[str, Any], dict[str, Any]]:
    live = load_live_registry()
    original = load_original_registry()
    core_rows = load_core_metadata()
    sdk = load_sdk_registry()
    production = production_metadata()

    canonical: dict[str, dict[str, Any]] = {}
    definitions: list[SourceDefinition] = []
    implementation_paths: dict[str, Path] = {}
    canonical_by_name: dict[str, list[str]] = {}

    def index_name(ka_id: str, name: str) -> None:
        canonical_by_name.setdefault(normalize_name(name), []).append(ka_id)
        canonical_by_name[normalize_name(name)].sort()

    def add_canonical(
        *,
        ka_id: str,
        name: str,
        purpose: str | None,
        identity_class: str,
        implementation: str | None,
        source: str,
        source_id: str,
        implementation_status: str,
    ) -> None:
        if ka_id in canonical:
            raise ValueError(f"Duplicate canonical ID proposal: {ka_id}")
        path = implementation_file(implementation) if implementation else None
        if path is not None:
            implementation_paths[ka_id] = path
        canonical[ka_id] = {
            "canonical_id": ka_id,
            "name": name,
            "purpose": purpose,
            "identity_class": identity_class,
            "implementation": (
                path.relative_to(ROOT).as_posix() if path is not None else None
            ),
            "implementation_status": implementation_status,
            "effect_class": "effect_oriented_review_required"
            if is_effect_oriented(name)
            else "pure_or_advisory_review_required",
            "contract_status": (
                "phase18_b_schema_review_required"
                if implementation
                else "phase18_b_implementation_and_schema_required"
            ),
            "input_descriptions": [],
            "output_descriptions": [],
            "categories": [],
            "layer_scope": (
                ["L9"]
                if ka_id.startswith("L9-")
                else ["L10"]
                if ka_id.startswith("L10-")
                else ["orchestration"]
                if ka_id == "KA-Master"
                else []
            ),
            "persona_scope": [],
            "subsystems": [],
            "dependency_source_ids": [],
            "triggers": [],
            "risk_classes": [],
            "design_contracts": [],
            "migration_notes": {
                "current_executable": (
                    "Retain the current ID and behavior until the canonical controller "
                    "and parity tests replace the legacy entry point."
                ),
                "current_unregistered_layer9": (
                    "Register through the canonical manifest without changing the "
                    "existing Layer-9 ID."
                ),
                "restored_original_design_capability": (
                    "Implement under the restored canonical ID; retain the conflicting "
                    "historical numeric ID only as a design-v1 scoped alias."
                ),
                "preserved_generated_named_capability": (
                    "Author and qualify a distinct production contract before enabling."
                ),
            }.get(identity_class, "Review during the canonical manifest migration."),
            "source_records": [],
            "scoped_aliases": [],
        }
        index_name(ka_id, name)
        definitions.append(
            SourceDefinition(
                source=source,
                source_id=source_id,
                name=name,
                purpose=purpose,
                disposition="canonical",
                canonical_id=ka_id,
                rationale=identity_class,
            )
        )

    def apply_design_contract(
        canonical_id: str,
        row: dict[str, Any],
        *,
        source: str,
        source_id: str,
    ) -> None:
        entry = canonical[canonical_id]
        inputs = split_catalog_values(row.get("Inputs"))
        outputs = split_catalog_values(row.get("Outputs"))
        categories = split_catalog_values(row.get("Category") or row.get("category"))
        layers = split_catalog_values(
            row.get("Allowed_Layers") or row.get("Primary_Layers") or row.get("layers")
        )
        dependencies = [
            normalize_ka_id(item)
            for item in split_catalog_values(row.get("Dependencies"))
        ]
        risk_classes = split_catalog_values(row.get("Risk_Class") or row.get("risk"))
        triggers = [
            label
            for field, label in (
                ("Can_Invoke_Chaos", "may_invoke_chaos"),
                ("Can_Invoke_External_Research", "may_invoke_external_research"),
                ("Can_Trigger_Recursion", "may_trigger_recursion"),
                ("Can_Veto", "may_veto"),
                ("Writes_Memory", "may_write_memory"),
            )
            if catalog_yes(row.get(field))
        ]
        owner = str(row.get("Owner") or "").strip()
        contract = {
            "source": source,
            "source_id": source_id,
            "version": str(row.get("Version") or "").strip() or None,
            "inputs": inputs,
            "outputs": outputs,
            "categories": categories,
            "primary_layers": split_catalog_values(row.get("Primary_Layers")),
            "allowed_layers": layers,
            "dependencies": dependencies,
            "risk_class": risk_classes,
            "reads_memory": catalog_yes(row.get("Reads_Memory")),
            "writes_memory": catalog_yes(row.get("Writes_Memory")),
            "produces_artifacts": catalog_yes(row.get("Produces_Artifacts")),
            "audit_events": catalog_yes(row.get("Audit_Events")),
            "triggers": triggers,
            "owner": owner or None,
            "notes": str(row.get("Notes") or "").strip() or None,
        }
        if not entry.get("purpose"):
            entry["purpose"] = (
                str(row.get("Purpose") or row.get("purpose") or "").strip() or None
            )
        design_name = str(row.get("KA_Name") or row.get("name") or "").strip()
        if design_name and normalize_name(design_name) == normalize_name(entry["name"]):
            entry["name"] = design_name
        entry["design_contracts"].append(contract)
        entry["input_descriptions"] = sorted(
            set(entry["input_descriptions"]) | set(inputs)
        )
        entry["output_descriptions"] = sorted(
            set(entry["output_descriptions"]) | set(outputs)
        )
        entry["categories"] = sorted(set(entry["categories"]) | set(categories))
        entry["layer_scope"] = sorted(set(entry["layer_scope"]) | set(layers))
        entry["subsystems"] = sorted(
            set(entry["subsystems"]) | ({owner} if owner else set())
        )
        entry["dependency_source_ids"] = sorted(
            set(entry["dependency_source_ids"]) | set(dependencies)
        )
        entry["triggers"] = sorted(set(entry["triggers"]) | set(triggers))
        entry["risk_classes"] = sorted(set(entry["risk_classes"]) | set(risk_classes))
        if any(
            (
                contract["writes_memory"],
                "may_invoke_external_research" in triggers,
                "may_invoke_chaos" in triggers,
            )
        ):
            entry["effect_class"] = "effect_oriented_review_required"

    for ka_id, implementation in sorted(live.items()):
        if ka_id == "KA-Master":
            name = "KA Master Controller"
            purpose = "Canonical Knowledge Algorithm orchestration controller"
        else:
            name = CANONICAL_NAME_OVERRIDES.get(
                ka_id, implementation_name(implementation, ka_id)
            )
            purpose = f"Layer 10 {name}" if ka_id.startswith("L10-") else None
        add_canonical(
            ka_id=ka_id,
            name=name,
            purpose=purpose,
            identity_class="current_executable",
            implementation=implementation,
            source=LIVE_REGISTRY_PATH.relative_to(ROOT).as_posix(),
            source_id=ka_id,
            implementation_status="existing_requires_phase18_qualification",
        )

    for ka_id, (name, module) in sorted(L9_DEFINITIONS.items()):
        add_canonical(
            ka_id=ka_id,
            name=name,
            purpose=f"Layer 9 {name}",
            identity_class="current_unregistered_layer9",
            implementation=module,
            source="backend/knowledge_algorithms/l9/__init__.py",
            source_id=ka_id,
            implementation_status="existing_unregistered_requires_qualification",
        )

    original_by_id = {normalize_ka_id(str(row.get("KA_ID"))): row for row in original}
    original_canonical_by_id: dict[str, str] = {}
    for source_id, row in sorted(original_by_id.items()):
        name = str(row.get("KA_Name") or source_id)
        purpose = str(row.get("Purpose") or "") or None
        reviewed_alias = ORIGINAL_CAPABILITY_ALIASES.get(
            (source_id, normalize_name(name))
        )
        match = reviewed_alias or choose_name_match(
            source_id=source_id,
            name=name,
            canonical_by_name=canonical_by_name,
        )
        if match is None:
            number = int(source_id.split("-")[1])
            canonical_id = f"KA-{1000 + number:04d}"
            restored_implementation = restored_implementation_module(canonical_id)
            add_canonical(
                ka_id=canonical_id,
                name=name,
                purpose=purpose,
                identity_class="restored_original_design_capability",
                implementation=restored_implementation,
                source=ORIGINAL_REGISTRY_PATH.relative_to(ROOT).as_posix(),
                source_id=source_id,
                implementation_status=(
                    "restored_implementation_requires_qualification"
                    if restored_implementation
                    else "implementation_required"
                ),
            )
            if source_id in canonical:
                canonical[canonical_id]["scoped_aliases"].append(
                    f"design-v1:{source_id}"
                )
            original_canonical_by_id[source_id] = canonical_id
        else:
            definitions.append(
                SourceDefinition(
                    source=ORIGINAL_REGISTRY_PATH.relative_to(ROOT).as_posix(),
                    source_id=source_id,
                    name=name,
                    purpose=purpose,
                    disposition="same_capability_or_scoped_alias",
                    canonical_id=match,
                    rationale=(
                        "reviewed semantic-equivalence alias"
                        if reviewed_alias
                        else "same stable ID and name"
                        if match == source_id
                        else "historical design ID conflicts with current runtime semantics; preserve as scoped alias"
                    ),
                )
            )
            if match != source_id:
                canonical[match]["scoped_aliases"].append(f"design-v1:{source_id}")
            original_canonical_by_id[source_id] = match
        apply_design_contract(
            original_canonical_by_id[source_id],
            row,
            source=ORIGINAL_REGISTRY_PATH.relative_to(ROOT).as_posix(),
            source_id=source_id,
        )

    core_appended_dispositions: list[dict[str, Any]] = []
    for row in core_rows:
        source_id = normalize_ka_id(str(row.get("KA_ID") or row.get("id")))
        name = str(row.get("KA_Name") or row.get("name") or source_id)
        purpose = str(row.get("Purpose") or row.get("purpose") or "") or None
        if source_id in original_by_id:
            match = original_canonical_by_id[source_id]
            disposition = "original_catalog_duplicate"
            rationale = "covered by the reviewed original 114-row source"
            definitions.append(
                SourceDefinition(
                    source=CORE_METADATA_PATH.relative_to(ROOT).as_posix(),
                    source_id=source_id,
                    name=name,
                    purpose=purpose,
                    disposition=disposition,
                    canonical_id=match,
                    rationale=rationale,
                )
            )
            continue
        if GENERIC_SCAFFOLD_RE.fullmatch(name):
            item = SourceDefinition(
                source=CORE_METADATA_PATH.relative_to(ROOT).as_posix(),
                source_id=source_id,
                name=name,
                purpose=purpose,
                disposition="generated_generic_scaffold",
                canonical_id=None,
                rationale="No distinct semantic contract beyond a numbered generic module label",
            )
            definitions.append(item)
            core_appended_dispositions.append(item.to_dict())
            continue
        reviewed_generated_alias = GENERATED_CAPABILITY_ALIASES.get(
            (source_id, normalize_name(name))
        )
        if reviewed_generated_alias:
            match = reviewed_generated_alias
        elif source_id == "KA-132" and normalize_name(name) == normalize_name(
            "Meta Orchestrator"
        ):
            match = "KA-Master"
        else:
            match = choose_name_match(
                source_id=source_id,
                name=name,
                canonical_by_name=canonical_by_name,
            )
        if match is not None:
            item = SourceDefinition(
                source=CORE_METADATA_PATH.relative_to(ROOT).as_posix(),
                source_id=source_id,
                name=name,
                purpose=purpose,
                disposition=(
                    "generated_semantic_duplicate_alias"
                    if reviewed_generated_alias
                    else "generated_alias"
                ),
                canonical_id=match,
                rationale=(
                    "Reviewed as adding no distinct contract beyond the canonical capability"
                    if reviewed_generated_alias
                    else "Generated row matches an existing preserved capability"
                ),
            )
            definitions.append(item)
            canonical[match]["scoped_aliases"].append(f"generated-v1:{source_id}")
            core_appended_dispositions.append(item.to_dict())
            continue
        restored_implementation = restored_implementation_module(source_id)
        add_canonical(
            ka_id=source_id,
            name=name,
            purpose=purpose,
            identity_class="preserved_generated_named_capability",
            implementation=restored_implementation,
            source=CORE_METADATA_PATH.relative_to(ROOT).as_posix(),
            source_id=source_id,
            implementation_status=(
                "restored_implementation_requires_qualification"
                if restored_implementation
                else "implementation_required"
            ),
        )
        apply_design_contract(
            source_id,
            row,
            source=CORE_METADATA_PATH.relative_to(ROOT).as_posix(),
            source_id=source_id,
        )
        core_appended_dispositions.append(definitions[-1].to_dict())

    for source_id, (name, canonical_id) in sorted(DELETED_STUB_ALIASES.items()):
        definitions.append(
            SourceDefinition(
                source="git:9db1927d-deleted-generated-stubs",
                source_id=source_id,
                name=name,
                purpose=None,
                disposition="deleted_generated_alias",
                canonical_id=canonical_id,
                rationale="Deleted 16-line generated stub duplicates a preserved canonical capability",
            )
        )
        canonical[canonical_id]["scoped_aliases"].append(f"generated-v1:{source_id}")

    for source_id, row in sorted(sdk.items()):
        name = str(row.get("KA_Name") or row.get("name") or source_id)
        purpose = str(row.get("Purpose") or row.get("purpose") or "") or None
        match = original_canonical_by_id.get(source_id) or choose_name_match(
            source_id=source_id,
            name=name,
            canonical_by_name=canonical_by_name,
        )
        definitions.append(
            SourceDefinition(
                source=SDK_REGISTRY_PATH.relative_to(ROOT).as_posix(),
                source_id=source_id,
                name=name,
                purpose=purpose,
                disposition="generated_sdk_catalog_source",
                canonical_id=match,
                rationale="SDK catalog must be generated from the approved manifest in CP18-B",
            )
        )

    source_definition_rows = [definition.to_dict() for definition in definitions]
    for row in source_definition_rows:
        canonical_id = row.get("canonical_id")
        if canonical_id in canonical:
            canonical[canonical_id]["source_records"].append(row)

    references = scan_references(canonical, implementation_paths)
    for ka_id, entry in canonical.items():
        entry["scoped_aliases"] = sorted(set(entry["scoped_aliases"]))
        entry["source_records"] = sorted(
            entry["source_records"],
            key=lambda item: (item["source"], item["source_id"], item["disposition"]),
        )
        entry["implementation_analysis"] = (
            analyze_implementation(implementation_paths[ka_id])
            if ka_id in implementation_paths
            else {
                "path": None,
                "exists": False,
                "has_run": False,
                "nonblank_noncomment_loc": 0,
                "signals": ["implementation_required"],
            }
        )
        entry.update(references[ka_id])
        if ka_id in production:
            entry["phase6_production_metadata"] = production[ka_id]
        else:
            entry["phase6_production_metadata"] = None
        entry["phase18_status"] = (
            "implementation_required"
            if entry["implementation"] is None
            else "existing_requires_phase18_qualification"
        )

    id_definitions: dict[str, list[dict[str, Any]]] = {}
    for row in source_definition_rows:
        id_definitions.setdefault(row["source_id"], []).append(row)
    conflicts = []
    for source_id, rows in sorted(id_definitions.items()):
        names = sorted({normalize_name(row["name"]) for row in rows if row["name"]})
        canonical_ids = sorted(
            {row["canonical_id"] for row in rows if row.get("canonical_id")}
        )
        if len(names) > 1 or len(canonical_ids) > 1:
            conflicts.append(
                {
                    "source_id": source_id,
                    "names": sorted({row["name"] for row in rows if row["name"]}),
                    "canonical_resolutions": canonical_ids,
                    "status": "classified_by_scoped_alias_or_restored_id",
                    "records": rows,
                }
            )

    unclassified = [
        row
        for row in source_definition_rows
        if not row.get("disposition")
        or (
            row["disposition"] != "generated_generic_scaffold"
            and not row.get("canonical_id")
        )
    ]
    entries = [canonical[key] for key in sorted(canonical)]
    duplicate_candidates = semantic_duplicate_candidates(entries)
    semantic_duplicate_aliases = [
        row
        for row in source_definition_rows
        if row["disposition"] == "generated_semantic_duplicate_alias"
    ]
    unresolved_duplicate_candidates = [
        row
        for row in duplicate_candidates
        if row["disposition"] == "unresolved_semantic_duplicate_candidate"
    ]
    canonical_names: dict[str, list[str]] = {}
    for entry in entries:
        canonical_names.setdefault(normalize_name(entry["name"]), []).append(
            entry["canonical_id"]
        )
    exact_name_collisions = [
        {"normalized_name": name, "canonical_ids": ids}
        for name, ids in sorted(canonical_names.items())
        if len(ids) > 1
    ]
    purpose_index: dict[str, list[str]] = {}
    contract_index: dict[tuple[str, tuple[str, ...], tuple[str, ...]], list[str]] = {}
    for entry in entries:
        normalized_purpose = normalize_name(entry.get("purpose"))
        if normalized_purpose:
            purpose_index.setdefault(normalized_purpose, []).append(
                entry["canonical_id"]
            )
        signature = (
            normalized_purpose,
            tuple(normalize_name(item) for item in entry["input_descriptions"]),
            tuple(normalize_name(item) for item in entry["output_descriptions"]),
        )
        if any(signature):
            contract_index.setdefault(signature, []).append(entry["canonical_id"])
    exact_purpose_collisions = [
        {"normalized_purpose": purpose, "canonical_ids": ids}
        for purpose, ids in sorted(purpose_index.items())
        if len(ids) > 1
    ]
    exact_contract_collisions = [
        {
            "normalized_purpose": signature[0],
            "normalized_inputs": list(signature[1]),
            "normalized_outputs": list(signature[2]),
            "canonical_ids": ids,
        }
        for signature, ids in sorted(contract_index.items())
        if len(ids) > 1
    ]
    implementation_surfaces = classify_implementation_surfaces(implementation_paths)
    integration_surfaces = classify_integration_surfaces(implementation_paths)
    summary = {
        "live_registry_entries": len(live),
        "live_numeric_entries": len(
            [key for key in live if re.fullmatch(r"KA-\d+", key)]
        ),
        "live_layer10_entries": len([key for key in live if key.startswith("L10-KA-")]),
        "live_master_entries": int("KA-Master" in live),
        "unregistered_layer9_implementations": len(L9_DEFINITIONS),
        "original_design_rows": len(original),
        "core_metadata_rows": len(core_rows),
        "sdk_registry_rows": len(sdk),
        "canonical_capability_proposals": len(entries),
        "existing_implementation_proposals": len(
            [entry for entry in entries if entry["implementation"]]
        ),
        "implementation_required_proposals": len(
            [entry for entry in entries if not entry["implementation"]]
        ),
        "phase6_production_enabled": len(
            [
                entry
                for entry in entries
                if (entry.get("phase6_production_metadata") or {}).get(
                    "production_enabled"
                )
            ]
        ),
        "generated_generic_scaffolds": len(
            [
                row
                for row in source_definition_rows
                if row["disposition"] == "generated_generic_scaffold"
            ]
        ),
        "classified_identity_conflicts": len(conflicts),
        "unclassified_source_definitions": len(unclassified),
        "semantic_duplicate_aliases": len(semantic_duplicate_aliases),
        "semantic_duplicate_candidate_pairs": len(duplicate_candidates),
        "reviewed_distinct_candidate_pairs": len(
            [
                row
                for row in duplicate_candidates
                if row["disposition"] == "reviewed_materially_distinct"
            ]
        ),
        "unresolved_semantic_duplicate_candidates": len(
            unresolved_duplicate_candidates
        ),
        "exact_canonical_name_collisions": len(exact_name_collisions),
        "exact_canonical_purpose_collisions": len(exact_purpose_collisions),
        "exact_canonical_contract_collisions": len(exact_contract_collisions),
        "implementation_surfaces": len(implementation_surfaces),
        "unclassified_implementation_surfaces": len(
            [
                row
                for row in implementation_surfaces
                if row["disposition"] == "unclassified_implementation"
            ]
        ),
        "integration_surfaces": len(integration_surfaces),
        "unclassified_integration_surfaces": len(
            [
                row
                for row in integration_surfaces
                if row["disposition"] == "unclassified_integration_surface"
            ]
        ),
        "canonical_with_runtime_execution_call_site": len(
            [entry for entry in entries if entry["execution_call_sites"]]
        ),
        "canonical_with_test_reference": len(
            [entry for entry in entries if entry["test_references"]]
        ),
        "canonical_with_named_test_function": len(
            [entry for entry in entries if entry["named_test_functions"]]
        ),
    }
    inventory = {
        "schema_version": SCHEMA_VERSION,
        "source_input_sha256": source_input_sha256(
            ROOT / row["path"] for row in integration_surfaces
        ),
        "status": "cp18_a_inventory_verified",
        "summary": summary,
        "source_authorities": {
            "current_executable_registry": LIVE_REGISTRY_PATH.relative_to(
                ROOT
            ).as_posix(),
            "original_design_registry": ORIGINAL_REGISTRY_PATH.relative_to(
                ROOT
            ).as_posix(),
            "expanded_historical_metadata": CORE_METADATA_PATH.relative_to(
                ROOT
            ).as_posix(),
            "sdk_registry": SDK_REGISTRY_PATH.relative_to(ROOT).as_posix(),
            "layer9_registry": "backend/knowledge_algorithms/l9/__init__.py",
            "layer10_registry": "backend/knowledge_algorithms/l10/__init__.py",
            "historical_research_context": HISTORICAL_RESEARCH_SOURCES,
        },
        "source_definitions": sorted(
            source_definition_rows,
            key=lambda item: (item["source"], item["source_id"], item["name"]),
        ),
        "identity_conflicts": conflicts,
        "unclassified_source_definitions": unclassified,
        "duplicate_review": {
            "method": (
                "Exact canonical-title uniqueness plus broad token-similarity "
                "candidate review against purpose, input/output, layer, effect, "
                "and decision semantics."
            ),
            "semantic_duplicate_aliases": semantic_duplicate_aliases,
            "reviewed_candidate_pairs": duplicate_candidates,
            "exact_canonical_name_collisions": exact_name_collisions,
            "exact_canonical_purpose_collisions": exact_purpose_collisions,
            "exact_canonical_contract_collisions": exact_contract_collisions,
            "unresolved_candidates": unresolved_duplicate_candidates,
        },
        "implementation_surfaces": implementation_surfaces,
        "integration_surfaces": integration_surfaces,
        "historical_research_context": [
            {
                "source": source,
                "disposition": "historical_research_not_runtime_authority",
            }
            for source in HISTORICAL_RESEARCH_SOURCES
        ],
    }
    crosswalk = {
        "schema_version": CROSSWALK_SCHEMA_VERSION,
        "source_input_sha256": inventory["source_input_sha256"],
        "status": "approved_cp18_a_authority",
        "decision": {
            "date": "2026-07-25",
            "checkpoint": "CP18-A",
            "basis": (
                "Product-owner authorization to proceed with the recommended "
                "lossless path plus the repository verification gate."
            ),
            "scope": (
                "Identity and capability authority only; implementation, schema, "
                "wiring, individual-test, and installed qualification remain CP18-B "
                "through CP18-H work."
            ),
        },
        "policy": {
            "current_runtime_ids": "Retained to avoid breaking current executable semantics.",
            "restored_original_ids": (
                "Original design capabilities that collide with current runtime semantics use "
                "KA-1xxx, where the final three digits preserve the original ID."
            ),
            "historical_aliases": (
                "Conflicting historical IDs are scoped by source generation and are never "
                "accepted as ambiguous public aliases."
            ),
            "generic_scaffolds": (
                "Numbered generic modules without a distinct semantic contract are retained "
                "as historical scaffold records, not claimed as production capabilities."
            ),
            "no_capability_reduction": (
                "Every distinct named design or executable capability remains canonical or "
                "compatibly aliased; runtime behavior is not removed by this proposal."
            ),
            "no_duplicate_kas": (
                "A semantically duplicate definition resolves to one canonical "
                "capability with a scoped compatibility alias; similar titles "
                "remain separate only with a reviewed material contract boundary."
            ),
        },
        "summary": summary,
        "canonical_capabilities": entries,
        "core_appended_dispositions": sorted(
            core_appended_dispositions,
            key=lambda item: (item["source_id"], item["name"]),
        ),
        "duplicate_review": inventory["duplicate_review"],
    }
    return inventory, crosswalk


def json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def csv_text(crosswalk: dict[str, Any]) -> str:
    buffer = io.StringIO(newline="")
    fields = [
        "canonical_id",
        "name",
        "identity_class",
        "implementation",
        "implementation_status",
        "effect_class",
        "runtime_call_sites",
        "test_references",
        "named_test_functions",
        "scoped_aliases",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for entry in crosswalk["canonical_capabilities"]:
        writer.writerow(
            {
                "canonical_id": entry["canonical_id"],
                "name": entry["name"],
                "identity_class": entry["identity_class"],
                "implementation": entry["implementation"] or "",
                "implementation_status": entry["implementation_status"],
                "effect_class": entry["effect_class"],
                "runtime_call_sites": len(entry["execution_call_sites"]),
                "test_references": len(entry["test_references"]),
                "named_test_functions": len(entry["named_test_functions"]),
                "scoped_aliases": ";".join(entry["scoped_aliases"]),
            }
        )
    return buffer.getvalue()


def summary_markdown(inventory: dict[str, Any], crosswalk: dict[str, Any]) -> str:
    summary = inventory["summary"]
    return f"""# Phase 18 KA capability inventory summary

## Identity

| Field | Value |
|---|---|
| Schema | `{inventory["schema_version"]}` |
| Source-input SHA-256 | `{inventory["source_input_sha256"]}` |
| Status | `{inventory["status"]}` |

## Counts

| Measure | Count |
|---|---:|
| Live executable registry entries | {summary["live_registry_entries"]} |
| Unregistered Layer-9 implementations | {summary["unregistered_layer9_implementations"]} |
| Original design rows | {summary["original_design_rows"]} |
| Expanded historical metadata rows | {summary["core_metadata_rows"]} |
| SDK registry rows | {summary["sdk_registry_rows"]} |
| Proposed canonical distinct capabilities | {summary["canonical_capability_proposals"]} |
| Existing implementations requiring Phase 18 qualification | {summary["existing_implementation_proposals"]} |
| Missing implementations to build | {summary["implementation_required_proposals"]} |
| Generated generic scaffolds retained as history, not capabilities | {summary["generated_generic_scaffolds"]} |
| Classified identity conflicts | {summary["classified_identity_conflicts"]} |
| Unclassified source definitions | {summary["unclassified_source_definitions"]} |
| Semantic duplicate definitions collapsed to aliases | {summary["semantic_duplicate_aliases"]} |
| Similar-name candidate pairs reviewed as materially distinct | {summary["reviewed_distinct_candidate_pairs"]} |
| Unresolved semantic duplicate candidates | {summary["unresolved_semantic_duplicate_candidates"]} |
| Exact canonical name collisions | {summary["exact_canonical_name_collisions"]} |
| Exact canonical purpose collisions | {summary["exact_canonical_purpose_collisions"]} |
| Exact canonical purpose/input/output contract collisions | {summary["exact_canonical_contract_collisions"]} |
| Classified implementation surfaces | {summary["implementation_surfaces"]} |
| Unclassified implementation surfaces | {summary["unclassified_implementation_surfaces"]} |
| Classified integration/API/SDK/UI surfaces | {summary["integration_surfaces"]} |
| Unclassified integration/API/SDK/UI surfaces | {summary["unclassified_integration_surfaces"]} |
| Canonical capabilities with literal runtime execution call sites | {summary["canonical_with_runtime_execution_call_site"]} |
| Canonical capabilities with any test reference | {summary["canonical_with_test_reference"]} |
| Canonical capabilities with an individually named test function | {summary["canonical_with_named_test_function"]} |

## Proposed identity policy

- Keep current executable IDs stable so existing runtime semantics are not
  silently changed.
- Restore original design capabilities displaced by current numeric semantics
  into `KA-1xxx` IDs that retain the historical final three digits.
- Preserve conflicting historical IDs only as generation-scoped aliases.
- Preserve every distinct named design/executable capability.
- Collapse a true semantic duplicate to one canonical KA plus a scoped
  compatibility alias; retain similar names separately only when their inputs,
  outputs, layer, effect, or decision semantics materially differ.
- Retain numbered generic scaffold rows as historical evidence; do not claim
  them as distinct production algorithms without a semantic contract.

## CP18-A disposition

The no-loss and identity decisions are `{crosswalk["status"]}` and enforced by
`scripts/verify_ka_capability_inventory.py`. Approval covers the capability
authority only. Implementation, wiring, individual-test, and installed
acceptance counts remain the work queue for CP18-B through CP18-H.
"""


def output_payloads(output_dir: Path) -> dict[Path, str]:
    inventory, crosswalk = build_inventory()
    return {
        output_dir / "ka-capability-inventory.json": json_text(inventory),
        output_dir / "ka-capability-crosswalk.json": json_text(crosswalk),
        output_dir / "ka-capability-crosswalk.csv": csv_text(crosswalk),
        output_dir / "ka-capability-inventory-summary.md": summary_markdown(
            inventory, crosswalk
        ),
    }


def write_or_check(output_dir: Path, *, check: bool) -> int:
    payloads = output_payloads(output_dir)
    changed = []
    for path, content in payloads.items():
        existing = path.read_text(encoding="utf-8") if path.exists() else None
        if existing != content:
            changed.append(path)
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="\n")
    if check and changed:
        for path in changed:
            print(f"STALE {path.relative_to(ROOT)}")
        return 1
    verb = "verified" if check else "generated"
    print(
        f"KA capability inventory {verb}: files={len(payloads)} changed={len(changed)}"
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    return write_or_check(output_dir.resolve(), check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
