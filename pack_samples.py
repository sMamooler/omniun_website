#!/usr/bin/env python3
"""
Pack website samples: pick 5 per category/modality, copy media locally,
write website/data/samples.json.

Only samples with validation_result.keep == True in data_validation are included.

Run from the repo root:
    python website/pack_samples.py
"""
from __future__ import annotations

import glob
import json
import os
import shutil
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
WEBSITE_DIR     = Path(__file__).resolve().parent
REPO_ROOT       = WEBSITE_DIR.parent
DATA_ROOT       = REPO_ROOT / "unanswerable_videoqa" / "generated_data"
VALIDATION_ROOT = REPO_ROOT / "unanswerable_videoqa" / "data_validation"
OUT_MEDIA       = WEBSITE_DIR / "static" / "media"
OUT_DATA        = WEBSITE_DIR / "static" / "data"

NEXTQA_VIDEO_ROOT = Path("/mnt/nlp/scratch/share/datasets/NEXTQA/NExTVideo")
SLUE_AUDIO_ROOT   = Path(
    "/mnt/nlp/scratch/home/mamooler/.cache/huggingface/datasets/"
    "AudioLLMs___slue_p2_sqa5_test/default/0.0.0/"
    "24809a6ef2e1243543d97a993c9b12765f0a0bff/audios"
)

VIDEO_EXTS = [".mp4", ".mkv", ".webm"]
AUDIO_EXTS = [".wav", ".mp3", ".flac", ".ogg", ".oga", ".m4a"]

PER_CATEGORY = 5
# Store media flat per modality so identical files aren't duplicated across categories
# e.g.  static/media/video/<file>.mp4   static/media/audio/<file>.wav
FLAT_MEDIA = True

# ── Helpers ────────────────────────────────────────────────────────────────

def load_kept_keys(category: str, modality: str) -> set[str]:
    """Return the set of keys with validation_result.keep == True."""
    jf = (
        VALIDATION_ROOT
        / category
        / modality
        / "gemini_single_pass_category_decision_tree"
        / "gemini_results.jsonl"
    )
    if not jf.exists():
        return set()
    kept: set[str] = set()
    with jf.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("validation_result", {}).get("keep") is True:
                kept.add(str(r.get("key") or ""))
    return kept


def resolve_media(modality: str, key: str) -> Path | None:
    if not key:
        return None
    root = NEXTQA_VIDEO_ROOT if modality == "video" else SLUE_AUDIO_ROOT
    exts = VIDEO_EXTS if modality == "video" else AUDIO_EXTS
    for ext in exts:
        p = root / f"{key}{ext}"
        if p.exists():
            return p
    # glob fallback
    matches = [
        Path(m)
        for m in glob.glob(str(root / "**" / f"{key}*"), recursive=True)
        if os.path.isfile(m)
    ]
    return matches[0] if matches else None


def read_jsonl(path: Path) -> list[dict]:
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def normalize_response(response) -> dict:
    if isinstance(response, dict):
        return response
    return {"question": str(response or ""), "explanation": None,
            "clarification": None, "answer": None}


def normalize_validation_record(record: dict) -> dict:
    """Map a data_validation record's flat fields to the response format."""
    return {
        "question":      str(record.get("question") or ""),
        "explanation":   record.get("reference_explanation") or None,
        "clarification": record.get("clarification_information") or None,
        "answer":        record.get("answer_given_clarification_information") or None,
    }


# ── Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    OUT_DATA.mkdir(parents=True, exist_ok=True)

    samples: list[dict] = []
    stats_by_category: dict[str, int] = {}
    stats_by_modality: dict[str, int] = {}

    # Track globally used keys per modality so different categories get different clips
    used_keys: dict[str, set[str]] = {}

    category_dirs = sorted(p for p in DATA_ROOT.iterdir() if p.is_dir())
    for cat_dir in category_dirs:
        category = cat_dir.name
        for mod_dir in sorted(p for p in cat_dir.iterdir() if p.is_dir()):
            modality = mod_dir.name
            jf = mod_dir / "gemini_results.jsonl"
            if not jf.exists():
                continue

            used_keys.setdefault(modality, set())
            records = read_jsonl(jf)

            # Only keep records validated as keep=True
            kept_keys = load_kept_keys(category, modality)
            if kept_keys:
                records = [r for r in records if str(r.get("key") or "") in kept_keys]

            # Two passes: prefer keys not yet used globally, then fall back to any with media
            def candidates():
                unused = [r for r in records if str(r.get("key") or "") not in used_keys[modality]]
                yield from unused
                yield from [r for r in records if str(r.get("key") or "") in used_keys[modality]]

            picked = 0
            for record in candidates():
                if picked >= PER_CATEGORY:
                    break

                key = str(record.get("key") or "")
                idx = records.index(record)
                src = resolve_media(modality, key)
                if src is None:
                    continue

                # Store media flat: static/media/<modality>/<filename>
                dest_dir = OUT_MEDIA / modality
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest = dest_dir / src.name
                if not dest.exists():
                    print(f"  copying {src.name} …")
                    shutil.copy2(src, dest)

                used_keys[modality].add(key)
                resp = normalize_response(record.get("response"))
                sample_id = f"{category}:{modality}:{idx}"

                samples.append({
                    "id":            sample_id,
                    "key":           key,
                    "category":      category,
                    "modality":      modality,
                    "question":      str(resp.get("question") or ""),
                    "explanation":   resp.get("explanation"),
                    "clarification": resp.get("clarification"),
                    "answer":        resp.get("answer"),
                    "media_url":     f"/static/media/{modality}/{dest.name}",
                    "media_exists":  True,
                })

                stats_by_category[category] = stats_by_category.get(category, 0) + 1
                stats_by_modality[modality] = stats_by_modality.get(modality, 0) + 1
                picked += 1

            print(f"{category}/{modality}: picked {picked}")

    # ── answerable category (sourced directly from data_validation) ──────────
    for modality in ["audio", "video"]:
        jf = (
            VALIDATION_ROOT
            / "answerable"
            / modality
            / "gemini_single_pass_category_decision_tree"
            / "gemini_results.jsonl"
        )
        if not jf.exists():
            print(f"answerable/{modality}: jsonl not found, skipping")
            continue

        used_keys.setdefault(modality, set())
        records = [
            r for r in read_jsonl(jf)
            if r.get("validation_result", {}).get("keep") is True
        ]

        def answerable_candidates():
            seen: set[str] = set()
            # First pass: keys not used by any other category
            for r in records:
                k = str(r.get("key") or "")
                if k not in used_keys[modality] and k not in seen:
                    seen.add(k)
                    yield r
            # Second pass: already-used keys (different category), still unique within answerable
            for r in records:
                k = str(r.get("key") or "")
                if k in used_keys[modality] and k not in seen:
                    seen.add(k)
                    yield r

        picked = 0
        for idx, record in enumerate(answerable_candidates()):
            if picked >= PER_CATEGORY:
                break

            key = str(record.get("key") or "")
            src = resolve_media(modality, key)
            if src is None:
                continue

            dest_dir = OUT_MEDIA / modality
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / src.name
            if not dest.exists():
                print(f"  copying {src.name} …")
                shutil.copy2(src, dest)

            used_keys[modality].add(key)
            resp = normalize_validation_record(record)
            sample_id = f"answerable:{modality}:{idx}"

            samples.append({
                "id":            sample_id,
                "key":           key,
                "category":      "answerable",
                "modality":      modality,
                "question":      resp["question"],
                "explanation":   resp["explanation"],
                "clarification": resp["clarification"],
                "answer":        resp["answer"],
                "media_url":     f"/static/media/{modality}/{dest.name}",
                "media_exists":  True,
            })

            stats_by_category["answerable"] = stats_by_category.get("answerable", 0) + 1
            stats_by_modality[modality] = stats_by_modality.get(modality, 0) + 1
            picked += 1

        print(f"answerable/{modality}: picked {picked}")

    output = {
        "stats": {
            "total_samples":       len(samples),
            "counts_by_category":  stats_by_category,
            "counts_by_modality":  stats_by_modality,
            "missing_media":       0,
        },
        "samples": samples,
    }

    out_file = OUT_DATA / "samples.json"
    out_file.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {len(samples)} samples → {out_file}")


if __name__ == "__main__":
    main()
