"""Inspect downloaded training resources without executing external project code.

Dependencies: numpy, scipy, xlrd. Does not train models or change source data.
Creates CSV indices and a verification report. Run after extracting SAM40.
"""
from collections import Counter
import csv
from hashlib import sha256
import importlib
import json
from pathlib import Path
import pickle
import random
import re

import numpy as np
from scipy.io import loadmat
import xlrd

ROOT = Path(__file__).resolve().parent
MOSI_SHA256 = "d3994fd25681f9c7ad6e9c6596a6fe9b4beb85ff7d478ba978b124139002e5f9"


class ArrayUnpickler(pickle.Unpickler):
    """Only permit NumPy array reconstruction used by this verified release."""
    def find_class(self, module, name):
        if module in {"numpy.core.multiarray", "numpy._core.multiarray"} and name in {"_reconstruct", "scalar"}:
            return getattr(importlib.import_module("numpy._core.multiarray"), name)
        if module == "numpy" and name in {"ndarray", "dtype"}:
            return getattr(np, name)
        raise pickle.UnpicklingError(f"Unexpected pickle global blocked: {module}.{name}")


def load_mosi():
    """Return train/valid/test arrays only after checking publisher SHA-256."""
    path = ROOT / "CMU-MOSI/aligned_50.pkl"
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != MOSI_SHA256:
        raise ValueError("MOSI file does not match publisher SHA-256")
    with path.open("rb") as stream:
        return ArrayUnpickler(stream).load()


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def inspect_mosi():
    data = load_mosi()
    report, rows, split_videos = {}, [], {}
    for split, part in data.items():
        count = len(part["id"])
        assert all(len(part[k]) == count for k in ("audio", "vision", "text", "raw_text", "regression_labels"))
        report[split] = {
            "samples": count,
            "shapes": {k: list(part[k].shape) for k in ("audio", "vision", "text", "text_bert")},
            "nonfinite_values": {k: int(np.size(part[k]) - np.isfinite(part[k]).sum()) for k in ("audio", "vision", "text")},
            "sentiment_range": [float(np.min(part["regression_labels"])), float(np.max(part["regression_labels"]))],
        }
        split_videos[split] = set()
        for i, sample_id in enumerate(part["id"]):
            video, clip = sample_id.split("$_$", 1)
            split_videos[split].add(video)
            rows.append({"sample_id": sample_id, "video_id": video, "clip_id": clip,
                         "split": split, "array_row": i, "sentiment_score": float(part["regression_labels"][i]),
                         "text": str(part["raw_text"][i])})
    overlaps = {f"{a}_{b}": len(split_videos[a] & split_videos[b])
                for a, b in (("train", "valid"), ("train", "test"), ("valid", "test"))}
    assert not any(overlaps.values())
    write_csv(ROOT / "CMU-MOSI/samples_index.csv", rows)
    report["total_samples"] = len(rows)
    report["video_overlap_between_splits"] = overlaps
    report["eeg_present"] = False
    report["raw_audio_video_present"] = False
    return report


def inspect_sam40():
    base = ROOT / "SAM40/extracted/Data"
    sheet = xlrd.open_workbook(base / "scales.xls").sheet_by_index(0)
    scales = {}
    rating_rows = []
    for row in range(2, sheet.nrows):
        subject = int(sheet.cell_value(row, 0))
        for trial in range(1, 4):
            for j, task in enumerate(("Arithmetic", "Symmetric", "Stroop")):
                rating = float(sheet.cell_value(row, 1 + (trial - 1) * 3 + j))
                scales[(subject, trial, task)] = rating
                rating_rows.append({"subject_id": subject, "trial": trial, "task": task, "original_self_rating": rating})
    subjects = list(range(1, 41))
    random.Random(2026).shuffle(subjects)
    split_map = {s: ("train" if i < 28 else "valid" if i < 34 else "test") for i, s in enumerate(subjects)}
    rows, bad = [], []
    shape_counts = {"raw": Counter(), "filtered": Counter()}
    for raw in sorted((base / "raw_data").glob("*.mat")):
        match = re.fullmatch(r"(.+)_sub_(\d+)_trial(\d+)\.mat", raw.name)
        if not match:
            raise ValueError(f"Unknown filename: {raw.name}")
        task, subject, trial = match[1], int(match[2]), int(match[3])
        clean = base / "filtered_data" / raw.name
        assert clean.is_file()
        for kind, path, key in (("raw", raw, "Data"), ("filtered", clean, "Clean_data")):
            value = loadmat(path)[key]
            shape_counts[kind][str(tuple(value.shape))] += 1
            if value.shape != (32, 3200) or not np.isfinite(value).all():
                bad.append(str(path.relative_to(ROOT)))
        rows.append({"subject_id": subject, "trial": trial, "task": task,
                     "split_example_subject_grouped": split_map[subject],
                     "raw_path": raw.relative_to(ROOT).as_posix(),
                     "filtered_path": clean.relative_to(ROOT).as_posix(),
                     "original_self_rating": scales.get((subject, trial, task), "")})
    assert len(rows) == 480 and len(scales) == 360
    assert len({r["subject_id"] for r in rows}) == 40
    write_csv(ROOT / "SAM40/trials_index.csv", rows)
    write_csv(ROOT / "SAM40/ratings_long.csv", rating_rows)
    return {
        "subjects": 40, "raw_trials": len(rows), "filtered_trials": len(rows),
        "unique_paired_trials": len(rows), "task_counts": dict(Counter(r["task"] for r in rows)),
        "shape_counts": {k: dict(v) for k, v in shape_counts.items()},
        "invalid_shape_or_nonfinite_files": bad,
        "self_rating_entries": len(scales), "self_rating_range": [min(scales.values()), max(scales.values())],
        "rating_distribution": dict(Counter(scales.values())),
        "relax_rating_policy": "Not present in scales.xls; left empty, never invented",
        "example_split_subject_counts": dict(Counter(split_map.values())),
        "example_split_seed": 2026,
        "audio_text_video_present": False,
    }


if __name__ == "__main__":
    report = {"MOSI": inspect_mosi(), "SAM40": inspect_sam40(),
              "four_modal_synchronized_dataset_downloaded": False,
              "five_level_psychological_risk_ground_truth_available": False,
              "models_trained": False}
    (ROOT / "verification_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
