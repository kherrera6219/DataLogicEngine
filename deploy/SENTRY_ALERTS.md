# Sentry alert guide — retired

**Status (2026-09-27): unsupported historical deployment guidance.**

DataLogicEngine is owner-operated installed software. There is no approved
Sentry DSN, crash-reporting or telemetry egress, or third-party alert
destination in the current product boundary. Do not configure Sentry, send
test events, or treat a remote alert receipt as release evidence.

Use the desktop's local diagnostics and the owner-controlled support-bundle
process described in
[`docs/ADMINISTRATOR_OPERATIONS_GUIDE.md`](../docs/ADMINISTRATOR_OPERATIONS_GUIDE.md)
and [`docs/TROUBLESHOOTING_SUPPORT_GUIDE.md`](../docs/TROUBLESHOOTING_SUPPORT_GUIDE.md).
Any proposal to add remote telemetry or alerting requires an explicit owner
decision and a revised data-handling/egress review before implementation.
