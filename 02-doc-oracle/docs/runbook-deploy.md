# Runbook: Deployment Procedures

## Standard deploy process

All production deployments go through ArgoCD. A merge to `main` triggers an automatic sync within 2 minutes.

To trigger a manual sync:
```bash
argocd app sync my-app --namespace production
```

Monitor the sync status:
```bash
argocd app get my-app
kubectl rollout status deployment/my-app -n production
```

## Rollback procedure

If a deploy causes issues, rollback immediately. Do not investigate in production — rollback first, investigate after.

### Option 1: ArgoCD rollback (recommended)
```bash
argocd app history my-app           # get the revision number
argocd app rollback my-app <rev>    # rollback to that revision
```

### Option 2: kubectl rollback
```bash
kubectl rollout undo deployment/my-app -n production
kubectl rollout status deployment/my-app -n production
```

### Option 3: Helm rollback
```bash
helm history my-app -n production   # list revisions
helm rollback my-app <revision> -n production
```

## Canary deploys

For high-risk changes, use Argo Rollouts:

```bash
kubectl argo rollouts get rollout my-app -n production
kubectl argo rollouts promote my-app -n production  # advance to next step
kubectl argo rollouts abort my-app -n production    # abort and rollback
```

## Freeze windows

No deployments on:
- Friday 18:00 → Monday 10:00
- Release freeze periods (announced in #deployments Slack channel)

If an emergency deploy is needed during a freeze, get approval from the on-call manager before proceeding.
