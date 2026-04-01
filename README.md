# WAYSCloud CLI

Command-line interface for [WAYSCloud](https://wayscloud.services). Built on the [Python SDK](https://pypi.org/project/wayscloud/).

## Installation

```bash
pip install wayscloud-cli
```

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
cloud storage credentials
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

### IoT

```bash
cloud iot devices
cloud iot devices-create --device-id sensor-01 --name "Temperature Sensor"
cloud iot devices-info <device-id>
cloud iot devices-delete <device-id> --confirm
cloud iot groups
cloud iot groups-create --name "Floor 2"
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
- wayscloud (SDK)

## Documentation

Full reference: [docs.wayscloud.services/cli](https://docs.wayscloud.services/cli)

## License

MIT
