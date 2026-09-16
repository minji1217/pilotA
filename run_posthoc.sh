#!/usr/bin/env bash
# 사후 탐색(C 계열). 지시서 §4의 조건표에 없는 실험이고 §5 판정 대상이 아니다.
#
# 동기: 지시서 §2-1 B가 b_LQ를 0으로 고정해 두었는데, log k_LQ의 평균이 6.7쯤이라
#       q_LQ가 통째로 밀려 올라간다(중앙값 0.9188). 실제 LQ 발생률은 229행 중 0.476이다.
#       b_LQ는 모든 행에 같은 상수라 순위(AUC)는 못 바꾸고 확률 수준만 움직이므로,
#       "순위는 그대로 두고 캘리브레이션만 고칠 수 있는가"를 확인한다.
#
#       단, 4상태 가중치가 달라지므로 사후확률과 LS 쪽에는 영향이 갈 수 있다. 그것도 함께 잰다.
#
# C0 = B0 + b_LQ 학습            (b_LS=0 고정, kappa 없음, omega=0)   1회
# C2 = B2 + b_LQ 학습            (b_LS·kappa 학습, omega=4.35)        5회
set -euo pipefail

PY="${PY:-python}"
OUT=results/posthoc
EVENTS=("2000 돗토리" "2004 니가타현주에쓰" "2016 구마모토" "2018 오사카" "2018 훗카이도")
AREA="--prior-family area --area-link log --lam-gamma 10 --b-min -2 --b-max 4 --seed 0 --epochs 3000"

$PY train.py $AREA --fix-b --free-b-lq --out "$OUT/C0"

for e in "${EVENTS[@]}"; do
  $PY train.py $AREA --mtn-prior --free-b-lq --ls-bce-weight 4.35 --test-event "$e" \
      --out "$OUT/C2/$e"
done

echo "완료: $OUT"
