# Gecko Coin Bot

A Telegram Bot which is working with [Gecko Coin API](https://www.coingecko.com/ru/api/documentation).
This is a pet-project for my portfolio that created to show my programming skills:
- designing RESTfull API service with FastAPI
- simple and readable Python code (flake8)
- designing microservice architecture with Docker and Docker-Compose
- working with NoSQL databases as MongoDB
- testing code with PyTest
- ML-model workflow with Mlflow

Whole project contains 6 services:
1. Telegram Bot in Aiogram 3
2. Backend with FastAPI + nginx
3. MongoDB
4. Redis
5. Mlflow client + Mlflow server to working with ml-models
6. Scheduler



Tree:
```
.
├── bot
│   ├── config.py
│   ├── Dockerfile
│   ├── handlers
│   │   ├── client.py
│   │   ├── handlers.py
│   │   ├── help_command.py
│   │   ├── __init__.py
│   │   ├── misc.py
│   ├── main.py
├── fastapi_app
│   ├── config.py
│   ├── Dockerfile
│   ├── main.py
│   ├── models
│   │   ├── exc.py
│   │   ├── __init__.py
│   │   ├── misc.py
│   │   ├── models.py
│   │   └── repository.py
│   ├── mongodb
│   │   ├── __init__.py
│   │   ├── mongodb.py
│   ├── routers
│   │   ├── __init__.py
│   │   ├── other.py
│   │   ├── pairs.py
│   │   └── users.py
│   └── tests
│       └── test_healthcheck.py
├── mlflow_client
│   ├── config.py
│   ├── Dockerfile
│   ├── main.py
│   └── routers
│       ├── __init__.py
│       ├── misc.py
│       └── proph.py
├── mlflow_server
│   ├── mlartifacts
│   └── mlruns
├── mongo
│   └── data
├── nginx
│   ├── Dockerfile
│   └── nginx.conf
├── pgdata
├── scheduler
│   ├── config.py
│   ├── Dockerfile
│   ├── main.py
│   └── tasks
│       ├── __init__.py
│       └── tasks.py
├── setup.cfg
├── tests
│   ├── conftest.py
│   └── test_handlers
│       ├── __init__.py
│       └── test_start.py
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── .gitignore
├── setup.cfg
├── poetry.lock
├── pyproject.toml
├── README.md

```
