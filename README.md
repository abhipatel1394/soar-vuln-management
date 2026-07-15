 # SOAR - Vulnerability Scanning & Management
 
 Automated vulnerability scanning and reporting pipeline built on open-source security tooling. Part of larger home-lab SOAR.

 **Status:** In Progress

 ## What this does

 Automates the full vulnerability management loop:

 1. Scheduled scans against target hosts using **OpenVAS / Greenbone (GVM)**
 2. Scheduling and Orchestration via **n8n**
 3. A custom built REST bridge translating n8n's HTTP calls into GVM's native GMP protocol (see [`gvm-bridge/`](./gvm-bridge))
 4. Structured report extraction from raw scan output

 ## Why this exists

 Most no-code automation platforms (like n8n) have no way to talk to OpenVAS, because OpenVAS communicates over GMP (Greenbone Management Protocol - XML over a TCP/TLS socket) rather than plain HTTP/REST. This projects builds and utilizes the missing translation later, rather than replacing the OpenVAS scanner with a scanner utilizing built-in REST API (e.g. Nessus). See [`docs/architecture.md`](./docs/architecture.md) for detailed reasoning.

 ## Architecture

 ![Pipeline Architecture](./docs/diagrams/pipeline-architecture.png)

 Full diagram and design: [[`docs/architecture.md`](./docs/architecture.md)]

 ## Repo structure

 | Path | Contents |
 | :--- | :--- |
 | `gvm-bridge/` | Standalone Flask service — HTTP↔GMP translation layer |
| `n8n-workflows/` | Exported n8n workflow JSON |
| `docs/` | Architecture decisions, setup log, testing notes, sample output |

## Setup 

Requires Docker Desktop, an existing Greenbone Community Containers deployment, and n8n running in Docker.


1. Clone this repo
2. Build and run the bridge

```
cd gvm-bridge
cp .env.example .env
```

Edit .env with your real GVM admin password, then:
```
docker compose up -d --build
```


3. Import [n8n-workflows/vuln-scan-pipeline.json](./n8n-workflows/vuln-scan-pipeline.json) into your n8n instance
4. Update the target task name in the workflow's Set Target node to match your own GVM task
5. Activate the Schedule Trigger, or run manually to test


**Status:** Phase 1 complete. Scheduled scanning, orchestration, and report extraction are fully working end to end. Report parsing into structured data is the next planned step.

## Roadmap

This is the first phase of a larger SOAR project. Planned next phases:

- Jira ticketing automation
- Wazuh SIEM integration + Alert enrichment + open-source threat intel
- Local LLM (Ollama/LLama3) triage and documentation assistance
- Suricata IDS implementation + Wireshark Packet analysis
- GRC/Compliance automation

## License

MIT - see [`LICENSE`](./LICENSE)