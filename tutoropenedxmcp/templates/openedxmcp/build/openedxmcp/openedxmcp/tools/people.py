"""Write tools for people & access (LMS facade).

Two-phase tools enforce the handshake server-side: call WITHOUT confirm_token to
get a preview + single-use token, show it to the human, then call again with the
IDENTICAL args plus confirm_token. enroll/unenroll apply directly (reversible)."""
from ..client import FacadeError


def _post(client, path, body):
    try:
        return client.post(path, json=body)
    except FacadeError as exc:
        return {"error": exc.detail, "status": exc.status_code}


def register(mcp, client):
    @mcp.tool()
    def enroll_user(username: str, course_id: str, mode: str = "audit") -> dict:
        """Enroll one user in one course. mode e.g. audit, honor, verified.
        Applies immediately. Requires write:enrollment."""
        return _post(client, "enroll/", {"username": username, "course_id": course_id, "mode": mode})

    @mcp.tool()
    def unenroll_user(username: str, course_id: str) -> dict:
        """Deactivate one enrollment. Applies immediately. Requires write:enrollment."""
        return _post(client, "unenroll/", {"username": username, "course_id": course_id})

    @mcp.tool()
    def bulk_enroll(course_id: str, entries: list, mode: str = "audit",
                    auto_enroll: bool = True, confirm_token: str = "") -> dict:
        """Enroll many into one course. entries = [{"email": ..., "mode"?: ...}].
        Unregistered emails get a pending allowed-enrollment. High blast radius:
        call without confirm_token first to preview the count. Requires
        write:enrollment."""
        body = {"course_id": course_id, "entries": entries, "mode": mode,
                "auto_enroll": auto_enroll}
        if confirm_token:
            body["confirm_token"] = confirm_token
        return _post(client, "bulk-enroll/", body)

    @mcp.tool()
    def create_user(email: str, username: str, name: str = "",
                    send_activation_email: bool = False, confirm_token: str = "") -> dict:
        """Create a new inactive account (no caller login side effect). Call
        without confirm_token to preview. Requires write:users."""
        body = {"email": email, "username": username, "name": name,
                "send_activation_email": send_activation_email}
        if confirm_token:
            body["confirm_token"] = confirm_token
        return _post(client, "users/create/", body)

    @mcp.tool()
    def deactivate_user(username: str, confirm_token: str = "") -> dict:
        """Disable an account (is_active=False). Destructive. Call without
        confirm_token to preview. Requires the destructive scope."""
        body = {"username": username}
        if confirm_token:
            body["confirm_token"] = confirm_token
        return _post(client, "users/deactivate/", body)

    @mcp.tool()
    def set_role(username: str, action: str, level: str, course_id: str = "",
                 confirm_token: str = "") -> dict:
        """Grant or revoke a role. action=grant|revoke. level is one of:
        global_staff, superuser (platform-wide), or a course role
        (instructor, staff, limited_staff, beta, data_researcher) — the latter
        need course_id. Call without confirm_token to preview. Requires
        write:users."""
        body = {"username": username, "action": action, "level": level}
        if course_id:
            body["course_id"] = course_id
        if confirm_token:
            body["confirm_token"] = confirm_token
        return _post(client, "roles/set/", body)

    @mcp.tool()
    def reset_student_attempts(username: str, course_id: str, block_locator: str,
                               delete_module: bool = False, confirm_token: str = "") -> dict:
        """Reset a learner's attempts on one problem block (delete_module=True wipes
        the state entirely). Call without confirm_token to preview. Requires
        write:users."""
        body = {"username": username, "course_id": course_id, "block_locator": block_locator,
                "delete_module": delete_module}
        if confirm_token:
            body["confirm_token"] = confirm_token
        return _post(client, "students/reset-attempts/", body)

    @mcp.tool()
    def instructor_access(username: str, course_id: str, action: str,
                          level: str = "staff", confirm_token: str = "") -> dict:
        """Allow or revoke instructor-dashboard access on a course (level
        staff|instructor|beta|data_researcher). action=grant|revoke. Call without
        confirm_token to preview. Requires write:users."""
        body = {"username": username, "course_id": course_id, "action": action, "level": level}
        if confirm_token:
            body["confirm_token"] = confirm_token
        return _post(client, "access/instructor/", body)
