# Project Structure

```
backend/
├── src/
│   ├── routes/            # flask route handlers
│   ├── services/          # business logic and external API calls
│   ├── tests/             # unit and integration tests
│   ├── db.py             # database connection and helper functions
│   └── main.py          # flask application entry point
├── Dockerfile           # docker configuration
├── poetry.lock          # package manager dependencies
├── pyproject.toml       # project dependencies and metadata
└── README.md
```

# Development

## Local Setup & Installation

### Install Docker

Installation will vary depending on Windows/WSL/MacOS.

### Run the Application

#### 1. Ensure docker daemon is running

On WSL:

```bash
sudo service --status-all    # check if docker service is running
sudo service docker start    # if it isn't, manually start
```

On other OS platforms, you may have different ways to have the docker daemon running.

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
To run tests and get a coverage report, run the following command from the `backend/src/tests/`
```bash
 docker compose exec backend pytest src/tests/ --cov=routes --cov=services --cov-report=html -v  -m 'integration or not integration'
```
You will find an html report of the coverage results in `backend/src/tests/htmlcov/index.html` after running the command.

To run individual test files, see the docstring of the testfiles in the `backend/src/tests/` directory for instructions.

**Note:** You need a valid Google ID Token to run the auth integration tests. Otherwise some tests will be skipped. Also keep in mind that the ID token expires within an hour, and when you refresh it, you need to rebuild the docker image for it to pick up the new token.

#### Getting a Google ID Token for Testing
1. Go to https://developers.google.com/oauthplayground
2. Click the gear icon in the top right corner and check the box that says "Use your own OAuth credentials". Then input the client ID and client secret that is shared in the env file
3. In the left panel, find and select the scope that says "https://www.googleapis.com/auth/userinfo.email" and "https://www.googleapis.com/auth/userinfo.profile" (under "Google OAuth2 API v2")
4. Click the "Authorize APIs" button and go through the Google sign-in flow
5. After authorizing, click the "Exchange authorization code for tokens" button
6. You should now see an ID token in the "ID Token" field. Copy this token and set it as the value for the `GOOGLE_ID_TOKEN` variable in the `.env` file.

## Remote Access Home Server

### 1. Remote SSH into server

Ask team member for steps.

### 2. View Backend Docker Container Logs

```bash
cd ~/projects/languine
docker compose logs -f
```

### 3. View Status and Metrics

Server main dashboard:

```bash
source ~/admin-dashboard/dashboard.sh
```

Monitor docker container metrics:

```bash
ctop
```

Monitor server resource usage:

```bash
btop
```
