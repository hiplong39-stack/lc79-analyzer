from __future__ import annotations
from collections import Counter
from itertools import product
from math import sqrt
from typing import Literal, Optional
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

BASE = Path(__file__).resolve().parent
app = FastAPI(
    title="LC79 Analyzer",
    version="2.0.0",
    description="Website và API thống kê độc lập. Không phải dịch vụ chính thức của LC79."
)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

Outcome = Literal["TAI", "XIU", "TRIPLE"]

class DiceRound(BaseModel):
    round_id: Optional[str] = None
    dice: list[int] = Field(min_length=3, max_length=3)

    @field_validator("dice")
    @classmethod
    def validate_dice(cls, values):
        if any(v < 1 or v > 6 for v in values):
            raise ValueError("Mỗi viên xúc xắc phải từ 1 đến 6.")
        return values

class DiceAnalysisRequest(BaseModel):
    rounds: list[DiceRound] = Field(min_length=1, max_length=10000)

class OutcomeHistoryRequest(BaseModel):
    outcomes: list[Outcome] = Field(min_length=2, max_length=10000)

class Md5Record(BaseModel):
    round_id: Optional[str] = None
    hash: str = Field(min_length=1, max_length=256)
    published_result: Optional[str] = None

    @field_validator("hash")
    @classmethod
    def clean_hash(cls, value):
        return value.strip()

class Md5BatchRequest(BaseModel):
    records: list[Md5Record] = Field(min_length=1, max_length=1000)

class BrowserTextRequest(BaseModel):
    page_text: str = Field(min_length=1, max_length=200000)
    page_url: Optional[str] = None

def classify_dice(dice: list[int]):
    total = sum(dice)
    if dice[0] == dice[1] == dice[2]:
        return total, "TRIPLE"
    if 4 <= total <= 10:
        return total, "XIU"
    if 11 <= total <= 17:
        return total, "TAI"
    return total, "SPECIAL"

def theoretical_probabilities():
    counts, sums = Counter(), Counter()
    for dice in product(range(1, 7), repeat=3):
        total, outcome = classify_dice(list(dice))
        counts[outcome] += 1
        sums[total] += 1
    return {
        "sample_space": 216,
        "tai": {"count": counts["TAI"], "probability": counts["TAI"] / 216},
        "xiu": {"count": counts["XIU"], "probability": counts["XIU"] / 216},
        "triple": {"count": counts["TRIPLE"], "probability": counts["TRIPLE"] / 216},
        "sum_distribution": {
            str(k): {"count": sums[k], "probability": sums[k] / 216}
            for k in range(3, 19)
        },
        "rule_note": "Luật phổ biến: bộ ba tách riêng; Xỉu 4–10; Tài 11–17. Cần đối chiếu luật bàn chơi."
    }

def wilson_interval(successes: int, n: int, z: float = 1.96):
    if n <= 0:
        return None
    p = successes / n
    denom = 1 + z*z/n
    center = (p + z*z/(2*n)) / denom
    margin = z * sqrt((p*(1-p) + z*z/(4*n))/n) / denom
    return [max(0.0, center-margin), min(1.0, center+margin)]

@app.get("/")
def home():
    return FileResponse(BASE / "static" / "index.html")

@app.get("/health")
def health():
    return {"status": "ok", "connected_to_lc79": False}

@app.post("/v1/browser/inspect")
def inspect_browser_text(request: BrowserTextRequest):
    """
    Inspect text copied by the user from the LC79 page.
    This does not fetch the page, access cookies, or automate betting.
    """
    raw = request.page_text
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    outcome_lines = [
        line[:240] for line in lines
        if re.search(r"\b(tài|xỉu|tai|xiu)\b", line, re.IGNORECASE)
    ][:80]
    hashes = list(dict.fromkeys(re.findall(r"\b[a-fA-F0-9]{32}\b", raw)))[:50]
    round_candidates = list(dict.fromkeys(
        re.findall(r"(?:phiên|round|#)\s*[:#-]?\s*(\d{5,})", raw, re.IGNORECASE)
    ))[:50]
    dice_candidates = []
    for line in lines:
        for match in re.finditer(r"(?<!\d)([1-6])\s*[,|/\-]\s*([1-6])\s*[,|/\-]\s*([1-6])(?!\d)", line):
            dice_candidates.append({
                "dice": [int(match.group(1)), int(match.group(2)), int(match.group(3))],
                "source_line": line[:240]
            })
            if len(dice_candidates) >= 50:
                break
        if len(dice_candidates) >= 50:
            break
    return {
        "page_url": request.page_url,
        "characters_received": len(raw),
        "lines_received": len(lines),
        "outcome_line_candidates": outcome_lines,
        "round_id_candidates": round_candidates,
        "md5_candidates": hashes,
        "dice_candidates": dice_candidates,
        "requires_user_review": True,
        "warning": (
            "Đây là các dấu hiệu trích xuất từ văn bản người dùng cung cấp, "
            "không phải dữ liệu đã xác thực từ LC79. Hãy đối chiếu với trang trước khi nhập."
        )
    }

@app.get("/v1/dice/theory")
def dice_theory():
    return theoretical_probabilities()

@app.post("/v1/dice/analyze")
def analyze_dice(request: DiceAnalysisRequest):
    rows, counts, sums = [], Counter(), Counter()
    for item in request.rounds:
        total, outcome = classify_dice(item.dice)
        counts[outcome] += 1
        sums[total] += 1
        rows.append({"round_id": item.round_id, "dice": item.dice, "total": total, "outcome": outcome})
    n = counts["TAI"] + counts["XIU"]
    return {
        "round_count": len(rows),
        "counts": {"tai": counts["TAI"], "xiu": counts["XIU"], "triple": counts["TRIPLE"], "special_other": counts["SPECIAL"]},
        "rates_excluding_triples": {
            "tai": counts["TAI"] / n if n else None,
            "xiu": counts["XIU"] / n if n else None
        },
        "confidence_interval_95": {
            "tai": wilson_interval(counts["TAI"], n),
            "xiu": wilson_interval(counts["XIU"], n)
        },
        "sum_distribution_observed": dict(sorted(sums.items())),
        "theoretical": theoretical_probabilities(),
        "rounds": rows,
        "warning": "Tần suất lịch sử không chứng minh phiên sau sẽ theo cùng xu hướng."
    }

@app.post("/v1/history/analyze")
def analyze_history(request: OutcomeHistoryRequest):
    outcomes = request.outcomes
    counts = Counter(outcomes)
    transitions = {"TAI": {"TAI": 0, "XIU": 0}, "XIU": {"TAI": 0, "XIU": 0}}
    for prev, cur in zip(outcomes, outcomes[1:]):
        if prev in transitions and cur in transitions[prev]:
            transitions[prev][cur] += 1
    last, streak = outcomes[-1], 0
    for value in reversed(outcomes):
        if value != last:
            break
        streak += 1
    correct = evaluated = 0
    for i in range(1, len(outcomes)):
        past = [x for x in outcomes[:i] if x in ("TAI", "XIU")]
        if not past or outcomes[i] not in ("TAI", "XIU"):
            continue
        c = Counter(past)
        pred = "TAI" if c["TAI"] >= c["XIU"] else "XIU"
        evaluated += 1
        correct += int(pred == outcomes[i])
    return {
        "round_count": len(outcomes),
        "counts": dict(counts),
        "rates": {k: counts[k] / len(outcomes) for k in ("TAI", "XIU", "TRIPLE")},
        "last_outcome": last,
        "current_streak": {"outcome": last, "length": streak},
        "transitions": transitions,
        "walk_forward_baseline": {
            "evaluated_predictions": evaluated,
            "correct": correct,
            "accuracy": correct / evaluated if evaluated else None,
            "confidence_interval_95": wilson_interval(correct, evaluated),
            "method": "Walk-forward baseline: chọn lớp chiếm đa số trong dữ liệu trước đó."
        },
        "warning": "Backtest không bảo đảm hiệu quả ở các phiên tương lai."
    }

@app.post("/v1/md5/inspect")
def inspect_md5(record: Md5Record):
    value = record.hash
    return {
        "round_id": record.round_id,
        "hash": value,
        "looks_like_md5": bool(re.fullmatch(r"[0-9a-fA-F]{32}", value)),
        "is_hex_string": bool(re.fullmatch(r"[0-9a-fA-F]+", value)),
        "length": len(value),
        "published_result": record.published_result,
        "can_reverse_hash_to_reveal_outcome": False,
        "note": "Không thể đảo ngược MD5 để biết kết quả. Muốn xác minh cần giao thức, seed, nonce và quy tắc công bố."
    }

@app.post("/v1/md5/batch")
def inspect_md5_batch(request: Md5BatchRequest):
    return {"count": len(request.records), "items": [inspect_md5(r) for r in request.records]}
