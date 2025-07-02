import pytest


def test_equal_or_not():
    assert 1 == 1


def test_is_instance():
    assert isinstance("hello", str)
    assert isinstance(123, int)


def test_boolean():
    val = True
    assert val is True
    assert ('hello' == 'heollo') is False


def test_list():
    list1 = [1, 2, 3]
    list2 = [False, False]
    assert 1 in list1
    assert 4 not in list1
    assert all(list1) is True  # all elements are not True
    assert any(list2) is False  # no elements are True


class Student:
    def __init__(self, first_name: str, last_name: str, major: str, years: int):
        self.first_name = first_name
        self.last_name = last_name
        self.major = major
        self.years = years


@pytest.fixture
def default_employee():
    return Student("John", "Doe", "Computer Science", 3)


def test_person_initialization(default_employee):
    assert default_employee.first_name == "John", "First name should be John"
    assert default_employee.last_name == "Doe", "Last name should be Doe"
    assert default_employee.major == "Computer Science"
    assert default_employee.years == 3
