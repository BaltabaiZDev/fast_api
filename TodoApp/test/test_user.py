from .utils import *
from ..routers.users import get_db, get_current_user
from fastapi import status

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


def test_return_users(test_user):
    response = client.get("/user")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    first_user = data[0]
    assert first_user["username"] == "zhani"
    assert first_user["email"] == "zhani@example.com"
    assert first_user["role"] == "admin"
    assert first_user["first_name"] == "Zhanibek"
    assert first_user["last_name"] == "Baltabay"
    assert first_user["phone_number"] == "1234567890"
    assert any(user["username"] == "zhani" for user in data)


def test_change_password_success(test_user):
    response = client.put(
        "/user/password",
        json={
            "password": "test1234",
            "new_password": "Newpasswo$rd1"
        }
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_change_password_invalid_current_password(test_user):
    response = client.put(
        "/user/password",
        json={
            "password": "wrongpassword",
            "new_password": "Newpasswo$rd1"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Error on password change"}


def test_change_phone_number_success(test_user):
    response = client.put("/user/phone_number/12345678900")
    assert response.status_code == status.HTTP_204_NO_CONTENT
