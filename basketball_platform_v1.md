# Basketball Player Discovery Platform — Version 1 (MVP)

## 1. Project Vision

Build a backend platform that makes basketball talent more visible and discoverable.

The platform allows basketball players to create professional profiles, associate themselves with schools and teams, record game statistics, and appear in position-based player rankings.

**Version 1 focuses entirely on the backend.**

A frontend developer can later build a web or mobile application on top of the API.

---

## 2. Version 1 Goal

By the end of Version 1, the system should allow:

- Players to create accounts and basketball profiles.
- Schools to exist in the system and have players associated with them.
- Teams to exist and contain players.
- Games to be recorded.
- Player statistics from games to be recorded.
- Rankings to be generated for different basketball positions.
- Authorized users to manage the appropriate resources.
- Developers to consume the entire system through a documented REST API.

The MVP should be **deployed and usable through the API** before additional features are added.

---

## 3. Suggested Technology Stack

### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- Alembic

### Authentication & Security

- JWT authentication
- Password hashing
- Role-based authorization

### Development

- Git + GitHub
- Pytest
- Docker
- Docker Compose
- Environment variables

### Optional for Version 1

- Redis
- GitHub Actions
- Cloud deployment platform

Do not add Redis or other infrastructure just for the sake of using it. Add it when the application has a genuine need for it.

---

# 4. Core Users

## Player

A player can:

- Create an account.
- Create/update their basketball profile.
- Select a primary position.
- Add their school.
- Add teams they have played for.
- View their statistics.
- View their ranking.

## Admin

An administrator can:

- Manage users.
- Manage schools.
- Manage teams.
- Manage games.
- Manage player statistics.
- Correct inaccurate data.
- Manage rankings/configuration.

### Important MVP decision

Do not build separate coach/scout accounts yet.

They can be introduced in Version 2.

---

# 5. Core Entities

The initial database should contain at least the following entities:

```text
User
PlayerProfile
School
Team
TeamMembership
Game
PlayerGameStats
```

A ranking does not necessarily need to be stored as a database table in Version 1. It can initially be calculated from player statistics.

---

# 6. Entity Requirements

## User

Represents authentication and account information.

Suggested fields:

```text
id
email
password_hash
role
is_active
created_at
updated_at
```

Possible roles:

```text
PLAYER
ADMIN
```

---

## PlayerProfile

Represents the basketball identity of a user.

Suggested fields:

```text
id
user_id
first_name
last_name
date_of_birth
height
weight
position
jersey_number
school_id
bio
profile_image_url
created_at
updated_at
```

Positions:

```text
PG — Point Guard
SG — Shooting Guard
SF — Small Forward
PF — Power Forward
C  — Center
```

A player should have one primary position in Version 1.

---

## School

Represents a school/university associated with players.

Suggested fields:

```text
id
name
location
description
logo_url
created_at
updated_at
```

The design should allow multiple players to belong to the same school.

---

## Team

Represents a basketball team.

Suggested fields:

```text
id
name
school_id
description
created_at
updated_at
```

A school may have multiple teams.

For example:

```text
University of Ghana
    ├── Men's Basketball Team
    └── Women's Basketball Team
```

---

## TeamMembership

Represents a player's membership in a team.

Suggested fields:

```text
id
player_id
team_id
jersey_number
start_date
end_date
is_active
```

Do not simply store a single `team_id` on the player if you want to preserve team history.

A player should be able to have:

```text
Team A → 2024
Team B → 2025
Team C → 2026
```

---

## Game

Represents a basketball game.

Suggested fields:

```text
id
home_team_id
away_team_id
game_date
venue
home_score
away_score
status
created_at
updated_at
```

Possible statuses:

```text
SCHEDULED
COMPLETED
CANCELLED
```

A completed game should have a final score.

---

## PlayerGameStats

Represents an individual player's performance in one game.

Suggested fields:

```text
id
game_id
player_id
minutes_played
points
rebounds
assists
steals
blocks
turnovers
field_goals_made
field_goals_attempted
three_pointers_made
three_pointers_attempted
free_throws_made
free_throws_attempted
created_at
updated_at
```

This entity is extremely important because it becomes the foundation for the ranking system.

---

# 7. Relationships

The initial relationship model should look approximately like this:

```text
User
  │
  │ 1:1
  ▼
PlayerProfile
  │
  │ many:1
  ▼
School

PlayerProfile
  │
  │ 1:N
  ▼
TeamMembership
  │
  │ N:1
  ▼
Team
  │
  │ many:1
  ▼
School

Team
  │
  └──────────────┐
                 │
                 ▼
               Game
                 │
                 │ 1:N
                 ▼
          PlayerGameStats
                 │
                 │ N:1
                 ▼
           PlayerProfile
```

You should create the ERD yourself before implementing the database.

---

# 8. Authentication API

Implement:

```http
POST /auth/register
POST /auth/login
GET  /auth/me
```

### Registration

A player should be able to register with:

```json
{
  "email": "player@example.com",
  "password": "secure-password"
}
```

### Login

Return an access token.

The API should use:

```text
Authorization: Bearer <token>
```

for protected endpoints.

---

# 9. Player API

Implement:

```http
POST   /players
GET    /players
GET    /players/{player_id}
PATCH  /players/{player_id}
DELETE /players/{player_id}
```

Players should be able to update their own profiles.

Admins should be able to manage any player profile.

### Player listing

Support basic filtering:

```http
GET /players?position=PG
GET /players?school_id=1
GET /players?position=PG&school_id=1
```

Add pagination.

Example:

```http
GET /players?page=1&limit=20
```

---

# 10. School API

Implement:

```http
POST   /schools
GET    /schools
GET    /schools/{school_id}
PATCH  /schools/{school_id}
DELETE /schools/{school_id}
```

Initially, school creation can be restricted to admins.

---

# 11. Team API

Implement:

```http
POST   /teams
GET    /teams
GET    /teams/{team_id}
PATCH  /teams/{team_id}
DELETE /teams/{team_id}
```

Team membership:

```http
POST   /teams/{team_id}/players
GET    /teams/{team_id}/players
DELETE /teams/{team_id}/players/{player_id}
```

---

# 12. Game API

Implement:

```http
POST   /games
GET    /games
GET    /games/{game_id}
PATCH  /games/{game_id}
DELETE /games/{game_id}
```

A game should contain two different teams.

The system must prevent:

```text
Team A vs Team A
```

---

# 13. Player Statistics API

Implement:

```http
POST /games/{game_id}/stats
GET  /games/{game_id}/stats
GET  /players/{player_id}/stats
```

Example:

```json
{
  "player_id": 12,
  "minutes_played": 32,
  "points": 21,
  "rebounds": 7,
  "assists": 6,
  "steals": 2,
  "blocks": 1,
  "turnovers": 3,
  "field_goals_made": 8,
  "field_goals_attempted": 15,
  "three_pointers_made": 3,
  "three_pointers_attempted": 7,
  "free_throws_made": 2,
  "free_throws_attempted": 3
}
```

The API should validate that the statistics make mathematical sense.

For example:

```text
field_goals_made <= field_goals_attempted
three_pointers_made <= three_pointers_attempted
free_throws_made <= free_throws_attempted
```

---

# 14. Player Statistics

The system should eventually calculate season averages.

For example:

```text
Games Played: 12
PPG: 18.4
RPG: 6.2
APG: 5.7
SPG: 1.8
BPG: 0.9
FG%: 48.2%
3P%: 36.5%
FT%: 81.4%
```

For Version 1, calculate these values dynamically from recorded game statistics.

Avoid manually storing derived averages unless there is a good reason.

---

# 15. Ranking System

This is one of the most important parts of the project.

Create:

```http
GET /rankings
GET /rankings/{position}
```

Examples:

```http
GET /rankings/PG
GET /rankings/SG
GET /rankings/SF
GET /rankings/PF
GET /rankings/C
```

The response might look like:

```json
[
  {
    "rank": 1,
    "player_id": 12,
    "player_name": "Player One",
    "position": "PG",
    "school": "Example University",
    "games_played": 12,
    "ppg": 18.4,
    "apg": 6.1,
    "rpg": 4.2,
    "score": 87.4
  }
]
```

---

# 16. Ranking Formula

Do not try to create a perfect ranking algorithm in Version 1.

Create a transparent scoring system.

For example:

```text
Performance Score =
    points contribution
  + assists contribution
  + rebounds contribution
  + steals contribution
  + blocks contribution
  - turnover penalty
```

The exact weights should be configurable.

Example:

```text
Points:     1.0
Rebounds:   1.2
Assists:    1.5
Steals:     2.0
Blocks:     2.0
Turnovers: -1.0
```

This is only a starting point.

The important engineering requirement is that the ranking calculation should be isolated from the API layer.

For example:

```text
app/
├── api/
├── services/
│   └── ranking_service.py
├── models/
├── schemas/
└── repositories/
```

Later, you can replace the formula with a much more sophisticated ranking model.

---

# 17. Validation Requirements

The backend should reject invalid data.

Examples:

- Invalid email.
- Duplicate email.
- Negative height.
- Negative weight.
- Negative statistics.
- Made shots greater than attempted shots.
- A player recording statistics for a game they did not participate in.
- A team playing against itself.
- Duplicate team membership.
- Unauthorized profile modification.

Return appropriate HTTP status codes.

Examples:

```text
400 — Bad Request
401 — Unauthorized
403 — Forbidden
404 — Not Found
409 — Conflict
422 — Validation Error
```

---

# 18. Authorization Rules

At minimum:

### Public

Anyone can:

```text
View player profiles
View schools
View teams
View rankings
View completed games
```

### Player

A player can:

```text
Edit their own profile
View their statistics
View their team information
```

### Admin

An admin can:

```text
Manage users
Manage players
Manage schools
Manage teams
Manage games
Manage statistics
```

Never trust a user-provided `user_id` to determine ownership.

Ownership must come from the authenticated user.

---

# 19. Database Requirements

Use PostgreSQL.

Use migrations with Alembic.

You should understand:

- Primary keys
- Foreign keys
- Unique constraints
- Indexes
- Relationships
- Transactions
- Cascading behavior

Add indexes where they make sense, especially for frequently queried fields such as:

```text
email
position
school_id
team_id
game_date
player_id
```

Do not blindly index every column.

---

# 20. Error Handling

Create consistent API error responses.

For example:

```json
{
  "error": {
    "code": "PLAYER_NOT_FOUND",
    "message": "The requested player does not exist."
  }
}
```

Avoid exposing internal database errors to API consumers.

---

# 21. Testing Requirements

Use Pytest.

At minimum, test:

### Authentication

- Registration
- Duplicate registration
- Login
- Invalid credentials
- Protected endpoints

### Players

- Create player
- Retrieve player
- Update own profile
- Attempt unauthorized update
- Delete player

### Games

- Create game
- Prevent same-team games
- Complete game

### Statistics

- Record statistics
- Reject impossible statistics
- Calculate averages

### Rankings

- Ranking calculation
- Position filtering
- Ranking order

Aim for meaningful test coverage rather than chasing an arbitrary percentage.

---

# 22. API Documentation

FastAPI automatically provides OpenAPI documentation.

Your final API should have clear:

- Endpoint descriptions
- Request schemas
- Response schemas
- Authentication requirements
- Error responses
- Examples

The Swagger documentation should be good enough that another developer can consume your API without asking you how it works.

---

# 23. Docker

Create a Docker setup that allows the project to run locally with:

```text
FastAPI
PostgreSQL
```

The target should eventually be:

```bash
docker compose up
```

and the entire backend should start.

---

# 24. Environment Variables

Never hard-code secrets.

Use environment variables for things such as:

```text
DATABASE_URL
JWT_SECRET_KEY
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
```

Provide a `.env.example`.

Never commit the real `.env` file.

---

# 25. Suggested Project Structure

A possible structure:

```text
basketball-platform/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── players.py
│   │       ├── schools.py
│   │       ├── teams.py
│   │       ├── games.py
│   │       ├── statistics.py
│   │       └── rankings.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── dependencies.py
│   │
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── repositories/
│   └── db/
│
├── tests/
│
├── alembic/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

This is a suggestion, not a rule. Your architecture may evolve as you learn.

---

# 26. Development Milestones

## Milestone 1 — Project Foundation

- [ ] Create GitHub repository
- [ ] Create FastAPI application
- [ ] Set up virtual environment
- [ ] Configure environment variables
- [ ] Create project structure
- [ ] Create health-check endpoint
- [ ] Set up PostgreSQL
- [ ] Connect SQLAlchemy
- [ ] Configure Alembic

### Completion condition

You can start the API and successfully connect to PostgreSQL.

---

## Milestone 2 — Authentication

- [ ] User model
- [ ] Password hashing
- [ ] Registration
- [ ] Login
- [ ] JWT authentication
- [ ] Current-user dependency
- [ ] Roles
- [ ] Authorization

### Completion condition

A user can register, log in, receive a JWT, and access protected endpoints.

---

## Milestone 3 — Players & Schools

- [ ] Player model
- [ ] School model
- [ ] Player-school relationship
- [ ] Player CRUD
- [ ] School CRUD
- [ ] Validation
- [ ] Pagination
- [ ] Filtering
- [ ] Authorization

### Completion condition

A player can create and maintain a complete basketball profile.

---

## Milestone 4 — Teams

- [ ] Team model
- [ ] Team membership
- [ ] Team CRUD
- [ ] Add/remove players
- [ ] Team history
- [ ] Authorization

### Completion condition

Players can be associated with teams and historical team membership can be represented.

---

## Milestone 5 — Games & Statistics

- [ ] Game model
- [ ] Game CRUD
- [ ] Player game statistics
- [ ] Statistics validation
- [ ] Player season statistics
- [ ] Game history

### Completion condition

You can record an actual basketball game and calculate a player's performance statistics.

---

## Milestone 6 — Ranking Engine

- [ ] Design ranking formula
- [ ] Implement ranking service
- [ ] Position rankings
- [ ] Ranking API
- [ ] Ranking tests

### Completion condition

The API can return ranked players based on recorded performance.

---

## Milestone 7 — Testing & Quality

- [ ] Unit tests
- [ ] API tests
- [ ] Authentication tests
- [ ] Database tests
- [ ] Ranking tests
- [ ] Error handling
- [ ] Code cleanup

### Completion condition

The core system is covered by meaningful automated tests.

---

## Milestone 8 — Docker & Deployment

- [ ] Dockerfile
- [ ] Docker Compose
- [ ] Production configuration
- [ ] Environment variables
- [ ] Deploy PostgreSQL
- [ ] Deploy API
- [ ] Configure HTTPS
- [ ] Test production API

### Completion condition

Someone can access your deployed API and use the documented endpoints.

---

# 27. What NOT to Build Yet

To prevent scope creep, Version 1 should NOT include:

- ❌ Mobile application
- ❌ Web frontend
- ❌ Chat
- ❌ Social media feed
- ❌ AI scouting
- ❌ Video processing
- ❌ Live game streaming
- ❌ Push notifications
- ❌ Complex recommendation system
- ❌ Microservices
- ❌ Payment system

Write these ideas down for Version 2 instead of building them immediately.

---

# 28. Definition of Done

Version 1 is finished when:

- [ ] A user can register.
- [ ] A player can create a basketball profile.
- [ ] Players can be associated with schools.
- [ ] Players can belong to teams.
- [ ] Games can be recorded.
- [ ] Player statistics can be recorded.
- [ ] Player averages can be calculated.
- [ ] Players can be ranked by position.
- [ ] Authentication works.
- [ ] Authorization works.
- [ ] Validation works.
- [ ] Tests pass.
- [ ] API documentation is complete.
- [ ] Docker setup works.
- [ ] The API is deployed.
- [ ] README explains how to use the system.

**Do not move to Version 2 until this checklist is complete.**

---

# 29. Future Vision — Version 2+

After Version 1 is deployed, possible future features include:

### Players

- Player verification
- Highlight videos
- Player comparison
- Advanced profiles
- Career history
- Awards and achievements

### Coaches & Scouts

- Coach accounts
- Scout accounts
- Scouting reports
- Watchlists
- Player recommendations

### Competition

- Leagues
- Tournaments
- Seasons
- Standings
- Team rankings

### Discovery

- Search
- Advanced filters
- Player similarity
- Recruiting tools

### ML

- Player performance prediction
- Player similarity models
- Talent identification
- Team/player recommendations

### Platform

- Notifications
- Mobile app
- Web application
- Analytics dashboard
- Public player profiles

---

# 30. Engineering Principles

Throughout the project:

1. **Understand before coding.**
2. **Design the database before implementing endpoints.**
3. **Keep business logic out of route handlers.**
4. **Validate input at the API boundary.**
5. **Never trust client-provided ownership information.**
6. **Use database constraints to protect data integrity.**
7. **Write tests as you build features.**
8. **Keep commits small and meaningful.**
9. **Do not add technology simply because it is popular.**
10. **Finish Version 1 before expanding the product.**

---

# 31. The First Task

Do NOT start by writing FastAPI endpoints.

Start by designing:

```text
1. Entity Relationship Diagram
2. Database tables
3. Relationships
4. Primary keys
5. Foreign keys
6. Important constraints
7. API resource structure
```

Then implement the database foundation.

The objective is not to finish quickly.

The objective is to build something you can eventually look at and say:

> "I built a real basketball platform from the ground up."

