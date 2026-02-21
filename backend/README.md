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
docker compose up --build db minio backend
```

### 3. Interact with APIs

For example, sending a request to the translation api:

```bash
curl "http://localhost:8080/translate?text=Hello&target=KO&source=EN"
```

Should get this output:

```
{"detectedSourceLang": "EN", "translatedText": "안녕하세요"}
```
