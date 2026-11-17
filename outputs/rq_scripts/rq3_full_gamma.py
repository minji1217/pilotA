"""RQ3 확인: 9개 지진 전체로 학습한 AdminDER 최종 설정의 γ를 지금 코드로 다시 내서 10월 파일(03b nolabels)과 비교.
설정은 rq4nl full과 같음(λ_γ = λ_κ = 10, 3000 에폭, 산사태 라벨 학습, 액상화 라벨 미사용, LQ b-only).
출력: outputs/rq3/gamma_full9.csv
"""
import sys
from pathlib import Path

REPO = r"C:\Users\PC\Desktop\pilotA"
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd

from train import GT_PATH, STATS_PATH, USGS_PATH, train
from loader import attach_ls_labels, load_eval_ground_truth, load_pilot_a_batch
from schema import CHANNELS

batch = load_pilot_a_batch(STATS_PATH, USGS_PATH)
batch = attach_ls_labels(GT_PATH, batch, load_eval_ground_truth(GT_PATH, batch))
reg, like, pri, hist = train(
    batch=batch, seed=0, epochs=3000, lr=0.02, lam_gamma=10.0,
    area_mode="fixed-cov-mtn", lam_kappa=10.0, mtn_standardize="train",
    reg_mtn=False, lq_mtn=False, lq_b_only=True, use_labels=True, lq_labels=False,
)
KOR = ["사망", "중상", "경상", "전파", "반파", "일부파손"]
new = pd.DataFrame({"channel": CHANNELS, "label": KOR, "gamma_ls": reg.gamma_ls.detach().numpy(),
                    "gamma_lq": reg.gamma_lq.detach().numpy()})
old = pd.read_csv(Path(REPO) / "outputs/언니전달_액상화J_설정/03b_전체판(분리없음)_파라미터_nolabels.csv")
for g, col in (("gamma_LS", "gamma_ls"), ("gamma_LQ", "gamma_lq")):
    o = old[old.group == g].set_index("label").value
    new[col + "_oct"] = new.label.map(o)
    print(g, "max |차이|", float((new[col] - new[col + "_oct"]).abs().max()))
out = Path(REPO) / "outputs" / "rq3"
out.mkdir(parents=True, exist_ok=True)
new.to_csv(out / "gamma_full9.csv", index=False, encoding="utf-8-sig")
print(new.to_string())
