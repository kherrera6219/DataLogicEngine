"""Find orphaned backend modules — the "TraceLogger pattern".

A26 removed ``backend/tracing/logger.py`` (TraceLogger): a fully-built helper
with **zero production callers** because the live path open-codes the same work
inline. This scanner systematizes that heuristic so the shape is caught by
construction instead of by luck.

For every module under ``backend/`` it extracts the public top-level symbols
(classes + functions not prefixed ``_``) via ``ast`` and asks: does any
*production* file (not the module itself, not under ``tests/``) reference the
module's dotted path or any of its public symbols?

  - referenced in production            -> live (not reported)
  - referenced only by tests            -> TEST-ONLY (dead production code)
  - referenced nowhere                  -> ORPHAN (no caller at all)

It is deliberately conservative: reference detection uses substring matching,
which OVER-counts references and therefore UNDER-reports orphans. A hit here is
a *candidate* for confirm-before-cut, never a verdict. Known dynamic-entry
shapes are annotated, not auto-excluded, so the reader can judge:

  - ``[bp]``   defines a Flask Blueprint (registered dynamically; if the bp
               symbol is referenced by an app factory it will not be flagged —
               a flagged ``[bp]`` is an unregistered = dead route module)
  - ``[main]`` has an ``if __name__ == "__main__"`` CLI entry point
  - ``[pkg]``  package ``__init__`` (re-export surface; skipped from flagging)

Usage:  python scripts/find_orphaned_modules.py [root]   (default root: backend)
"""
import ast
import os
import re
import sys

SCAN_ROOT = sys.argv[1] if len(sys.argv) > 1 else "backend"

# Directories never searched for references or scanned for modules.
EXCLUDE_DIRS = {
    "__pycache__", ".git", ".venv", ".venv311", "node_modules", "dist",
    "dist-smoke", "htmlcov", "build", ".claude", ".pytest_cache", "coverage",
}

# This scanner's own output report and source must never enter the corpora —
# the report lists candidate paths (which would self-poison the next run as
# "references"), and the source docstring names example modules.
SELF_EXCLUDE = {"orphaned_modules.txt", "scripts/find_orphaned_modules.py",
                "core_backend_inversions.txt"}


def _iter_py_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for name in filenames:
            if name.endswith(".py"):
                yield os.path.join(dirpath, name).replace("\\", "/")


def _is_test_path(path):
    return "/tests/" in path or path.startswith("tests/") or "/test_" in path \
        or os.path.basename(path).startswith("test_")


# --- Build the production + test reference corpora once -----------------------
prod_corpus = {}   # path -> text (production .py only)
test_corpus = {}   # path -> text (test .py only)
# Registry/spec/doc references use dotted/slashed paths, not Python imports.
aux_corpus = {}    # path -> text (.yaml/.yml/.json/.spec/.txt/.md/.cfg/.toml)

for dirpath, dirnames, filenames in os.walk("."):
    dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
    for name in filenames:
        path = os.path.join(dirpath, name).replace("\\", "/").lstrip("./")
        if path in SELF_EXCLUDE:
            continue
        ext = os.path.splitext(name)[1]
        try:
            if ext == ".py":
                text = open(path, encoding="utf-8", errors="ignore").read()
                (test_corpus if _is_test_path(path) else prod_corpus)[path] = text
            elif ext in {".yaml", ".yml", ".json", ".spec", ".txt", ".md",
                         ".cfg", ".toml", ".ini"}:
                aux_corpus[path] = open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue


def _public_symbols(tree):
    syms = []
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                syms.append(node.name)
        # Module-level Flask Blueprint singletons are referenced by name in the
        # app factory (``from .x import foo_bp``) rather than as a def, so they
        # would otherwise be missed and the (registered) route module flagged.
        elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            func = node.value.func
            callee = getattr(func, "id", None) or getattr(func, "attr", None)
            if callee == "Blueprint":
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name) and not tgt.id.startswith("_"):
                        syms.append(tgt.id)
    return syms


def _has_main(tree):
    for node in tree.body:
        if isinstance(node, ast.If):
            test = node.test
            if (isinstance(test, ast.Compare) and isinstance(test.left, ast.Name)
                    and test.left.id == "__main__"):
                return True
            # `if __name__ == "__main__":`
            src = ast.dump(test)
            if "__main__" in src and "__name__" in src:
                return True
    return False


def _defines_blueprint(text):
    return "Blueprint(" in text


def _word_in(symbol, text):
    return re.search(r"\b" + re.escape(symbol) + r"\b", text) is not None


def _referenced_in(corpus, exclude_path, dotted, slashed, symbols):
    for path, text in corpus.items():
        if path == exclude_path:
            continue
        if dotted in text or slashed in text or slashed.replace("/", "\\") in text:
            return True
        for sym in symbols:
            if _word_in(sym, text):
                return True
    return False


orphans = []   # (kind, path, tags, symbols)
for path in sorted(_iter_py_files(SCAN_ROOT)):
    base = os.path.basename(path)
    rel = path  # already repo-relative, forward-slashed
    try:
        tree = ast.parse(open(path, encoding="utf-8", errors="ignore").read())
    except SyntaxError:
        continue

    symbols = _public_symbols(tree)
    text = prod_corpus.get(path, "")

    tags = []
    if base == "__init__.py":
        tags.append("pkg")
    if _defines_blueprint(text):
        tags.append("bp")
    if _has_main(tree):
        tags.append("main")

    # Package __init__ files are re-export surfaces; skip flagging.
    if base == "__init__.py":
        continue
    # A module with no public symbols and no dynamic-entry tag carries no API to
    # orphan; skip to avoid noise.
    if not symbols and not tags:
        continue

    dotted = rel[:-3].replace("/", ".")          # backend/x/y.py -> backend.x.y
    slashed = rel[:-3]                            # backend/x/y

    in_prod = _referenced_in(prod_corpus, path, dotted, slashed, symbols)
    if in_prod:
        continue
    # Module path may be referenced by a registry/spec/doc (KA registry, .spec
    # collect, etc.) even with no Python importer — treat that as "wired".
    if any(dotted in t or slashed in t or slashed.replace("/", "\\") in t
           for t in aux_corpus.values()):
        continue

    in_test = _referenced_in(test_corpus, path, dotted, slashed, symbols)
    kind = "TEST-ONLY" if in_test else "ORPHAN"
    orphans.append((kind, rel, tags, symbols))


lines = []
orphans.sort(key=lambda r: (r[0] != "ORPHAN", r[1]))  # ORPHANs first
for kind, path, tags, symbols in orphans:
    tagstr = "".join(f"[{t}]" for t in tags)
    symstr = ", ".join(symbols[:6]) + (" ..." if len(symbols) > 6 else "")
    lines.append(f"{kind:9} {path} {tagstr}")
    if symstr:
        lines.append(f"          symbols: {symstr}")

n_orphan = sum(1 for o in orphans if o[0] == "ORPHAN")
n_test = sum(1 for o in orphans if o[0] == "TEST-ONLY")
lines.append("")
lines.append(f"TOTAL candidates under {SCAN_ROOT}/: {len(orphans)} "
             f"({n_orphan} ORPHAN, {n_test} TEST-ONLY). "
             f"Candidates only — verify (confirm-before-cut) before any change.")

report = "\n".join(lines)
with open("orphaned_modules.txt", "w", encoding="utf-8") as fh:
    fh.write(report + "\n")
print(report)
