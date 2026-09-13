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


# ============================================================
# Coach vs Admin School Ownership & Single-School Rule Tests
# ============================================================

def test_coach_can_create_and_manage_only_one_school(client):
    coach_token = create_token(client, "coach_pop", "pop@spurs.com", "pass123", role="COACH")

    # 1. Coach creates their first school -> SUCCESS
    payload = {"name": "Pop Academy", "location": "San Antonio"}
    res1 = client.post("/schools", json=payload, headers={"Authorization": f"Bearer {coach_token}"})
    assert res1.status_code == 201
    school_id = res1.json()["id"]

    # 2. Coach tries to create a SECOND school -> 409 Conflict
    res2 = client.post("/schools", json={"name": "Second Academy"}, headers={"Authorization": f"Bearer {coach_token}"})
    assert res2.status_code == 409
    assert "A coach can only create and manage one school" in res2.json()["detail"]

    # 3. Coach can update their own school
    patch_res = client.patch(f"/schools/{school_id}", json={"location": "Texas"}, headers={"Authorization": f"Bearer {coach_token}"})
    assert patch_res.status_code == 200
    assert patch_res.json()["location"] == "Texas"

    # 4. Coach CANNOT update a school created by someone else (e.g. initial school ID 1)
    patch_other = client.patch("/schools/1", json={"name": "Hacked"}, headers={"Authorization": f"Bearer {coach_token}"})
    assert patch_other.status_code == 403

    # 5. Coach CANNOT delete a school created by someone else
    del_other = client.delete("/schools/1", headers={"Authorization": f"Bearer {coach_token}"})
    assert del_other.status_code == 403

    # 6. Coach can delete their own school
    del_own = client.delete(f"/schools/{school_id}", headers={"Authorization": f"Bearer {coach_token}"})
    assert del_own.status_code == 204


def test_admin_can_manage_any_school(client):
    admin_token = create_token(client, "super_admin", "admin@baller.com", "adminpass", role="ADMIN")

    # 1. Admin creates first school
    res1 = client.post("/schools", json={"name": "Admin School 1"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert res1.status_code == 201

    # 2. Admin creates second school -> Allowed for Admin
    res2 = client.post("/schools", json={"name": "Admin School 2"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert res2.status_code == 201

    # 3. Admin can update any school (including seeded school ID 1)
    patch_res = client.patch("/schools/1", json={"location": "Accra Central"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert patch_res.status_code == 200
    assert patch_res.json()["location"] == "Accra Central"


# ============================================================
# School-Name Player Discovery Tests (User's specific request)
# ============================================================

def test_search_players_by_school_name_and_school_roster(client):
    token_ug = create_token(client, "ug_player", "ug@test.com", "pass123", role="PLAYER")
    token_knust = create_token(client, "knust_player", "knust@test.com", "pass123", role="PLAYER")

    # UG is school_id 1, KNUST is school_id 2
    client.post("/players", json={"first_name": "Kofi", "last_name": "Mensah", "position": "PG", "school_id": 1}, headers={"Authorization": f"Bearer {token_ug}"})
    client.post("/players", json={"first_name": "Kwame", "last_name": "Boateng", "position": "C", "school_id": 2}, headers={"Authorization": f"Bearer {token_knust}"})

    # 1. Search players by typing school name: "Ghana"
    search_res = client.get("/players?school_name=Ghana")
    assert search_res.status_code == 200
    players = search_res.json()
    assert len(players) == 1
    assert players[0]["first_name"] == "Kofi"
    assert players[0]["school"]["name"] == "University of Ghana"

    # 2. Search players by typing school name: "Science and Technology"
    search_res2 = client.get("/players?school_name=Science and Technology")
    assert search_res2.status_code == 200
    players2 = search_res2.json()
    assert len(players2) == 1
    assert players2[0]["first_name"] == "Kwame"

    # 3. Direct school players endpoint: GET /schools/1/players
    school_players_res = client.get("/schools/1/players")
    assert school_players_res.status_code == 200
    assert len(school_players_res.json()) == 1
    assert school_players_res.json()[0]["last_name"] == "Mensah"


# ============================================================
# Teams & Team Memberships (Milestone 4 Tests)
# ============================================================

def test_team_crud_and_roster_management(client):
    coach_token = create_token(client, "coach_kerr", "kerr@warriors.com", "pass123", role="COACH")
    player_token = create_token(client, "curry_player", "curry@test.com", "pass123", role="PLAYER")

    # 1. Coach creates a school
    school_res = client.post("/schools", json={"name": "Davidson Academy"}, headers={"Authorization": f"Bearer {coach_token}"})
    school_id = school_res.json()["id"]

    # 2. Player creates profile under that school
    p_res = client.post("/players", json={"first_name": "Wardell", "last_name": "Curry", "position": "PG", "school_id": school_id}, headers={"Authorization": f"Bearer {player_token}"})
    player_id = p_res.json()["id"]

    # 3. Coach creates team for their school
    team_payload = {
        "name": "Wildcats Men's Basketball",
        "school_id": school_id,
        "description": "Varsity Team"
    }
    team_res = client.post("/teams", json=team_payload, headers={"Authorization": f"Bearer {coach_token}"})
    assert team_res.status_code == 201
    team_id = team_res.json()["id"]
    assert team_res.json()["name"] == "Wildcats Men's Basketball"
    assert team_res.json()["school"]["name"] == "Davidson Academy"

    # 4. Add player to team roster
    member_res = client.post(f"/teams/{team_id}/players", json={"player_id": player_id, "jersey_number": 30}, headers={"Authorization": f"Bearer {coach_token}"})
    assert member_res.status_code == 201
    assert member_res.json()["jersey_number"] == 30

    # 5. Prevent duplicate active membership in same team
    dup_member_res = client.post(f"/teams/{team_id}/players", json={"player_id": player_id, "jersey_number": 30}, headers={"Authorization": f"Bearer {coach_token}"})
    assert dup_member_res.status_code == 409

    # 6. Retrieve team roster
    roster_res = client.get(f"/teams/{team_id}/players")
    assert roster_res.status_code == 200
    roster = roster_res.json()
    assert len(roster) == 1
    assert roster[0]["player"]["first_name"] == "Wardell"
    assert roster[0]["jersey_number"] == 30

    # 7. Remove player from team roster
    del_member_res = client.delete(f"/teams/{team_id}/players/{player_id}", headers={"Authorization": f"Bearer {coach_token}"})
    assert del_member_res.status_code == 204

    # 8. Confirm roster is now empty
    roster_res2 = client.get(f"/teams/{team_id}/players")
    assert len(roster_res2.json()) == 0

