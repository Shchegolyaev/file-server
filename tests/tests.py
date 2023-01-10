from http import HTTPStatus

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_ping():
    response = client.get('api/v1/ping')
    assert response.status_code == HTTPStatus.OK
    result = response.json()
    assert result['db'] == 'Not available'
    assert result['cache'] == 'Not available'


def test_list_file():
    response = client.get('api/v1/files/list')
    result = response.json()
    assert len(result) == 1
    assert result.get("detail") == "Not authenticated"


def test_files_download():
    response = client.get('api/v1/files/download')
    result = response.json()
    assert len(result) == 1
    assert result.get("detail") == "Not authenticated"
