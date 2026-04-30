from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Protocol, runtime_checkable

import httpx

from app.config import get_settings


@runtime_checkable
class BundleStorage(Protocol):
    name: str

    async def put(self, *, scan_id: str, finding_id: str, ciphertext: bytes) -> str: ...


class NullStorage:
    name = "null"

    async def put(self, *, scan_id: str, finding_id: str, ciphertext: bytes) -> str:
        digest = hashlib.sha256(ciphertext).hexdigest()
        return f"null://{scan_id}/{finding_id}#{digest[:16]}"


class LocalBundleStorage:
    name = "local"

    def __init__(self, root: str | None = None) -> None:
        self.root = Path(root or get_settings().bundle_local_dir)

    async def put(self, *, scan_id: str, finding_id: str, ciphertext: bytes) -> str:
        scan_dir = self.root / scan_id
        scan_dir.mkdir(parents=True, exist_ok=True)
        target = scan_dir / f"{finding_id}.age"
        target.write_bytes(ciphertext)
        return f"file://{target.resolve()}"


class IPFSPinningStorage:
    name = "ipfs"

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        token: str | None = None,
        timeout: float = 20.0,
    ) -> None:
        settings = get_settings()
        self.endpoint = (endpoint or settings.ipfs_pinning_endpoint).rstrip("/")
        self.token = token or settings.ipfs_pinning_token
        self.timeout = timeout

    async def put(self, *, scan_id: str, finding_id: str, ciphertext: bytes) -> str:
        if not self.endpoint or not self.token:
            raise RuntimeError("IPFS pinning endpoint or token not configured")

        url = f"{self.endpoint}/upload"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {self.token}"},
                files={
                    "file": (
                        f"{scan_id}-{finding_id}.age",
                        ciphertext,
                        "application/octet-stream",
                    )
                },
            )
        response.raise_for_status()
        body = response.json()
        cid = body.get("cid") or body.get("Hash") or body.get("ipfs_cid")
        if not cid:
            raise RuntimeError(f"pinning service returned no cid: {body}")
        return f"ipfs://{cid}"


class ZeroGStorage:
    name = "zerog"

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        api_key: str | None = None,
        timeout: float = 20.0,
    ) -> None:
        settings = get_settings()
        self.endpoint = (endpoint or settings.zerog_endpoint).rstrip("/")
        self.api_key = api_key or settings.zerog_api_key
        self.timeout = timeout

    async def put(self, *, scan_id: str, finding_id: str, ciphertext: bytes) -> str:
        if not self.endpoint or not self.api_key:
            raise RuntimeError("ZeroG endpoint or api_key not configured")

        url = f"{self.endpoint}/objects"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                headers=headers,
                content=ciphertext,
                params={"scanId": scan_id, "findingId": finding_id},
            )
        response.raise_for_status()
        body = response.json()
        uri = body.get("uri") or body.get("objectUri")
        if not uri:
            raise RuntimeError(f"ZeroG returned no uri: {body}")
        return uri


def get_bundle_storage() -> BundleStorage:
    settings = get_settings()
    if settings.zerog_endpoint and settings.zerog_api_key:
        return ZeroGStorage()
    if settings.ipfs_pinning_endpoint and settings.ipfs_pinning_token:
        return IPFSPinningStorage()
    return LocalBundleStorage()
