#!/usr/bin/env python3
"""
후속실험 3 일괄 실행기.

조건마다 브랜치가 다르므로(면적 항은 prior.py/loader.py 자체가 다르다) 한 checkout에서
전부 돌 수 없다. 이 스크립트는 조건별로 git worktree를 하나씩 띄우고, 같은 raw/validation
데이터를 물린 뒤 각 브랜치의 experiment.py를 돌려 결과 CSV를 한 곳으로 모은다.

    python run_followup3.py                  # 전체
    python run_followup3.py --only 1 2 3     # 번호로 고르기
    python run_followup3.py --group area     # 묶음으로 고르기
    python run_followup3.py --list           # 뭐가 돌지 먼저 보기
    python run_followup3.py --epochs 50 ...  # 배선 점검용 짧은 실행

데이터는 저장소에 없다. --data-dir 아래에 아래 파일이 있어야 한다.

    raw/재난프로젝트_시정촌별_통계데이터.xlsx
    raw/재난프로젝트_시정촌별_USGS.xlsx
    raw/시정촌_면적.csv              (면적 항 실험에만 필요)
    validation/LS_LF 데이터자료.xlsx

결과:
    outputs/followup3/<이름>.csv                실험 요약 한 줄 + 베이스라인
    outputs/followup3/<이름>/                   해당 조건의 outputs/ 전체
    outputs/followup3/summary.csv               전 조건 요약 한 장
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent
WORKTREE_DIR = REPO / ".followup3-worktrees"
RESULT_DIR = REPO / "outputs" / "followup3"

# 어느 조건에서나 필요한 입력.
BASE_DATA = (
    Path("raw/재난프로젝트_시정촌별_통계데이터.xlsx"),
    Path("raw/재난프로젝트_시정촌별_USGS.xlsx"),
    Path("validation/LS_LF 데이터자료.xlsx"),
)
# 면적 항(후속실험 3-④)에서만 추가로 필요한 입력.
AREA_DATA = (Path("raw/시정촌_면적.csv"),)


@dataclass(frozen=True)
class Run:
    """실험 하나. no/name은 교수님께 드린 표의 번호·이름 그대로다."""

    no: str
    name: str
    group: str
    branch: str
    args: tuple[str, ...] = ()
    needs_area: bool = False
    note: str = ""

    # 결과 이름. ③처럼 같은 브랜치를 평가 옵션만 바꿔 두 번 돌리는 경우가 있어
    # 브랜치명이 아니라 실험마다 따로 둔다.
    result_name: str = ""

    @property
    def stem(self) -> str:
        return self.result_name or self.branch

    @property
    def out_name(self) -> str:
        return f"{self.stem}.csv"


# ② 교수님 피드백 실험 — b 범위만 넓힌 조건. 브랜치의 DEFAULT_PRESET이 조건을 고정한다.
FEEDBACK_RUNS = [
    Run("1", "3번 b4", "feedback", "followup3-avg-b4",
        note="followup1-1-wood(3번) + b in [-2, 4]"),
    Run("2", "3번 b10", "feedback", "followup3-avg-b10",
        note="followup1-1-wood(3번) + b in [-2, 10]"),
    Run("3", "6번 b10", "feedback", "followup3-lqmax-b10",
        note="followup2-1-wood(6번, LQ 최대집계) + b in [-2, 10]"),
]

# ④ 면적 항 실험 — z = a·log p̄ + b + c·log k. 브랜치의 DEFAULT_AREA_MODE가 조건을 고정한다.
AREA_RUNS = [
    Run("A", "fixed", "area", "followup3-area-avg-fixed", needs_area=True,
        note="a=1 b=0 c=1 고정. 유도식 그대로(기준)"),
    Run("B", "tied", "area", "followup3-area-avg-tied", needs_area=True,
        note="a 학습, b 학습[-2,4], c=a. 순위는 fixed와 같고 확률 수준만 학습"),
    Run("C", "bounded", "area", "followup3-area-avg-bounded", needs_area=True,
        note="a 학습, b 학습[-2,4], c=1 고정. 기존 G2 방식"),
    Run("D", "free", "area", "followup3-area-avg-free", needs_area=True,
        note="a 학습, b 학습[-2,4], c 학습[0,2]"),
    Run("E", "c 작게", "area", "followup3-area-avg-a1-c05", needs_area=True,
        note="a=1 b=0 c=0.5 고정. 넓은 곳을 감점"),
    Run("F", "c 크게", "area", "followup3-area-avg-a1-c2", needs_area=True,
        note="a=1 b=0 c=2 고정. 넓은 곳에 가산점"),
]

# ③ 자연+혼재 재평가 — 학습을 새로 하지 않는다. 학습은 GT를 쓰지 않으므로 같은 seed면
# 모델이 완전히 동일하고, 바뀌는 것은 LS 평가에 들어가는 행뿐이다. 그래서 브랜치를
# 따로 만들지 않고 기반 모델의 브랜치에서 평가 옵션만 켜 결과 이름으로 구분한다.
NATMIX_RUNS = [
    Run("4", "3번 b10 자연혼재", "natmix", "followup3-avg-b10",
        args=("--gt-variant", "natmix"),
        result_name="followup3-avg-b10-natmix",
        note="2번과 같은 모델. ls_type이 자연/혼재인 행만 LS 양성으로 센다"),
    Run("5", "6번 b10 자연혼재", "natmix", "followup3-lqmax-b10",
        args=("--gt-variant", "natmix"),
        result_name="followup3-lqmax-b10-natmix",
        note="3번과 같은 모델. ls_type이 자연/혼재인 행만 LS 양성으로 센다"),
]

# ④-2 c를 hazard별로 분리 — 기존 6개는 c를 LS·LQ에 똑같이 강요했다. 실측으로 LS는
# 유도식 c=1에서 편향 +0.006으로 이미 맞고 LQ만 +0.256으로 과대예측한다.
# a=1, b=0, c_LS=1은 그대로 두고 c_LQ만 움직인다.
SPLIT_RUNS = [
    Run("G", "LQ c=0.5", "split", "followup3-area-avg-lq-c05", needs_area=True,
        note="c_LS=1 고정, c_LQ=0.5 고정"),
    Run("H", "LQ c=0.75", "split", "followup3-area-avg-lq-c075", needs_area=True,
        note="c_LS=1 고정, c_LQ=0.75 고정 (편향이 0을 지나는 지점의 선형 추정)"),
    Run("I", "LQ c 학습", "split", "followup3-area-avg-lq-c-free", needs_area=True,
        note="c_LS=1 고정, c_LQ만 학습 [0, 2]"),
]

# ④-3 눈금은 c가 아니라 b로 — b는 z에 더해지는 상수라 hazard 안에서 순위를 바꾸지
# 않는다. fixed의 prior 순위를 그대로 두고 확률 수준만 옮길 수 있다.
# 중심화는 b가 흡수하는 재매개변수화라 둘이 같은 답에 가야 정상이다.
BONLY_RUNS = [
    Run("J", "b만 학습", "bonly", "followup3-area-avg-b-only", needs_area=True,
        note="a=1 c=1 고정, b만 학습 [-12,12]. log k 원값"),
    Run("K", "b만 학습+중심화", "bonly", "followup3-area-avg-b-only-ctr", needs_area=True,
        note="같은 조건에 log k 평균 중심화. J와 같은 답에 가야 정상"),
]

RUNS: list[Run] = [*FEEDBACK_RUNS, *NATMIX_RUNS, *AREA_RUNS, *SPLIT_RUNS, *BONLY_RUNS]
GROUPS = ("feedback", "natmix", "area", "split", "bonly")


def sh(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd, text=True)


def check_data(data_dir: Path, runs: list[Run]) -> list[Path]:
    """없는 입력 파일을 모아서 돌려준다. 하나라도 없으면 그 조건은 돌지 않는다."""
    needed = set(BASE_DATA)
    if any(r.needs_area for r in runs):
        needed |= set(AREA_DATA)
    return sorted(p for p in needed if not (data_dir / p).exists())


def ensure_worktree(run: Run, *, fetch: bool) -> Path:
    """조건별 checkout을 만든다. 이미 있으면 그대로 쓴다."""
    path = WORKTREE_DIR / run.branch
    if path.exists():
        return path

    if fetch:
        sh(["git", "fetch", "origin", run.branch], cwd=REPO)

    WORKTREE_DIR.mkdir(parents=True, exist_ok=True)
    # 로컬 브랜치가 있으면 그것을, 없으면 origin/<branch>를 detach로 띄운다.
    local = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{run.branch}"],
        cwd=REPO, text=True, capture_output=True,
    )
    ref = run.branch if local.returncode == 0 else f"origin/{run.branch}"
    add = ["git", "worktree", "add", "-f", str(path), ref]
    if ref != run.branch:
        add.append("--detach")
    if sh(add, cwd=REPO).returncode != 0:
        raise RuntimeError(f"worktree 생성 실패: {run.branch}")
    return path


def link_data(work: Path, data_dir: Path, run: Run) -> None:
    """입력 파일을 조건별 checkout 안에 심볼릭 링크로 물린다(복사하면 8벌이 된다)."""
    wanted = [*BASE_DATA, *(AREA_DATA if run.needs_area else ())]
    for rel in wanted:
        dst = work / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.is_symlink() or dst.exists():
            dst.unlink()
        dst.symlink_to((data_dir / rel).resolve())


def collect(work: Path, run: Run) -> None:
    """그 조건의 outputs/ 전체를 결과 폴더로 옮겨 담는다."""
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    src = work / "outputs"
    if not src.exists():
        print(f"  ! outputs/가 없습니다: {src}")
        return

    dst = RESULT_DIR / run.stem
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

    summary = dst / run.out_name
    if summary.exists():
        shutil.copy2(summary, RESULT_DIR / run.out_name)
    print(f"  -> {dst}")


def build_summary() -> None:
    """조건별 요약 CSV를 한 장으로 합친다. 표로 만들어야 비교가 된다."""
    import pandas as pd

    frames = []
    for run in RUNS:
        path = RESULT_DIR / run.out_name
        if not path.exists():
            continue
        df = pd.read_csv(path)
        df.insert(0, "실험", f"{run.no} {run.name}")
        df.insert(1, "브랜치", run.branch)
        df.insert(2, "결과", run.stem)
        frames.append(df)

    if not frames:
        print("합칠 결과가 없습니다.")
        return

    out = RESULT_DIR / "summary.csv"
    merged = pd.concat(frames, ignore_index=True)
    merged.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\n저장: {out}  ({len(merged)}행)")

    show = ["실험", "결과", "prior_mode", "lam_gamma", "b_min", "b_max",
            "mse_ls", "mse_lq", "n_ls",
            "auc_ls", "auc_prior_ls", "auc_lq", "auc_prior_lq",
            "a_LS", "b_LS", "c_LS", "frac_middle"]
    print(merged[[c for c in show if c in merged.columns]].round(4).to_string(index=False))


def run_one(run: Run, *, data_dir: Path, epochs: int, seed: int, fetch: bool) -> bool:
    print(f"\n{'='*70}\n[{run.no}] {run.name}  ({run.branch})\n  {run.note}\n{'='*70}")

    work = ensure_worktree(run, fetch=fetch)
    link_data(work, data_dir, run)

    # ③은 기반 모델과 같은 checkout을 쓴다. 앞 실험의 outputs/를 그대로 두면
    # collect()가 남의 파일까지 퍼 간다.
    shutil.rmtree(work / "outputs", ignore_errors=True)

    cmd = [sys.executable, "experiment.py",
           "--epochs", str(epochs), "--seed", str(seed),
           "--out", run.out_name, *run.args]
    if sh(cmd, cwd=work).returncode != 0:
        print(f"  ! 실패: {run.branch}")
        return False

    collect(work, run)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="후속실험 3 일괄 실행")
    ap.add_argument("--data-dir", default=str(REPO),
                    help="raw/ 와 validation/ 이 들어 있는 폴더 (기본: 저장소 루트)")
    ap.add_argument("--only", nargs="+", metavar="NO",
                    help="실험 번호로 고른다. 예: --only 1 2 A F")
    ap.add_argument("--group", choices=GROUPS, help="묶음으로 고른다")
    ap.add_argument("--epochs", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-fetch", action="store_true", help="origin fetch를 건너뛴다")
    ap.add_argument("--list", action="store_true", help="돌릴 목록만 보여주고 끝낸다")
    ap.add_argument("--summary-only", action="store_true",
                    help="이미 모인 결과로 summary.csv만 다시 만든다")
    a = ap.parse_args()

    if a.summary_only:
        build_summary()
        return 0

    runs = RUNS
    if a.group:
        runs = [r for r in runs if r.group == a.group]
    if a.only:
        wanted = {s.upper() for s in a.only}
        runs = [r for r in runs if r.no.upper() in wanted]
    if not runs:
        print("고른 조건이 없습니다.")
        return 1

    print(f"실행할 조건 {len(runs)}개 x {a.epochs}에폭")
    for r in runs:
        print(f"  [{r.no}] {r.name:<16} {r.stem:<34} {r.note}")
    if a.list:
        return 0

    data_dir = Path(a.data_dir).resolve()
    missing = check_data(data_dir, runs)
    if missing:
        print(f"\n입력 파일이 없어 실행할 수 없습니다 (--data-dir={data_dir}):")
        for p in missing:
            print(f"  - {p}")
        print("\n이 파일들은 저장소에 커밋되어 있지 않습니다. "
              "로컬 사본이 있는 폴더를 --data-dir로 넘겨 주세요.")
        return 2

    ok = [run_one(r, data_dir=data_dir, epochs=a.epochs, seed=a.seed,
                  fetch=not a.no_fetch) for r in runs]

    print(f"\n{'='*70}\n성공 {sum(ok)}/{len(ok)}")
    build_summary()
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
