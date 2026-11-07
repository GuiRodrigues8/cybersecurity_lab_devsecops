import pytest
import baseline_secure_coding_api as api


@pytest.fixture
def client():
    with api.app.test_client() as client:
        yield client


def login(client, username, password):
    response = client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_student_can_access_own_grades(client):
    login(client, "alice", "alicepw")

    response = client.get("/grades/1001")

    assert response.status_code == 200


def test_student_cannot_access_other_student_grades(client):
    login(client, "alice", "alicepw")

    response = client.get("/grades/1002")

    assert response.status_code == 403


def test_student_can_access_own_profile(client):
    login(client, "alice", "alicepw")

    response = client.get("/students/1001/profile")

    assert response.status_code == 200


def test_student_cannot_access_other_student_profile(client):
    login(client, "alice", "alicepw")

    response = client.get("/students/1002/profile")

    assert response.status_code == 403

@pytest.fixture
def isolated_materials(tmp_path, monkeypatch):
    materials = tmp_path / "materials"
    materials.mkdir()

    nested = materials / "nested"
    nested.mkdir()

    (materials / "safe.txt").write_text(
        "This is an authorised file."
    )

    outside = tmp_path / "outside.txt"
    outside.write_text("CONFIDENTIAL OUTSIDE FILE")

    outside_variation = tmp_path / "outside-variation.txt"
    outside_variation.write_text("ANOTHER CONFIDENTIAL FILE")

    monkeypatch.setattr(api, "MATERIALS_DIR", materials)

    return materials, outside, outside_variation


def test_authenticated_user_can_download_allowed_file(
    client, isolated_materials
):
    login(client, "alice", "alicepw")

    response = client.get(
        "/files",
        query_string={"path": "safe.txt"},
    )

    assert response.status_code == 200
    assert response.get_data(as_text=True) == (
        "This is an authorised file."
    )


def test_path_traversal_is_rejected(
    client, isolated_materials
):
    login(client, "alice", "alicepw")

    _, outside, _ = isolated_materials

    response = client.get(
        "/files",
        query_string={"path": "../outside.txt"},
    )


    assert response.status_code in (403, 404)
    assert outside.read_text() not in response.get_data(as_text=True)


def test_absolute_path_access_is_rejected(
    client, isolated_materials
):
    login(client, "alice", "alicepw")

    _, outside, _ = isolated_materials

    response = client.get(
        "/files",
        query_string={"path": str(outside)},
    )


    assert response.status_code in (403, 404)
    assert outside.read_text() not in response.get_data(as_text=True)