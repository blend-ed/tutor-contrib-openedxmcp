"""MCP tool registration. LMS tools take the LMS client; authoring tools take
the CMS client (course content lives in the Studio modulestore)."""
from . import authoring as _authoring
from . import ops as _ops
from . import people as _people
from . import reads as _reads


def register_all(mcp, lms_client, cms_client):
    _reads.register(mcp, lms_client)
    _people.register(mcp, lms_client)
    _ops.register(mcp, lms_client)
    _authoring.register(mcp, cms_client)
