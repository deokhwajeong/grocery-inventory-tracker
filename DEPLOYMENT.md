# 🚀 Heroku 배포 가이드

## 빠른 배포 (5분 안에 완료)

### 1. Heroku CLI 설치

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Linux
curl https://cli-assets.heroku.com/install.sh | sh

# Windows
# https://devcenter.heroku.com/articles/heroku-cli 에서 다운로드
```

### 2. Heroku 로그인

```bash
heroku login
```

### 3. 앱 생성 및 배포

```bash
cd /workspaces/grocery-inventory-tracker

# Heroku 앱 생성
heroku create grocery-tracker-app

# Buildpack 추가 (Tesseract OCR)
heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-apt
heroku buildpacks:add --index 2 heroku/python

# 배포
git add .
git commit -m "Ready for Heroku deployment"
git push heroku main

# 앱 열기
heroku open
```

### 4. 환경 변수 설정 (선택사항)

```bash
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=your-secret-key-here
```

---

## Heroku 배포 파일 설명

### Procfile
앱 실행 명령어를 정의합니다.

```
web: gunicorn app:app
```

### Aptfile
Tesseract OCR 시스템 패키지를 설치합니다.

```
tesseract-ocr
tesseract-ocr-eng
tesseract-ocr-kor
```

### runtime.txt
Python 버전을 지정합니다.

```
python-3.12.3
```

---

## Railway 배포 (Heroku 대안)

### 1. Railway 계정 생성
https://railway.app

### 2. GitHub 연결

```bash
# GitHub에 푸시
git add .
git commit -m "Ready for Railway"
git push origin main
```

### 3. Railway에서 배포

1. Railway 대시보드에서 "New Project" 클릭
2. "Deploy from GitHub repo" 선택
3. 저장소 선택
4. 자동 배포 시작
5. 도메인 생성

---

## Vercel 배포

```bash
# Vercel CLI 설치
npm i -g vercel

# 로그인
vercel login

# 배포
vercel

# 프로덕션 배포
vercel --prod
```

---

## Docker 배포

### 로컬에서 실행

```bash
# Docker 이미지 빌드
docker build -t grocery-tracker .

# 컨테이너 실행
docker run -p 5000:5000 grocery-tracker

# 또는 docker-compose 사용
docker-compose up -d
```

### Docker Hub에 푸시

```bash
# 로그인
docker login

# 태그 지정
docker tag grocery-tracker yourusername/grocery-tracker:latest

# 푸시
docker push yourusername/grocery-tracker:latest
```

---

## 환경 변수

프로덕션 배포 시 다음 환경 변수를 설정하세요:

```bash
FLASK_ENV=production
SECRET_KEY=your-secure-secret-key
DATABASE_URL=sqlite:///grocery.db
UPLOAD_FOLDER=uploads
```

---

## SSL/HTTPS 설정

Heroku, Railway, Vercel은 자동으로 HTTPS를 제공합니다.

커스텀 도메인 사용 시:
1. 도메인 등록
2. DNS 설정
3. SSL 인증서 (Let's Encrypt 무료)

---

## 모니터링

### Heroku

```bash
# 로그 확인
heroku logs --tail

# 성능 모니터링
heroku ps
```

### Railway

Railway 대시보드에서 실시간 로그 확인

---

## 비용

### Heroku
- **Eco Plan:** $5/월
- **Basic:** $7/월
- **무료 옵션:** Hobby (월 550시간)

### Railway
- **Starter:** $5/월 (500시간)
- **Developer:** $20/월

### Vercel
- **Hobby:** 무료
- **Pro:** $20/월

### Docker + VPS
- **Digital Ocean:** $6/월
- **Linode:** $5/월
- **AWS Lightsail:** $3.50/월

---

## PWA 설치 가능 확인

배포 후 반드시 확인:
1. HTTPS 활성화 ✅
2. manifest.json 접근 가능 ✅
3. Service Worker 등록 ✅
4. Chrome에서 설치 프롬프트 표시 ✅

---

## 트러블슈팅

### Tesseract 오류
```bash
# Heroku에서 Aptfile 확인
heroku run bash
which tesseract
```

### 데이터베이스 초기화
```bash
heroku run python -c "import sqlite3; conn = sqlite3.connect('grocery.db'); conn.executescript(open('schema.sql').read()); conn.close()"
```

### 로그 확인
```bash
heroku logs --tail
```
