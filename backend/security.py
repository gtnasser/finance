from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from config import settings

password_hash = PasswordHash((BcryptHasher(),))

# bcrypt tem limite de 72 bytes — validar ANTES do hash evita erro 500
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_BYTES = 72


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha em texto plano corresponde ao hash."""
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Gera o hash Bcrypt de uma senha."""
    return password_hash.hash(password)

def validate_password_policy(password: str) -> None:
    """Valida a política de senha. Levanta ValueError se inválida."""
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(
            f"A senha deve ter no mínimo {PASSWORD_MIN_LENGTH} caracteres."
        )
    if len(password.encode("utf-8")) > PASSWORD_MAX_BYTES:
        raise ValueError("A senha excede o limite de 72 bytes do bcrypt.")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria um token JWT codificado."""
    to_encode = data.copy()
    
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

