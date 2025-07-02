from ..routers.admin import get_db, get_current_user
from .utils import *
from fastapi import status
from ..models import Todos


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


def test_read_all_admin_authenticated(test_todo):
    response = client.get("/admin/todos")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{
        "id": 1,
        "title": "Test Todo",
        "description": "This is a test todo item",
        "priority": 5,
        "complete": False,
        "owner_id": 1
    }]


def test_delete_todo_admin(test_todo):
    response = client.delete("/admin/todo/1")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == 1).first()

    assert model is None



def test_delete_todo_admin_not_found(test_todo):
    response = client.delete("/admin/todo/1999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Todo not found"}


