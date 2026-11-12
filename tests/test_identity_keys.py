import os

import pytest

from openworkspace.identity import IdentityError, IdentityRegistry
from openworkspace.identity_keys import IdentityKeyError, IdentityKeyStore

IDENTITY = {
    "id": "local.key-owner", "kind": "user", "issuer": "local",
    "key_reference": None, "status": "active", "valid_from": None,
    "valid_until": None, "attributes": {}
}
PASSPHRASE = "correct horse battery staple"


def test_encrypted_ed25519_key_generation_sign_and_verify(tmp_path):
    database = tmp_path / "runtime.sqlite3"
    registry = IdentityRegistry(database)
    registry.create(IDENTITY)
    keys = IdentityKeyStore(tmp_path / "keys")
    binding = keys.generate(IDENTITY["id"], PASSPHRASE, registry)
    record = registry.get(IDENTITY["id"])
    assert record["key_reference"] == binding["key_reference"]
    assert record["attributes"]["public_key_ed25519"] == binding["public_key"]
    signature = keys.sign(IDENTITY["id"], b"test payload", PASSPHRASE, registry)
    assert keys.verify(IDENTITY["id"], b"test payload", signature, registry)
    assert not keys.verify(IDENTITY["id"], b"changed payload", signature, registry)


def test_key_generation_requires_strong_passphrase_and_no_existing_key(tmp_path):
    registry = IdentityRegistry(tmp_path / "runtime.sqlite3")
    registry.create(IDENTITY)
    keys = IdentityKeyStore(tmp_path / "keys")
    with pytest.raises(IdentityKeyError, match="at least 12"):
        keys.generate(IDENTITY["id"], "short", registry)
    keys.generate(IDENTITY["id"], PASSPHRASE, registry)
    with pytest.raises(IdentityKeyError, match="already has a key"):
        keys.generate(IDENTITY["id"], PASSPHRASE, registry)


def test_wrong_passphrase_and_key_file_tampering_fail_closed(tmp_path):
    registry = IdentityRegistry(tmp_path / "runtime.sqlite3")
    registry.create(IDENTITY)
    keys = IdentityKeyStore(tmp_path / "keys")
    keys.generate(IDENTITY["id"], PASSPHRASE, registry)
    with pytest.raises(IdentityKeyError, match="unlock"):
        keys.sign(IDENTITY["id"], b"payload", "incorrect passphrase", registry)
    key_path = keys._key_path(IDENTITY["id"])
    key_path.write_text("tampered", encoding="utf-8")
    with pytest.raises(IdentityKeyError, match="unlock"):
        keys.sign(IDENTITY["id"], b"payload", PASSPHRASE, registry)


def test_suspended_or_revoked_identity_cannot_sign(tmp_path):
    database = tmp_path / "runtime.sqlite3"
    registry = IdentityRegistry(database)
    registry.create(IDENTITY)
    keys = IdentityKeyStore(tmp_path / "keys")
    keys.generate(IDENTITY["id"], PASSPHRASE, registry)
    registry.set_status(IDENTITY["id"], "suspended", reason="Test suspension")
    with pytest.raises(IdentityKeyError, match="not active"):
        keys.sign(IDENTITY["id"], b"payload", PASSPHRASE, registry)
    registry.set_status(IDENTITY["id"], "revoked", reason="Test revocation")
    with pytest.raises(IdentityKeyError, match="not active"):
        keys.sign(IDENTITY["id"], b"payload", PASSPHRASE, registry)


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission bits are not portable to Windows")
def test_private_key_file_has_restrictive_permissions(tmp_path):
    registry = IdentityRegistry(tmp_path / "runtime.sqlite3")
    registry.create(IDENTITY)
    keys = IdentityKeyStore(tmp_path / "keys")
    keys.generate(IDENTITY["id"], PASSPHRASE, registry)
    mode = keys._key_path(IDENTITY["id"]).stat().st_mode & 0o777
    assert mode == 0o600



def test_identity_registry_rejects_mismatched_public_key_fingerprint(tmp_path):
    registry = IdentityRegistry(tmp_path / "runtime.sqlite3")
    registry.create(IDENTITY)
    with pytest.raises(IdentityError, match="fingerprint"):
        registry.bind_public_key(
            IDENTITY["id"], "ed25519-sha256:" + "0" * 64, "bm90LWEtcHVibGljLWtleQ=="
        )
