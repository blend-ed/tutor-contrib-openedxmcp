# tutor-contrib-openedxmcp

[![PyPI](https://img.shields.io/pypi/v/tutor-contrib-openedxmcp.svg)](https://pypi.org/project/tutor-contrib-openedxmcp/)
[![CI](https://github.com/blend-ed/tutor-contrib-openedxmcp/actions/workflows/ci.yml/badge.svg)](https://github.com/blend-ed/tutor-contrib-openedxmcp/actions/workflows/ci.yml)
[![License: AGPL-3.0](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](LICENSE)

Tutor plugin that stands up the **Open edX Admin MCP** for staff/superusers:

1. **Installs** the [`openedx-mcp`](https://pypi.org/project/openedx-mcp/) Django
   app into the LMS/CMS image (the REST facade at `/api/mcp/` and `/api/mcp/cms/`).
2. **Runs** a standalone `openedxmcp` container — a FastMCP streamable-http server
   that proxies to that facade, fronted by Caddy at `mcp.<LMS_HOST>`.

The MCP server holds no secrets: each request carries its own MCP key, forwarded
to the facade as `X-MCP-Key`. Authorization is enforced by the facade
(`is_staff`/`is_superuser`, live). No Hasura, no external stack. **Ulmo.**

## Architecture

```
Claude / MCP client ──(Bearer key)──▶ openedxmcp container (FastMCP proxy)
                                         │  X-MCP-Key
                             ┌───────────┴───────────┐
                       LMS /api/mcp/           CMS /api/mcp/cms/
                    (people, enroll,          (course authoring,
                     analytics, certs,          modulestore)
                     reports, retire)
```

## Install

```bash
pip install tutor-contrib-openedxmcp
tutor plugins enable openedxmcp

# The openedx-mcp Django app auto-installs into the openedx image (Dockerfile
# patch) — no extra step. To PIN a version/source, append to Tutor's list, e.g.
#   tutor config save --append OPENEDX_EXTRA_PIP_REQUIREMENTS=openedx-mcp==0.1.4

tutor images build openedx openedxmcp    # rebuild LMS/CMS w/ the app; build MCP server
tutor local launch                        # or: tutor k8s launch
tutor local do init                        # migrations -> MCPKey tables
```

Then mint a key in Django admin (**Open edX Admin MCP → MCP keys**) and connect a
client to `https://mcp.<LMS_HOST>/mcp`. The key-creation banner prints ready-to-
paste connect steps. Full connect/security/tool docs live in the
[`openedx-mcp` README](https://pypi.org/project/openedx-mcp/).

## Config

| Key | Default | Meaning |
|---|---|---|
| `OPENEDXMCP_IMAGE` | `openedxmcp:latest` | MCP server image tag |
| `OPENEDXMCP_ENDPOINT` | `mcp.{{ LMS_HOST }}` | public MCP host |
| `OPENEDXMCP_PORT` | `8080` | server port |
| `OPENEDXMCP_LMS_BASE_URL` | `http://lms:8000` | in-cluster LMS upstream |
| `OPENEDXMCP_CMS_BASE_URL` | `http://cms:8000` | in-cluster CMS upstream |
| `OPENEDXMCP_PUBLIC_URL` | `https://{{ ENDPOINT }}/mcp` | shown in the Django key page (injected into LMS/CMS as `OPENEDX_MCP_PUBLIC_URL`) |

The Django app auto-installs via a Dockerfile patch
(`openedx-dockerfile-post-python-requirements`). To pin a version/source, append
to Tutor's standard `OPENEDX_EXTRA_PIP_REQUIREMENTS` list.

## What ships

- Docker image build context (`templates/openedxmcp/build/…`) — the FastMCP proxy.
- Patches: `caddyfile` (route `/mcp*`), docker-compose services (+ healthcheck),
  k8s deployment/service (+ readiness/liveness on `/health`),
  `openedx-common-settings` (injects `OPENEDX_MCP_PUBLIC_URL`),
  `openedx-dockerfile-post-python-requirements` (pip-installs the app).

The MCP server exposes an unauthenticated `/health` for probes.

## Develop

```bash
pip install ruff build
ruff check tutoropenedxmcp
python -m build .          # CI asserts the wheel ships templates/
```

See [CHANGELOG.md](CHANGELOG.md) · [CONTRIBUTING.md](CONTRIBUTING.md).
