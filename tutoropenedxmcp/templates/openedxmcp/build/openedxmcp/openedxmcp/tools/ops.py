"""Certificates, async reports (grade export), and account retirement (LMS)."""
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
    # --- certificates ---
    @mcp.tool()
    def list_course_certificates(course_id: str, limit: int = 200, offset: int = 0) -> dict:
        """Issued (downloadable) certificates for a course. Requires read."""
        return _get(client, f"certificates/course/{course_id}/",
                    {"limit": limit, "offset": offset})

    @mcp.tool()
    def user_certificates(username: str) -> dict:
        """All certificates a user has earned across courses. Requires read."""
        return _get(client, f"certificates/user/{username}/")

    @mcp.tool()
    def generate_certificate(course_id: str, username: str = "", student_set: str = "") -> dict:
        """Generate certificates. With username: one learner. Without: batch for the
        course (student_set = all_allowlisted | allowlisted_not_generated |
        specific_student, default all). Async. Requires write:certificates."""
        body = {"course_id": course_id}
        if username:
            body["username"] = username
        if student_set:
            body["student_set"] = student_set
        return _post(client, "certificates/generate/", body)

    @mcp.tool()
    def regenerate_certificates(course_id: str, statuses: list, confirm_token: str = "") -> dict:
        """Regenerate course certificates for the given statuses (e.g.
        ['downloadable','error']). Async. Call without confirm_token to preview.
        Requires write:certificates."""
        body = {"course_id": course_id, "statuses": statuses}
        if confirm_token:
            body["confirm_token"] = confirm_token
        return _post(client, "certificates/regenerate/", body)

    @mcp.tool()
    def invalidate_certificate(username: str, course_id: str, notes: str = "",
                               confirm_token: str = "") -> dict:
        """Invalidate a learner's certificate. Destructive. Call without
        confirm_token to preview. Requires write:certificates + destructive."""
        body = {"username": username, "course_id": course_id, "notes": notes}
        if confirm_token:
            body["confirm_token"] = confirm_token
        return _post(client, "certificates/invalidate/", body)

    # --- async reports / grade export ---
    @mcp.tool()
    def submit_report(course_id: str, kind: str = "grades", features: list = None) -> dict:
        """Enqueue an async report. kind = grades | problem_grade | students_features
        | may_enroll | inactive_enrolled | proctored_exam | course_survey. Returns a
        task id; poll with report_tasks and fetch links with report_downloads.
        Requires write:reports."""
        body = {"course_id": course_id, "kind": kind}
        if features:
            body["features"] = features
        return _post(client, "reports/submit/", body)

    @mcp.tool()
    def report_tasks(course_id: str) -> dict:
        """Recent instructor-task status for a course (poll report progress).
        Requires read."""
        return _get(client, f"reports/tasks/{course_id}/")

    @mcp.tool()
    def report_downloads(course_id: str, config: str = "GRADES_DOWNLOAD") -> dict:
        """Download links (name, url) for generated reports, newest first.
        Requires read."""
        return _get(client, f"reports/downloads/{course_id}/",
                    {"config": config} if config else None)

    # --- account retirement ---
    @mcp.tool()
    def retirement_status(username: str) -> dict:
        """Current retirement-pipeline state for a user (or none). Requires read."""
        return _get(client, f"retirement/status/{username}/")

    @mcp.tool()
    def request_retirement(username: str, full: bool = True, confirm_token: str = "") -> dict:
        """Start account retirement. full=True (default) deactivates credentials +
        queues PII removal — IRREVERSIBLE. full=False queues a status row only.
        Distinct from deactivate_user (reversible is_active flag). Call without
        confirm_token to preview. Requires write:users + destructive."""
        body = {"username": username, "full": full}
        if confirm_token:
            body["confirm_token"] = confirm_token
        return _post(client, "retirement/request/", body)
