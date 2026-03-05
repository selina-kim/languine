# Project Structure

```
backend/
├── src/
│   ...
│   └── main.py          # flask application entry point
├── Dockerfile           # docker configuration
├── poetry.lock          # package manager dependencies
├── pyproject.toml       # project dependencies and metadata
└── README.md
```

# Development

## Setup & Installation

### Install Docker

Installation will vary depending on Windows/WSL/MacOS.

### Run the Application

#### 1. Ensure docker daemon is running

On WSL:

```bash
sudo service --status-all
sudo service docker start
```

#### 2. Start the docker image of the backend service

```bash
cd backend

docker compose down -v            # removes all volumes
docker compose build --no-cache   # rebuild images (takes long time, can be skipped depending on circumstance)
docker compose up                 # start docker containers (terminal stays open after executing command, can see logs in real time)
# or, alternatively
docker compose up -d              # start docker containers in background (can close terminal)
```

Check if tables exist:
```bash
docker compose exec db psql -U postgres -d languine -c "\dt"
```

Check if test user exists:
```bash
docker compose exec db psql -U postgres -d languine -c "SELECT * FROM Users WHERE u_id = 'test-user-id';"
```

#### 3. Interact with APIs

For example, sending a request to the translation api:

```bash
curl "http://localhost:8080/translate?text=Hello&target=KO&source=EN"
```

Should get this output:

```
{"detectedSourceLang": "EN", "translatedText": "안녕하세요"}
```

### Run Tests

```bash
cd backend
py -3.12 -m pytest
```