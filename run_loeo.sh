#!/usr/bin/env bash
# 후속실험 3 (LOEO) 전체 실행. 지시서 §4의 조건을 모두 돌린다.
#
# 필수 14회  : A0, A1, B0, B1 (각 1회) + A2, B2 (각 5회차)
# 선택 10회  : B2-w1, B2-w10 (각 5회차)
# 추가  6회  : B0-log, B2-log — 지시서 §2-1 B는 logit(pi)를 쓰는데
#              기존 면적 항 브랜치(followup3-area-avg-*)는 log(pi)를 썼다.
#              주 조건은 지시서대로 logit이고, log는 민감도로 따로 남긴다.
#
# 공통: 3000 epoch / Adam lr 0.02 / lam_gamma 10 / seed 0
set -euo pipefail

PY="${PY:-python}"
OUT=results/loeo

EVENTS=("2000 돗토리" "2004 니가타현주에쓰" "2016 구마모토" "2018 오사카" "2018 훗카이도")

COMMON="--prior-mode bounded --lam-gamma 10 --b-min -2 --b-max 2 --seed 0 --epochs 3000"          # A 계열
AREA="--prior-family area   --lam-gamma 10 --b-min -2 --b-max 4 --seed 0 --epochs 3000"           # B 계열
OMEGA=4.35

# ---- omega = 0 : 1회씩 ----
$PY train.py $COMMON                          --out "$OUT/A0"
$PY train.py $COMMON --mtn-prior              --out "$OUT/A1"
$PY train.py $AREA   --fix-b                  --out "$OUT/B0"
$PY train.py $AREA   --mtn-prior              --out "$OUT/B1"
$PY train.py $AREA   --fix-b --area-link log  --out "$OUT/B0-log"

# ---- omega > 0 : 지진 하나씩 가리기 5회차 ----
for e in "${EVENTS[@]}"; do
  $PY train.py $COMMON --mtn-prior --ls-bce-weight $OMEGA --test-event "$e" --out "$OUT/A2/$e"
  $PY train.py $AREA   --mtn-prior --ls-bce-weight $OMEGA --test-event "$e" --out "$OUT/B2/$e"
  $PY train.py $AREA   --mtn-prior --ls-bce-weight 1      --test-event "$e" --out "$OUT/B2-w1/$e"
  $PY train.py $AREA   --mtn-prior --ls-bce-weight 10     --test-event "$e" --out "$OUT/B2-w10/$e"
  $PY train.py $AREA   --mtn-prior --ls-bce-weight $OMEGA --test-event "$e" --area-link log \
                                                                            --out "$OUT/B2-log/$e"
done

echo "완료: $OUT"
