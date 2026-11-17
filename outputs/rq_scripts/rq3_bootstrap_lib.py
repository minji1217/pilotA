"""rq3_bootstrap.py의 재표집 함수 복사본 (rq3_bootstrap.py는 import하면 바로 실행되므로)."""
import dataclasses

import numpy as np
import torch


def take_rows(batch, idx):
    """idx(행 번호, 중복 허용) 순서대로 행을 모은 batch. 모든 필드가 행 단위임을 확인한다."""
    n = batch.batch_size
    changes = {}
    for f in dataclasses.fields(batch):
        v = getattr(batch, f.name)
        if isinstance(v, torch.Tensor):
            assert v.shape[0] == n, f.name
            changes[f.name] = v[torch.as_tensor(idx)]
        elif isinstance(v, tuple):
            assert len(v) == n, f.name
            changes[f.name] = tuple(v[i] for i in idx)
    return dataclasses.replace(batch, **changes)


def stratified_idx(batch, b):
    rng = np.random.default_rng(b)
    ev = batch.event_idx.numpy()
    parts = [rng.choice(np.flatnonzero(ev == e), size=int((ev == e).sum()), replace=True) for e in np.unique(ev)]
    return np.sort(np.concatenate(parts))


