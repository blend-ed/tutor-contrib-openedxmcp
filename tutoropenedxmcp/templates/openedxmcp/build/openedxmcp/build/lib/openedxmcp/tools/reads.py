"""Read-only tools (LMS facade). Require a staff/superuser key."""
from ..client import FacadeError


def _get(client, path, params=None):
    try:
        return client.get(path, params=params)
    except FacadeError as exc:
        return {"error": exc.detail, "status": exc.status_code}


def register(mcp, client):
    @mcp.tool()
    def whoami() -> dict:
        """Identity, staff/superuser flags, auth method, and scopes for the
        current key. Run this first to confirm what you are permitted to do."""
        return _get(client, "whoami/")

    @mcp.tool()
    def analytics_overview(org: str = "") -> dict:
        """Platform (or single-org) stat cards: course count, total enrollments,
        per-course enrollment counts. Cheap cached reads."""
        return _get(client, "analytics/overview/", {"org": org} if org else None)

    @mcp.tool()
    def list_courses(org: str = "", limit: int = 100, offset: int = 0) -> dict:
        """List courses from the CourseOverview cache (course_id, name, org,
        schedule, pacing). Filter by org; paginate with limit/offset."""
        params = {"limit": limit, "offset": offset}
        if org:
            params["org"] = org
        return _get(client, "courses/", params)

    @mcp.tool()
    def course_detail(course_id: str) -> dict:
        """One course's metadata plus per-mode enrollment counts. course_id is the
        course-v1 key (e.g. course-v1:Org+CS101+2024)."""
        return _get(client, f"courses/{course_id}/")

    @mcp.tool()
    def list_users(q: str = "", is_staff: str = "", limit: int = 50, offset: int = 0) -> dict:
        """Search users by username/email. is_staff='true'|'false' filters by the
        staff flag. Paginate with limit/offset."""
        params = {"limit": limit, "offset": offset}
        if q:
            params["q"] = q
        if is_staff:
            params["is_staff"] = is_staff
        return _get(client, "users/", params)

    @mcp.tool()
    def user_roles(username: str) -> dict:
        """All course/org roles plus staff/superuser flags for one user."""
        return _get(client, f"users/{username}/roles/")

    @mcp.tool()
    def course_team(course_id: str) -> dict:
        """Instructors and staff on a course."""
        return _get(client, f"courses/{course_id}/team/")

    @mcp.tool()
    def user_grade(username: str, course_id: str) -> dict:
        """One learner's course grade (percent, passed, letter). May compute if
        not persisted — do not sweep many users with this."""
        return _get(client, f"grades/{username}/{course_id}/")
