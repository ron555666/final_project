import math

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


def haversine_miles(lat1, lon1, lat2, lon2):
    radius_miles = 3958.8

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return radius_miles * c


def test_distance_calculation_haversine():
    distance = haversine_miles(37.7749, -122.4194, 34.0522, -118.2437)

    assert 330 <= distance <= 370


def test_bounding_box_calculation():
    lat = 37.77
    lon = -122.41
    radius = 10

    latitude_delta = radius / 69.0
    longitude_delta = radius / (69.0 * math.cos(math.radians(lat)))

    min_lat = lat - latitude_delta
    max_lat = lat + latitude_delta
    min_lon = lon - longitude_delta
    max_lon = lon + longitude_delta

    assert min_lat < lat < max_lat
    assert min_lon < lon < max_lon


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