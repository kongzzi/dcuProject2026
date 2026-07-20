"""FastAPI 백엔드 서버.

실행: uvicorn server:app --reload --port 8000
문서: http://localhost:8000/docs
"""

import asyncio
import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

# ---------------------------------------------------------------
# 설정 로드 (.env) — 키는 코드에 절대 직접 쓰지 않는다
# ---------------------------------------------------------------
load_dotenv()

BASE_URL   = os.getenv("MLAPI_BASE_URL")
API_KEY    = os.getenv("MLAPI_API_KEY")
MODEL_NAME = os.getenv("MLAPI_MODEL", "openai/gpt-5-mini")

if not API_KEY or API_KEY.startswith("여기에"):
    raise RuntimeError("MLAPI_API_KEY가 설정되어 있지 않습니다. .env 파일을 확인하세요.")

# 클라이언트는 모듈 레벨에서 한 번만 생성해 재사용
client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)

# ---------------------------------------------------------------
# TODO 1: 서비스 이름과 system 프롬프트를 내 주제로 바꾸세요.
#   - system 프롬프트에 역할·출력 형식·금지사항을 구체적으로 적을수록 좋습니다.
#   - 프롬프트를 고칠 때마다 예시 입력 3개로 전/후 출력을 비교해 기록하세요.
# ---------------------------------------------------------------
APP_TITLE = "요점정리 + 퀴즈 생성기"  # 예시입니다. 내 서비스 이름으로 교체

SYSTEM_PROMPT = """너는 대학생의 학습을 돕는 조교야.
사용자가 강의 노트를 주면 아래 형식으로 답해.

## 요점 정리
- 핵심 내용을 5개 이내의 불릿으로

## 확인 퀴즈
객관식 퀴즈 3문항 (각 4지선다, 정답은 맨 아래에 모아서)

노트에 없는 내용을 지어내지 마."""


class GenerateRequest(BaseModel):
    message: str = Field(..., min_length=1, description="사용자 입력 (예: 강의 노트 전문)")
    # ---------------------------------------------------------------
    # TODO 2: 내 주제에 필요한 입력 필드를 추가하세요. 예시:
    #   tone: Optional[str] = None            # 격식 변환기: 정중/간결/친근
    #   budget: Optional[int] = Field(None, ge=0)   # 플래너: 예산
    # 추가한 필드는 아래 messages를 만들 때 user 내용에 함께 넣으면 됩니다.
    # ---------------------------------------------------------------


app = FastAPI(title=APP_TITLE)


@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL_NAME}


@app.post("/generate/stream")
async def generate_stream(req: GenerateRequest):
    """핵심 기능: 입력을 받아 LLM 응답을 토큰 단위로 흘려보낸다.

    본문 마지막 줄은 항상 [DONE] / [EMPTY] / [ERROR] 중 하나 —
    받는 쪽은 이 한 줄로 종료 사유를 판단한다.
    """

    async def gen():
        produced = False
        try:
            stream = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": req.message},
                ],
                #temperature=0.7,
                stream=True,
                timeout=60,
            )
            async for chunk in stream:
                if not chunk.choices:          # usage만 담긴 빈 chunk 가드
                    continue
                piece = getattr(chunk.choices[0].delta, "content", None)
                if not piece:                  # None·빈 문자열 가드
                    continue
                produced = True
                yield piece
            yield "\n[DONE]" if produced else "\n[EMPTY]"
        except asyncio.CancelledError:
            # 클라이언트가 도중에 끊은 경우 — 로그만 남기고 반드시 raise
            print("[stream] cancelled by client")
            raise
        except Exception as e:
            # 원본 예외 메시지는 클라이언트에 노출하지 않는다
            print(f"[stream] error: {type(e).__name__}: {e}")
            yield "\n[ERROR] LLM 호출에 실패했습니다"
        finally:
            print("[stream] generator finished or cancelled")

    return StreamingResponse(gen(), media_type="text/plain")
