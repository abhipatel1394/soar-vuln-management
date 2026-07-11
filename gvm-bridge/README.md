# gvm-bridge

A minimal REST API that bridges HTTP requests to Greenbone Vulnerability Management (GVM/OpenVAS) via the Greenbone Management Protocol (GMP).

## Why this exists

GVM/OpenVAS does not speak HTTP — it communicates exclusively over GMP, an XML-based protocol sent over a TCP/TLS socket. This service exposes REST endpoints that internally use `python-gvm` (Greenbone's official
Python library) to perform the translation.

## Status

In development — see main repo's [`docs/setup-log.md`](../docs/setup-log.md) for progress.