import hashlib
import hmac

from src.verify import verify_signature


def _sign(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_valid_signature():
    body = b'{"hello":"world"}'
    secret = "shh"
    assert verify_signature(body, _sign(body, secret), secret) is True


def test_wrong_secret():
    body = b'{"hello":"world"}'
    assert verify_signature(body, _sign(body, "wrong"), "right") is False


def test_tampered_body():
    body = b'{"hello":"world"}'
    sig = _sign(body, "shh")
    assert verify_signature(b'{"hello":"evil"}', sig, "shh") is False


def test_missing_header():
    assert verify_signature(b"x", None, "shh") is False


def test_bad_prefix():
    body = b"x"
    digest = hmac.new(b"shh", body, hashlib.sha256).hexdigest()
    assert verify_signature(body, digest, "shh") is False
