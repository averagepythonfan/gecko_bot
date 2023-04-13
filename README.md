# Gecko Coin Bot

A Telegram Bot which is working with (Gecko Coin API)[https://www.coingecko.com/ru/api/documentation].
This is a pet-project for my portfolio that created to show my programming skills:
- designing RESTfull API service with FastAPI
- simple and readable Python code
- designing microservice architecture with Docker and Docker-Compose
- working with NoSQL databases as MongoDB
- testing code with PyTest

Whole project contains 4 services:
1. Telegram Bot in Aiogram 3
2. Backend with FastAPI
3. MongoDB
4. mlflow server to working with ml-models

Tree:
```
.
├── bot
│   ├── handlers
│   │   ├── client.py
│   │   ├── handlers.py
│   │   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── Dockerfile
├── docker-compose.yml
├── fastapi
│   ├── models
│   │   ├── exceptions.py
│   │   ├── __init__.py
│   │   ├── misc.py
│   │   ├── models.py
│   │   └── repository.py
│   ├── mongodb
│   │   ├── __init__.py
│   │   ├── mongodb.py
│   └── routers
│       ├── __init__.py
│       ├── other.py
│       ├── pairs.py
│       └── users.py
│   ├── config.py
│   ├── Dockerfile
│   ├── main.py
├── poetry.lock
├── pyproject.toml
├── README.md
└── tests
    ├── conftest.py
    └── test_handlers
        ├── __init__.py
        └── test_start.py

```