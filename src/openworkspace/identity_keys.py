"""Encrypted local Ed25519 key storage and signature helpers."""

from __future__ import annotations

import base64
import binascii
import hashlib
import os
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from openworkspace.identity import IdentityError, IdentityRegistry


class IdentityKeyError(ValueError):
    """Raised when a local identity key operation cannot be completed."""


class IdentityKeyStore:
    """Store passphrase-encrypted Ed25519 private keys outside the identity database."""

    MIN_PASSPHRASE_LENGTH = 12

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)

    @staticmethod
    def _filename(identity_id: str) -> str:
        digest = hashlib.sha256(identity_id.encode("utf-8")).hexdigest()
        return f"{digest}.private.pem"

    def _key_path(self, identity_id: str) -> Path:
        if not identity_id or len(identity_id) > 256:
            raise IdentityKeyError("invalid identity identifier")
        if self.directory.is_symlink():
            raise IdentityKeyError("key directory must not be a symbolic link")
        return self.directory / self._filename(identity_id)

    def generate(
        self,
        identity_id: str,
        passphrase: str,
        registry: IdentityRegistry,
    ) -> dict[str, str]:
        """Generate and bind one encrypted Ed25519 key to an active identity record."""
        if len(passphrase) < self.MIN_PASSPHRASE_LENGTH:
            raise IdentityKeyError(
                f"passphrase must contain at least {self.MIN_PASSPHRASE_LENGTH} characters"
            )
        try:
            record = registry.get(identity_id)
        except IdentityError as exc:
            raise IdentityKeyError(str(exc)) from exc
        if record["status"] != "active":
            raise IdentityKeyError("only active identities may generate keys")
        if record.get("key_reference") is not None:
            raise IdentityKeyError("identity already has a key binding")

        path = self._key_path(identity_id)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.directory.is_symlink():
            raise IdentityKeyError("key directory must not be a symbolic link")
        if os.name == "posix":
            self.directory.chmod(0o700)

        private_key = Ed25519PrivateKey.generate()
        encrypted_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(
                passphrase.encode("utf-8")
            ),
        )
        public_raw = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        public_key = base64.b64encode(public_raw).decode("ascii")
        fingerprint = hashlib.sha256(public_raw).hexdigest()
        key_reference = f"ed25519-sha256:{fingerprint}"

        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc:
            raise IdentityKeyError("a local key file already exists for this identity") from exc
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(encrypted_pem)
                stream.flush()
                os.fsync(stream.fileno())
            registry.bind_public_key(identity_id, key_reference, public_key)
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return {"identity_id": identity_id, "key_reference": key_reference, "public_key": public_key}

    def sign(
        self,
        identity_id: str,
        payload: bytes,
        passphrase: str,
        registry: IdentityRegistry,
    ) -> str:
        """Sign bytes for an active identity and return a base64 signature."""
        try:
            record = registry.get(identity_id)
        except IdentityError as exc:
            raise IdentityKeyError(str(exc)) from exc
        if record["status"] != "active":
            raise IdentityKeyError("identity is not active")
        expected_public = record.get("attributes", {}).get("public_key_ed25519")
        reference = record.get("key_reference") or ""
        if not expected_public or not reference.startswith("ed25519-sha256:"):
            raise IdentityKeyError("identity has no bound Ed25519 key")
        path = self._key_path(identity_id)
        try:
            private_key = serialization.load_pem_private_key(
                path.read_bytes(), password=passphrase.encode("utf-8")
            )
        except (OSError, TypeError, ValueError) as exc:
            raise IdentityKeyError("cannot unlock local identity key") from exc
        if not isinstance(private_key, Ed25519PrivateKey):
            raise IdentityKeyError("local key is not Ed25519")
        public_raw = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        actual_public = base64.b64encode(public_raw).decode("ascii")
        fingerprint = hashlib.sha256(public_raw).hexdigest()
        if actual_public != expected_public or reference != f"ed25519-sha256:{fingerprint}":
            raise IdentityKeyError("local private key does not match the registered public key")
        return base64.b64encode(private_key.sign(payload)).decode("ascii")

    @staticmethod
    def verify(
        identity_id: str,
        payload: bytes,
        signature: str,
        registry: IdentityRegistry,
    ) -> bool:
        """Verify a signature against the identity's bound public key.

        A valid signature proves key possession for these bytes, not a real-world identity.
        Callers must separately inspect the identity status and authorization policy.
        """
        try:
            record = registry.get(identity_id)
        except IdentityError as exc:
            raise IdentityKeyError(str(exc)) from exc
        encoded_key = record.get("attributes", {}).get("public_key_ed25519")
        reference = record.get("key_reference") or ""
        if not encoded_key or not reference.startswith("ed25519-sha256:"):
            raise IdentityKeyError("identity has no bound Ed25519 key")
        try:
            public_raw = base64.b64decode(encoded_key, validate=True)
            signature_raw = base64.b64decode(signature, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise IdentityKeyError("public key or signature is not valid base64") from exc
        fingerprint = hashlib.sha256(public_raw).hexdigest()
        if reference != f"ed25519-sha256:{fingerprint}":
            raise IdentityKeyError("registered public key fingerprint mismatch")
        try:
            Ed25519PublicKey.from_public_bytes(public_raw).verify(signature_raw, payload)
        except InvalidSignature:
            return False
        except ValueError as exc:
            raise IdentityKeyError("registered Ed25519 public key is malformed") from exc
        return True
