from pathlib import Path
import json
from fastapi import APIRouter

router = APIRouter()

@router.get("/ui-spec")
async def get_ui_spec():
    spec_path = Path(__file__).resolve().parent.parent / "ui_spec.json"
    with spec_path.open("r", encoding="utf-8") as f:
        return json.load(f)
