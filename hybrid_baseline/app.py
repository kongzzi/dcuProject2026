"""Streamlit UI — 일기를 쓰면 내 모델이 감정을 판정하고 LLM이 코멘트를 스트리밍.

실행: streamlit run app.py  (서버가 먼저 떠 있어야 합니다)
"""

import httpx
import streamlit as st

SERVER_BASE = "http://localhost:8000"

st.set_page_config(page_title="감정분석 일기장", page_icon="📔")
st.title("📔 감정분석 일기장")
st.caption("오늘 하루를 적으면, 내가 학습시킨 모델이 감정을 읽고 AI가 한마디를 건넵니다.")

message = st.text_area("오늘의 일기", height=200, placeholder="오늘은...")

if st.button("기록하기", type="primary"):
    if not message.strip():
        st.warning("내용을 입력해 주세요.")
        st.stop()

    badge = st.empty()  # 감정 판정 배지가 들어갈 자리 (스트리밍 시작 전에 채워짐)

    def stream_response():
        """첫 줄([SENTIMENT] ...)은 배지로 표시하고, 나머지만 본문으로 흘린다."""
        buffer = ""
        header_done = False
        try:
            with httpx.Client(timeout=60.0) as c:
                with c.stream("POST", f"{SERVER_BASE}/analyze/stream", json={"message": message}) as r:
                    if r.status_code != 200:
                        yield f"⚠️ 서버 오류 (status {r.status_code})"
                        return
                    for piece in r.iter_text():
                        if header_done:
                            yield piece
                            continue
                        buffer += piece
                        if "\n" not in buffer:
                            continue
                        header, rest = buffer.split("\n", 1)
                        header_done = True
                        # header 예: "[SENTIMENT] 부정 0.87"
                        parts = header.replace("[SENTIMENT]", "").split()
                        if len(parts) == 2:
                            label, conf = parts[0], float(parts[1])
                            if label == "부정":
                                badge.error(f"😞 오늘의 감정: 부정 (확신도 {conf:.0%})")
                            else:
                                badge.success(f"😊 오늘의 감정: 긍정 (확신도 {conf:.0%})")
                        if rest:
                            yield rest
        except httpx.TimeoutException:
            yield "\n⚠️ 응답 시간이 초과되었습니다. 다시 시도해 주세요."
        except httpx.ConnectError:
            yield "\n⚠️ 서버에 연결할 수 없습니다. uvicorn 이 떠 있는지 확인하세요."

    st.write_stream(stream_response)

    # ---------------------------------------------------------------
    # TODO 3 (심화):
    #  - 종료 마커([DONE]/[EMPTY]/[ERROR])를 본문에서 숨기고 st.success/st.error 로 표시
    #  - st.session_state 에 일기·판정 기록을 쌓아 "이번 주 감정 그래프" 그리기
    # ---------------------------------------------------------------
