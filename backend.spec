# -*- mode: python ; coding: utf-8 -*-

import os
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

block_cipher = None

# The gateway imports `ukg_sdk` (provider HTTP clients, overlay, KA executor) from
# the in-repo SDK at sdk/UKG_Python_SDK via a runtime sys.path insert. That path
# does not exist in the frozen app, so the package must be analyzed and collected
# here. Put it on sys.path so collect_submodules/collect_data_files resolve it.
_SDK_PATH = os.path.abspath(os.path.join('sdk', 'UKG_Python_SDK'))
if _SDK_PATH not in sys.path:
    sys.path.insert(0, _SDK_PATH)


def runtime_submodule(name):
    """Exclude package test suites from dynamic runtime collection."""
    return not any(part.lower() in {"test", "tests", "testing"} for part in name.split("."))


def chroma_runtime_submodule(name):
    """Keep Chroma client internals while excluding server/developer entry points."""
    return runtime_submodule(name) and not name.startswith(("chromadb.cli", "chromadb.server"))


def runtime_data(entries):
    """Remove test/cache/source-only package data from the frozen payload."""
    output = []
    for entry in entries:
        destination = entry[0].replace("\\", "/")
        parts = {part.lower() for part in destination.split("/")}
        if parts.intersection({"test", "tests", "testing", "__pycache__"}):
            continue
        if destination.endswith((".py", ".pyc")) and not destination.startswith("migrations/"):
            continue
        output.append(entry)
    return output

a = Analysis(
    ['main.py'],
    pathex=[_SDK_PATH],
    binaries=[],
    datas=[
        ('config/product-versions.json', 'config'),
        ('config/provider_manifest.v1.json', 'config'),
        ('deploy/internal-data-plane.candidate-lock.json', 'deploy'),
        ('migrations', 'migrations'),

        ('core/data', 'core/data'),
        ('backend/dsqp/templates', 'backend/dsqp/templates'),
        ('backend/knowledge_algorithms/config', 'backend/knowledge_algorithms/config'),
        ('backend/knowledge_algorithms/ka_registry.yaml', 'backend/knowledge_algorithms'),
        ('backend/knowledge_algorithms/ka_manifest.v1.generated.json', 'backend/knowledge_algorithms'),
        ('core/persona/quad/config', 'core/persona/quad/config'),
        ('docs/evaluation', 'docs/evaluation'),
    ] + collect_data_files('rfc3987_syntax') + collect_data_files('ukg_sdk') + collect_data_files('chromadb', excludes=['test/**', 'tests/**', '**/test/**', '**/tests/**']) + collect_data_files('llama_index', excludes=['test/**', 'tests/**', '**/test/**', '**/tests/**']) + copy_metadata('tiktoken'),
    hiddenimports=[
        # Alembic loads migrations/env.py dynamically after freeze analysis;
        # keep its standard-library configuration module in the executable.
        'logging.config',
        'flask',
        'flask_sqlalchemy',
        'flask_migrate',
        'flask_cors',
        'psycopg2',
        'redis',
        'win32api',
        'win32security',
        'win32crypt',
        'langgraph',
        'langchain_core',
        'langsmith',
        'neo4j',
        'networkx',
        'pydantic',
        'pydantic_core',
        'sqlalchemy.ext.baked',
        'celery.fixups',
        'celery.fixups.django',
        'kombu.transport.redis',
        'eventlet',
        'engineio.async_drivers.threading',
        'simple_websocket',
        'wsproto',
        'h11',
        'dns',
        'cv2',
        'web3',
        'eth_account',
        'reportlab',
        'pypdf',
        'docx',
        'openai',
        'tiktoken',
        # tiktoken registers encodings (e.g. cl100k_base) through the tiktoken_ext
        # namespace-package plugin mechanism, which PyInstaller does not auto-detect.
        # Without these the frozen app raises "Unknown encoding cl100k_base".
        'tiktoken_ext',
        'tiktoken_ext.openai_public',
        'langchain_openai',
        'langchain_community',
        'dotenv',
    ] + collect_submodules('chromadb', filter=chroma_runtime_submodule) + collect_submodules('ukg_sdk', filter=runtime_submodule) + collect_submodules('backend.desktop', filter=runtime_submodule) + collect_submodules('backend.ingestion', filter=runtime_submodule) + collect_submodules('backend.dsqp', filter=runtime_submodule) + collect_submodules('backend.dmrf', filter=runtime_submodule) + collect_submodules('backend.knowledge_algorithms', filter=runtime_submodule) + collect_submodules('backend.local_model_acceleration', filter=runtime_submodule) + collect_submodules('core.self_evolving', filter=runtime_submodule),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # The app uses Chroma only as a supervised HTTP client and always supplies
    # embedding_function=None. Chroma's generic embedding-function registry has
    # optional imports for this entire local-ML stack; do not freeze those unused
    # implementations into the production desktop payload.
    excludes=[
        'pytest',
        '_pytest',
        'sentence_transformers',
        'transformers',
        'torch',
        'sklearn',
        'onnxruntime',
        'tokenizers',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
a.datas = runtime_data(a.datas)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DataLogic_Backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='build/backend-version-info.txt',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='DataLogic_Backend',
)

