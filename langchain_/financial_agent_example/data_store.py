import json
from pathlib import Path
from shutil import copyfile

DATA_DIR = Path(__file__).resolve().parent / "data"
INITIAL_PATH = DATA_DIR / "initial_data.json"
BANK_PATH = DATA_DIR / "bank_data.json"


def prepare_data():
    """작업용 데이터가 없을 때만 초기 데이터를 복사한다."""
    if not BANK_PATH.exists():
        copyfile(INITIAL_PATH, BANK_PATH)


def read_data():
    return json.loads(BANK_PATH.read_text(encoding="utf-8"))


def save_data(data):
    """완성된 JSON을 임시 파일에 쓴 뒤 작업용 파일을 교체한다."""
    temporary_path = BANK_PATH.with_name(".bank_data.tmp")
    try:
        temporary_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary_path.replace(BANK_PATH)
    finally:
        temporary_path.unlink(missing_ok=True)
