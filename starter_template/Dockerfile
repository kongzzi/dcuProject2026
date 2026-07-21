FROM python:3.11-slim

WORKDIR /app

# 의존성 먼저 설치 (캐시 활용 → 빌드가 빨라짐)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 나머지 소스 복사
COPY . .

# 실행 스크립트에 권한 부여
RUN chmod +x start.sh

# HF Spaces 기본 포트(7860). Render는 자동으로 $PORT를 넣어줌
EXPOSE 7860

CMD ["./start.sh"]