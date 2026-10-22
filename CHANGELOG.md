# Changelog

All notable changes to `tutor-contrib-openedxmcp`. Format based on
[Keep a Changelog](https://keepachangelog.com/). Ulmo release line.

## [Unreleased]

### Fixed
- MCP server no longer forwards whole non-JSON upstream bodies to the model. An
  HTML page (e.g. the LMS 500 page, which carries the caller's username and
  profile-image URL) becomes a one-line message with the HTTP status; other
  text is capped at 300 characters. JSON error bodies pass through unchanged.

## [0.1.7]

### Changed
- Auto-install the `openedx-mcp` app via the
  `openedx-dockerfile-post-python-requirements` patch again (hardcoded
  `pip install openedx-mcp`, no custom config var) — zero operator steps. Pin a
  version/source with `OPENEDX_EXTRA_PIP_REQUIREMENTS` if desired.

## [0.1.6]

### Changed
- Dropped the custom `OPENEDXMCP_PIP_REQUIREMENT` config; briefly used
  `OPENEDX_EXTRA_PIP_REQUIREMENTS` as the sole install path (superseded by 0.1.7's
  zero-touch patch).

## [0.1.5]

### Added
- MCP server exposes an unauthenticated `/health` route; k8s deployment gains
  readiness/liveness probes and the docker-compose service a healthcheck.
- `ruff` lint + a wheel-ships-templates assertion in CI.

## [0.1.4]

### Added
- `OPENEDXMCP_PUBLIC_URL` config + `openedx-common-settings` patch inject
  `OPENEDX_MCP_PUBLIC_URL` into LMS/CMS, so the Django key page shows connect steps.
- Server tool scope docstrings aligned to the 9-scope model.

## [0.1.3]

### Fixed
- **Packaging:** an unanchored `build/` in `.gitignore` had excluded the MCP
  server build context from git entirely, so earlier wheels could not build the
  `openedxmcp` image. Templates are now committed and shipped (CI asserts it).

## [0.1.2]

### Fixed
- Add `MANIFEST.in` + `include-package-data` (superseded by 0.1.3's real fix).

## [0.1.1]

### Changed
- Tutor dependency pin widened to `>=19,<22` (Ulmo = Tutor v21).

[0.1.7]: https://github.com/blend-ed/tutor-contrib-openedxmcp/releases/tag/v0.1.7
[0.1.6]: https://github.com/blend-ed/tutor-contrib-openedxmcp/releases/tag/v0.1.6
[0.1.5]: https://github.com/blend-ed/tutor-contrib-openedxmcp/releases/tag/v0.1.5
[0.1.4]: https://github.com/blend-ed/tutor-contrib-openedxmcp/releases/tag/v0.1.4
[0.1.3]: https://github.com/blend-ed/tutor-contrib-openedxmcp/releases/tag/v0.1.3
[0.1.2]: https://github.com/blend-ed/tutor-contrib-openedxmcp/releases/tag/v0.1.2
[0.1.1]: https://github.com/blend-ed/tutor-contrib-openedxmcp/releases/tag/v0.1.1
