from fastapi.testclient import TestClient
from main import app

client = TestClient(app=app)


async def test_create_user():
    response = client.post(
        '/user/create',
        json={
            "user_id": 37317,
            "user_name": "kegga",
            "n_pairs": 3
        })
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "detail": "True"
    }


def test_create_same_user():
    response = client.post(
        '/user/create',
        json={
            "user_id": 37317,
            "user_name": "Jegga",
            "n_pairs": 3
        })
    assert response.status_code == 434


def test_users_data():
    response = client.get(
        '/user/all'
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "deatil": "users data",
        "data": [
            {
                "user_id": 37317,
                "user_name": "kegga",
                "n_pairs": 3,
                "pairs": []
            }
        ]
    }


def test_user_data_fail():
    response = client.get(
        '/user/345272'
    )

    assert response.status_code == 435
    assert response.json() == {
        "detail": "user not found"
    }


def test_user_data_success():
    response = client.get(
        '/user/37317'
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "user_data": {
            "user_id": 37317,
            "user_name": "kegga",
            "n_pairs": 3,
            "pairs": []
        }
    }


def test_user_set_n_pairs_success():
    response = client.put(
        '/user/37317/set_n_pairs/4'
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "user_data": "True"
    }


def test_user_set_n_pairs_success():
    response = client.put(
        '/user/37317/set_n_pairs/a'
    )

    assert response.status_code == 422


def test_delete_user():
    resp = client.delete('/user/37317/delete_user')
    assert resp.status_code == 200
    assert resp.json() == {
        "status": "success",
        "detail": "True"
    }
