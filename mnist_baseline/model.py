"""모델 정의 — 노트북(학습)과 server.py(서빙)가 같이 import 합니다.

모델 구조를 바꾸면 반드시 노트북에서 다시 학습·저장한 뒤 서버를 재시작하세요.
"""

import torch.nn as nn

# MNIST 정규화 상수 — 학습과 서빙에서 반드시 동일하게 사용
MNIST_MEAN = 0.1307
MNIST_STD = 0.3081


class SmallCNN(nn.Module):
    """28x28 흑백 이미지 → 0~9 (10 클래스). CPU에서도 1 epoch 2~3분."""

    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2),   # 28 → 14
            nn.Conv2d(16, 32, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2),  # 14 → 7
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(32 * 7 * 7, 128), nn.ReLU(),
            # TODO(심화): 여기에 nn.Dropout(0.3) 을 넣고 정확도 변화를 기록해 보세요
            nn.Linear(128, 10),
        )

    def forward(self, x):
        return self.classifier(self.features(x))
