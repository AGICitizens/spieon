from __future__ import annotations

import json

import pyrage

from app.chain import decrypt_bundle, encrypt_bundle


def test_encrypt_bundle_roundtrips_json_payload() -> None:
    identity = pyrage.x25519.Identity.generate()
    pubkey = str(identity.to_public())

    payload = {"finding_id": "f-1", "summary": "fastmcp accepts unicode confusables"}
    bundle = encrypt_bundle(payload, recipient_pubkey=pubkey)

    assert bundle.ciphertext.startswith(b"age-encryption.org/v1\n")
    assert bundle.sha256 != ""
    assert bundle.recipient == pubkey

    decrypted = decrypt_bundle(bundle.ciphertext, identity=str(identity))
    assert json.loads(decrypted) == payload


def test_encrypt_bundle_accepts_raw_bytes() -> None:
    identity = pyrage.x25519.Identity.generate()
    pubkey = str(identity.to_public())

    bundle = encrypt_bundle(b"raw payload bytes", recipient_pubkey=pubkey)
    decrypted = decrypt_bundle(bundle.ciphertext, identity=str(identity))
    assert decrypted == b"raw payload bytes"
