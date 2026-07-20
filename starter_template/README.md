# 프로젝트 스타터 템플릿 (초급 ★ LLM 프롬프트형)

수업에서 배운 **FastAPI + MLAPI(LLM) + 스트리밍 + Streamlit** 구조가 이미 동작하는 상태로 들어 있습니다.
여러분이 할 일은 `TODO` 주석이 붙은 곳을 자기 주제에 맞게 바꾸는 것입니다.

```
[Streamlit UI (app.py)] → [FastAPI 서버 (server.py)] → [MLAPI LLM]
```

## 1. 처음 한 번만 하는 설정

```bash
# 1) 패키지 설치
pip install -r requirements.txt

# 2) .env 만들기 (.env.example 복사 후 API 키 입력)
cp .env.example .env
```

`.env` 파일을 열어 `MLAPI_API_KEY`에 발급받은 키를 넣으세요.
`.env`는 절대 깃에 올리지 않습니다 (.gitignore에 이미 등록됨).

## 2. 실행 (터미널 2개)

```bash
# 터미널 1 — 백엔드 서버
uvicorn server:app --reload --port 8000

# 터미널 2 — 화면(UI)
streamlit run app.py
```

- 서버 확인: http://localhost:8000/docs 에서 POST /generate/stream 테스트
- UI 확인: 브라우저에 뜬 Streamlit 화면에서 입력 → 생성 버튼 → 글자가 흐르면 성공

## 3. 내 주제로 바꾸기 (TODO 순서대로)

| TODO | 파일 | 할 일 |
|---|---|---|
| TODO 1 | server.py | 서비스 이름과 **system 프롬프트**를 내 주제로 교체 |
| TODO 2 | server.py | 입력 필드 추가 (예: 톤 선택, 예산, 재료 목록 …) |
| TODO 3 | app.py | 화면 제목·입력 위젯을 내 주제에 맞게 교체 |
| TODO 4 | app.py | (심화) 종료 마커([DONE] 등)를 화면에서 숨기기 |

**프롬프트를 고칠 때마다 예시 입력 3개로 출력을 비교하고, 전/후를 기록해 두세요.**
그 기록이 발표 자료의 "실험 결과"가 됩니다.

## 4. 종료 마커 규칙 (서버가 본문 마지막 줄에 붙여줌)

| 마커 | 의미 |
|---|---|
| `[DONE]` | 정상 종료 |
| `[EMPTY]` | 호출은 성공했지만 생성된 내용이 없음 |
| `[ERROR] ...` | LLM 호출 실패 (키·모델명·네트워크 확인) |

스트리밍은 응답이 시작되면 status가 이미 200이므로, **성공/실패는 본문 마지막 줄로 판단**합니다.

## 5. 막혔을 때

- 서버가 안 뜸 → `.env`에 키가 있는지 확인 (시작 시 에러 메시지를 읽어보세요)
- 401 → API 키가 잘못됨 / 400 → 모델명 오타 / 응답 없음 → 터미널 1의 로그 확인
- 포트 충돌 → `--port 8001`로 바꾸고 app.py의 `SERVER_BASE`도 같이 변경
