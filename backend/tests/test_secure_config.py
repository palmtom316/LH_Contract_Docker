import socket

import pytest

from app.core.errors import ValidationError
from app.core.secure_config import validate_external_api_url


def test_external_api_url_rejects_private_resolution(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))])
    with pytest.raises(ValidationError):
        validate_external_api_url("https://mineru.example.test/api")


def test_external_api_url_accepts_global_https_resolution(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))])
    assert validate_external_api_url("https://mineru.example.test/api") == "https://mineru.example.test/api"


def test_external_api_url_rejects_metadata_hostname():
    with pytest.raises(ValidationError):
        validate_external_api_url("https://metadata.google.internal/computeMetadata/v1")
