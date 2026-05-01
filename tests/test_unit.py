import pytest
from app.routes.stores import is_store_open_now
from datetime import datetime


class DummyStore:
    def __init__(self, hours):
        self.hours_mon = hours
        self.hours_tue = hours
        self.hours_wed = hours
        self.hours_thu = hours
        self.hours_fri = hours
        self.hours_sat = hours
        self.hours_sun = hours


def test_hours_open():
    store = DummyStore("00:00-23:59")
    assert is_store_open_now(store) == True


def test_hours_closed():
    store = DummyStore("closed")
    assert is_store_open_now(store) == False


def test_hours_invalid():
    store = DummyStore("invalid")
    assert is_store_open_now(store) == False


def test_hours_format():
    store = DummyStore("09:00-17:00")
    result = is_store_open_now(store)
    assert isinstance(result, bool)