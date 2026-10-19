"""Public MOSI feature mirror, verified against the publisher's SHA-256.

This is not raw video/audio and contains no EEG. Never treats HF's license
tag as replacing the original dataset's terms. Does not unpickle the file.
"""
import json
from pathlib import Path
from download_public import download

ROOT = Path(__file__).resolve().parent
EXPECTED_SHA256 = "d3994fd25681f9c7ad6e9c6596a6fe9b4beb85ff7d478ba978b124139002e5f9"
ASSET = (
    "CMU-MOSI/aligned_50.pkl",
    "https://huggingface.co/datasets/tamb2203579/CMU-MOSI/resolve/main/Processed/aligned_50.pkl?download=true",
    367257274,
    None,
)

if __name__ == "__main__":
    result = download(ASSET)
    result["publisher_sha256_source"] = "https://github.com/thuiar/MMSA#2-datasets"
    result["expected_sha256"] = EXPECTED_SHA256
    result["publisher_sha256_verified"] = result.get("sha256") == EXPECTED_SHA256
    if result["status"] == "downloaded" and not result["publisher_sha256_verified"]:
        result["status"] = "verification_failed"
    (ROOT / "mosi_download_manifest.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    if result["status"] != "downloaded":
        raise SystemExit(1)
