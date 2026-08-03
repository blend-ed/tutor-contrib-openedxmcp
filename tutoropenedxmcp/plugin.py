"""
Tutor plugin for the open-source Open edX Admin MCP.

Two moving parts, both wired here:

  1. The `openedx_mcp` Django app is pip-installed into the openedx image (LMS+CMS)
     by a Dockerfile patch, so the facade endpoints (/api/mcp/ and /api/mcp/cms/)
     come up inside the existing LMS/CMS with no extra operator steps.
  2. A standalone `openedxmcp` container runs the MCP server (streamable-http),
     fronted by Caddy at mcp.<LMS_HOST>. It forwards each caller's X-MCP-Key to the
     LMS/CMS facade. It holds no secrets — auth is the per-request key.

No blend-ed stack, no Hasura, no external identity. Ulmo release.
"""
from __future__ import annotations

import os
import typing as t
from glob import glob

import click
import importlib_resources
from tutor import hooks

from .__about__ import __version__

HERE = os.path.abspath(os.path.dirname(__file__))

config: dict[str, dict[str, t.Any]] = {
    "defaults": {
        "VERSION": __version__,
        # MCP server image. Build locally or push to your own registry.
        "IMAGE": "openedxmcp:latest",
        # Public host the MCP client connects to (streamable-http at /mcp).
        "ENDPOINT": "mcp.{{ LMS_HOST }}",
        # Port the uvicorn server listens on inside the container.
        "PORT": "8080",
        # In-cluster upstreams the MCP server proxies to. Internal service names;
        # the hop stays inside the docker/k8s network, no public TLS needed.
        "LMS_BASE_URL": "http://lms:8000",
        "CMS_BASE_URL": "http://cms:8000",
        # Public connector URL shown to admins on the Django key-creation page so
        # they can paste it straight into their Claude client. Streamable-http
        # mounts at /mcp. Override the scheme if this deployment does not
        # terminate TLS.
        "PUBLIC_URL": "https://{{ OPENEDXMCP_ENDPOINT }}/mcp",
    },
}

hooks.Filters.CONFIG_DEFAULTS.add_items(
    [(f"OPENEDXMCP_{k}", v) for k, v in config["defaults"].items()]
)

# --- auto-install the Django app into the openedx image (LMS+CMS) ---
# This patch runs a plain `pip install` in the openedx Dockerfile, so the app is
# present with zero operator steps — just `tutor images build openedx`. To pin a
# specific version or source instead, append to Tutor's standard list, e.g.
#     tutor config save --append OPENEDX_EXTRA_PIP_REQUIREMENTS=openedx-mcp==0.1.4
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-dockerfile-post-python-requirements",
        "RUN pip install openedx-mcp",
    )
)

# --- MCP server image build/pull/push ---
hooks.Filters.IMAGES_BUILD.add_item(
    ("openedxmcp", ("plugins", "openedxmcp", "build", "openedxmcp"), "{{ OPENEDXMCP_IMAGE }}", ())
)
hooks.Filters.IMAGES_PULL.add_item(("openedxmcp", "{{ OPENEDXMCP_IMAGE }}"))
hooks.Filters.IMAGES_PUSH.add_item(("openedxmcp", "{{ OPENEDXMCP_IMAGE }}"))

# --- template + patch loading ---
hooks.Filters.ENV_TEMPLATE_ROOTS.add_items(
    [str(importlib_resources.files("tutoropenedxmcp") / "templates")]
)
hooks.Filters.ENV_TEMPLATE_TARGETS.add_items([("openedxmcp/build", "plugins")])

for path in glob(str(importlib_resources.files("tutoropenedxmcp") / "patches" / "*")):
    with open(path, encoding="utf-8") as patch_file:
        hooks.Filters.ENV_PATCHES.add_item((os.path.basename(path), patch_file.read()))


# --- public host (Caddy routing) ---
@hooks.Filters.APP_PUBLIC_HOSTS.add()
def _openedxmcp_public_hosts(hosts: list[str], context_name: str) -> list[str]:
    if context_name == "dev":
        hosts += ["{{ OPENEDXMCP_ENDPOINT }}:{{ OPENEDXMCP_PORT }}"]
    else:
        hosts += ["{{ OPENEDXMCP_ENDPOINT }}"]
    return hosts


@click.group(help="Open edX Admin MCP plugin commands")
def openedxmcp() -> None:
    pass


hooks.Filters.CLI_COMMANDS.add_item(openedxmcp)
