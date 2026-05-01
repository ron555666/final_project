from app.routes.stores import is_store_open_now
from app.utils.security import hash_password, verify_password


class FakeStore:
    hours_mon = "00:00-23:59"
    hours_tue = "00:00-23:59"
    hours_wed = "00:00-23:59"
    hours_thu = "00:00-23:59"
    hours_fri = "00:00-23:59"
    hours_sat = "00:00-23:59"
    hours_sun = "00:00-23:59"


class ClosedStore:
    hours_mon = "closed"
    hours_tue = "closed"
    hours_wed = "closed"
    hours_thu = "closed"
    hours_fri = "closed"
    hours_sat = "closed"
    hours_sun = "closed"


def test_password_hash_and_verify():
    password = "TestPassword123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True


def test_password_verify_wrong_password():
    password = "TestPassword123!"
    hashed = hash_password(password)

    assert verify_password("WrongPassword123!", hashed) is False


def test_store_open_now():
    store = FakeStore()

    assert is_store_open_now(store) is True


def test_store_closed_now():
    store = ClosedStore()

    assert is_store_open_now(store) is False