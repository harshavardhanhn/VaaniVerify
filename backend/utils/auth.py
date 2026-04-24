import base64
import hmac
import hashlib
import json
import os
import binascii
from datetime import datetime, timedelta, UTC

def create_session_token(data: dict, secret: str, ttl_minutes: int) -> str:
    payload = data.copy()
    payload["exp"] = (datetime.now(UTC) + timedelta(minutes=ttl_minutes)).timestamp()
    
    header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').decode('utf-8').rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8').rstrip('=')
    
    signature = hmac.new(
        secret.encode('utf-8'),
        f"{header}.{payload_b64}".encode('utf-8'),
        hashlib.sha256
    ).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
    
    return f"{header}.{payload_b64}.{signature_b64}"

def verify_session_token(token: str, secret: str) -> dict:
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("Invalid token format")
        
    header, payload_b64, signature_b64 = parts
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        f"{header}.{payload_b64}".encode('utf-8'),
        hashlib.sha256
    ).digest()
    expected_signature_b64 = base64.urlsafe_b64encode(expected_signature).decode('utf-8').rstrip('=')
    
    if not hmac.compare_digest(signature_b64, expected_signature_b64):
        raise ValueError("Invalid signature")
        
    payload_b64_padded = payload_b64 + '=' * (-len(payload_b64) % 4)
    payload = json.loads(base64.urlsafe_b64decode(payload_b64_padded).decode('utf-8'))
    
    if payload.get("exp", 0) < datetime.now(UTC).timestamp():
        raise ValueError("Token expired")
        
    return payload

def hash_password(password: str) -> str:
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')

def verify_password(password: str, provided_hash: str) -> bool:
    salt = provided_hash[:64].encode('ascii')
    provided_pwdhash = provided_hash[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == provided_pwdhash
