# Sentry Alert Verification

Use this guide to validate that Sentry alerts reach the correct team or on-call rotation.

---

## ✅ Prerequisites

- `SENTRY_DSN` configured in `.env`
- Sentry project alert rules configured (email, Slack, PagerDuty, OpsGenie, etc.)

---

## ✅ Send a Test Event

Run the helper script to send a warning-level test event:

```bash
python scripts/send_sentry_test_event.py \
  --message "DataLogicEngine alert validation" \
  --tag service=ukg \
  --tag environment=production
```

---

## ✅ Verification Checklist

- [ ] Event appears in the Sentry project.
- [ ] Alert rule triggers correctly.
- [ ] Notification reaches the expected team/channel.
- [ ] Incident response runbook is updated with the Sentry link.
