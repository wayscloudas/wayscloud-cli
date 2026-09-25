# WAYSCloud CLI

Command-line interface for [WAYSCloud](https://wayscloud.services). Built on the [Python SDK](https://pypi.org/project/wayscloud/).

## Installation

```bash
pip install wayscloud-cli
```

Version 0.5.0 adds Managed Kubernetes (`cloud k8s …`) and requires SDK `wayscloud>=0.4.0`.

## Authentication

```bash
cloud login --token wayscloud_pat_...
cloud whoami
cloud logout
```

Priority: `--token` flag > `WAYSCLOUD_TOKEN` env var > `~/.wayscloud/credentials` file.

## Commands

### VPS

```bash
cloud vps list
cloud vps create --hostname web01 --plan vps-medium --region no --os ubuntu-24.04
cloud vps info <id>
cloud vps delete <id> --confirm
cloud vps start <id>
cloud vps stop <id>
cloud vps plans
cloud vps os-templates
```

### DNS

```bash
cloud dns zones
cloud dns zones-create example.com
cloud dns records example.com
cloud dns records-create example.com --type A --name www --value 192.0.2.1
cloud dns records-delete example.com <record-id> --confirm
```

### Database

```bash
cloud db list
cloud db create mydb --type postgresql --tier standard
cloud db info postgresql mydb
cloud db delete postgresql mydb --confirm
```

### Redis

```bash
cloud redis list
cloud redis create myredis --plan redis-starter --region no
cloud redis info <id>
cloud redis delete <id> --confirm
cloud redis plans
```

### Storage

```bash
cloud storage buckets
cloud storage buckets-create my-bucket
cloud storage buckets-delete my-bucket --confirm
cloud storage keys my-bucket
cloud storage keys-create my-bucket --name ci
```

### Apps

```bash
cloud app list
cloud app create my-app --plan app-basic --region eu
cloud app deploy <id> --image ghcr.io/org/app:latest
cloud app start <id>
cloud app stop <id>
cloud app delete <id> --confirm
```

### Kubernetes

```bash
cloud k8s plans --kind node
cloud k8s list
cloud k8s create shop --pool k8s-node-2c4g:2 --plan k8s-cluster-dev --region no --wait
cloud k8s info <cluster-id>
cloud k8s kubeconfig <cluster-id> -o ~/.kube/shop.yaml   # written with mode 0600
cloud k8s scale <cluster-id> default 4
cloud k8s add-pool <cluster-id> batch --plan k8s-node-4c16g --count 2 \
  --label role=worker --taint dedicated=gpu:NoSchedule --ssh-key-id <key-id>
cloud k8s delete-pool <cluster-id> batch
cloud k8s api-access <cluster-id> --cidr 203.0.113.0/24
cloud k8s ip-allocate <cluster-id>
cloud k8s ip-release <cluster-id> <address>
cloud k8s ptr <cluster-id> <address> mail.example.com
cloud k8s backups <cluster-id>
cloud k8s backup <cluster-id>
cloud k8s restore <cluster-id> <backup-id> -n shop
cloud k8s upgrade <cluster-id>            # list available versions
cloud k8s upgrade <cluster-id> 1.34       # upgrade to a version
cloud k8s delete <cluster-id> --confirm-name shop --wait
```

### IoT

```bash
cloud iot devices
cloud iot devices-create --device-id sensor-01 --name "Temperature Sensor"
cloud iot devices-info <device-id>
cloud iot devices-delete <device-id> --confirm
cloud iot groups
cloud iot groups-create --name "Floor 2"
```

### Impact

```bash
cloud impact forest create "My forest"
cloud impact forest status --visualize emoji
cloud impact tree grow --count 10 --idempotency-key <key>
cloud impact commitments list
```

### Shell

```bash
cloud shell connect
```

## Output formats

```bash
# Default: formatted tables
cloud vps list

# JSON (for scripting)
cloud vps list --json
```

## Requirements

- Python 3.9+
- [wayscloud](https://pypi.org/project/wayscloud/) SDK `>=0.4.0` (installed automatically; the Kubernetes commands need a release that exposes `client.kubernetes`)

## Documentation

Full reference: [docs.wayscloud.services/cli](https://docs.wayscloud.services/cli)

## License

MIT
