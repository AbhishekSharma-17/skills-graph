# Grafana — Overview & Setup

> Source: [grafana.com/docs/grafana/latest](https://grafana.com/docs/grafana/latest/) — Grafana 13.0

## What Is Grafana

Grafana is an open-source observability and data visualization platform. It lets you query, visualize, alert on, and explore metrics, logs, and traces from any storage backend. With 73K+ GitHub stars and 35M+ users, it is the de facto standard for monitoring dashboards.

## Core Capabilities

- **Multi-source queries** — Connect 170+ data sources (Prometheus, Loki, Elasticsearch, PostgreSQL, CloudWatch, etc.)
- **Rich visualizations** — 20+ panel types (time series, gauge, stat, table, heatmap, geomap, etc.)
- **Alerting** — Unified alerting across data sources with routing, silences, and escalation
- **Explore** — Ad-hoc querying interface for debugging and investigation
- **Provisioning** — Define dashboards, data sources, and alerts as code (YAML, Terraform, API)
- **Plugin ecosystem** — Extend with community and enterprise plugins from the Grafana Marketplace

## Editions

| Edition | License | Use Case |
|---------|---------|----------|
| **Grafana OSS** | AGPL-3.0 | Self-hosted, full core features |
| **Grafana Enterprise** | Commercial | Self-hosted + enterprise plugins, RBAC, reporting, SLA |
| **Grafana Cloud** | SaaS | Managed Grafana + Prometheus (Mimir) + Loki + Tempo |

## Architecture

```
┌─────────────────────────────────────────────┐
│                  Grafana UI                  │
│   Dashboards │ Explore │ Alerting │ Admin   │
├─────────────────────────────────────────────┤
│              Query Engine                    │
│   PromQL │ LogQL │ SQL │ TraceQL │ Custom   │
├─────────────────────────────────────────────┤
│            Data Source Layer                 │
│  Prometheus │ Loki │ Tempo │ Elasticsearch  │
│  PostgreSQL │ MySQL │ CloudWatch │ ...      │
└──────────────┬──────────────────────────────┘
               │
    ┌──────────┴──────────┐
    │  grafana.db (SQLite) │  ← dashboards, users, orgs, alerts
    │  or PostgreSQL/MySQL │
    └─────────────────────┘
```

Grafana itself does not store metrics/logs. It connects to external backends and renders their data. Dashboard definitions, users, and alert state are stored in an embedded SQLite database (or an external PostgreSQL/MySQL instance for HA).

## Installation

### Docker (Recommended)

```bash
docker run -d \
  --name grafana \
  -p 3000:3000 \
  -v grafana-storage:/var/lib/grafana \
  grafana/grafana-oss:13.0.2
```

### Docker Compose

```yaml
services:
  grafana:
    image: grafana/grafana-oss:13.0.2
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-storage:/var/lib/grafana
      - ./provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    restart: unless-stopped

volumes:
  grafana-storage:
```

### Package Managers

```bash
# macOS
brew install grafana
brew services start grafana

# Debian/Ubuntu
sudo apt-get install -y adduser libfontconfig1 musl
wget https://dl.grafana.com/oss/release/grafana_13.0.2_amd64.deb
sudo dpkg -i grafana_13.0.2_amd64.deb
sudo systemctl daemon-reload
sudo systemctl start grafana-server
sudo systemctl enable grafana-server

# RHEL/Fedora
sudo yum install -y https://dl.grafana.com/oss/release/grafana-13.0.2-1.x86_64.rpm
sudo systemctl start grafana-server
```

### First Login

1. Navigate to `http://localhost:3000`
2. Log in with `admin` / `admin`
3. Change the admin password when prompted
4. Add your first data source under **Connections → Data sources**

## Configuration

Grafana is configured via `grafana.ini` (or environment variables in Docker).

### Key Configuration Sections

```ini
[server]
http_port = 3000
root_url = https://grafana.example.com

[database]
type = sqlite3            # or postgres, mysql
path = grafana.db

[security]
admin_user = admin
admin_password = admin
secret_key = SW2YcwTIb9zpOOhoPsMm

[auth]
disable_login_form = false

[auth.anonymous]
enabled = false

[smtp]
enabled = true
host = smtp.example.com:587
user = grafana@example.com
password = secret
from_address = grafana@example.com

[alerting]
enabled = true

[unified_alerting]
enabled = true

[log]
mode = console file
level = info
```

### Environment Variable Override

Every `grafana.ini` setting can be overridden with an environment variable using the pattern:

```
GF_<SECTION>_<KEY>=value
```

Examples:
```bash
GF_SERVER_HTTP_PORT=3000
GF_SECURITY_ADMIN_PASSWORD=mysecretpassword
GF_DATABASE_TYPE=postgres
GF_DATABASE_HOST=db:5432
GF_SMTP_ENABLED=true
GF_AUTH_ANONYMOUS_ENABLED=false
GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-piechart-panel
```

### Data Persistence

| Path | Purpose |
|------|---------|
| `/var/lib/grafana` | Database, plugins, file-based sessions |
| `/etc/grafana/grafana.ini` | Main config file |
| `/etc/grafana/provisioning/` | Provisioning YAML files |
| `/var/log/grafana/` | Log files |

## Observability Stack Patterns

### Metrics Stack (Prometheus + Grafana)

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana-oss:13.0.2
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### Full LGTM Stack (Loki + Grafana + Tempo + Mimir)

```yaml
services:
  grafana:
    image: grafana/grafana-oss:13.0.2
    ports: ["3000:3000"]
  loki:
    image: grafana/loki:3.4.0
    ports: ["3100:3100"]
  tempo:
    image: grafana/tempo:latest
    ports: ["3200:3200"]
  mimir:
    image: grafana/mimir:latest
    ports: ["9009:9009"]
  alloy:
    image: grafana/alloy:latest   # collector agent
```

## Common Pitfalls

- **Default credentials** — Always change `admin`/`admin` in production; set `GF_SECURITY_ADMIN_PASSWORD`
- **SQLite in production** — Use PostgreSQL or MySQL for HA deployments; SQLite does not support concurrent writes well
- **Volume mounts** — Always persist `/var/lib/grafana` or you lose dashboards/users on container restart
- **Time zones** — Grafana uses the browser's time zone by default; set dashboard time zone explicitly for shared dashboards
- **Reverse proxy** — Set `root_url` and `serve_from_sub_path` when running behind nginx/Caddy
