#!/usr/bin/env bash
# 사후 탐색: 산지 항을 사전확률 식에서 빼고 BCE만 적용한다.
#
# 산지 항이 없으면 사전확률은 log(pi) + log k + b_LS 이고,
# BCE가 손댈 수 있는 것은 b_LS 하나뿐이다. b_LS는 모든 행에 같은 상수라
# 순위(AUC)를 못 바꾸고 확률 수준만 옮긴다.
#
# 그래도 값어치가 있다. b_LQ 건에서 확인했듯 수준이 맞으면 4상태 가중치가
# 제대로 잡혀 사후가 오를 수 있다(LQ 0.7812 -> 0.8158).
# 즉 BCE를 '순위 조정'이 아니라 '수준 보정'에 쓰는 실험이다.
#
# F0 : b_LS 학습, BCE 없음        (대조군 — BCE 효과만 분리)     1회
# F1 : b_LS 학습, BCE 적용                                      5회차
# F2 : b_LS + b_LQ 학습, BCE 적용                               5회차
# F3 : A 계열(a, b 학습), BCE 적용                              5회차
set -euo pipefail
PY="${PY:-python}"
OUT=results/bceonly
EVENTS=("2000 돗토리" "2004 니가타현주에쓰" "2016 구마모토" "2018 오사카" "2018 훗카이도")
COMMON="--prior-mode bounded --lam-gamma 10 --b-min -2 --b-max 2 --seed 0 --epochs 3000"
AREA="--prior-family area --area-link log --lam-gamma 10 --b-min -2 --b-max 4 --seed 0 --epochs 3000"

$PY train.py $AREA --out "$OUT/F0"

for e in "${EVENTS[@]}"; do
  $PY train.py $AREA               --ls-bce-weight 4.35 --test-event "$e" --out "$OUT/F1/$e"
  $PY train.py $AREA --free-b-lq   --ls-bce-weight 4.35 --test-event "$e" --out "$OUT/F2/$e"
  $PY train.py $COMMON             --ls-bce-weight 4.35 --test-event "$e" --out "$OUT/F3/$e"
done
echo "완료: $OUT"
