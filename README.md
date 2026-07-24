# tutor-contrib-openedxmcp

Tutor plugin that (1) pip-installs the `openedx-mcp` Django app into the LMS/CMS
image and (2) runs the standalone FastMCP server that proxies to its facade,
fronted by Caddy at `mcp.<LMS_HOST>`. Ulmo.

```bash
pip install -e .
tutor plugins enable openedxmcp
tutor config save --set OPENEDXMCP_PIP_REQUIREMENT=./open-source/openedx-mcp
tutor images build openedx openedxmcp
tutor local launch && tutor local do init
```

## Config keys

| Key | Default | Meaning |
|---|---|---|
| `OPENEDXMCP_IMAGE` | `openedxmcp:latest` | MCP server image tag |
| `OPENEDXMCP_ENDPOINT` | `mcp.{{ LMS_HOST }}` | public MCP host |
| `OPENEDXMCP_PORT` | `8080` | server port |
| `OPENEDXMCP_LMS_BASE_URL` | `http://lms:8000` | in-cluster LMS upstream |
| `OPENEDXMCP_CMS_BASE_URL` | `http://cms:8000` | in-cluster CMS upstream |
| `OPENEDXMCP_PIP_REQUIREMENT` | `openedx-mcp` | the Django app to install |

The MCP server holds no secrets — each request carries its own MCP key, forwarded
to the facade as `X-MCP-Key`. See `../README.md`.
