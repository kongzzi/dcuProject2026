"""FastAPI 서빙 서버 — 노트북에서 학습·저장한 model.pt 를 로드해 /predict 제공.

실행: uvicorn server:app --reload --port 8000
문서: http://localhost:8000/docs
"""

import os

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from model import MNIST_MEAN, MNIST_STD, SmallCNN

MODEL_PATH = "model.pt"

if not os.path.exists(MODEL_PATH):
    raise RuntimeError(
        "model.pt 가 없습니다. 먼저 train_mnist.ipynb 를 실행해 모델을 학습·저장하세요."
    )

# 모델은 서버 시작 시 한 번만 로드해 재사용 (LLM client 패턴과 동일)
model = SmallCNN()
model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
model.eval()

app = FastAPI(title="손글씨 숫자 인식 API")


class PredictRequest(BaseModel):
    pixels: list[list[float]] = Field(
        ..., description="28x28 흑백 픽셀 값 (0~255, 검은 배경에 흰 글씨)"
    )


class PredictResponse(BaseModel):
    prediction: int
    probs: list[float]


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_PATH}


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    # 입력 형태 검증 — 잘못된 요청은 LLM(모델)까지 가기 전에 400으로 차단
    if len(req.pixels) != 28 or any(len(row) != 28 for row in req.pixels):
        raise HTTPException(status_code=400, detail="pixels 는 28x28 배열이어야 합니다")

    # 학습 때와 동일한 전처리: 0~1 스케일 → 정규화
    x = torch.tensor(req.pixels, dtype=torch.float32) / 255.0
    x = (x - MNIST_MEAN) / MNIST_STD
    x = x.unsqueeze(0).unsqueeze(0)  # (1, 1, 28, 28)

    with torch.no_grad():
        probs = torch.softmax(model(x), dim=1)[0]

    return PredictResponse(
        prediction=int(probs.argmax()),
        probs=[round(float(p), 4) for p in probs],
    )
