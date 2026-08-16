# Post-QC first rebuild runtime blocker

## Candidate identity

| Item | Result |
|---|---|
| Source commit | `2d1664560215befed4df29a24506f282dda6319e` |
| Installer | `DataLogicEngine Setup 4.4.0.exe` |
| Size | 358,856,090 bytes |
| SHA-256 | `ed0d7f8f14e61294f5d09265d5539335fa34ab732d3a98c9d4b8d0a74650c881` |
| Signature | `NotSigned` |

The clean backend, Next/Electron, and NSIS build completed. Installer integrity,
NSIS governance, packaged-resource verification, and the existing process-alive
portable smoke passed. This artifact is an engineering diagnostic candidate,
not a release artifact.

## Runtime result

The exact unpacked desktop shell launched, but `/ready` never opened on port
5000 during a 240-second poll. The fresh desktop runtime log showed the frozen
backend exiting during `runtime_lock`:

```text
RuntimeError: installation_version_mismatch
RuntimeError: startup_failed:runtime_lock
Backend process exited with code 1
```

The retained runtime identity was product `DataLogicEngine`, version `4.3.0`.
The 4.4.0 version authority allowed only `0.1.1` as an upgrade source, so the
existing 4.3.0 engineering candidate could not enter the fail-closed migration
path. The Electron shell remained alive, which also proves that the existing
portable packaging smoke is not a readiness assertion.

## Installer lifecycle observation

One isolated silent lifecycle attempt returned exit code 0 from both install and
uninstall, but the installed executable remained beyond the script's 120-second
cleanup threshold and disappeared shortly afterward. A retry was not conclusive
because Windows canceled the elevated process through UAC. Per-machine
installed acceptance therefore remains open; it is not recorded as a product
install failure or a pass.

## Remediation

Commit `16faaeb4` adds `4.3.0` to the authoritative supported upgrade sources and
adds a lifecycle regression proving that the retained identity advances to
4.4.0 only after the managed migration gate succeeds. The focused product-
version, runtime-lifecycle, and migration suite passed 34 tests. A new clean
artifact must be built and all artifact-bound evidence must use its new hash.

Production/public release remains **NO-GO**. This first artifact must not be
signed, distributed, or used to close CP19-M.
