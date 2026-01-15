# Uptime Monitoring Setup

This guide provides a lightweight setup checklist for uptime monitoring against the DataLogicEngine API.

---

## ✅ Recommended Health Endpoint

Use the REST API health endpoint:

```
GET /api/v1/health
```

**Expected Response**

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "service": "UKG REST API",
    "version": "1.0.0"
  }
}
```

---

## ✅ Example Monitors

### UptimeRobot
- **Monitor Type**: HTTP(s)
- **URL**: `https://<your-domain>/api/v1/health`
- **Keyword** (optional): `"status": "healthy"`
- **Check Interval**: 1–5 minutes

### Pingdom
- **Check Type**: HTTP
- **URL**: `https://<your-domain>/api/v1/health`
- **Response Time Threshold**: 2s

---

## ✅ Alerting Recommendations

- Route alerts to Slack, PagerDuty, or OpsGenie.
- Configure at least **one on-call escalation** target.
- Add a "maintenance window" during deploys.

---

## ✅ Verification Checklist

- [ ] Health endpoint responds with HTTP 200.
- [ ] Monitor transitions to **UP** state.
- [ ] Alert is delivered to primary on-call destination.
