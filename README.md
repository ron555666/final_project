# Store Locator API

A backend service for searching and managing store locations, built with FastAPI.

---

## Features

### Store Search

- Search by:
  - Coordinates (latitude / longitude)
  - Address
  - ZIP code
- Filters:
  - Radius
  - Store types
  - Services (many-to-many)
  - Open now
  - Minimum rating

---

### Store Management

- Create, update, and delete stores
- Partial update (PATCH)
- Many-to-many relationship with services

---

### Authentication and RBAC

- JWT-based authentication
- Roles:
  - Admin
  - Marketer
  - Viewer
- Permissions:
  - Admin: full access
  - Marketer: manage stores
  - Viewer: read-only access

---

### Reviews

- Add reviews to stores
- Calculate average rating
- Flag inappropriate reviews

---

### Import / Export

- CSV import for bulk store creation
- Validation and error reporting

---

### Additional Features

- Rate limiting
- Geocoding integration
- Error handling for edge cases

---

## Tech Stack

- FastAPI (API framework)
- SQLAlchemy (ORM)
- Pydantic (data validation and serialization)
- PostgreSQL (production database)
- SQLite (testing database)
- In-memory cache (for geocoding results)
- Pytest (testing)
- GitHub Actions (CI)

---

## Testing

Run tests locally:

```bash
$env:DATABASE_URL="sqlite:///./test.db"
$env:SECRET_KEY="test-secret-key"
$env:PYTHONPATH="."
pytest --cov=app
```
