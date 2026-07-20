"""하이브리드 서버: 내 모델이 감성 분류 → LLM이 코멘트 생성(스트리밍).

실행: uvicorn server:app --reload --port 8000
문서: http://localhost:8000/docs

응답 본문 구조 (/analyze/stream):
  1번째 줄  : [SENTIMENT] <라벨> <확신도>     ← 내 모델의 판정
  2번째 줄~ : LLM이 생성하는 코멘트 (토큰 단위 스트리밍)
  마지막 줄 : [DONE] / [ERROR] ...
"""

import asyncio
import os

import joblib
import torch
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from model import LABELS, SentimentMLP

# ---------------------------------------------------------------
# 1) 내 모델 로드 (노트북에서 저장한 두 파일)
# ---------------------------------------------------------------
for path in ("sentiment.pt", "vectorizer.pkl"):
    if not os.path.exists(path):
        raise RuntimeError(f"{path} 가 없습니다. 먼저 train_sentiment.ipynb 를 실행하세요.")

ckpt = torch.load("sentiment.pt", map_location="cpu")
clf_model = SentimentMLP(input_dim=ckpt["input_dim"])
clf_model.load_state_dict(ckpt["state_dict"])
clf_model.eval()
vectorizer = joblib.load("vectorizer.pkl")

# ---------------------------------------------------------------
# 2) LLM 클라이언트 (.env에서 키 로드 — 코드에 직접 쓰지 않는다)
# ---------------------------------------------------------------
load_dotenv()

BASE_URL   = os.getenv("MLAPI_BASE_URL", "https://mlapi.run/40cc17ae-a89b-4f12-a7d6-13293180fc87/v1")
API_KEY    = os.getenv("MLAPI_API_KEY")
MODEL_NAME = os.getenv("MLAPI_MODEL", "openai/gpt-4o-mini")

if not API_KEY or API_KEY.startswith("여기에"):
    raise RuntimeError("MLAPI_API_KEY가 설정되어 있지 않습니다. .env 파일을 확인하세요.")

llm = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)

# ---------------------------------------------------------------
# TODO 1: 라벨별 system 프롬프트를 내 서비스 컨셉에 맞게 다듬으세요.
# ---------------------------------------------------------------
SYSTEM_PROMPTS = {
    "부정": "너는 다정한 친구야. 사용자의 힘든 하루 이야기를 읽고 3~4문장으로 공감하고 위로해줘. 설교하지 마.",
    "긍정": "너는 다정한 친구야. 사용자의 기쁜 하루 이야기를 읽고 3~4문장으로 함께 기뻐하고 축하해줘.",
}

app = FastAPI(title="감정분석 일기장 (하이브리드)")


class AnalyzeRequest(BaseModel):
    message: str = Field(..., min_length=1, description="오늘의 일기 또는 리뷰")


def classify(text: str) -> tuple[str, float]:
    """내 모델로 긍정/부정 판정. (라벨, 확신도) 반환."""
    x = torch.tensor(vectorizer.transform([text]).toarray().astype("float32"))
    with torch.no_grad():
        probs = torch.softmax(clf_model(x), dim=1)[0]
    return LABELS[int(probs.argmax())], float(probs.max())


@app.get("/health")
async def health():
    return {"status": "ok", "classifier": "sentiment.pt", "llm": MODEL_NAME}


@app.post("/classify")
async def classify_only(req: AnalyzeRequest):
    """분류만 (LLM 없이) — 테스트·비교 실험용."""
    label, confidence = classify(req.message)
    return {"label": label, "confidence": round(confidence, 4)}


@app.post("/analyze/stream")
async def analyze_stream(req: AnalyzeRequest):
    """전체 파이프라인: 분류 → 판정 결과 한 줄 → LLM 코멘트 스트리밍."""

    async def gen():
        produced = False
        try:
            # ── 1단계: 내 모델이 분류 ─────────────────────────
            label, confidence = classify(req.message)
            yield f"[SENTIMENT] {label} {confidence:.2f}\n"

            # ── 2단계: 판정 결과에 맞는 LLM 코멘트 생성 ──────
            stream = await llm.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPTS[label]},
                    {"role": "user", "content": req.message},
                ],
                temperature=0.7,
                stream=True,
                timeout=60,
            )
            async for chunk in stream:
                if not chunk.choices:
                    continue
                piece = getattr(chunk.choices[0].delta, "content", None)
                if not piece:
                    continue
                produced = True
                yield piece
            yield "\n[DONE]" if produced else "\n[EMPTY]"
        except asyncio.CancelledError:
            print("[analyze] cancelled by client")
            raise
        except Exception as e:
            print(f"[analyze] error: {type(e).__name__}: {e}")
            yield "\n[ERROR] 처리에 실패했습니다"
        finally:
            print("[analyze] generator finished or cancelled")

    return StreamingResponse(gen(), media_type="text/plain")


# ---------------------------------------------------------------
# TODO 2 (심화): "내 모델 vs LLM 대결" 엔드포인트 만들기
#   POST /compare : 같은 문장을 (1) 내 모델과 (2) LLM("긍정/부정 한 단어로만
#   답해" 프롬프트)에 각각 분류시키고, 판정·소요시간을 JSON으로 반환.
#   → 발표에서 "LLM이 더 정확하지만 내 모델이 훨씬 빠르고 무료" 비교 가능
# ---------------------------------------------------------------
