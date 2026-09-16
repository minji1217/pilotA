#!/usr/bin/env bash
# log k 중심화 비교. 사후 탐색이며 §5 판정 대상이 아니다.
#
# 규칙: b를 '학습하는' 채널에서만 log k의 학습 418행 평균을 뺀다.
#       b를 고정한 채널(B0의 LS·LQ, C0의 LS)에서는 빼지 않는다.
#       빼면 z = log(p_bar * k) = log lambda 라는 유도식이 깨지기 때문이다.
#
# 공정한 비교를 위해 양쪽 모두 b 상자를 [-12, 20]으로 넉넉히 연다.
# 기존 상자 [-2, 4]는 실제로 걸리고 있었다(B1의 b_LS가 하한 -2에 붙었다).
# 상자가 안 걸리면 두 계열의 최적해는 같아야 하고, 차이는 최적화 안정성에서만 나와야 한다.
#
#   Bc / Cc : 센터링 함        Bu / Cu : 센터링 안 함 (같은 상자)
set -euo pipefail

PY="${PY:-python}"
OUT=results/centering
EVENTS=("2000 돗토리" "2004 니가타현주에쓰" "2016 구마모토" "2018 오사카" "2018 훗카이도")
BOX="--b-min -12 --b-max 20 --b-lq-min -12 --b-lq-max 20"
BASE="--prior-family area --area-link log --lam-gamma 10 --seed 0 --epochs 3000 $BOX"

for mode in c u; do
  [ "$mode" = c ] && CEN="--center-logk" || CEN=""
  $PY train.py $BASE $CEN --mtn-prior                 --out "$OUT/B1$mode"
  $PY train.py $BASE $CEN --fix-b --free-b-lq         --out "$OUT/C0$mode"
  for e in "${EVENTS[@]}"; do
    $PY train.py $BASE $CEN --mtn-prior --ls-bce-weight 4.35 --test-event "$e" \
        --out "$OUT/B2$mode/$e"
    $PY train.py $BASE $CEN --mtn-prior --free-b-lq --ls-bce-weight 4.35 --test-event "$e" \
        --out "$OUT/C2$mode/$e"
  done
done
echo "완료: $OUT"
