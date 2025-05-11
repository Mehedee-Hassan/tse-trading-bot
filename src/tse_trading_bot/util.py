from pathlib import Path
from typing import List, Dict

def _load_tickers(path: str = "../../resource/tickers.txt") -> List[str]:
    f = Path(path)
    if not f.exists():
        print("Nai desu :V")
        exit(1)
        return ["7203.T", "6758.T", "9984.T", "8306.T", "9432.T"]

    return [
        line.strip()
        for line in f.read_text(encoding="utf‑8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]