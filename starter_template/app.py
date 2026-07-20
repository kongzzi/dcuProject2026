"""Streamlit UI.

실행: streamlit run app.py  (서버가 먼저 떠 있어야 합니다)
"""

import httpx
import streamlit as st

SERVER_BASE = "http://localhost:8000"   # 서버 포트를 바꿨다면 여기도 같이 변경

# ---------------------------------------------------------------
# TODO 3: 화면 제목과 입력 위젯을 내 주제에 맞게 바꾸세요. 예시:
#   - 격식 변환기: st.selectbox("톤", ["정중", "간결", "친근"])
#   - 플래너:     st.number_input("예산(원)", ...), st.slider("시간", ...)
#   - 냉장고 요리사: st.multiselect("재료", [...]) 또는 st.text_input
# 위젯 값이 늘어나면 아래 payload에도 같은 이름으로 넣으면 됩니다
# (server.py의 TODO 2에서 추가한 필드와 이름을 맞추세요).
# ---------------------------------------------------------------
st.set_page_config(page_title="요점정리 + 퀴즈 생성기", page_icon="📚")
st.title("📚 요점정리 + 퀴즈 생성기")
st.caption("강의 노트를 붙여넣으면 요약과 확인 퀴즈를 만들어 줍니다.")

message = st.text_area("강의 노트", height=240, placeholder="여기에 노트 내용을 붙여넣으세요...")

if st.button("생성하기", type="primary"):
    if not message.strip():
        st.warning("내용을 입력해 주세요.")
        st.stop()

    payload = {"message": message}

    def stream_response():
        """서버의 스트리밍 응답을 도착하는 대로 흘려보낸다."""
        try:
            with httpx.Client(timeout=60.0) as c:
                with c.stream("POST", f"{SERVER_BASE}/generate/stream", json=payload) as r:
                    if r.status_code != 200:
                        yield f"⚠️ 서버 오류 (status {r.status_code})"
                        return
                    for piece in r.iter_text():
                        # -----------------------------------------------
                        # TODO 4 (심화): 종료 마커([DONE]/[EMPTY]/[ERROR])를
                        # 화면에 그대로 보여주는 대신, 감지해서 숨기고
                        # st.success / st.error 로 바꿔 표시해 보세요.
                        # -----------------------------------------------
                        yield piece
        except httpx.TimeoutException:
            yield "\n⚠️ 응답 시간이 초과되었습니다. 다시 시도해 주세요."
        except httpx.ConnectError:
            yield "\n⚠️ 서버에 연결할 수 없습니다. 터미널 1에서 서버가 떠 있는지 확인하세요."

    st.write_stream(stream_response)
