# GSA-TTS Local Development

This document covers the GSA-TTS fork-specific setup for running SpiffArena locally with the [spiffworkflow-connector](https://github.com/GSA-TTS/spiffworkflow-connector) and PIC backend configuration.

## Prerequisites

Clone the connector repo alongside this one:

```
parent/
├── spiff-arena/                # this repo
└── spiffworkflow-connector/    # https://github.com/GSA-TTS/spiffworkflow-connector
```

If you want to deviate from this directory structure, you can override the connector path by setting `CONNECTOR_REPO_PATH` in a `.env` file or as an environment variable.

## Quick Start

```bash
make local
```

This single command builds all images, installs dependencies, recreates the database, and starts every service. It is equivalent to running `make dev-env-local` followed by `make start-dev` with the local overlay files.

Once running:

- **Frontend:** http://localhost:8001 (admin/admin)
- **Backend API:** http://localhost:8000
- **Minio Console:** http://localhost:9002 (minioadmin/minioadmin)
- **Minio S3 API:** http://localhost:9001

This allows you to then fire up the [Astro frontend](https://github.com/GSA-TTS/pic-blm-cxworks) and interact with Spiff transparently as you would with the [Docker Compose images](https://github.com/GSA-TTS/pic-blm-cxworks/tree/main/workflow) over there.

## How It Works

The `make local` target layers two overlay compose files on top of the upstream defaults:

| File                                                | Purpose                                                                                   |
| --------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `dev-local.docker-compose.yml`                      | PIC backend env vars, venv volume isolation, GSA-TTS connector image, Minio + bucket init |
| `connector-proxy-demo/dev-local.docker-compose.yml` | Builds the connector from the local `spiffworkflow-connector` repo with hot-reload        |

These overlays are only included when you use the `local` or `dev-env-local` Makefile targets. The upstream `make dev-env` / `make start-dev` workflow use the sartography connector-proxy-demo dummy content as is in the file system.

## Makefile Targets

| Target               | Description                                                         |
| -------------------- | ------------------------------------------------------------------- |
| `make local`         | One-shot: build + install deps + start all services with PIC config |
| `make dev-env-local` | Build + install local deps only (no `start-dev`)                    |

## Environment Variables

| Variable               | Default                      | Description                   |
| ---------------------- | ---------------------------- | ----------------------------- |
| `CONNECTOR_REPO_PATH`  | `../spiffworkflow-connector` | Path to the connector repo    |
| `CONNECTOR_PROXY_PORT` | `8004`                       | Port the connector listens on |

These can be set in a `.env` file at the project root or in `connector-proxy-demo/.env`.

For additional commands, please reference the [Makefile](./Makefile) directly.
