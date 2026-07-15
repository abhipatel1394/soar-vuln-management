# Setup Log

Running notes captured during setup. Serves as both a proof-of-work trail
and a troubleshooting reference.

## Baseline (as of start)

- OpenVAS/GVM running in Docker (isolated container)
- n8n running in Docker (isolated container)
- Metasploitable running as a VMware VM

## Step 2 - Feed sync verification
- [x] Confirmed NVT feed sync status - current
- [x] Confirmed SCAP feed sync status - current
- [x] Confirmed CERT feed sync status - current
- Notes: Deployed via official Greenbone Community Containers stack. All feed containers (scap-data, vulnerability-tests, notus-data, dfn-cert-data, cert-bund-data) healthy and current as of July 11th, 2026.

## Step 3 - Network reachability
- [x] Confirmed via `docker network ls`: two isolated networks - `greenbone-community-edition_default` and `n8n-local_default`.
- [x] Tested cross-network reachability with throwaway alpine container:
      - ping to n8n_automation succeeded (proves network-bridging concept works)
      - curl to gvmd:9390 returned "connection refused" 
- Key finding: gvmd exposes GMP via a Unix socket (gvmd_socket_vol volume), shared with gsad. Greenbone's own recommended pattern for external GMP access is to mount this same volume into another container, rather than enabling TCP (community forum reports of TCP mode causing gvmd instability).
- Decision: gvm-bridge will connect via UnixSocketConnection against the mounted gvmd_socket_vol, not TLSConnection over port 9390.

### Step 3.1 - Network reachability (OpenVAS - Metasploitable)
- [x] Confirmed OpenVAS's Docker network can reach Metasploitable VM
      (tested via disposable alpine container on greenbone-community-edition_default, ping to 192.168.192.128 succeeded)
- All reachability assumptions now confirmed: n8n↔bridge, bridge↔gvmd (socket), OpenVAS↔Metasploitable (network)

## Note: GVM web UI task detail navigation
The GSA web UI in this version renders task details as an in-page overlay rather than a real page navigation - no URL change occurs on click, making it unreliable for extracting task IDs via the browser. Worked around by querying gvmd directly via gvm-tools CLI over the same Unix socket the bridge uses, confirms the socket-based GMP connection is fully functional independent of the web UI.

## Step 4 - Bridge built and verified
- [x] gvm-bridge container built and running successfully
- [x] /status/<task_id> endpoint tested against real task
      (2e6315c0-a9a9-4bf6-8d80-09c7d2769ec9), confirmed working
- Bug encountered: initial get_gmp() called gmp.authenticate() before the GMP connection context was actually opened, causing
  AttributeError: 'GMP' object has no attribute 'authenticate'.
  Fixed by wrapping get_gmp() with @contextmanager and moving authenticate() inside the `with Gmp(...) as gmp:` block.
- Secondary issue during debugging: rebuilt the Docker image after editing app.py, but forgot to actually run `docker build` before re-running the container, meant the old, broken code kept running despite the file being fixed. Confirmed via matching image ID between builds. Resolved by rebuilding properly and confirming a new image ID before re-running.

## Step 5 - Bridge fully functional
- [x] /tasks - lists all tasks with id/name
- [x] /status/<task_id> - returns live status/progress
- [x] /start_scan/<task_id> - triggers a scan
- [x] /report/<task_id> - returns real XML report content
- Bug fixed: report_xml field showed Python's default object repr (`<Element ... at 0x...>`) instead of actual XML text. `str()` doesn't serialize lxml Element objects, fixed using `etree.tostring(rep, pretty_print=True).decode()`, which properly walks the XML tree into text, then decodes it from bytes to a string.
- All four endpoints confirmed working against a real completed scan (task: Metasploitable - Full Scan).

## Step 6 - Final network topology confirmed
- [x] gvm-bridge attached to both greenbone-community-edition_default (172.18.0.18) and n8n-local_default (172.19.0.3)
- [x] Confirmed n8n_automation can resolve and ping gvm-bridge by name
- n8n workflows will reach the bridge via http://gvm-bridge:5000/...

## Bug: /start_scan failed silently when task already running
gvmd refuses to start a task that's already mid-scan, returning a response with no <report_id> element. Original code assumed report_id would always be present, causing an unhandled crash. Fixed by checking if the element exists before accessing it, returning a proper 409 Conflict response instead of crashing.

## Debugging note: don't test isolated nodes with cross-node expressions
Spent significant time chasing an "undefined" report_id in n8n's URL expression, initially suspecting expression syntax. Root cause was actually the bridge returning old (pre-fix) data because the container hadn't been rebuilt after code changes (a repeat of an earlier lesson). Confirmed via direct curl testing, bypassing n8n, before returning to the workflow, isolating "does the bridge work" from "does n8n's expression work" resolved it quickly once separated.

## Polling loop confirmed working end-to-end
Start Scan → Wait (30s) → Check Report Status → IF (scan_run_status == "Done") → loops back to Wait if not done, proceeds if done. Verified against a real, live Metasploitable scan run.

## Bridge cleanup: progress added, redundant endpoint removed

Added progress percentage to the same `/report_status` response that already returns scan_run_status, rather than keeping it in a separate `/status/<task_id>` endpoint. Once this was in place, `/status/<task_id>` was no longer called by anything in the workflow, so it was removed entirely to avoid leaving dead code in the bridge.

## Bridge security fix: password moved to environment variable

GVM_PASSWORD was hardcoded in app.py during initial development. Since this repo is going public, moved it to an environment variable read at startup, with a check that fails immediately and clearly if the variable is missing, instead of failing later during the first real request. Added a `.env.example` file with placeholder values and confirmed `.env` is in `.gitignore`.

## Bridge moved to docker-compose

Replaced the long manual `docker run` command (network, volume, port, password flag all typed by hand each time) with a `gvm-bridge/docker-compose.yml` file, so rebuilding is now `docker compose up -d --build`. Both networks and the socket volume are declared as external and attached automatically.

## n8n workflow: Start Scan failure handling added

Added a check right after Start Scan that verifies a report_id was actually returned. If not, the workflow stops with a clear error message naming the task id and the likely causes, rather than continuing forward with missing data and failing confusingly a few nodes later.

## n8n file write bug: application level restriction, not a permissions problem

Save Report failed with "the file is not writable" even after confirming the mounted folder had open permissions. Ran `docker exec n8n_automation touch` directly against the same path and it succeeded, which ruled out an OS level permissions problem. Researched the exact error message and found this is a known n8n behavior, the `Read/Write Files from Disk` node respects an application level allowlist, `N8N_RESTRICT_FILE_ACCESS_TO`, separate from actual filesystem permissions. The project's reports folder was not included in that variable. Fixed by adding it to the existing list in the n8n compose file and recreating the container. Workflows and credentials in the named volume were unaffected by the recreation.

## Final pipeline confirmed end to end

Full chain confirmed working on a real scan: Manual Trigger, Set Target, Get Tasks, Extract Task ID, Start Scan, Check Scan Started, Wait, Check Report Status, Is Scan Done, Get Report, Convert JSON to Data, Save Report. Real report file confirmed saved to disk with genuine scan content.

Manual Trigger later swapped for Schedule Trigger, set to run weekly, Sunday 3am.

## Discovery: report_format_id used is actually CSV, not XML
The report_format_id hardcoded in the bridge (c1645568-627a-11e3-a660-406186ea4fc5) was assumed early on to correspond to plain XML output. Inspecting a real saved report showed it is actually Greenbone's CSV Results format, confirmed by the report_format name field in the response itself. The actual scan content is base64 encoded CSV text embedded inside the outer XML wrapper, not raw XML findings. This does not break anything, the data is still complete and usable, but the report_xml field name in the bridge is a slight misnomer worth revisiting, and decoding the base64 content is needed to get a human readable CSV rather than raw XML structure. 