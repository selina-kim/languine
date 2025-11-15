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

Start the backend service:

```bash
cd backend
docker compose up
```
