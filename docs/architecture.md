# Architecture & Design

## System Overview

![Pipeline Architecture](./diagrams/pipeline-architecture.png)

## Key Decision: Why a custom bridge?

**Problem:** n8n (and most no-code orchestration tools) can only make HTTP requests. OpenVAS/GVM communicates over GMP, an CML-based protocol sent over raw TCP/TLS socket. It is not possible for n8n's built-in HTTP request node to talk to GVM directly. 

**Options considered:**
 
 1. **Build custom HTTP-GMP bridge** (chosen) - a small lightweight service using Greenbone's official `python-gvm` library.
 2. **Use `gmv-cli` via n8n Execute Command node** - avoids writing a persistent service, but requires installing `gvm-tools` inside the n8n container/image and constructing raw GMP XML strings per call. Comparable to option 1 in terms of effort, but less reusable and versatile for future phases.
 3. **Switch to a scanner with a native REST API (e.g. Nessus)** - would eliminate the translation problem entirely. Nessus expposes a documented JSON REST API. Rejected because (a) Nessus is proprietary, which conflicts with the project's all-open-source design goal, (b) the custom bridge has no existing well-maintained open-source equivalent currently.

 **Prior art checked:** [`MixewayOpenVASRestAPI`](https://github.com/Mixeway/MixewayOpenVASRestAPI) exists but targets a pre-GVM11 socket protocol and appears unmaintained. No n8n community node exists for GVM/OpenVAS as of this writing.

 # Networking

_(filled in once Docker network setup between n8n, gvm-bridge, and gvmd is finalized)_

## Report format & data extraction

_(filled in once report parsing is implemented)_