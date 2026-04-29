from __future__ import annotations

import ctypes
import hashlib
import json
from dataclasses import dataclass
from typing import Any

import pyrage


@dataclass(slots=True)
class EncryptedBundle:
    ciphertext: bytes
    sha256: str
    recipient: str

    @property
    def hex_sha256(self) -> str:
        return self.sha256


def _zeroize(buf: bytearray) -> None:
    if not buf:
        return
    addr = (ctypes.c_char * len(buf)).from_buffer(buf)
    ctypes.memset(ctypes.addressof(addr), 0, len(buf))


def encrypt_bundle(
    payload: dict[str, Any] | bytes,
    *,
    recipient_pubkey: str,
) -> EncryptedBundle:
    if isinstance(payload, (bytes, bytearray)):
        plaintext = bytearray(bytes(payload))
    else:
        plaintext = bytearray(json.dumps(payload, sort_keys=True).encode("utf-8"))

    recipient = pyrage.x25519.Recipient.from_str(recipient_pubkey)
    try:
        ciphertext = pyrage.encrypt(bytes(plaintext), [recipient])
    finally:
        _zeroize(plaintext)

    digest = hashlib.sha256(ciphertext).hexdigest()
    return EncryptedBundle(
        ciphertext=ciphertext,
        sha256=digest,
        recipient=recipient_pubkey,
    )


def decrypt_bundle(ciphertext: bytes, *, identity: str) -> bytes:
    ident = pyrage.x25519.Identity.from_str(identity)
    return pyrage.decrypt(ciphertext, [ident])
