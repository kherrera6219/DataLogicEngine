# Local health monitoring (engineering only)

DataLogicEngine 4.4.5 is `release_blocked`. It is installed Windows software,
not a public web service. The historical instructions for UptimeRobot, Pingdom,
public DNS, and third-party alert delivery are **not approved** for this
product. Do not expose a health endpoint to the internet or configure a
third-party monitor to poll it.

For engineering qualification on the owner-controlled machine, use the
installation-bound loopback API and the desktop diagnostics surface:

- `GET /ready` reports whether mandatory startup gates have passed.
- `GET /health` reports safe aggregate health. A live process can be not ready.
- Verify that the listener belongs to the launched package process tree before
  treating either response as evidence for that installation.

The installed candidate must still pass the exact-artifact health, readiness,
recovery, and sustained-operation gates in
[`docs/ADMINISTRATOR_OPERATIONS_GUIDE.md`](../docs/ADMINISTRATOR_OPERATIONS_GUIDE.md),
[`docs/VERIFICATION_VALIDATION_REPORT.md`](../docs/VERIFICATION_VALIDATION_REPORT.md),
and [`docs/RELEASE_READINESS_RECORD.md`](../docs/RELEASE_READINESS_RECORD.md).
Do not turn a local development probe into a production or release claim.
