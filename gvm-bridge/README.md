# gvm-bridge

A minimal REST API that bridges HTTP requests to Greenbone Vulnerability Management (GVM/OpenVAS) via the Greenbone Management Protocol (GMP).

## Why this exists

GVM/OpenVAS does not speak HTTP, it communicates exclusively over GMP, an XML-based protocol sent over a Unix socket or TCP/TLS socket. Automation tools that only support HTTP, like n8n or most no-code platforms, cannot talk to GVM directly. This service exposes a small set of REST endpoints that internally use `python-gvm` (Greenbone's official Python library) to perform the translation.

No maintained open source project currently fills this gap. See the reasoning in the main project's [`architecture.md`](../docs/architecture.md).

## How it connects to GVM

This bridge connects to gvmd over a Unix socket, not TCP. The official Greenbone Community Containers deployment does not expose GMP over TCP by default, it shares a socket file through a Docker volume instead. This service mounts that same volume and talks to the socket directly.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/tasks` | Lists all tasks with id and name |
| POST | `/start_scan/<task_id>` | Starts a scan for the given task, returns the report_id for that run |
| GET | `/report_status/<report_id>` | Returns scan_run_status and progress for a specific run |
| GET | `/report/<task_id>` | Returns the most recent completed report for a task, as XML |

## Requirements

- Python 3.11
- `flask`, `python-gvm`, `lxml`
- Network access to a running gvmd instance
- Read/write access to gvmd's shared socket volume

## Running

Copy the example environment file and fill in your real password:
```
cp .env.example .env
```
Then build and run:
```
docker compose up -d --build
```
The compose file expects two external Docker networks and one external volume, matching whatever your existing Greenbone and n8n deployments already created:

- `greenbone-community-edition_default`
- `n8n-local_default`
- `greenbone-community-edition_gvmd_socket_vol`

If your own setup uses different names, update `docker-compose.yml` accordingly.

## Known limitations

- Development Flask server, not a production WSGI server. Fine for a homelab, not meant for exposure beyond a trusted local network.
- Error handling covers the most common failure case encountered during development (starting a task that is already running). Other failure modes return generic errors rather than specific, handled responses.

## License

[MIT](../LICENSE)