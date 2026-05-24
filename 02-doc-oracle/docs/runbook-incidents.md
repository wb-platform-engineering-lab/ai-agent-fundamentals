# Runbook: Incident Response

## Severity levels

| Level | Definition | Response time | Example |
|---|---|---|---|
| P0 | Complete outage, all users affected | 5 minutes | Site down, database unreachable |
| P1 | Major functionality broken, >30% users | 15 minutes | Login failing, payment errors |
| P2 | Degraded performance, <30% users | 1 hour | Slow search, intermittent errors |
| P3 | Minor issue, workaround exists | Next business day | UI glitch, non-critical feature broken |

## P0/P1 response procedure

1. **Acknowledge** the alert in PagerDuty (stops escalation)
2. **Join** the incident Slack channel `#incident-<date>`
3. **Declare** incident commander (usually the first responder)
4. **Assess** impact: how many users? which services? since when?
5. **Communicate** status to `#status` channel every 10 minutes
6. **Mitigate** before investigating: rollback if recent deploy, scale if resource issue
7. **Resolve** and close the incident
8. **Post-mortem** within 48 hours for P0/P1

## Common mitigations

### High error rate
```bash
# Check which pods are failing
kubectl get pods -n production | grep -v Running

# Check recent events
kubectl get events -n production --sort-by=.lastTimestamp | tail -20

# Rollback if recent deploy caused it
kubectl rollout undo deployment/<name> -n production
```

### High latency
```bash
# Check resource usage
kubectl top pods -n production
kubectl top nodes

# Scale up if CPU/memory bound
kubectl scale deployment/<name> --replicas=6 -n production
```

### Database connection errors
```bash
# Check connection pool
kubectl exec -it <pod> -n production -- psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Restart the service (last resort)
kubectl rollout restart deployment/<name> -n production
```

## Post-mortem template

Every P0 and P1 requires a blameless post-mortem within 48 hours:

- **What happened** (timeline, impact)
- **Root cause** (the actual cause, not the symptom)
- **What went well** (what helped us resolve faster)
- **What went poorly** (what slowed us down)
- **Action items** (specific, with owner and due date)
