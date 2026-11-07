#!/usr/bin/env python3
"""Download, verify, and extract the official ZAIC 2026 DataMate datasets."""

from __future__ import annotations

import hashlib
import pathlib
import shutil
import stat
import sys
import tempfile
import urllib.request
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
DATASETS = {
    "train": {
        "url": "https://dl-challenge.zalo.ai/2026/datamate_dkewxftdzo/train.zip",
        "sha256": "c1adbc654a301c30e4cf20b55d301381025f49db1162d88322b552d7472fea01",
    },
    "public_test": {
        "url": "https://dl-challenge.zalo.ai/2026/datamate_dkewxftdzo/public_test.zip",
        "sha256": "46fb50f926ed1510b9f099a53918f45e304b256680452c93e74401b4a5442c52",
    },
}


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_archive(name: str, url: str, expected_hash: str) -> pathlib.Path:
    archive = ROOT / f"{name}.zip"
    if not archive.exists():
        print(f"Downloading {archive.name}...")
        with tempfile.NamedTemporaryFile(
            prefix=f".{name}-", suffix=".part", dir=ROOT, delete=False
        ) as temporary:
            temporary_path = pathlib.Path(temporary.name)
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": "query-processing-agent dataset setup"}
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                with temporary_path.open("wb") as target:
                    shutil.copyfileobj(response, target)
            actual_hash = sha256_file(temporary_path)
            if actual_hash != expected_hash:
                raise RuntimeError(
                    f"SHA-256 mismatch for {name}.zip: expected {expected_hash}, "
                    f"received {actual_hash}"
                )
            temporary_path.replace(archive)
        finally:
            temporary_path.unlink(missing_ok=True)

    actual_hash = sha256_file(archive)
    if actual_hash != expected_hash:
        raise RuntimeError(
            f"SHA-256 mismatch for {archive.name}: expected {expected_hash}, "
            f"received {actual_hash}. Remove the archive and retry, or verify "
            "the official release before changing the pinned hash."
        )
    return archive


def checked_members(archive: pathlib.Path, expected_root: str) -> tuple[list[str], list[str]]:
    with zipfile.ZipFile(archive) as package:
        corrupt_member = package.testzip()
        if corrupt_member:
            raise RuntimeError(f"CRC check failed for {archive.name}: {corrupt_member}")

        files: list[str] = []
        directories: list[str] = []
        for member in package.infolist():
            path = pathlib.PurePosixPath(member.filename)
            if (
                path.is_absolute()
                or ".." in path.parts
                or "\\" in member.filename
                or not path.parts
                or path.parts[0] != expected_root
            ):
                raise RuntimeError(f"Unsafe path in {archive.name}: {member.filename}")

            mode = member.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise RuntimeError(f"Symbolic link in {archive.name}: {member.filename}")

            if member.is_dir():
                directories.append(member.filename.rstrip("/"))
            else:
                files.append(member.filename)

    if not files:
        raise RuntimeError(f"No files found in {archive.name}")
    return files, directories


def extract_dataset(name: str, archive: pathlib.Path) -> int:
    destination = ROOT / name
    files, directories = checked_members(archive, name)
    expected = {str(pathlib.PurePosixPath(member)) for member in files}

    if destination.exists():
        actual = {
            path.relative_to(ROOT).as_posix()
            for path in destination.rglob("*")
            if path.is_file()
        }
        if actual != expected:
            raise RuntimeError(
                f"{destination.name}/ already exists but differs from the archive; "
                "move it aside before retrying."
            )
    else:
        with zipfile.ZipFile(archive) as package:
            package.extractall(ROOT)

    required = {
        "train": ("train/questions.jsonl", "train/answers.jsonl", "train/calendar.csv", "train/data"),
        "public_test": (
            "public_test/questions.jsonl",
            "public_test/calendar.csv",
            "public_test/data",
        ),
    }[name]
    missing = [item for item in required if not (ROOT / item).exists()]
    if missing:
        raise RuntimeError(f"Missing required {name} contents: {', '.join(missing)}")

    print(f"{name}/: verified {len(files)} files, {len(directories)} directories")
    return len(files)


def main() -> int:
    try:
        counts = {}
        for name, metadata in DATASETS.items():
            archive = ensure_archive(name, metadata["url"], metadata["sha256"])
            counts[name] = extract_dataset(name, archive)
        print(
            "Data setup complete: "
            + ", ".join(f"{name}={count} files" for name, count in counts.items())
        )
        return 0
    except (OSError, RuntimeError, urllib.error.URLError, zipfile.BadZipFile) as error:
        print(f"Data setup failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
