"""
Pilot A - reporting.py

교수님 공유용 산출물 두 가지를 만든다.

1) dump_params()       -> outputs/params.csv
   학습된 41개 파라미터 + 기준 이벤트 1개(고정 0)를 저장한다.

   컬럼:
     module      reg / lik / pri
     group       설계식에 등장하는 이름 (alpha_c, alpha_e, beta_c, ...)
     param       코드상의 nn.Parameter 이름
     idx         채널 파라미터는 채널번호 0~5,
                 alpha_e는 EVENTS 번호 0~7, a/b는 0=LS 1=LQ.
                 ※ alpha_event_free는 코드상 길이가 7이지만 여기서는
                   벡터 위치가 아니라 이벤트 번호를 적는다.
                   기준 이벤트가 빠져 번호가 건너뛸 수 있다.
     label       사람이 읽는 이름
     transform   none / softplus / fixed(reference)
     raw_value   옵티마이저가 실제로 들고 있는 값 (변환 전)
     value       설계식에 등장하는 실제 값 (변환 후)

   transform=none이면 raw_value와 value가 같다.
   transform=fixed(reference)인 한 행만 학습 대상이 아니며, 나머지 41행이 학습 파라미터다.

2) save_loss_history() -> outputs/loss_history.csv, outputs/loss_curve.png
   에폭별 loss를 전부 저장하고 선형/로그 두 패널로 그린다.

모델 계산에는 관여하지 않는다. 학습이 끝난 뒤에만 호출한다.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")          # 창을 띄우지 않고 파일로만 저장한다
import matplotlib.pyplot as plt
import pandas as pd
import torch.nn.functional as F

from schema import (
    CHANNELS,
    DAMAGE_COLUMN_MAP,
    INDEX_TO_EVENT,
    NUM_EVENTS,
)

# 채널 라벨은 schema의 순서를 그대로 따른다.
# 여기서 리스트를 직접 적으면 schema가 바뀔 때 라벨만 조용히 어긋난다.
CHANNEL_LABELS = [DAMAGE_COLUMN_MAP[c] for c in CHANNELS]
CHANNEL_IDX = list(range(len(CHANNEL_LABELS)))

EXPECTED_NUM_PARAMS = 41

# 설계식에 나오는 순서대로 정렬하기 위한 기준
GROUP_ORDER = ["alpha_c", "alpha_e", "beta_c", "gamma_LS", "gamma_LQ", "phi_c", "a", "b"]


def dump_params(reg, like, pri, path="outputs/params.csv"):
    """학습된 파라미터를 CSV로 저장한다."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    ref = reg.reference_event_idx
    # alpha_event_free는 기준 이벤트를 제외한 7개다.
    # idx에는 벡터 위치가 아니라 EVENTS 번호를 적어야 기준 행과 같은 자로 읽힌다.
    event_free_idx = [i for i in range(NUM_EVENTS) if i != ref]
    event_free_labels = [INDEX_TO_EVENT[i] for i in event_free_idx]

    spec = [
        ("reg", "alpha_channel",           "alpha_c",  CHANNEL_IDX,    CHANNEL_LABELS,     "none"),
        ("reg", "alpha_event_free",        "alpha_e",  event_free_idx, event_free_labels,  "none"),
        ("reg", "beta_pgv",                "beta_c",   CHANNEL_IDX,    CHANNEL_LABELS,     "none"),
        ("reg", "_gamma_ls_unconstrained", "gamma_LS", CHANNEL_IDX,    CHANNEL_LABELS,     "softplus"),
        ("reg", "_gamma_lq_unconstrained", "gamma_LQ", CHANNEL_IDX,    CHANNEL_LABELS,     "softplus"),
        ("lik", "_phi_unconstrained",      "phi_c",    CHANNEL_IDX,    CHANNEL_LABELS,     "softplus"),
        ("pri", "a",                       "a",        [0, 1],         ["LS", "LQ"],       "none"),
        ("pri", "b",                       "b",        [0, 1],         ["LS", "LQ"],       "none"),
    ]
    mods = {"reg": reg, "lik": like, "pri": pri}
    named = {k: dict(m.named_parameters()) for k, m in mods.items()}

    rows, total = [], 0
    for mod_key, pname, group, idxs, labels, transform in spec:
        if pname not in named[mod_key]:
            raise KeyError(
                f"{mod_key}에 '{pname}' 파라미터가 없습니다. "
                f"실제 이름: {sorted(named[mod_key])}"
            )

        raw = named[mod_key][pname].detach()
        val = F.softplus(raw) if transform == "softplus" else raw

        raw_np, val_np = raw.cpu().numpy(), val.cpu().numpy()
        if not (raw_np.size == len(labels) == len(idxs)):
            raise ValueError(
                f"{pname}: 값 {raw_np.size}개 / 라벨 {len(labels)}개 / "
                f"idx {len(idxs)}개가 서로 다릅니다."
            )
        total += raw_np.size

        for i, lab, r, v in zip(idxs, labels, raw_np, val_np):
            rows.append({
                "module": mod_key, "group": group, "param": pname,
                "idx": int(i), "label": lab, "transform": transform,
                "raw_value": float(r), "value": float(v),
            })

    # 기준 이벤트는 학습 파라미터가 아니라 식별을 위해 0으로 고정한 값이다.
    # alpha_e 그룹 안에 같은 idx 체계로 넣어야 8개 이벤트가 한자리에서 읽힌다.
    rows.append({
        "module": "reg", "group": "alpha_e", "param": "alpha_event_free",
        "idx": ref, "label": INDEX_TO_EVENT[ref], "transform": "fixed(reference)",
        "raw_value": 0.0, "value": 0.0,
    })

    if total != EXPECTED_NUM_PARAMS:
        raise ValueError(
            f"학습 파라미터 수가 {EXPECTED_NUM_PARAMS}이 아닙니다: {total}"
        )

    df = pd.DataFrame(rows)
    df = df.sort_values(
        ["group", "idx"],
        key=lambda s: s.map({g: i for i, g in enumerate(GROUP_ORDER)})
        if s.name == "group" else s,
    ).reset_index(drop=True)

    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"저장: {path}  (학습 {total}개 + 기준이벤트 1개 = {len(df)}행)")
    return df


def save_loss_history(hist_df, dir_="outputs"):
    """에폭별 loss를 CSV와 PNG로 저장한다.

    hist_df 컬럼: epoch, nll_total, nll_per_row
    """
    Path(dir_).mkdir(parents=True, exist_ok=True)

    csv_path = f"{dir_}/loss_history.csv"
    png_path = f"{dir_}/loss_curve.png"
    hist_df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    fig, ax = plt.subplots(1, 2, figsize=(11, 4))

    ax[0].plot(hist_df["epoch"], hist_df["nll_total"])
    ax[0].set_xlabel("epoch")
    ax[0].set_ylabel("NLL (total)")
    ax[0].set_title("Training loss")
    ax[0].grid(alpha=0.3)

    # 초반 급락 때문에 선형 축에서는 후반이 바닥에 붙어 수렴 여부가 안 보인다.
    ax[1].plot(hist_df["epoch"], hist_df["nll_total"])
    ax[1].set_yscale("log")
    ax[1].set_xlabel("epoch")
    ax[1].set_ylabel("NLL (log scale)")
    ax[1].set_title("Training loss (log scale)")
    ax[1].grid(alpha=0.3, which="both")

    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)

    first, last = hist_df["nll_total"].iloc[0], hist_df["nll_total"].iloc[-1]
    print(f"저장: {csv_path}, {png_path}")
    print(f"  loss {first:,.1f} -> {last:,.1f}  ({len(hist_df)} epochs)")
    return hist_df
