# -*- mode: python ; coding: utf-8 -*-

import os
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules, copy_metadata

block_cipher = None

# The gateway imports `ukg_sdk` (provider HTTP clients, overlay, KA executor) from
# the in-repo SDK at sdk/UKG_Python_SDK via a runtime sys.path insert. That path
# does not exist in the frozen app, so the package must be analyzed and collected
# here. Put it on sys.path so collect_submodules/collect_data_files resolve it.
_SDK_PATH = os.path.abspath(os.path.join('sdk', 'UKG_Python_SDK'))
if _SDK_PATH not in sys.path:
    sys.path.insert(0, _SDK_PATH)

a = Analysis(
    ['main.py'],
    pathex=[_SDK_PATH],
    binaries=collect_dynamic_libs('onnxruntime') + collect_dynamic_libs('tokenizers'),
    datas=[
        ('backend', 'backend'),
        ('core', 'core'),
        ('config/product-versions.json', 'config'),
        # static/ is produced by the frontend build; skip when absent (CI packaging smoke).
        *([('static', 'static')] if os.path.isdir('static') else []),

        ('extensions.py', '.'),
        ('models.py', '.'),
        ('core/data', 'core/data'),
        ('backend/dsqp/templates', 'backend/dsqp/templates'),
    ] + collect_data_files('rfc3987_syntax') + collect_data_files('ukg_sdk') + collect_data_files('chromadb') + collect_data_files('llama_index') + collect_data_files('onnxruntime') + collect_data_files('tokenizers') + copy_metadata('tiktoken') + copy_metadata('onnxruntime') + copy_metadata('tokenizers'),
    hiddenimports=[
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
        'pydantic_settings',
        'sqlalchemy.ext.baked',
        'celery.fixups',
        'celery.fixups.flask',
        'celery.fixups.django',
        'kombu.transport.redis',
        'eventlet',
        'eventlet.hubs.epolls',
        'eventlet.hubs.kqueue',
        'eventlet.hubs.selects',
        'engineio.async_drivers.threading',
        'simple_websocket',
        'wsproto',
        'h11',
        'dns',
        'pkg_resources.py2_warn',
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
        'sentence_transformers',
        'transformers',
        'torch',
        'dotenv',
        'onnxruntime',
        'tokenizers',
    ] + collect_submodules('chromadb') + collect_submodules('onnxruntime') + collect_submodules('tokenizers') + collect_submodules('sentence_transformers') + collect_submodules('ukg_sdk') + collect_submodules('backend.desktop') + collect_submodules('backend.ingestion') + collect_submodules('backend.dsqp') + collect_submodules('backend.dmrf') + collect_submodules('backend.knowledge_algorithms.l10') + collect_submodules('backend.local_model_acceleration') + collect_submodules('core.self_evolving'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
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

