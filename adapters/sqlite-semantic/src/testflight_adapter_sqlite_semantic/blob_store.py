"""Filesystem-backed content-addressed storage for source and derived media."""

import hashlib
import os
import re
import tempfile
from contextlib import suppress
from pathlib import Path

from testflight_creative_field import BlobReference

_HEX_HASH = re.compile(r"^[0-9a-f]{64}$")


class ContentAddressedBlobStore:
    """Store bytes below an explicit data root, addressed by SHA-256 content hash."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.blobs_root = root / "blobs"
        self.blobs_root.mkdir(parents=True, exist_ok=True)

    def put(self, content: bytes, *, media_type: str) -> BlobReference:
        return self._put(content, media_type=media_type)

    def put_derived(
        self,
        content: bytes,
        *,
        media_type: str,
        source_hash: str,
        derivative_kind: str,
    ) -> BlobReference:
        if not _HEX_HASH.fullmatch(source_hash):
            raise ValueError("source_hash must be a lowercase SHA-256 hex digest")
        if not derivative_kind.strip():
            raise ValueError("derivative_kind must not be empty")
        return self._put(
            content,
            media_type=media_type,
            source_hash=source_hash,
            derivative_kind=derivative_kind,
        )

    def path_for(self, content_hash: str) -> Path:
        if not _HEX_HASH.fullmatch(content_hash):
            raise ValueError("content_hash must be a lowercase SHA-256 hex digest")
        return self.blobs_root / content_hash[:2] / content_hash[2:4] / content_hash

    def read(self, content_hash: str) -> bytes:
        return self.path_for(content_hash).read_bytes()

    def _put(
        self,
        content: bytes,
        *,
        media_type: str,
        source_hash: str | None = None,
        derivative_kind: str | None = None,
    ) -> BlobReference:
        if not isinstance(content, bytes):
            raise TypeError("content-addressed store accepts bytes")
        if not media_type.strip():
            raise ValueError("media_type must not be empty")
        content_hash = hashlib.sha256(content).hexdigest()
        target = self.path_for(content_hash)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.read_bytes() != content:
                raise OSError(f"content hash collision or corrupt blob: {content_hash}")
        else:
            fd, temporary_name = tempfile.mkstemp(prefix=f".{content_hash}.", dir=target.parent)
            try:
                with os.fdopen(fd, "wb") as temporary:
                    temporary.write(content)
                    temporary.flush()
                    os.fsync(temporary.fileno())
                os.replace(temporary_name, target)
            except BaseException:
                with suppress(FileNotFoundError):
                    os.unlink(temporary_name)
                raise
        return BlobReference(
            content_hash=content_hash,
            size=len(content),
            media_type=media_type,
            uri=f"blob://sha256/{content_hash}",
            source_hash=source_hash,
            derivative_kind=derivative_kind,
        )


__all__ = ["ContentAddressedBlobStore"]
