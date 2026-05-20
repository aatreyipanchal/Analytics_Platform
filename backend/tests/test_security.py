from jose import jwt

from app.core.config import settings
from app.core.security import (
    ALGORITHM,
    create_access_token,
    create_refresh_token,
    generate_api_key,
    hash_api_key,
)


def test_access_token_contains_org_and_role() -> None:
    token = create_access_token("42", 7, "Owner")
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "42"
    assert payload["org"] == 7
    assert payload["role"] == "Owner"
    assert payload["type"] == "access"


def test_refresh_token_has_refresh_type() -> None:
    token = create_refresh_token("42", 7)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["type"] == "refresh"
    assert payload["org"] == 7


def test_api_key_hashing_is_stable() -> None:
    secret, hashed = generate_api_key()
    assert secret.startswith("ak_")
    assert hashed == hash_api_key(secret)
