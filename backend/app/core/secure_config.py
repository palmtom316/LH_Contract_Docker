"""Encryption and outbound endpoint validation for sensitive integrations."""
import base64
import hashlib
import ipaddress
import socket
from urllib.parse import urlparse

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings
from app.core.errors import ValidationError


_METADATA_HOSTS = {"metadata", "metadata.google.internal", "instance-data", "instance-data.ec2.internal"}


def protect_config_secret(value: str) -> str:
    if not settings.CONFIG_ENCRYPTION_KEY:
        raise ValidationError(message="未配置 CONFIG_ENCRYPTION_KEY，不能保存 MinerU 密钥")
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.CONFIG_ENCRYPTION_KEY.encode()).digest())
    return Fernet(key).encrypt(value.encode()).decode()


def reveal_config_secret(value: str) -> str:
    if not settings.CONFIG_ENCRYPTION_KEY:
        raise ValidationError(message="未配置 CONFIG_ENCRYPTION_KEY，不能读取 MinerU 密钥")
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.CONFIG_ENCRYPTION_KEY.encode()).digest())
    try:
        return Fernet(key).decrypt(value.encode()).decode()
    except (InvalidToken, ValueError):
        raise ValidationError(message="MinerU 密钥配置损坏")


def validate_external_api_url(value: str) -> str:
    parsed = urlparse(value)
    allowed_schemes = {"https", "http"} if settings.DEBUG else {"https"}
    if parsed.scheme not in allowed_schemes or not parsed.hostname or parsed.username or parsed.password:
        raise ValidationError(message="MinerU API 地址无效；生产环境必须使用 HTTPS")
    hostname = parsed.hostname.rstrip(".").lower()
    if hostname in _METADATA_HOSTS or hostname.endswith(".internal") or hostname.endswith(".local"):
        raise ValidationError(message="MinerU API 地址不能指向元数据或内部主机")
    try:
        addresses = {
            info[4][0]
            for info in socket.getaddrinfo(
                hostname,
                parsed.port or (443 if parsed.scheme == "https" else 80),
                type=socket.SOCK_STREAM,
            )
        }
    except socket.gaierror:
        raise ValidationError(message="MinerU API 域名无法解析")
    if not addresses:
        raise ValidationError(message="MinerU API 域名无法解析")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise ValidationError(message="MinerU API 地址不能指向内部或保留网络")
    return value
