import socket

import pytest

from app.core.errors import ValidationError
from app.core.secure_config import (
    create_pinned_http_transport,
    validate_external_api_url,
)


def test_external_api_url_rejects_private_resolution(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))
        ],
    )
    with pytest.raises(ValidationError):
        validate_external_api_url("https://mineru.example.test/api")


def test_external_api_url_accepts_global_https_resolution(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ],
    )
    assert (
        validate_external_api_url("https://mineru.example.test/api")
        == "https://mineru.example.test/api"
    )


def test_external_api_url_rejects_metadata_hostname():
    with pytest.raises(ValidationError):
        validate_external_api_url("https://metadata.google.internal/computeMetadata/v1")


def test_external_api_transport_pins_validated_address(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ],
    )
    transport = create_pinned_http_transport("https://mineru.example.test/api")
    backend = transport._pool._network_backend
    assert backend.hostname == "mineru.example.test"
    assert backend.addresses == ["93.184.216.34"]
