"""RQ4 Ablation study 러너.

교수님 논리구조 v1.1 문서의 RQ4(각 층위의 설계는 정확도에 얼마나 기여하는가)를
LOEO(Leave-One-Event-Out) 방식으로 돌린다.

조건 6개 (Full 기준선 + ablation 5개):
    full          아무것도 빼지 않은 제안 모델(TRACE)
    no_prior      [입력 층위]  prior를 균등분포로 교체 (z = 0 상수)
    no_pgv        [입력 층위]  흔들림 강도 항 beta_c*log(PGV) 제거
    poisson       [구조 층위]  음이항분포 -> 포아송분포
    no_offset     [구조 층위]  노출 offset 제거 (mu = E*lambda -> mu = lambda)
    single_event  [학습 층위]  크로스이벤트 학습 -> 평가 이벤트 하나만으로 단독 학습

평가 이벤트 7개: 2007 주에쓰오키·2008 이와테미야기는 LS·LQ 모두 한쪽 클래스만
있어 AUC가 정의되지 않고 어떤 가중평균에도 기여하지 못하므로 제외한다.

중간에 끊겨도 results.csv에 남은 조합은 건너뛴다(이어서 실행 가능).

실행:
    python rq4_ablation.py                 # 남은 조합을 전부
    python rq4_ablation.py --budget 150    # 150초 안에 들어가는 만큼만
    python rq4_ablation.py --only full     # 한 조건만
"""
import argparse
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import pandas as pd
import torch

from infer import infer
from loader import attach_ls_labels, load_eval_ground_truth, load_pilot_a_batch, subset_batch
from marginal import marginalize
from prior import prior_log_w
from reporting import dump_params
from schema import EVENT_TO_INDEX
from train import GT_PATH, STATS_PATH, USGS_PATH, report_holdout, train

OUT = Path("outputs/rq4")
RESULTS = OUT / "results.csv"

# 논문 기준 조건(E3 + 액상화 J + 라벨 학습). followup4-lq-J-labels 브랜치 기본값과 동일하다.
BASE = dict(
    seed=0, epochs=3000, lr=0.02, lam_gamma=10.0,
    area_mode="fixed-cov-mtn", lam_kappa=10.0, mtn_standardize="train",
    use_labels=True, lq_labels=True, lq_b_only=True,
)

CONDITIONS = {
    "full":         {},
    "no_prior":     {"prior_uniform": True},
    "no_pgv":       {"use_pgv": False},
    "poisson":      {"like_dist": "poisson"},
    "no_offset":    {"use_exposure": False},
    # 단독 학습은 평가 이벤트 자신으로만 학습하므로 라벨을 쓰면 정답 누수가 된다.
    "single_event": {"_single": True, "use_labels": False, "lq_labels": False},
}

EVAL_EVENTS = [
    "2000 돗토리",
    "2004 니가타현주에쓰",
    "2016 구마모토",
    "2018 오사카",
    "2018 훗카이도",
    "2021 후쿠시마",
    "2024 노토반도",
]

EST_SECONDS = 32.0  # 1회 소요 실측(학습 약 21초 + 추론·채점). 스모크 추정 127초는 과대였다.


def run_one(batch, cond_name, event):
    """조건 하나 x 이벤트 하나. report_holdout이 기존 결과와 같은 형식의 summary를 돌려준다."""
    kw = dict(BASE)
    kw.update({k: v for k, v in CONDITIONS[cond_name].items() if not k.startswith("_")})
    single = CONDITIONS[cond_name].get("_single", False)

    ho = EVENT_TO_INDEX[event]
    if single:
        # 단독 학습: 그 이벤트만으로 학습한다(기준 이벤트가 되어 alpha_e = 0).
        train_batch = subset_batch(batch, batch.event_idx == ho)
    else:
        # 크로스이벤트 학습: 그 이벤트를 빼고 나머지 8개로 학습한다.
        train_batch = subset_batch(batch, batch.event_idx != ho)

    t0 = time.time()
    reg, like, pri, hist = train(train_batch, **kw)
    train_sec = time.time() - t0

    sfx = f"_rq4_{cond_name}_{event.replace(' ', '')}"
    t1 = time.time()
    with torch.no_grad():
        out_r = reg(batch)
        out_l = like(batch, out_r.mu)
        log_w = prior_log_w(pri, batch)
        log_joint, log_Py = marginalize(log_w, out_l.log_L)
        p_ls, p_lq = infer(log_joint, log_Py)
    infer_sec = time.time() - t1

    summary = report_holdout(batch, reg, like, pri, p_ls, p_lq, event, sfx)
    dump_params(reg, like, pri, path=str(OUT / f"params{sfx}.csv"))

    n_trainable = sum(p.numel() for m in (reg, like, pri)
                      for p in m.parameters() if p.requires_grad)
    row = {
        "condition": cond_name,
        "event": event,
        "n_train_rows": int(train_batch.batch_size),
        "n_params": n_trainable,
        "train_sec": round(train_sec, 2),
        "infer_sec": round(infer_sec, 4),
        "nll_final": round(float(hist.iloc[-1]["nll_total"]), 4),
        "loss_final": round(float(hist.iloc[-1]["loss_total"]), 4),
    }
    row.update(summary)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, default=None,
                    help="이 초 안에 들어가는 만큼만 돌리고 깨끗하게 종료한다")
    ap.add_argument("--only", nargs="+", default=None, choices=list(CONDITIONS),
                    help="이 조건만 돌린다")
    args = ap.parse_args()

    started = time.time()
    OUT.mkdir(parents=True, exist_ok=True)

    done = set()
    rows = []
    if RESULTS.exists():
        prev = pd.read_csv(RESULTS, encoding="utf-8-sig")
        rows = prev.to_dict("records")
        done = {(r["condition"], r["event"]) for r in rows}

    conds = args.only or list(CONDITIONS)
    todo = [(c, e) for c in conds for e in EVAL_EVENTS if (c, e) not in done]
    print(f"완료 {len(done)}개 / 남은 조합 {len(todo)}개")
    if not todo:
        print("전부 완료됨.")
        return

    for i, (cond, event) in enumerate(todo, 1):
        elapsed = time.time() - started
        if args.budget is not None and i > 1 and elapsed + EST_SECONDS > args.budget:
            print(f"\n[예산 종료] {elapsed:.0f}초 경과. 남은 {len(todo) - i + 1}개는 다음 실행에서.")
            break
        print(f"\n{'='*64}\n[{i}/{len(todo)}] {cond}  x  {event}\n{'='*64}", flush=True)
        row = run_one(batch_global, cond, event)
        rows.append(row)
        # 매회 즉시 저장. 중간에 끊겨도 여기까지는 남는다.
        pd.DataFrame(rows).to_csv(RESULTS, index=False, encoding="utf-8-sig")
        print(f"  -> LS prior {row.get('auc_cov_kappa_prior')} / 사후 {row.get('auc_posterior')}"
              f" | LQ prior {row.get('auc_lq_kappa_prior')} / 사후 {row.get('auc_lq_posterior')}"
              f" | {row['train_sec']}초", flush=True)

    print(f"\n저장: {RESULTS} ({len(rows)}행)")


if __name__ == "__main__":
    print("데이터 로드 중...", flush=True)
    _b = load_pilot_a_batch(STATS_PATH, USGS_PATH)
    _gt = load_eval_ground_truth(GT_PATH, _b)
    batch_global = attach_ls_labels(GT_PATH, _b, _gt)
    print(f"batch {batch_global.batch_size}행 / 평가 GT {_gt.batch_size}행", flush=True)
    main()
