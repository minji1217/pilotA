#!/usr/bin/env bash
# 사후 탐색: BCE 대상을 LS 라벨 5개 지진(음성이 있는 지진)으로 제한한다.
#
# 지시서 §2-4는 음성 0인 4개 지진(2007·2008·2021·2024, 42행)을 매 회차 BCE에 포함하라고
# 했는데, 전부 양성이라 판별 정보가 없고 'q를 올려라'는 수준 압력만 준다.
# 면적 항 사전은 q가 이미 0.94~0.99로 포화라 그 압력이 κ를 엉뚱한 방향으로 밀 수 있다.
#
# E2  : omega = 4.35 그대로 (B2와 직접 비교 — 행 제한 효과만 분리)
# E2r : omega = 418 ÷ 실제 BCE 행수로 재보정 (54~76행이면 5.5~7.7)
set -euo pipefail
PY="${PY:-python}"
OUT=results/bce5
EVENTS=("2000 돗토리" "2004 니가타현주에쓰" "2016 구마모토" "2018 오사카" "2018 훗카이도")
COMMON="--prior-mode bounded --lam-gamma 10 --b-min -2 --b-max 2 --seed 0 --epochs 3000"
AREA="--prior-family area --area-link log --lam-gamma 10 --b-min -2 --b-max 4 --seed 0 --epochs 3000"

for e in "${EVENTS[@]}"; do
  $PY train.py $COMMON --mtn-prior --bce-require-negatives --ls-bce-weight 4.35 --test-event "$e" --out "$OUT/A2e/$e"
  $PY train.py $AREA   --mtn-prior --bce-require-negatives --ls-bce-weight 4.35 --test-event "$e" --out "$OUT/B2e/$e"
  $PY train.py $COMMON --mtn-prior --bce-require-negatives --ls-bce-weight -1   --test-event "$e" --out "$OUT/A2er/$e"
  $PY train.py $AREA   --mtn-prior --bce-require-negatives --ls-bce-weight -1   --test-event "$e" --out "$OUT/B2er/$e"
done
echo "완료: $OUT"
