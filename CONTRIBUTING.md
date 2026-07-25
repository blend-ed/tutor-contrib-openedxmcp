# Contributing to tutor-contrib-openedxmcp

This Tutor plugin packages the FastMCP server image and installs the
[`openedx-mcp`](https://github.com/blend-ed/openedx-mcp) Django app into LMS/CMS.

## Ground rules

- The MCP server is a **thin proxy** — it holds no secrets and enforces no authz;
  it forwards each request's `X-MCP-Key` to the facade. Keep it that way.
- New MCP tools mirror facade endpoints 1:1. Add the tool in
  `templates/openedxmcp/build/openedxmcp/openedxmcp/tools/*.py` and the endpoint
  in `openedx-mcp`.
- **Packaging:** the build context lives under `templates/…/build/`. Do not let
  `.gitignore` swallow it (`build/` must stay anchored as `/build/`). CI asserts
  the wheel ships `templates/`.

## Dev setup

```bash
pip install ruff build
ruff check tutoropenedxmcp
python -m build .           # verify wheel + templates
```

## PRs

- Keep `ruff` green and the CI templates-assertion passing.
- Conventional-commit subjects. Update `CHANGELOG.md`.

## Releasing

Bump `pyproject.toml` + `tutoropenedxmcp/__about__.py`, update `CHANGELOG.md`, tag
`vX.Y.Z`, push — CI publishes to PyPI via trusted publishing.
