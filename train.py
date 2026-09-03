from pathlib import Path

import pandas as pd
import torch

from likelihood import DamageLikelihood
from regression import DamageRegression
from prior import Prior
from marginal import marginalize
from infer import infer
from loader import EVAL_EVENT_NAME, load_eval_ground_truth, load_pilot_a_batch
from eval import evaluate
from schema import INDEX_TO_EVENT, EvalGroundTruthBatch, PilotABatch

from reporting import dump_params, save_loss_history

STATS_PATH = "raw/재난프로젝트_시정촌별_통계데이터.xlsx"
USGS_PATH = "raw/재난프로젝트_시정촌별_USGS.xlsx"
GT_PATH = "validation/LS_LF_데이터자료.xlsx"


def save_predictions(batch, p_ls, p_lq, path="outputs/predictions.csv"):
    """전체 382행의 사후확률을 저장한다."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame({
        "event_idx": batch.event_idx.tolist(),
        "event": [INDEX_TO_EVENT[i] for i in batch.event_idx.tolist()],
        "muni_code": list(batch.municipality_code),
        "p_ls": p_ls.detach().numpy(),
        "p_lq": p_lq.detach().numpy(),
    })
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"저장: {path}  ({len(df)}행)")
    return df


def to_eval_pred(batch: PilotABatch, p_ls, p_lq, eval_gt: EvalGroundTruthBatch):
    """eval.py에 넘길 훗카이도 행만 뽑는다.

    loader가 만든 model_row_idx가 이미 GT와 같은 순서로 정렬돼 있으므로
    event_idx로 다시 마스킹하지 않고 그대로 쓴다.
    """
    idx = eval_gt.model_row_idx

    return pd.DataFrame({
        "muni_code": list(eval_gt.municipality_code),
        "p_ls": p_ls[idx].detach().numpy(),
        "p_lq": p_lq[idx].detach().numpy(),
    })


def to_eval_gt(eval_gt: EvalGroundTruthBatch):
    """EvalGroundTruthBatch를 eval.py가 쓰는 컬럼명으로 바꾼다."""
    return pd.DataFrame({
        "muni_code": list(eval_gt.municipality_code),
        "ls_true": eval_gt.gt_ls.tolist(),
        "lq_true": eval_gt.gt_lq.tolist(),
        "ls_eval_mask": eval_gt.ls_eval_mask.tolist(),
    })


def save_eval(result, gt_df, dir_="outputs", tag=""):
    Path(dir_).mkdir(parents=True, exist_ok=True)
    sfx = f"_{tag}" if tag else ""

    # ① 요약 — 나중에 여러 실험을 세로로 쌓기 좋게
    summary = pd.DataFrame([{
        "event": EVAL_EVENT_NAME,
        "n": result.n,
        "n_ls": result.n_ls,
        "mse_ls": result.mse_ls,
        "mse_lq": result.mse_lq,
        "n_pos_ls": int(gt_df.loc[gt_df["ls_eval_mask"], "ls_true"].sum()),
        "n_pos_lq": int(gt_df["lq_true"].sum()),
        "note": "LS는 원본 NA 행 평가 제외(ls_eval_mask), LQ는 NA를 0으로 간주",
    }])
    summary.to_csv(f"{dir_}/eval_summary{sfx}.csv", index=False, encoding="utf-8-sig")

    # ② 상세 — 시정촌별로 정답/예측/오차를 펼쳐서 확인용
    detail = result.merged.copy()
    detail["err_ls"] = (detail["p_ls"] - detail["ls_true"]) ** 2
    detail["err_lq"] = (detail["p_lq"] - detail["lq_true"]) ** 2

    # ls_eval_mask=False인 행의 ls_true는 원본이 NA라서 넣어둔 placeholder 0이다.
    # 진짜 정답이 아니므로 err_ls를 계산해봐야 의미가 없고, mse_ls에도 안 들어간다.
    # 파일만 보고 오해하지 않도록 비워둔다.
    excluded_ls = ~detail["ls_eval_mask"].astype(bool)
    detail.loc[excluded_ls, ["ls_true", "err_ls"]] = pd.NA
    # 시정촌코드 순으로 정렬한다. 5자리 고정폭 문자열이라 문자열 정렬이 곧 번호 순이다.
    detail.sort_values("muni_code").to_csv(
        f"{dir_}/eval_detail{sfx}.csv", index=False, encoding="utf-8-sig"
    )
    print(f"저장: {dir_}/eval_summary{sfx}.csv, {dir_}/eval_detail{sfx}.csv")


def train(batch, *,seed=0,epochs=3000,lr=0.02,lam_gamma=0.0,prior_mode="free",b_bound=2.0):
    """
    lam_gamma  : gamma에 거는 L2 정규화 계수. loss에 lam_gamma * sum(gamma^2)를 더한다.
                 gamma에 N(0, 1/(2*lam_gamma)) prior를 준 MAP 추정과 같다.
                 0이면 정규화 없음(= 기존 MLE).
    prior_mode : Prior의 a, b 제약 방식. "free" / "fixed" / "bounded"
    b_bound    : prior_mode="bounded"일 때 b의 범위. b in [-b_bound, +b_bound]
    """
    torch.manual_seed(seed)

    like=DamageLikelihood()
    reg=DamageRegression()
    pri=Prior(mode=prior_mode,b_bound=b_bound)

    history = []
    reg.initialize_from_batch(batch)
    opt=torch.optim.Adam(list(like.parameters())+list(reg.parameters())+list(pri.parameters()),lr=lr)
    #total param??
    print(f"총 학습될 파라미터 : {sum(p.numel() for p in opt.param_groups[0]['params'])}개")
    

    for epoch in range(epochs):
        out_r=reg(batch)
        # -> 이제 람다들을 만들었으니 이걸... 어떻게 하더라 곱해서 L 하나 내뱉는걸로
        out_l=like(batch,out_r.mu)
        w_batch=pri(batch.pi_ls,batch.pi_lq)
        
        _,log_Py=marginalize(w_batch,out_l.log_L)
        nll=-log_Py.sum()

        # gamma는 softplus를 거친 실제 값에 건다. 변환 전 raw에 걸면 식의 gamma가 아니다.
        if lam_gamma > 0:
            penalty = lam_gamma * (
                (reg.gamma_ls ** 2).sum() + (reg.gamma_lq ** 2).sum()
            )
        else:
            penalty = torch.zeros((), dtype=nll.dtype)
        loss = nll + penalty

        opt.zero_grad() #기울기 누적 초기화
        loss.backward()
        opt.step()

        nll_val = float(nll.item())
        history.append({
            "epoch": epoch,
            "nll_total": nll_val,
            "nll_per_row": nll_val / batch.batch_size,
            "penalty": float(penalty.item()),
            "loss_total": float(loss.item()),
        })

        if epoch%100==0:
            print(f"{epoch}번째 학습=> loss :{loss}")

    return reg,like,pri,pd.DataFrame(history)



if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="Pilot A 학습 1회 실행. 에폭별 loss와 학습 파라미터를 CSV로 저장한다."
    )
    ap.add_argument("--prior-mode", default="free", choices=["free", "fixed", "bounded"],
                    help="prior의 a, b 제약. free=제약없음(기본) / fixed=a1,b0 고정 / bounded=범위제한")
    ap.add_argument("--lam-gamma", type=float, default=0.0,
                    help="gamma L2 정규화 계수. 0이면 정규화 없음(기본)")
    ap.add_argument("--b-bound", type=float, default=2.0,
                    help="prior-mode=bounded일 때 b의 범위. b in [-b_bound, +b_bound]")
    ap.add_argument("--epochs", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--lr", type=float, default=0.02)
    ap.add_argument("--tag", default="",
                    help="출력 파일명 뒤에 붙일 꼬리표. 여러 설정을 비교할 때 서로 덮이지 않는다")
    args = ap.parse_args()

    sfx = f"_{args.tag}" if args.tag else ""

    # 학습용 batch(382행)를 만들고, 선배가 만든 API로 평가용 GT를 정렬해 받는다.
    # GT는 eval 전용이라 train()에는 넘기지 않는다.
    batch = load_pilot_a_batch(STATS_PATH, USGS_PATH)
    eval_gt = load_eval_ground_truth(GT_PATH, batch)
    print(f"batch {batch.batch_size}행 / 평가 GT {eval_gt.batch_size}행 ({EVAL_EVENT_NAME})")
    print(f"설정: prior_mode={args.prior_mode} / lam_gamma={args.lam_gamma}"
          + (f" / b_bound=±{args.b_bound}" if args.prior_mode == "bounded" else ""))

    reg, like, pri, hist = train(
        batch=batch, seed=args.seed, epochs=args.epochs, lr=args.lr,
        lam_gamma=args.lam_gamma, prior_mode=args.prior_mode, b_bound=args.b_bound,
    )
    save_loss_history(hist, tag=args.tag)
    dump_params(reg, like, pri, path=f"outputs/params{sfx}.csv")

    with torch.no_grad():                        # ← grad 안 만듦
        out_r = reg(batch)
        out_l = like(batch, out_r.mu)
        log_w = pri(batch.pi_ls, batch.pi_lq)
        log_joint, log_Py = marginalize(log_w, out_l.log_L)
        p_ls, p_lq = infer(log_joint, log_Py)

    save_predictions(batch, p_ls, p_lq, path=f"outputs/predictions{sfx}.csv")

    gt = to_eval_gt(eval_gt)
    pred = to_eval_pred(batch, p_ls, p_lq, eval_gt)
    result = evaluate(gt, pred)
    save_eval(result, gt, tag=args.tag)

    print(
        f"MSE_LS {result.mse_ls:.4f} (n={result.n_ls}) / "
        f"MSE_LQ {result.mse_lq:.4f} (n={result.n})"
    )
