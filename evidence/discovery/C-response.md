Here is the fully secured version of the Flask application addressing
all security requirements (R1 through R7).
Secured API Implementation (baseline_secure_coding_api.py)
Python
import dataclasses
import pathlib
import typing

import flask

app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key"

# -----------------------------------------------------------------------------
# Intentionally small in-memory "database"
# -----------------------------------------------------------------------------

BASE_DIR = pathlib.Path(__file__).resolve().parent
MATERIALS_DIR = BASE_DIR / "materials"
MATERIALS_DIR.mkdir(exist_ok=True)

# Seed a couple of demo files.
(MATERIALS_DIR / "srs-summary.txt").write_text(
    "Secure Requirements Engineering summary", encoding="utf-8"
)
(MATERIALS_DIR / "secure-coding.txt").write_text(
    "Secure coding practices notes", encoding="utf-8"
)


@dataclasses.dataclass
class User:
    username: str
    password: str
    role: str
    student_id: typing.Optional[int] = None
    courses: typing.Optional[list[str]] = None


USERS = {
    "alice": User(username="alice", password="alicepw", role="student", student_id=1001),
    "bob": User(username="bob", password="bobpw", role="student", student_id=1002),
    "prof_srs": User(
        username="prof_srs", password="profpw", role="professor", courses=["SRS"]
    ),
    "admin1": User(username="admin1", password="adminpw", role="admin"),
}

STUDENT_PROFILES = {
    1001: {"student_id": 1001, "name": "Alice", "email": "alice@uc.pt", "program": "MEI"},
    1002: {"student_id": 1002, "name": "Bob", "email": "bob@uc.pt", "program": "MEI"},
}

GRADES = [
    {"student_id": 1001, "course_id": "SRS", "grade": 14},
    {"student_id": 1002, "course_id": "SRS", "grade": 15},
    {"student_id": 1001, "course_id": "SSD", "grade": 16},
]

KNOWN_COURSES = {"SRS", "SSD"}


def find_grade(student_id, course_id):
    for row in GRADES:
        if row["student_id"] == student_id and row["course_id"] == course_id:
            return row
    return None


def parse_student_id(student_id_str):
    try:
        sid = int(student_id_str)
        if sid <= 0:
            return None
        return sid
    except (ValueError, TypeError):
        return None


# -----------------------------------------------------------------------------
# REST API Endpoints
# -----------------------------------------------------------------------------

@app.get("/")
def index():
    return {
        "message": "Secure Coding API",
        "endpoints": [
            "POST /login",
            "POST /logout",
            "GET /me",
            "GET /students/<student_id>/profile",
            "POST /grades/update",
            "GET /grades/<student_id>",
            "GET /files?path=<name>",
        ],
    }


@app.post("/login")
def login():
    username = flask.request.form.get("username", "")
    password = flask.request.form.get("password", "")

    user = USERS.get(username)
    if user is None or user.password != password:
        return {"error": "invalid credentials"}, 401

    flask.session["user"] = user.username
    flask.session["role"] = user.role
    flask.session["student_id"] = user.student_id
    flask.session["courses"] = user.courses or []

    return flask.redirect("/me")


@app.post("/logout")
def logout():
    flask.session.clear()
    return {"status": "logged out"}


@app.get("/me")
def me():
    if "user" not in flask.session:
        return {"user": None}

    return {
        "user": flask.session.get("user"),
        "role": flask.session.get("role"),
        "student_id": flask.session.get("student_id"),
        "courses": flask.session.get("courses"),
    }


@app.get("/students/<student_id>/profile")
def get_profile(student_id):
    if "user" not in flask.session:
        return {"error": "unauthenticated"}, 401

    sid = parse_student_id(student_id)
    if sid is None:
        return {"error": "invalid student id"}, 400

    role = flask.session.get("role")
    session_student_id = flask.session.get("student_id")

    # R2 & R3: Enforcement of student privacy and academic staff scope
    if role == "student":
        if sid != session_student_id:
            return {"error": "unauthorized"}, 403
    elif role == "professor":
        # Professors are not permitted to read student profile records in this exercise
        return {"error": "unauthorized"}, 403
    elif role == "admin":
        pass
    else:
        return {"error": "unauthorized"}, 403

    profile = STUDENT_PROFILES.get(sid)
    if profile is None:
        return {"error": "student not found"}, 404
    return flask.jsonify(profile)


@app.get("/grades/<student_id>")
def get_grades(student_id):
    if "user" not in flask.session:
        return {"error": "unauthenticated"}, 401

    sid = parse_student_id(student_id)
    if sid is None:
        return {"error": "invalid student id"}, 400

    if sid not in STUDENT_PROFILES:
        return {"error": "student not found"}, 404

    role = flask.session.get("role")
    session_student_id = flask.session.get("student_id")
    courses = flask.session.get("courses", [])

    # R3 & R4: Complete authorization and record scoping
    if role == "student":
        if sid != session_student_id:
            return {"error": "unauthorized"}, 403
        rows = [row for row in GRADES if row["student_id"] == sid]
    elif role == "professor":
        # Professors may read grades only for their assigned courses
        rows = [row for row in GRADES if row["student_id"] == sid and row["course_id"] in courses]
        if not rows:
            return {"error": "unauthorized or no permitted records"}, 403
    elif role == "admin":
        rows = [row for row in GRADES if row["student_id"] == sid]
    else:
        return {"error": "unauthorized"}, 403

    return flask.jsonify(rows)


@app.post("/grades/update")
def update_grade():
    if "user" not in flask.session:
        return {"error": "unauthenticated"}, 401

    data = flask.request.get_json(silent=True)
    if not isinstance(data, dict):
        return {"error": "malformed input or missing json"}, 400

    # R5: Validate missing fields
    required_fields = ["student_id", "course_id", "grade"]
    for field in required_fields:
        if field not in data:
            return {"error": f"missing field: {field}"}, 400

    student_id = data["student_id"]
    course_id = data["course_id"]
    grade = data["grade"]

    # R5: Validate student identifier format and existence
    sid = parse_student_id(student_id)
    if sid is None or sid not in STUDENT_PROFILES:
        return {"error": "invalid or non-existent student id"}, 400

    # R5: Validate known course identifier
    if not isinstance(course_id, str) or course_id not in KNOWN_COURSES:
        return {"error": "unknown course identifier"}, 400

    # R5: Validate numeric grade from 0 to 20 inclusive; reject booleans (isinstance(True, int) is True)
    if isinstance(grade, bool) or not isinstance(grade, (int, float)):
        return {"error": "grade must be a numeric value"}, 400
    if not (0 <= grade <= 20):
        return {"error": "grade must be between 0 and 20"}, 400

    # R3 & R4: Role and course scope authorization
    role = flask.session.get("role")
    courses = flask.session.get("courses", [])

    if role == "student":
        return {"error": "unauthorized"}, 403
    elif role == "professor":
        if course_id not in courses:
            return {"error": "unauthorized for this course"}, 403
    elif role == "admin":
        pass
    else:
        return {"error": "unauthorized"}, 403

    # R7: A denied or invalid update leaves stored data unchanged
    row = find_grade(sid, course_id)
    if row is None:
        GRADES.append({"student_id": sid, "course_id": course_id, "grade": grade})
    else:
        row["grade"] = grade

    return {"status": "ok", "student_id": sid, "course_id": course_id, "grade": grade}


@app.get("/files")
def download_file():
    if "user" not in flask.session:
        return {"error": "unauthenticated"}, 401

    raw_path = flask.request.args.get("path", "")
    if not raw_path:
        return {"error": "missing path parameter"}, 400

    try:
        # R6: Prevent path traversal and restrict downloads strictly to materials directory
        target = (MATERIALS_DIR / raw_path).resolve()
        materials_resolved = MATERIALS_DIR.resolve()

        if not target.is_relative_to(materials_resolved):
            return {"error": "access denied"}, 403

        if not target.is_file():
            return {"error": "file not found"}, 404

        return flask.send_file(target)
    except (ValueError, OSError):
        return {"error": "invalid path or access denied"}, 403


@app.errorhandler(Exception)
def handle_error(exc):
    # R7: Secure error handling without leaking internal paths, tracebacks, or exception details
    return {"error": "internal server error"}, 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
Summary of Security Enhancements
- R1 & R7 (Authentication & Error Handling): Protected endpoints
  check session state and return 401 Unauthorized when missing.
  Global exception handler avoids leaking stack traces or internal
  exception details.
- R2 & R3 (Student Privacy & Staff Scope): Students are restricted
  strictly to their own profiles and grades. Professors are explicitly
  blocked from reading student profile records, and grade
  access/updates are limited to their assigned courses (courses).
  Admins retain full read/write privileges.
- R4 (Complete Authorization): Every protected request validates
  permissions dynamically. Grade lists return only records authorized
  for the requester; if no permitted records exist, access is denied
  with 403 Forbidden.
- R5 (Input Validation): Student identifiers are strictly parsed
  as positive integers. Grade updates enforce JSON structure, required
  fields, known courses (SRS, SSD), and numeric grade constraints
  (0 to 20), explicitly rejecting booleans and out-of-bounds
  numbers without modifying stored data.
- R6 (File Access): Material downloads require authentication and
  use path resolution checking (is_relative_to) to completely
  mitigate path traversal attacks (../).
