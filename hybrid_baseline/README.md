# 감정분석 일기장 — 하이브리드 베이스라인 (초급 ★★★ 도전형)

**내가 학습한 모델이 분류하고, LLM이 생성한다** — 실무에서 자주 쓰는 역할 분담 구조입니다.

```
[Streamlit UI (app.py)]
        │  일기 텍스트
        ▼
[FastAPI 서버 (server.py)]
        │ ① 내 모델(sentiment.pt)이 긍정/부정 판정   ← train_sentiment.ipynb 에서 학습
        │ ② 판정에 맞는 system 프롬프트로 LLM 호출
        ▼
[MLAPI LLM] ── 위로/축하 코멘트를 토큰 단위 스트리밍
```

응답 본문 규칙: **1번째 줄 `[SENTIMENT] 라벨 확신도`** → LLM 코멘트 스트리밍 → **마지막 줄 `[DONE]`/`[EMPTY]`/`[ERROR]`**.
UI는 첫 줄을 배지로, 마지막 줄을 종료 신호로 해석합니다.

## 1. 설치·설정

```bash
pip install -r requirements.txt
cp .env.example .env    # 열어서 MLAPI_API_KEY 입력
```

## 2. 진행 순서

```bash
# 1) 노트북 실행 → 분류 모델 학습 → sentiment.pt + vectorizer.pkl 저장
jupyter notebook train_sentiment.ipynb

# 2) 터미널 1 — 서버 (두 파일과 .env 키가 있어야 뜹니다)
uvicorn server:app --reload --port 8000

# 3) 터미널 2 — UI
streamlit run app.py
```

일기를 쓰고 [기록하기] → 감정 배지가 뜨고 AI 코멘트가 흐르면 성공.

## 3. 파일 구성

| 파일 | 역할 |
|---|---|
| `train_sentiment.ipynb` | NSMC로 감성분류 학습 → 평가 → 저장. TODO·실험 기록 표 포함 |
| `model.py` | `SentimentMLP` 정의 + 라벨 (노트북·서버 공유) |
| `server.py` | 모델+벡터라이저 로드, `/classify`(분류만), `/analyze/stream`(전체 파이프라인) |
| `app.py` | 일기 입력 → 감정 배지 + LLM 코멘트 스트리밍 표시 |

## 4. 과제 흐름 (5일 기준 — ★★★ 규칙)

| 일차 | 목표 | 완성 기준 |
|---|---|---|
| 1 | 환경 설치, 노트북 완주(baseline 정확도 기록) | `sentiment.pt`/`vectorizer.pkl` 생성 |
| 2 | 분류 정확도 개선 실험 + LLM 프롬프트 다듬기 (병렬 가능) | 정확도 80%+ / 프롬프트 전후 비교 기록 |
| 3 | 서버·UI 연결 — 파이프라인 관통 | 일기 → 배지 + 코멘트가 화면에 표시 |
| 4 | 심화 TODO + 오류 처리 점검. **통합이 안 됐으면 ★★로 축소 결정** | E2E 데모 성공 |
| 5 | PPT(아키텍처 그림 + 실험 표) + 리허설 + 시연 영상 | 30초 데모 성공 + 역할 분담 설명 |

2인 팀이면: 한 명은 노트북(모델·실험), 한 명은 서버·UI(프롬프트·오류 처리)로 나누고 3일차에 합치세요.

## 5. 심화 TODO (코드 안 주석에도 있음)

- **내 모델 vs LLM 대결** (`server.py` TODO 2): 같은 문장을 둘 다에게 분류시켜 정확도·속도 비교 → "LLM이 정확하지만 내 모델이 1000배 빠르고 무료"는 그 자체로 좋은 발표 결론
- 주간 감정 그래프 (`app.py` TODO 3): 기록을 쌓아 시각화
- 틀린 판정 문장 수집 → 유형 분석 → 재학습 스토리 (미니 MLOps)

## 6. 자주 막히는 곳

- 서버가 안 뜸 → ① `sentiment.pt`/`vectorizer.pkl` 있는지 (노트북 먼저) ② `.env` 키 확인
- 판정이 이상함 → NSMC는 영화리뷰 데이터라 일기 문체에선 정확도가 떨어질 수 있음. **이 한계를 발표에서 언급하면 오히려 플러스** (도메인 차이, 개선안 제시)
- 모델 구조(`model.py`)를 바꿨다면: 노트북 재학습·재저장 → 서버 재시작 순서 준수
