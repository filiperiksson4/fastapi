from base64 import b64encode

from fastapi import FastAPI, Security
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.testclient import TestClient

app = FastAPI()

security = HTTPBasic(realm="simple")


@app.get("/users/me")
def read_current_user(credentials: HTTPBasicCredentials = Security(security)):
    return {"username": credentials.username, "password": credentials.password}


client = TestClient(app)


def test_security_http_basic():
    response = client.get("/users/me", auth=("john", "secret"))
    assert response.status_code == 200, response.text
    assert response.json() == {"username": "john", "password": "secret"}


def test_security_http_basic_no_credentials():
    response = client.get("/users/me")
    assert response.status_code == 401, response.text
    assert response.json() == {
        "detail": "Not authenticated. (Check the WWW-Authenticate header for authentication hints)"
    }
    assert response.headers["WWW-Authenticate"] == 'Basic realm="simple"'


def test_security_http_basic_invalid_credentials():
    response = client.get(
        "/users/me", headers={"Authorization": "Basic notabase64token"}
    )
    assert response.status_code == 401, response.text
    assert (
        response.headers["WWW-Authenticate"]
        == 'Basic realm="simple", error="invalid_token", error_description="base64 token has invalid format"'
    )
    assert response.json() == {
        "detail": "Invalid authentication credentials. (Check the WWW-Authenticate header for authentication hints)"
    }


def test_security_http_basic_non_basic_credentials():
    payload = b64encode(b"johnsecret").decode("ascii")
    auth_header = f"Basic {payload}"
    response = client.get("/users/me", headers={"Authorization": auth_header})
    assert response.status_code == 401, response.text
    assert (
        response.headers["WWW-Authenticate"]
        == 'Basic realm="simple", error="invalid_token", error_description="base64 token has invalid format"'
    )
    assert response.json() == {
        "detail": "Invalid authentication credentials. (Check the WWW-Authenticate header for authentication hints)"
    }


def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == {
        "openapi": "3.1.0",
        "info": {"title": "FastAPI", "version": "0.1.0"},
        "paths": {
            "/users/me": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "Successful Response",
                            "content": {"application/json": {"schema": {}}},
                        }
                    },
                    "summary": "Read Current User",
                    "operationId": "read_current_user_users_me_get",
                    "security": [{"HTTPBasic": []}],
                }
            }
        },
        "components": {
            "securitySchemes": {
                "HTTPBasic": {"type": "http", "scheme": "basic", "realm": "simple"}
            }
        },
    }
