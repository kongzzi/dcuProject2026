#!/usr/bin/env bash
# 1) 백엔드 FastAPI — 컨테이너 내부 8000 포트 (외부 노출 안 함)
uvicorn server:app --host 127.0.0.1 --port 8000 &

# 2) 화면 Streamlit — 플랫폼이 주는 포트로 노출
#    Render는 $PORT를 줌 / 없으면 7860 (HF Spaces 기본)
streamlit run app.py \
  --server.port "${PORT:-7860}" \
  --server.address 0.0.0.0