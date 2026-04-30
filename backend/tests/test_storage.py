from __future__ import annotations

import tempfile

import httpx
import pytest
import respx

from app.storage import IPFSPinningStorage, LocalBundleStorage, NullStorage


@pytest.mark.asyncio
async def test_local_storage_writes_under_root(tmp_path) -> None:
    storage = LocalBundleStorage(root=str(tmp_path))
    uri = await storage.put(
        scan_id="scan-1", finding_id="f-1", ciphertext=b"age-ciphertext"
    )
    assert uri.startswith("file://")
    target = tmp_path / "scan-1" / "f-1.age"
    assert target.exists()
    assert target.read_bytes() == b"age-ciphertext"


@pytest.mark.asyncio
async def test_local_storage_creates_scan_directory_lazily() -> None:
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        storage = LocalBundleStorage(root=tmp)
        uri = await storage.put(scan_id="abc", finding_id="def", ciphertext=b"x")
        expected = Path(tmp).resolve() / "abc" / "def.age"
        assert uri == f"file://{expected}"
        assert expected.read_bytes() == b"x"


@pytest.mark.asyncio
async def test_null_storage_returns_digest_uri() -> None:
    storage = NullStorage()
    uri = await storage.put(scan_id="s", finding_id="f", ciphertext=b"hello")
    assert uri.startswith("null://s/f#")


@pytest.mark.asyncio
@respx.mock
async def test_ipfs_pinning_storage_returns_cid_uri() -> None:
    respx.post("https://pin.example/upload").mock(
        return_value=httpx.Response(200, json={"cid": "bafyfake1234"})
    )

    storage = IPFSPinningStorage(endpoint="https://pin.example", token="t")
    uri = await storage.put(scan_id="s", finding_id="f", ciphertext=b"x")
    assert uri == "ipfs://bafyfake1234"


@pytest.mark.asyncio
async def test_ipfs_pinning_storage_requires_config() -> None:
    storage = IPFSPinningStorage(endpoint="", token="")
    with pytest.raises(RuntimeError):
        await storage.put(scan_id="s", finding_id="f", ciphertext=b"x")
