"""Streamlit 그림판 UI — 마우스로 숫자를 그리면 서버가 인식.

실행: streamlit run app.py  (서버가 먼저 떠 있어야 합니다)
"""

import httpx
import numpy as np
import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas

SERVER_BASE = "http://localhost:8000"  # 서버 포트를 바꿨다면 여기도 같이 변경

st.set_page_config(page_title="손글씨 숫자 인식", page_icon="✏️")
st.title("✏️ 손글씨 숫자 인식 그림판")
st.caption("검은 캔버스에 흰 글씨로 숫자(0~9) 하나를 크게 그리고 [인식하기]를 누르세요.")

canvas = st_canvas(
    stroke_width=18,
    stroke_color="#FFFFFF",      # 흰 글씨
    background_color="#000000",  # 검은 배경 — MNIST와 같은 형태
    width=280,
    height=280,
    drawing_mode="freedraw",
    key="canvas",
)

if st.button("인식하기", type="primary"):
    if canvas.image_data is None:
        st.warning("먼저 숫자를 그려주세요.")
        st.stop()

    # 캔버스 RGBA(280x280) → 흑백 28x28 로 축소 (MNIST 입력과 동일한 형태)
    img = Image.fromarray(canvas.image_data.astype("uint8")).convert("L").resize((28, 28))
    pixels = np.array(img, dtype=float)

    if pixels.max() == 0:
        st.warning("캔버스가 비어 있어요. 숫자를 그려주세요.")
        st.stop()

    try:
        r = httpx.post(f"{SERVER_BASE}/predict", json={"pixels": pixels.tolist()}, timeout=10.0)
    except httpx.ConnectError:
        st.error("서버에 연결할 수 없습니다. 터미널에서 uvicorn 이 떠 있는지 확인하세요.")
        st.stop()

    if r.status_code != 200:
        st.error(f"서버 오류 (status {r.status_code}): {r.json().get('detail', '')}")
        st.stop()

    result = r.json()

    # ---------------------------------------------------------------
    # TODO(심화): 최대 확률이 0.6 미만이면 "잘 모르겠어요 🤔" 를 표시해 보세요.
    # TODO(심화): 틀린 예측이 나온 그림을 파일로 저장해 두면
    #             "오답 수집 → 재학습" 이라는 MLOps 스토리가 됩니다.
    # ---------------------------------------------------------------
    st.metric("예측 결과", str(result["prediction"]))
    st.bar_chart({"확률": result["probs"]})
