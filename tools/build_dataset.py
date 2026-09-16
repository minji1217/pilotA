#!/usr/bin/env python3
"""
이벤트별 CSV를 loader.py가 읽는 워크북 3개로 조립한다.

자료가 이벤트 단위 CSV로 들어오는데 loader.py는 "이벤트 = 시트" 구조의 XLSX를
기대한다. 이 스크립트가 그 사이를 잇는다.

입력 (기본 raw/events/, 이벤트 폴더 이름은 schema.EVENTS와 정확히 같아야 한다)

    raw/events/2000 돗토리/
    ├── stats.csv    통계   (제목 줄 + 부현/시정촌코드 헤더, 원본 그대로)
    ├── usgs.csv     USGS   (제목 줄 + 부현/시정촌코드 헤더, 원본 그대로)
    ├── gt_ls.csv    LS GT  (muni_code / ls_flag 또는 ls_area_ha, ls_type)
    └── gt_lq.csv    LQ GT  (muni_code / jshis_flag 또는 lq_flag)

출력

    raw/재난프로젝트_시정촌별_통계데이터.xlsx
    raw/재난프로젝트_시정촌별_USGS.xlsx
    raw/시정촌_면적.csv                    (usgs.csv에 area_km2가 있으면)
    validation/LS_LF 데이터자료.xlsx

실행:
    python tools/build_dataset.py            # 어떤 이벤트가 준비됐는지 보고 조립
    python tools/build_dataset.py --check    # 조립하지 않고 상태만 확인
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from schema import EVENTS, MUNICIPALITY_CODE_COLUMN

# 면적 관련 상수는 followup3-area-avg-* 브랜치의 schema.py에만 있다.
# 이 러너 브랜치는 main 기준이라 직접 들고 있는다. 이름이 바뀌면 여기만 고치면 된다.
AREA_EVENT_COLUMN = "event"
AREA_COLUMN = "area_km2"

EVENT_DIR = REPO / "raw" / "events"
STATS_OUT = REPO / "raw" / "재난프로젝트_시정촌별_통계데이터.xlsx"
USGS_OUT = REPO / "raw" / "재난프로젝트_시정촌별_USGS.xlsx"
AREA_OUT = REPO / "raw" / "시정촌_면적.csv"
GT_OUT = REPO / "validation" / "LS_LF 데이터자료.xlsx"

# 파일이름 -> 무엇인지. 넷 다 있어야 그 이벤트를 쓸 수 있다.
PARTS = ("stats.csv", "usgs.csv", "gt_ls.csv", "gt_lq.csv")


def event_status(event_dir: Path) -> dict[str, list[str]]:
    """이벤트마다 어떤 파일이 있고 없는지."""
    status = {}
    for event in EVENTS:
        d = event_dir / event
        status[event] = [p for p in PARTS if not (d / p).exists()]
    return status


def _raw_rows(path: Path) -> pd.DataFrame:
    """제목 줄까지 그대로 읽는다. loader가 헤더 행을 직접 찾으므로 건드리지 않는다."""
    return pd.read_csv(path, header=None, dtype=object, keep_default_na=False)


def _gt_rows(path: Path) -> pd.DataFrame:
    """GT는 첫 줄이 헤더다. loader가 header=0으로 읽는다."""
    return pd.read_csv(path)


def build(events: list[str], event_dir: Path) -> None:
    STATS_OUT.parent.mkdir(parents=True, exist_ok=True)
    GT_OUT.parent.mkdir(parents=True, exist_ok=True)

    for out, name in ((STATS_OUT, "stats.csv"), (USGS_OUT, "usgs.csv")):
        with pd.ExcelWriter(out, engine="openpyxl") as xw:
            for event in events:
                _raw_rows(event_dir / event / name).to_excel(
                    xw, sheet_name=event, index=False, header=False
                )
        print(f"저장: {out}  (시트 {len(events)}개)")

    with pd.ExcelWriter(GT_OUT, engine="openpyxl") as xw:
        for event in events:
            for part, kind in (("gt_ls.csv", "LS"), ("gt_lq.csv", "LQ")):
                _gt_rows(event_dir / event / part).to_excel(
                    xw, sheet_name=f"{event}({kind})", index=False
                )
    print(f"저장: {GT_OUT}  (시트 {len(events) * 2}개)")

    # 면적은 USGS 표에 area_km2로 같이 들어오는 경우가 있다. 있으면 뽑아 쓴다.
    frames = []
    for event in events:
        raw = _raw_rows(event_dir / event / "usgs.csv")
        header = next(
            (i for i, row in raw.iterrows()
             if {MUNICIPALITY_CODE_COLUMN, AREA_COLUMN} <= set(map(str, row))),
            None,
        )
        if header is None:
            continue
        df = pd.read_csv(event_dir / event / "usgs.csv", header=header,
                         dtype={MUNICIPALITY_CODE_COLUMN: str})
        df = df[[MUNICIPALITY_CODE_COLUMN, AREA_COLUMN]].dropna()
        df = df.loc[df[MUNICIPALITY_CODE_COLUMN].astype(str).str.strip() != ""]
        df.insert(0, AREA_EVENT_COLUMN, event)
        frames.append(df)

    if not frames:
        print(f"! {AREA_OUT.name}을 만들지 못했습니다. usgs.csv에 {AREA_COLUMN}가 없습니다.")
        print("  면적 항 실험(④)은 이 파일이 있어야 돕니다.")
        return

    area = pd.concat(frames, ignore_index=True)
    area.to_csv(AREA_OUT, index=False, encoding="utf-8-sig")
    print(f"저장: {AREA_OUT}  ({len(area)}행 / 이벤트 {len(frames)}개)")
    if len(frames) != len(events):
        missing = len(events) - len(frames)
        print(f"! {missing}개 이벤트의 usgs.csv에 {AREA_COLUMN}가 없어 면적이 비었습니다.")


def main() -> int:
    ap = argparse.ArgumentParser(description="이벤트별 CSV를 워크북으로 조립")
    ap.add_argument("--event-dir", default=str(EVENT_DIR))
    ap.add_argument("--check", action="store_true", help="조립하지 않고 상태만 본다")
    ap.add_argument("--partial", action="store_true",
                    help="이벤트가 다 모이지 않아도 있는 것만으로 조립한다. "
                         "loader는 9개 이벤트를 모두 요구하므로 학습은 돌지 않는다")
    a = ap.parse_args()

    event_dir = Path(a.event_dir)
    status = event_status(event_dir)
    ready = [e for e, missing in status.items() if not missing]

    print(f"이벤트 {len(ready)}/{len(EVENTS)}개 준비됨 ({event_dir})")
    for event in EVENTS:
        missing = status[event]
        mark = "OK  " if not missing else "없음"
        detail = "" if not missing else f"  <- {', '.join(missing)}"
        print(f"  [{mark}] {event}{detail}")

    if a.check:
        return 0
    if not ready:
        print("\n조립할 이벤트가 없습니다.")
        return 1
    if len(ready) != len(EVENTS) and not a.partial:
        print(f"\nloader는 {len(EVENTS)}개 이벤트를 모두 요구합니다. "
              f"있는 것만 조립하려면 --partial을 주세요(학습은 돌지 않습니다).")
        return 2

    print()
    build(ready, event_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
