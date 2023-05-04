from fastapi.testclient import TestClient
from main import app

client = TestClient(app=app)

def test_healthcheck():
    response = client.get('/healthcheck')
    assert response.status_code == 200
    assert response.json() == {
        'status': 'success',
        'message': 'Server is running!'
    }

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
        "detail": "Inserted: True"
    }

# def test_create_same_user():
#     response = client.post(
#         '/user/create',
#         json={
#             "user_id": 37317,
#             "user_name": "Jegga",
#             "n_pairs": 3
#         })
#     assert response.status_code == 434

def test_delete_user():
    resp = client.delete('/user/37317/delete_user')
    assert resp.status_code == 200
    assert resp.json() == {
        "status": "success",
        "detail": "{'n': 1, 'ok': 1.0}"
    }
