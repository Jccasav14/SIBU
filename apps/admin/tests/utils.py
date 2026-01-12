from __future__ import annotations

import time

import jwt


def make_token(*, secret: str, alg: str, email: str, role: str, exp_seconds: int = 3600) -> str:
    payload = {
        "email": email,
        "role": role,
        "exp": int(time.time()) + exp_seconds,
    }
    return jwt.encode(payload, secret, algorithm=alg)
