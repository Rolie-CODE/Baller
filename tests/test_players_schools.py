import pytest
from tests.conftest import TestingSessionLocal
import models
from security import hash_password


def create_token(client, username, email, password, role="PLAYER"):
    db = TestingSessionLocal()
    user = models.User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    res = client.post("/auth/login", json={"username": username, "password": password})
    return res.json()["access_token"]


# ==========================================
# School Tests
# ==========================================

def test_initial_schools_seeded(client):
    res = client.get("/schools")
    assert res.status_code == 200
    names = [s["name"] for s in res.json()]
    assert "University of Ghana" in names
    assert "Kwame Nkrumah University of Science and Technology" in names
    assert "University of Cape Coast" in names


def test_create_school_as_admin(client):
    admin_token = create_token(client, "admin1", "admin1@platform.com", "adminpass", role="ADMIN")
    payload = {
        "name": "Ashesi University",
        "location": "Berekuso",
        "description": "Private university"
    }
    res = client.post("/schools", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 201
    assert res.json()["name"] == "Ashesi University"
    assert res.json()["location"] == "Berekuso"


def test_create_school_as_player_forbidden(client):
    player_token = create_token(client, "player1", "player1@test.com", "pass123", role="PLAYER")
    res = client.post("/schools", json={"name": "New School"}, headers={"Authorization": f"Bearer {player_token}"})
    assert res.status_code == 403


def test_create_school_duplicate_conflict(client):
    admin_token = create_token(client, "admin2", "admin2@platform.com", "adminpass", role="ADMIN")
    res = client.post("/schools", json={"name": "University of Ghana"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 409
    assert "already exists" in res.json()["detail"]


def test_update_and_delete_school_as_admin(client):
    admin_token = create_token(client, "admin3", "admin3@platform.com", "adminpass", role="ADMIN")
    # 1. Update
    res = client.patch("/schools/1", json={"location": "Legon, Accra"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert res.json()["location"] == "Legon, Accra"

    # 2. Delete
    del_res = client.delete("/schools/1", headers={"Authorization": f"Bearer {admin_token}"})
    assert del_res.status_code == 204

    # 3. Confirm 404
    get_res = client.get("/schools/1")
    assert get_res.status_code == 404


# ==========================================
# Player Profile Tests
# ==========================================

def test_create_player_profile_success(client):
    player_token = create_token(client, "curry30", "curry@warriors.com", "splash123", role="PLAYER")
    payload = {
        "first_name": "Stephen",
        "last_name": "Curry",
        "position": "PG",
        "height": 74.0,
        "weight": 185.0,
        "jersey_number": 30,
        "school_id": 1,
        "bio": "Greatest shooter of all time"
    }
    res = client.post("/players", json=payload, headers={"Authorization": f"Bearer {player_token}"})
    assert res.status_code == 201
    data = res.json()
    assert data["first_name"] == "Stephen"
    assert data["position"] == "PG"
    assert data["height"] == 74.0
    assert data["school"]["name"] == "University of Ghana"


def test_create_player_profile_as_coach_forbidden(client):
    coach_token = create_token(client, "coachkerr", "kerr@warriors.com", "coachpass", role="COACH")
    payload = {
        "first_name": "Steve",
        "last_name": "Kerr",
        "position": "PG"
    }
    res = client.post("/players", json=payload, headers={"Authorization": f"Bearer {coach_token}"})
    assert res.status_code == 403
    assert "Only players can create a basketball profile" in res.json()["detail"]


def test_create_duplicate_player_profile_conflict(client):
    player_token = create_token(client, "lebron23", "lebron@lakers.com", "kingpass", role="PLAYER")
    payload = {
        "first_name": "LeBron",
        "last_name": "James",
        "position": "SF"
    }
    client.post("/players", json=payload, headers={"Authorization": f"Bearer {player_token}"})

    # Try creating a second profile for the same user
    res2 = client.post("/players", json=payload, headers={"Authorization": f"Bearer {player_token}"})
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_create_player_invalid_position(client):
    player_token = create_token(client, "invalidpos", "inv@test.com", "pass123", role="PLAYER")
    payload = {
        "first_name": "Bad",
        "last_name": "Player",
        "position": "GOALKEEPER"  # Invalid basketball position
    }
    res = client.post("/players", json=payload, headers={"Authorization": f"Bearer {player_token}"})
    assert res.status_code == 422


def test_create_player_negative_height_or_weight(client):
    player_token = create_token(client, "negval", "neg@test.com", "pass123", role="PLAYER")
    payload = {
        "first_name": "Negative",
        "last_name": "Values",
        "position": "C",
        "height": -10.0
    }
    res = client.post("/players", json=payload, headers={"Authorization": f"Bearer {player_token}"})
    assert res.status_code == 422


def test_create_player_nonexistent_school(client):
    player_token = create_token(client, "noschool", "noschool@test.com", "pass123", role="PLAYER")
    payload = {
        "first_name": "No",
        "last_name": "School",
        "position": "PF",
        "school_id": 9999
    }
    res = client.post("/players", json=payload, headers={"Authorization": f"Bearer {player_token}"})
    assert res.status_code == 404
    assert "School not found" in res.json()["detail"]


def test_get_and_list_players_filtering(client):
    token1 = create_token(client, "pg_player", "pg@test.com", "pass123", role="PLAYER")
    token2 = create_token(client, "c_player", "c@test.com", "pass123", role="PLAYER")

    client.post("/players", json={"first_name": "PG", "last_name": "One", "position": "PG", "school_id": 1}, headers={"Authorization": f"Bearer {token1}"})
    client.post("/players", json={"first_name": "C", "last_name": "Two", "position": "C", "school_id": 2}, headers={"Authorization": f"Bearer {token2}"})

    # Filter by position
    pg_res = client.get("/players?position=PG")
    assert pg_res.status_code == 200
    assert len(pg_res.json()) == 1
    assert pg_res.json()[0]["position"] == "PG"

    # Filter by school
    school2_res = client.get("/players?school_id=2")
    assert school2_res.status_code == 200
    assert len(school2_res.json()) == 1
    assert school2_res.json()[0]["school_id"] == 2


def test_update_player_profile_authorization(client):
    owner_token = create_token(client, "owner", "owner@test.com", "pass123", role="PLAYER")
    intruder_token = create_token(client, "intruder", "intruder@test.com", "pass123", role="PLAYER")
    admin_token = create_token(client, "admin_user", "admin_user@test.com", "adminpass", role="ADMIN")

    res = client.post("/players", json={"first_name": "Real", "last_name": "Owner", "position": "SG"}, headers={"Authorization": f"Bearer {owner_token}"})
    player_id = res.json()["id"]

    # 1. Other player cannot update
    intruder_res = client.patch(f"/players/{player_id}", json={"first_name": "Hacked"}, headers={"Authorization": f"Bearer {intruder_token}"})
    assert intruder_res.status_code == 403

    # 2. Owner can update
    owner_res = client.patch(f"/players/{player_id}", json={"jersey_number": 24}, headers={"Authorization": f"Bearer {owner_token}"})
    assert owner_res.status_code == 200
    assert owner_res.json()["jersey_number"] == 24

    # 3. Admin can update
    admin_res = client.patch(f"/players/{player_id}", json={"first_name": "Verified"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_res.status_code == 200
    assert admin_res.json()["first_name"] == "Verified"

    # 4. Admin can delete
    del_res = client.delete(f"/players/{player_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert del_res.status_code == 204
