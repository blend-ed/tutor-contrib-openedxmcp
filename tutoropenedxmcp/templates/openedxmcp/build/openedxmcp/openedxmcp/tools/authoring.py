"""Course-authoring tools (CMS facade). Content hierarchy:
course > chapter (section) > sequential (subsection) > vertical (unit) > component.
Everything created lands on the DRAFT branch; publish to expose to learners.
Draft edits (create/update block, settings) apply immediately; publish/delete
block use the confirm handshake. Course create/clone/delete lifecycle is not
included here."""
from ..client import FacadeError


def _get(client, path, params=None):
    try:
        return client.get(path, params=params)
    except FacadeError as exc:
        return {"error": exc.detail, "status": exc.status_code}


def _post(client, path, body):
    try:
        return client.post(path, json=body)
    except FacadeError as exc:
        return {"error": exc.detail, "status": exc.status_code}


def register(mcp, client):
    @mcp.tool()
    def read_course_outline(course_id: str) -> dict:
        """Full draft outline as a nested tree with every block's locator and
        display name. course_id is the course-v1 key. Requires read."""
        return _get(client, f"courses/{course_id}/outline/")

    @mcp.tool()
    def create_block(parent_locator: str, category: str, display_name: str = "",
                     boilerplate: str = "") -> dict:
        """Create one block under parent_locator. category is chapter, sequential,
        vertical, html, problem, video, discussion, ... Applies to draft
        immediately. Requires write:courses."""
        body = {"parent_locator": parent_locator, "category": category}
        if display_name:
            body["display_name"] = display_name
        if boilerplate:
            body["boilerplate"] = boilerplate
        return _post(client, "blocks/create/", body)

    @mcp.tool()
    def create_block_tree(parent_locator: str, nodes: list) -> dict:
        """Create a whole subtree in one call. nodes is a list of
        {"category", "display_name"?, "data"?, "metadata"?, "children"?: [...]}
        — e.g. chapters containing sequentials containing verticals containing
        components. Draft only; publish separately. Requires write:courses."""
        return _post(client, "blocks/create-tree/", {"parent_locator": parent_locator,
                                                      "nodes": nodes})

    @mcp.tool()
    def update_block(locator: str, data: str = "", metadata: dict = None,
                     fields: dict = None, publish: str = "") -> dict:
        """Update a block's body (data), metadata, or fields. publish may be
        make_public | republish | discard_changes. Applies immediately. Requires
        write:courses."""
        body = {"locator": locator}
        if data:
            body["data"] = data
        if metadata:
            body["metadata"] = metadata
        if fields:
            body["fields"] = fields
        if publish:
            body["publish"] = publish
        return _post(client, "blocks/update/", body)

    @mcp.tool()
    def publish_block(locator: str, confirm_token: str = "") -> dict:
        """Publish a block (and its subtree) to learners. Call without
        confirm_token to preview. Requires write:courses."""
        body = {"locator": locator}
        if confirm_token:
            body["confirm_token"] = confirm_token
        return _post(client, "blocks/publish/", body)

    @mcp.tool()
    def delete_block(locator: str, confirm_token: str = "") -> dict:
        """Delete a block. Call without confirm_token to preview. Requires
        write:courses."""
        body = {"locator": locator}
        if confirm_token:
            body["confirm_token"] = confirm_token
        return _post(client, "blocks/delete/", body)

    @mcp.tool()
    def update_course_settings(course_id: str, details: dict = None, grading: dict = None,
                               advanced: dict = None) -> dict:
        """Update schedule/pacing (details), grading policy (grading), or advanced
        settings (advanced). A course needs schedule + grading before it can be
        launched. Applies immediately. Requires write:courses."""
        body = {"course_id": course_id}
        if details:
            body["details"] = details
        if grading:
            body["grading"] = grading
        if advanced:
            body["advanced"] = advanced
        return _post(client, "courses/settings/", body)
