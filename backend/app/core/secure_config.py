"""Encryption and outbound endpoint validation for sensitive integrations."""

import base64
import hashlib
import ipaddress
import socket
import ssl
from typing import Set
from urllib.parse import urlparse

from cryptography.fernet import Fernet, InvalidToken
import httpcore
import httpx

from app.config import settings
from app.core.errors import ValidationError


_METADATA_HOSTS = {
    "metadata",
    "metadata.google.internal",
    "instance-data",
    "instance-data.ec2.internal",
}


def protect_config_secret(value: str) -> str:
    if not settings.CONFIG_ENCRYPTION_KEY:
        raise ValidationError(
            message="未配置 CONFIG_ENCRYPTION_KEY，不能保存 MinerU 密钥"
        )
    key = base64.urlsafe_b64encode(
        hashlib.sha256(settings.CONFIG_ENCRYPTION_KEY.encode()).digest()
    )
    return Fernet(key).encrypt(value.encode()).decode()


def reveal_config_secret(value: str) -> str:
    if not settings.CONFIG_ENCRYPTION_KEY:
        raise ValidationError(
            message="未配置 CONFIG_ENCRYPTION_KEY，不能读取 MinerU 密钥"
        )
    key = base64.urlsafe_b64encode(
        hashlib.sha256(settings.CONFIG_ENCRYPTION_KEY.encode()).digest()
    )
    try:
        return Fernet(key).decrypt(value.encode()).decode()
    except (InvalidToken, ValueError):
        raise ValidationError(message="MinerU 密钥配置损坏")


def _validated_public_addresses(hostname: str, port: int) -> Set[str]:
    try:
        addresses = {
            info[4][0]
            for info in socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
        }
    except socket.gaierror:
        raise ValidationError(message="MinerU API 域名无法解析")
    if not addresses:
        raise ValidationError(message="MinerU API 域名无法解析")
    for address in addresses:
        if not ipaddress.ip_address(address).is_global:
            raise ValidationError(message="MinerU API 地址不能指向内部或保留网络")
    return addresses


def validate_external_api_url(value: str) -> str:
    parsed = urlparse(value)
    allowed_schemes = {"https", "http"} if settings.DEBUG else {"https"}
    if (
        parsed.scheme not in allowed_schemes
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValidationError(message="MinerU API 地址无效；生产环境必须使用 HTTPS")
    hostname = parsed.hostname.rstrip(".").lower()
    if (
        hostname in _METADATA_HOSTS
        or hostname.endswith(".internal")
        or hostname.endswith(".local")
    ):
        raise ValidationError(message="MinerU API 地址不能指向元数据或内部主机")
    _validated_public_addresses(
        hostname, parsed.port or (443 if parsed.scheme == "https" else 80)
    )
    return value


class _PinnedNetworkBackend(httpcore.AsyncNetworkBackend):
    def __init__(self, hostname: str, addresses: Set[str]):
        self.hostname = hostname
        self.addresses = sorted(addresses, key=lambda value: (":" in value, value))
        self.backend = httpcore.AnyIOBackend()

    async def connect_tcp(
        self, host, port, timeout=None, local_address=None, socket_options=None
    ):
        if host.rstrip(".").lower() != self.hostname:
            raise httpcore.ConnectError("Outbound redirect host is not pinned")
        last_error = None
        for address in self.addresses:
            try:
                return await self.backend.connect_tcp(
                    address, port, timeout, local_address, socket_options
                )
            except Exception as exc:
                last_error = exc
        raise httpcore.ConnectError(
            "Unable to connect to validated MinerU address"
        ) from last_error

    async def connect_unix_socket(self, path, timeout=None, socket_options=None):
        raise httpcore.ConnectError("Unix sockets are not allowed for MinerU")

    async def sleep(self, seconds):
        await self.backend.sleep(seconds)


class PinnedAsyncHTTPTransport(httpx.AsyncHTTPTransport):
    """HTTPX transport that never re-resolves the validated outbound hostname."""

    def __init__(self, hostname: str, addresses: Set[str]):
        super().__init__(trust_env=False)
        self._pool = httpcore.AsyncConnectionPool(
            ssl_context=ssl.create_default_context(),
            max_connections=5,
            max_keepalive_connections=2,
            network_backend=_PinnedNetworkBackend(hostname, addresses),
        )


def create_pinned_http_transport(value: str) -> PinnedAsyncHTTPTransport:
    validate_external_api_url(value)
    parsed = urlparse(value)
    hostname = parsed.hostname.rstrip(".").lower()
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    addresses = _validated_public_addresses(hostname, port)
    return PinnedAsyncHTTPTransport(hostname, addresses)
