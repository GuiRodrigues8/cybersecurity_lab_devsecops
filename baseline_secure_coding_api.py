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

def find_grade(student_id, course_id):
    for row in GRADES:
        if row["student_id"] == student_id and row["course_id"] == course_id:
            return row
    return None


# -----------------------------------------------------------------------------
# REST API Endpoints
# -----------------------------------------------------------------------------

@app.get("/")
def index():
    return {
        "message": "Baseline Secure Coding API",
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
    #profile = STUDENT_PROFILES.get(int(student_id))
    if "user" not in flask.session:
      return {"error": "unauthenticated"}, 401

    try:
        sid = int(student_id)
    except (ValueError, TypeError):
        return {"error": "invalid student id"}, 400

    role = flask.session.get("role")
    if role == "student":
        if flask.session.get("student_id") != sid:
            return {"error": "forbidden"}, 403
    elif role == "professor":
        student_courses = [row["course_id"] for row in GRADES if row["student_id"] == sid]
        prof_courses = flask.session.get("courses", [])
        if not any(c in prof_courses for c in student_courses):
            return {"error": "forbidden"}, 403
    elif role != "admin":
        return {"error": "forbidden"}, 403

    profile = STUDENT_PROFILES.get(sid)
    if profile is None:
        return {"error": "student not found"}, 404
    return flask.jsonify(profile)

@app.get("/grades/<student_id>")
def get_grades(student_id):
#    sid = int(student_id)
#    rows = [row for row in GRADES if row["student_id"] == sid]
    if "user" not in flask.session:
       return {"error": "unauthenticated"}, 401

    try:
        sid = int(student_id)
    except (ValueError, TypeError):
        return {"error": "invalid student id"}, 400

    role = flask.session.get("role")
    if role == "student":
        if flask.session.get("student_id") != sid:
            return {"error": "forbidden"}, 403
        rows = [row for row in GRADES if row["student_id"] == sid]
    elif role == "professor":
        prof_courses = flask.session.get("courses", [])
        rows = [row for row in GRADES if row["student_id"] == sid and row["course_id"] in prof_courses]
    elif role == "admin":
        rows = [row for row in GRADES if row["student_id"] == sid]
    else:
        return {"error": "forbidden"}, 403
    return flask.jsonify(rows)

@app.post("/grades/update")
def update_grade():
    data = flask.request.get_json()

    student_id = data["student_id"]
    course_id = data["course_id"]
    grade = data["grade"]

    row = find_grade(student_id, course_id)
    if row is None:
        GRADES.append({"student_id": student_id, "course_id": course_id, "grade": grade})
    else:
        row["grade"] = grade

    return {"status": "ok", "student_id": student_id, "course_id": course_id, "grade": grade}

@app.get("/files")
def download_file():
    raw_path = flask.request.args.get("path", "")
#    target = MATERIALS_DIR / raw_path
#    return flask.send_file(target)
    if not raw_path:
        return {"error": "path parameter required"}, 400
    
    try:
        base_dir = MATERIALS_DIR.resolve()
        target = (base_dir / raw_path).resolve()
        
        if not target.is_relative_to(base_dir) or not target.is_file():
            return {"error": "file not found"}, 404
            
        return flask.send_file(target)
    except (ValueError, FileNotFoundError, OSError):
        return {"error": "file not found"}, 404

@app.errorhandler(Exception)
def handle_error(exc):
    return {
        "error": str(exc),
        "type": exc.__class__.__name__,
    }, 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)