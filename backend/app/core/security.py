import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
from jose import jwt, JWTError  # type: ignore
from app.core.config import settings
from app.core.errors import UnauthorizedError

ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None, claims: Optional[Dict[str, Any]] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access"
    }
    if claims:
        to_encode.update(claims)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise UnauthorizedError(message="Invalid or expired authentication token")


def _get_encryption_cipher() -> Any:
    import base64
    import hashlib
    from cryptography.fernet import Fernet
    # Derive 32-byte urlsafe base64 key from SECRET_KEY
    key_bytes = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def encrypt_broker_secret(raw_secret: str) -> str:
    """Encrypt broker API secret or token for secure persistence at rest."""
    if not raw_secret:
        return ""
    cipher = _get_encryption_cipher()
    return cipher.encrypt(raw_secret.encode("utf-8")).decode("utf-8")


def decrypt_broker_secret(encrypted_secret: str) -> str:
    """Decrypt broker API secret or token into memory."""
    if not encrypted_secret:
        return ""
    cipher = _get_encryption_cipher()
    return cipher.decrypt(encrypted_secret.encode("utf-8")).decode("utf-8")

