#!/usr/bin/env python3
"""Compare the hash of a local file with the hash of a file fetched from a remote URL."""

import hashlib
import sys
import urllib.request
from pathlib import Path
from typing import Final


DEFAULT_ALGORITHM: Final[str] = "sha256"


def compute_hash(path: Path, algorithm: str = DEFAULT_ALGORITHM) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python check_remote_hash.py <remote_url> <local_file>")
        return 2

    remote_url = sys.argv[1]
    local_path = Path(sys.argv[2]).expanduser()

    if not local_path.exists():
        print(f"[X] Local file not found: {local_path}")
        return 1

    try:
        remote_bytes = fetch_bytes(remote_url)
    except Exception as exc:  # pragma: no cover - network failure path
        print(f"[X] Failed to download remote file: {exc}")
        return 1

    remote_hash = hashlib.new(DEFAULT_ALGORITHM, remote_bytes).hexdigest()
    local_hash = compute_hash(local_path, DEFAULT_ALGORITHM)

    print("[i] Remote URL: " + remote_url)
    print(f"[i] Local file: {local_path}")
    print(f"[i] Remote hash: {remote_hash}")
    print(f"[i] Local hash:  {local_hash}")

    if remote_hash == local_hash:
        print("[+] Hashes match. The downloaded file matches the remote source.")
        return 0

    print("[X] Hashes do not match. The downloaded file may be altered or incomplete.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
