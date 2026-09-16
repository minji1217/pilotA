import json
import sys
from pathlib import Path

import pandas as pd
import torch
import torch.nn.functional as F

from likelihood import DamageLikelihood
from regression import DamageRegression
from prior import AreaPrior, Prior, prior_log_w, prior_z
from marginal import marginalize
from infer import infer
from loader import load_eval_ground_truth, load_pilot_a_batch
from eval import evaluate
from schema import EVENT_TO_INDEX, INDEX_TO_EVENT, EvalGroundTruthBatch, PilotABatch

from reporting import dump_params, save_eval, save_loss_history

STATS_PATH = "raw/재난프로젝트_시정촌별_통계데이터.xlsx"
USGS_PATH = "raw/재난프로젝트_시정촌별_USGS.xlsx"
GT_PATH = "validation/LS_LF 데이터자료.xlsx"


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

    prior_ls / prior_lq는 보정 전 USGS prior 그대로다.
    사후가 사전보다 나아졌는지 보려면 같은 행에서 잰 prior AUC가 있어야 한다.
    """
    idx = eval_gt.model_row_idx

    return pd.DataFrame({
        # 같은 시정촌코드가 여러 이벤트에 나오므로 event_idx까지 있어야 join이 성립한다.
        "event_idx": eval_gt.event_idx.tolist(),
        "muni_code": list(eval_gt.municipality_code),
        "p_ls": p_ls[idx].detach().numpy(),
        "p_lq": p_lq[idx].detach().numpy(),
        "prior_ls": batch.pi_ls[idx].detach().numpy(),
        "prior_lq": batch.pi_lq[idx].detach().numpy(),
    })


def to_eval_gt(eval_gt: EvalGroundTruthBatch):
    """EvalGroundTruthBatch를 eval.py가 쓰는 컬럼명으로 바꾼다."""
    return pd.DataFrame({
        "event_idx": eval_gt.event_idx.tolist(),
        "event": [INDEX_TO_EVENT[i] for i in eval_gt.event_idx.tolist()],
        "muni_code": list(eval_gt.municipality_code),
        "ls_true": eval_gt.gt_ls.tolist(),
        "lq_true": eval_gt.gt_lq.tolist(),
        # LS와 LQ는 원본 NA 처리 규칙이 달라 평가 가능한 행이 서로 다르다.
        "ls_eval_mask": eval_gt.ls_eval_mask.tolist(),
        "lq_eval_mask": eval_gt.lq_eval_mask.tolist(),
    })


def build_bce_targets(eval_gt: EvalGroundTruthBatch, *, test_event=None):
    """지시서 §2-3의 BCE 대상 행을 고른다.

    대상: ls_flag가 0 또는 1인 평가 행(=ls_eval_mask) 중 시험 지진이 아닌 행.
    시험 지진의 피해 건수는 NLL에 그대로 들어간다. 가리는 것은 그 지진의 ls_flag뿐이다.

    출력: (batch 내 행 index [n], 정답 0/1 [n])
    """
    mask = eval_gt.ls_eval_mask.clone()
    if test_event is not None:
        if test_event not in EVENT_TO_INDEX:
            raise ValueError(
                f"--test-event '{test_event}'는 EVENTS에 없습니다: {sorted(EVENT_TO_INDEX)}"
            )
        mask &= eval_gt.event_idx != EVENT_TO_INDEX[test_event]

    return eval_gt.model_row_idx[mask], eval_gt.gt_ls[mask]


def build_prior(*, prior_family="base", prior_mode="free", b_bound=2.0,
                b_min=None, b_max=None, mtn_prior=False, fix_b=False, area_link="log"):
    """지시서 §2-1의 A 계열(base) / B 계열(area) prior를 만든다."""
    if prior_family == "area":
        return AreaPrior(
            b_min=-2.0 if b_min is None else b_min,
            b_max=4.0 if b_max is None else b_max,
            fix_b=fix_b, mtn_prior=mtn_prior, link=area_link,
        )
    return Prior(mode=prior_mode, b_bound=b_bound, b_min=b_min, b_max=b_max,
                 mtn_prior=mtn_prior)


def train(batch, *,seed=0,epochs=3000,lr=0.02,lam_gamma=0.0,prior_mode="free",b_bound=2.0,
          b_min=None,b_max=None,
          prior_family="base",mtn_prior=False,fix_b=False,area_link="log",
          ls_bce_weight=0.0,bce_idx=None,bce_y=None):
    """
    lam_gamma  : gamma에 거는 L2 정규화 계수. loss에 lam_gamma * sum(gamma^2)를 더한다.
                 gamma에 N(0, 1/(2*lam_gamma)) prior를 준 MAP 추정과 같다.
                 0이면 정규화 없음(= 기존 MLE).
    prior_mode : Prior의 a, b 제약 방식. "free" / "fixed" / "bounded"
    b_bound    : prior_mode="bounded"일 때 b의 범위. b in [-b_bound, +b_bound]
    b_min/b_max: 비대칭 b 범위가 필요할 때 b_bound 대신 쓴다.
                 후속실험 2의 b in [-2, 4]가 이 경우다. 둘 다 줘야 한다.

    ---- 아래는 후속실험 3(LOEO)에서 옵션으로 추가한 것이다. 기본값이면 기존과 같다. ----

    prior_family  : "base"(A 계열, 기존 Prior) / "area"(B 계열, AreaPrior)
    mtn_prior     : True면 z_LS에 kappa * z_mtn을 더한다. kappa도 같은 optimizer에 들어간다.
    fix_b         : prior_family="area"에서 b_LS를 0으로 고정한다(B0).
    area_link     : "log"(주 조건) / "logit"(지시서 §2-1 B 표기, 민감도)
    ls_bce_weight : 지시서 §2-3의 omega. 0이면 BCE 항이 loss에 전혀 들어가지 않는다.
    bce_idx/bce_y : BCE 대상 행의 batch 내 행 index [n]와 산사태 정답 0/1 [n].
                    시험 지진의 행은 호출하는 쪽에서 미리 빼고 넘긴다.

    기존 loss(NLL + lam_gamma 패널티)는 한 글자도 바꾸지 않았다.
    BCE는 그 위에 omega * sum(BCE_i)로 더해지기만 한다.
    """
    torch.manual_seed(seed)

    like=DamageLikelihood()
    reg=DamageRegression()
    pri=build_prior(prior_family=prior_family,prior_mode=prior_mode,b_bound=b_bound,
                    b_min=b_min,b_max=b_max,mtn_prior=mtn_prior,fix_b=fix_b,
                    area_link=area_link)

    use_bce = ls_bce_weight > 0 and bce_idx is not None and bce_idx.numel() > 0
    if use_bce:
        bce_y = bce_y.to(dtype=batch.pi_ls.dtype)

    history = []
    reg.initialize_from_batch(batch)
    opt=torch.optim.Adam(list(like.parameters())+list(reg.parameters())+list(pri.parameters()),lr=lr)
    #total param??
    n_param = sum(p.numel() for p in opt.param_groups[0]['params'])
    print(f"총 학습될 파라미터 : {n_param}개")
    if mtn_prior:
        # kappa가 정말 optimizer 안에 있는지 눈으로 확인한다(지시서 §2-3, §7-6).
        in_opt = any(p is pri.kappa for p in opt.param_groups[0]["params"])
        print(f"  kappa optimizer 포함 여부 : {in_opt}")
        if not in_opt:
            raise RuntimeError("kappa가 optimizer에 들어가지 않았습니다.")
    if use_bce:
        print(f"  BCE 대상 {int(bce_idx.numel())}행 / omega={ls_bce_weight}")

    for epoch in range(epochs):
        out_r=reg(batch)
        # -> 이제 람다들을 만들었으니 이걸... 어떻게 하더라 곱해서 L 하나 내뱉는걸로
        out_l=like(batch,out_r.mu)
        w_batch=prior_log_w(pri,batch)
        
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

        # 지시서 §2-3. 기존 loss 위에 omega * sum(BCE)를 더하기만 한다.
        # 수치 안정성 때문에 q_LS가 아니라 z_LS로 직접 계산한다.
        if use_bce:
            z_ls, _ = prior_z(pri, batch)
            bce = F.binary_cross_entropy_with_logits(
                z_ls[bce_idx], bce_y, reduction="sum"
            )
            loss = loss + ls_bce_weight * bce
        else:
            bce = torch.zeros((), dtype=nll.dtype)

        opt.zero_grad() #기울기 누적 초기화
        loss.backward()
        opt.step()

        nll_val = float(nll.item())
        history.append({
            "epoch": epoch,
            "nll_total": nll_val,
            "nll_per_row": nll_val / batch.batch_size,
            "penalty": float(penalty.item()),
            # 기존 loss = NLL + penalty. BCE를 빼고도 비교할 수 있게 따로 남긴다.
            "loss_base": nll_val + float(penalty.item()),
            "bce_sum": float(bce.item()),
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
    ap.add_argument("--b-min", type=float, default=None,
                    help="비대칭 b 범위의 하한. --b-max와 함께 주면 --b-bound를 대신한다")
    ap.add_argument("--b-max", type=float, default=None,
                    help="비대칭 b 범위의 상한. 후속실험 2는 --b-min -2 --b-max 4")
    ap.add_argument("--epochs", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--lr", type=float, default=0.02)
    ap.add_argument("--tag", default="",
                    help="출력 파일명 뒤에 붙일 꼬리표. 여러 설정을 비교할 때 서로 덮이지 않는다")

    # ---- 후속실험 3(LOEO) 옵션. 전부 기본값이면 위의 기존 동작과 완전히 같다. ----
    ap.add_argument("--prior-family", default="base", choices=["base", "area"],
                    help="base=기존 prior(A 계열) / area=면적 항 prior(B 계열, 지시서 §2-1 B)")
    ap.add_argument("--area-link", default="log", choices=["log", "logit"],
                    help="prior-family=area의 링크. log=주 조건(기본) / logit=지시서 §2-1 B 표기, 민감도")
    ap.add_argument("--fix-b", action="store_true",
                    help="prior-family=area에서 b_LS를 0으로 고정한다(B0)")
    ap.add_argument("--mtn-prior", action="store_true",
                    help="z_LS에 kappa * z_mtn(표준화 산지 비율)을 더한다")
    ap.add_argument("--ls-bce-weight", type=float, default=0.0,
                    help="지시서 §2-3의 omega. 0(기본)이면 BCE 항이 loss에 들어가지 않는다")
    ap.add_argument("--test-event", default=None,
                    help="이 지진의 ls_flag를 BCE 대상에서 뺀다(LOEO 시험 지진)")
    ap.add_argument("--out", default=None,
                    help="결과 저장 폴더. 주면 outputs/ 대신 이 폴더에 전부 저장한다")
    args = ap.parse_args()

    sfx = f"_{args.tag}" if args.tag else ""
    out_dir = args.out or "outputs"
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    # 학습용 batch(382행)를 만들고, 선배가 만든 API로 평가용 GT를 정렬해 받는다.
    # GT는 eval 전용이라 train()에는 넘기지 않는다.
    batch = load_pilot_a_batch(STATS_PATH, USGS_PATH)
    eval_gt = load_eval_ground_truth(GT_PATH, batch)
    n_ev = int(eval_gt.event_idx.unique().numel())
    print(f"batch {batch.batch_size}행 / 평가 GT {eval_gt.batch_size}행 / 이벤트 {n_ev}개")
    if args.b_min is not None or args.b_max is not None:
        b_desc = f"b∈[{args.b_min}, {args.b_max}]"
    else:
        b_desc = f"b∈[-{args.b_bound}, {args.b_bound}]"
    print(f"설정: prior_family={args.prior_family} / prior_mode={args.prior_mode}"
          f" / lam_gamma={args.lam_gamma}"
          + (f" / {b_desc}" if args.prior_mode == "bounded" or args.prior_family == "area" else "")
          + (f" / area_link={args.area_link}" if args.prior_family == "area" else "")
          + (" / mtn_prior" if args.mtn_prior else "")
          + (f" / omega={args.ls_bce_weight}" if args.ls_bce_weight else ""))

    # 지시서 §2-3의 BCE 대상 행을 고른다.
    # 학습 지진(= 시험 지진을 뺀 나머지)에서 ls_flag가 0 또는 1인 행이다. NA는 애초에 빠져 있다.
    bce_idx, bce_y = build_bce_targets(eval_gt, test_event=args.test_event)
    if args.test_event is not None:
        n_test = int((eval_gt.event_idx == EVENT_TO_INDEX[args.test_event]).logical_and(
            eval_gt.ls_eval_mask).sum())
        print(f"시험 지진 '{args.test_event}': 시험 {n_test}행 / BCE 대상 {int(bce_idx.numel())}행")

    reg, like, pri, hist = train(
        batch=batch, seed=args.seed, epochs=args.epochs, lr=args.lr,
        lam_gamma=args.lam_gamma, prior_mode=args.prior_mode, b_bound=args.b_bound,
        b_min=args.b_min, b_max=args.b_max,
        prior_family=args.prior_family, mtn_prior=args.mtn_prior, fix_b=args.fix_b,
        area_link=args.area_link,
        ls_bce_weight=args.ls_bce_weight, bce_idx=bce_idx, bce_y=bce_y,
    )
    save_loss_history(hist, dir_=out_dir, tag=args.tag)
    dump_params(reg, like, pri, path=f"{out_dir}/params{sfx}.csv")

    with torch.no_grad():                        # ← grad 안 만듦
        out_r = reg(batch)
        out_l = like(batch, out_r.mu)
        log_w = prior_log_w(pri, batch)
        log_joint, log_Py = marginalize(log_w, out_l.log_L)
        p_ls, p_lq = infer(log_joint, log_Py)

    save_predictions(batch, p_ls, p_lq, path=f"{out_dir}/predictions{sfx}.csv")

    gt = to_eval_gt(eval_gt)
    pred = to_eval_pred(batch, p_ls, p_lq, eval_gt)
    result = evaluate(gt, pred)
    save_eval(result, gt, dir_=out_dir, tag=args.tag)

    # 학습된 prior 자체의 점수 q_LS = sigmoid(z_LS)를 평가 행마다 남긴다.
    # 채점에서 '사전'은 보정 전 USGS pi가 아니라 이 q_LS다(지시서 §3: BCE 확률 = prior q_LS).
    with torch.no_grad():
        z_ls_all, z_lq_all = prior_z(pri, batch)
    idx = eval_gt.model_row_idx
    pd.DataFrame({
        "event": [INDEX_TO_EVENT[i] for i in eval_gt.event_idx.tolist()],
        "muni_code": list(eval_gt.municipality_code),
        "ls_true": eval_gt.gt_ls.tolist(),
        "ls_eval_mask": eval_gt.ls_eval_mask.tolist(),
        "lq_true": eval_gt.gt_lq.tolist(),
        "lq_eval_mask": eval_gt.lq_eval_mask.tolist(),
        "pi_ls_usgs": batch.pi_ls[idx].numpy(),
        "q_ls_prior": torch.sigmoid(z_ls_all[idx]).numpy(),
        "q_lq_prior": torch.sigmoid(z_lq_all[idx]).numpy(),
        "p_ls_post": p_ls[idx].numpy(),
        "p_lq_post": p_lq[idx].numpy(),
    }).to_csv(f"{out_dir}/eval_scores{sfx}.csv", index=False, encoding="utf-8-sig")

    # 회차별 기록용 요약(지시서 §4). 학습이 끝난 뒤의 값만 담는다.
    last = hist.iloc[-1]
    meta = {
        "argv": " ".join(sys.argv),
        "prior_family": args.prior_family,
        "prior_mode": args.prior_mode,
        "area_link": args.area_link if args.prior_family == "area" else "",
        "fix_b": bool(args.fix_b),
        "mtn_prior": bool(args.mtn_prior),
        "omega": args.ls_bce_weight,
        "test_event": args.test_event or "",
        "n_bce_rows": int(bce_idx.numel()),
        "n_params": sum(p.numel() for m in (reg, like, pri) for p in m.parameters()),
        "kappa": float(pri.kappa) if args.mtn_prior else "",
        "b_ls": float(pri.b_value if args.prior_family == "area" else pri.b_value[0]),
        "a_ls": "" if args.prior_family == "area" else float(pri.a_value[0]),
        "loss_base_final": float(last["loss_base"]),
        "bce_sum_final": float(last["bce_sum"]),
        "loss_total_final": float(last["loss_total"]),
    }
    with open(f"{out_dir}/run_meta{sfx}.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"저장: {out_dir}/run_meta{sfx}.json")

    print(
        f"MSE_LS {result.mse_ls:.4f} (n={result.n_ls}) / "
        f"MSE_LQ {result.mse_lq:.4f} (n={result.n_lq}) / 전체 {result.n}행"
    )
    print(
        f"AUC_LS {result.auc_ls:.4f} (prior {result.auc_prior_ls:.4f}) / "
        f"AUC_LQ {result.auc_lq:.4f} (prior {result.auc_prior_lq:.4f})"
    )
    print(
        f"이벤트내 가중평균 AUC_LS {result.auc_ls_wavg:.4f} "
        f"(prior {result.auc_prior_ls_wavg:.4f}) / "
        f"AUC_LQ {result.auc_lq_wavg:.4f} "
        f"(prior {result.auc_prior_lq_wavg:.4f})"
    )
    print()
    print("이벤트별:")
    print(result.per_event.round(4).to_string(index=False))
