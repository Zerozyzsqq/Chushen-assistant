"""Project-wide filesystem paths."""

from pathlib import Path

# gustobot/infrastructure/core/paths.py -> project root is 3 levels up
PROJECT_ROOT = Path(__file__).resolve().parents[3]
UPLOAD_ROOT = PROJECT_ROOT / "uploads"
UPLOAD_IMAGE_ROOT = UPLOAD_ROOT / "images"
DISH_IMAGE_ROOT = UPLOAD_ROOT / "dish_images"


def ensure_upload_dirs() -> None:
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    UPLOAD_IMAGE_ROOT.mkdir(parents=True, exist_ok=True)
    DISH_IMAGE_ROOT.mkdir(parents=True, exist_ok=True)


def resolve_upload_path(raw_path: str | None) -> Path | None:
    """Resolve an upload path returned by the API to an on-disk file."""
    if not raw_path:
        return None

    candidate = Path(raw_path)
    if candidate.is_file():
        return candidate.resolve()

    normalized = str(raw_path).replace("\\", "/").lstrip("/")
    search_roots = (
        PROJECT_ROOT,
        Path.cwd(),
        PROJECT_ROOT / "gustobot",
    )

    relative_candidates = {normalized}
    if normalized.startswith("uploads/"):
        relative_candidates.add(normalized)
    else:
        relative_candidates.add(f"uploads/{normalized}")
        if "images/" in normalized:
            relative_candidates.add(f"uploads/images/{Path(normalized).name}")

    for root in search_roots:
        for rel in relative_candidates:
            resolved = (root / rel).resolve()
            if resolved.is_file():
                return resolved

    # Last resort: search by filename under uploads/
    filename = Path(normalized).name
    if filename:
        for root in search_roots:
            uploads_dir = root / "uploads"
            if not uploads_dir.is_dir():
                continue
            for hit in uploads_dir.rglob(filename):
                if hit.is_file():
                    return hit.resolve()

    return None
