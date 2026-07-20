"""감성분류 모델 정의 — 노트북(학습)과 server.py(서빙)가 같이 import 합니다."""

import torch.nn as nn

# NSMC 라벨: 0 = 부정, 1 = 긍정
LABELS = ["부정", "긍정"]


class SentimentMLP(nn.Module):
    """TF-IDF 벡터(input_dim) → 긍정/부정 2 클래스. CPU에서 수 분 내 학습."""

    def __init__(self, input_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128), nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 2),
        )

    def forward(self, x):
        return self.net(x)
