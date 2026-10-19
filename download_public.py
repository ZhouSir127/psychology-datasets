"""Download public, verified-source files only; never requests restricted data.

Run from Windows or Linux: python download_public.py
Does not install or execute downloaded code. SAM40 is EEG-only pretraining data.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import md5, sha256
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
ASSETS = [
    ("SAM40/Data.rar", "https://ndownloader.figshare.com/files/27937632",
     760372439, "53fc78152d60bf5e87a0c1a3f2546530"),
    ("applications/MARS/EULA_MARS_dataset.pdf",
     "https://raw.githubusercontent.com/reactmultimodalchallenge/baseline_react2026/main/EULA_MARS%20dataset.pdf", None, None),
    ("applications/MARS/README_official.md",
     "https://raw.githubusercontent.com/reactmultimodalchallenge/baseline_react2026/main/README.md", None, None),
    ("applications/EAV/README_official.md",
     "https://raw.githubusercontent.com/nubcico/EAV/main/README.md", None, None),
    ("reference_code/EAV-main.zip", "https://codeload.github.com/nubcico/EAV/zip/refs/heads/main", None, None),
    ("papers/MARS_REACT2026.pdf", "https://arxiv.org/pdf/2606.07935", None, None),
    ("CMU-MOSI/SDK_README.md",
     "https://raw.githubusercontent.com/CMU-MultiComp-Lab/CMU-MultimodalSDK/main/README.md", None, None),
    ("CMU-MOSI/MultiBench_download_instructions.rst",
     "https://raw.githubusercontent.com/pliang279/MultiBench/main/sphinx/source/start/datadownload.rst", None, None),
]


def checksums(path):
    sh, mh = sha256(), md5()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            sh.update(block)
            mh.update(block)
    return sh.hexdigest(), mh.hexdigest()


def download(asset):
    relative, url, expected_size, expected_md5 = asset
    dest = ROOT / relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    error = ""
    for attempt in range(3):
        try:
            if dest.is_file():
                digest, md = checksums(dest)
                if (expected_size is None or dest.stat().st_size == expected_size) and (expected_md5 is None or md == expected_md5):
                    return {"path": relative, "source": url, "status": "downloaded", "size_bytes": dest.stat().st_size,
                            "sha256": digest, "md5": md, "publisher_md5_verified": expected_md5 is not None}
                raise ValueError("Existing destination does not match publisher metadata; inspect before replacing")
            offset = part.stat().st_size if part.exists() else 0
            headers = {"User-Agent": "MindTrack academic dataset downloader"}
            if offset:
                headers["Range"] = f"bytes={offset}-"
            with urlopen(Request(url, headers=headers), timeout=45) as response:
                resume = offset > 0 and response.status == 206
                size = offset if resume else 0
                if response.headers.get("Content-Type", "").startswith("text/html"):
                    raise ValueError("Received HTML instead of a file")
                next_progress = size + 64 * 1024 * 1024
                with part.open("ab" if resume else "wb") as stream:
                    for block in iter(lambda: response.read(1024 * 1024), b""):
                        stream.write(block)
                        size += len(block)
                        if size >= next_progress:
                            print(f"{relative}: {size / 1024**2:.0f} MiB", flush=True)
                            next_progress = size + 64 * 1024 * 1024
            digest, md = checksums(part)
            if expected_size is not None and part.stat().st_size != expected_size:
                raise ValueError(f"Size mismatch: {part.stat().st_size} != {expected_size}")
            if expected_md5 is not None and md != expected_md5:
                raise ValueError("Publisher MD5 mismatch")
            part.replace(dest)
            print(f"DONE {relative}: {dest.stat().st_size} bytes", flush=True)
            return {"path": relative, "source": url, "status": "downloaded", "size_bytes": dest.stat().st_size,
                    "sha256": digest, "md5": md, "publisher_md5_verified": expected_md5 is not None}
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            print(f"RETRY {relative}: {error[:180]}", flush=True)
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
    return {"path": relative, "source": url, "status": "failed", "error": error}


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(download, ASSETS))
    (ROOT / "download_manifest.json").write_text(json.dumps({
        "checked_at": datetime.now(timezone.utc).isoformat(), "files": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps([{k: v for k, v in r.items() if k in ("path", "status", "size_bytes", "error")} for r in results], indent=2), flush=True)
