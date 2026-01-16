# 🚀 앱스토어 배포 가이드

이 문서는 Grocery Inventory Tracker를 Google Play Store와 Apple App Store에 배포하는 방법을 안내합니다.

## 📱 배포 옵션

### 옵션 1: PWA (Progressive Web App) - 가장 간단
현재 앱은 이미 PWA로 설정되어 있습니다. 사용자가 브라우저에서 직접 설치할 수 있습니다.

**장점:**
- 별도의 앱 스토어 승인 불필요
- 즉시 배포 가능
- 업데이트가 자동으로 적용됨
- 하나의 코드베이스로 모든 플랫폼 지원

**설치 방법:**
1. Chrome/Safari에서 https://your-domain.com 접속
2. "홈 화면에 추가" 선택
3. 앱처럼 사용 가능

### 옵션 2: TWA (Trusted Web Activity) - Google Play Store
Android 앱스토어에 배포하려면 TWA를 사용합니다.

### 옵션 3: 하이브리드 앱 - 전체 앱스토어 배포
React Native, Flutter, Capacitor를 사용하여 네이티브 앱으로 변환합니다.

---

## 🤖 Google Play Store 배포 (TWA 방식)

### 1단계: 준비사항

```bash
# Node.js 및 npm 설치 확인
node --version
npm --version

# Bubblewrap 설치 (TWA 생성 도구)
npm install -g @bubblewrap/cli
```

### 2단계: TWA 프로젝트 생성

```bash
cd /workspaces/grocery-inventory-tracker

# TWA 초기화
bubblewrap init --manifest https://your-domain.com/static/manifest.json

# 프로젝트 정보 입력
# - Application Name: Grocery Inventory Tracker
# - Package ID: com.yourcompany.grocerytracker
# - Host: your-domain.com
# - Start URL: /
# - Icon: static/icons/icon-512x512.png
```

### 3단계: Digital Asset Links 설정

`/.well-known/assetlinks.json` 파일 생성:

```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "com.yourcompany.grocerytracker",
    "sha256_cert_fingerprints": ["YOUR_FINGERPRINT_HERE"]
  }
}]
```

### 4단계: APK 빌드

```bash
# 개발용 APK 빌드
bubblewrap build

# 릴리즈용 APK 빌드 (서명 필요)
bubblewrap build --release
```

### 5단계: Google Play Console 업로드

1. https://play.google.com/console 접속
2. 새 앱 만들기
3. APK 업로드
4. 스토어 리스팅 작성
5. 심사 제출

---

## 🍎 Apple App Store 배포

### 옵션 A: PWA Builder (권장)

1. https://www.pwabuilder.com 방문
2. 웹사이트 URL 입력: https://your-domain.com
3. "Build My PWA" 클릭
4. iOS 플랫폼 선택
5. 생성된 Xcode 프로젝트 다운로드

### 옵션 B: Capacitor 사용

```bash
# Capacitor 설치
npm install @capacitor/core @capacitor/cli
npm install @capacitor/ios

# Capacitor 초기화
npx cap init

# iOS 프로젝트 추가
npx cap add ios

# 빌드
npx cap build ios

# Xcode로 열기
npx cap open ios
```

### App Store Connect 제출

1. https://appstoreconnect.apple.com 접속
2. 새 앱 만들기
3. Xcode에서 Archive 생성
4. App Store에 업로드
5. 메타데이터 및 스크린샷 추가
6. 심사 제출

---

## 📦 Capacitor를 사용한 크로스 플랫폼 앱

이 방법을 사용하면 iOS와 Android 모두에 배포할 수 있습니다.

### 설치 및 설정

```bash
cd /workspaces/grocery-inventory-tracker

# Capacitor 설치
npm init -y
npm install @capacitor/core @capacitor/cli
npm install @capacitor/android @capacitor/ios
npm install @capacitor/camera @capacitor/filesystem

# Capacitor 초기화
npx cap init "Grocery Tracker" "com.yourcompany.grocerytracker" --web-dir="."

# 플랫폼 추가
npx cap add android
npx cap add ios

# 빌드 및 동기화
npx cap sync
npx cap copy

# Android Studio에서 열기
npx cap open android

# Xcode에서 열기
npx cap open ios
```

### capacitor.config.json 설정

```json
{
  "appId": "com.yourcompany.grocerytracker",
  "appName": "Grocery Tracker",
  "webDir": ".",
  "bundledWebRuntime": false,
  "server": {
    "url": "http://localhost:5000",
    "cleartext": true
  }
}
```

---

## 📸 앱스토어 스크린샷 요구사항

### Google Play Store

**필수 스크린샷:**
- 최소 2개, 최대 8개
- JPEG 또는 24-bit PNG
- 크기: 1080 x 1920 (세로) 또는 1920 x 1080 (가로)
- 최소: 320px, 최대: 3840px

### Apple App Store

**필수 스크린샷:**
- iPhone 14 Pro Max: 1290 x 2796
- iPhone 8 Plus: 1242 x 2208
- iPad Pro 12.9": 2048 x 2732

현재 프로젝트의 스크린샷은 `docs/screenshots/` 폴더에 있습니다.

---

## 🔒 앱 서명

### Android (Google Play)

```bash
# 키스토어 생성
keytool -genkey -v -keystore release-key.keystore \
  -alias grocery-tracker -keyalg RSA -keysize 2048 -validity 10000

# SHA-256 지문 확인
keytool -list -v -keystore release-key.keystore
```

### iOS (App Store)

1. Apple Developer 계정 필요 ($99/년)
2. Xcode에서 자동 서명 설정
3. 프로비저닝 프로필 생성

---

## 💰 비용 안내

### Google Play Store
- **일회성 등록 비용:** $25
- **연간 유지 비용:** 없음

### Apple App Store
- **연간 개발자 비용:** $99
- **처음 가입 시:** $99
- **매년 갱신:** $99

### 대안: PWA (무료)
- 앱 스토어 비용 없음
- 웹 호스팅 비용만 필요
- 사용자가 브라우저에서 직접 설치

---

## 🌐 PWA 배포 (현재 상태)

현재 앱은 이미 PWA로 동작합니다!

### 확인 방법

1. 앱 실행:
```bash
python app.py
```

2. Chrome에서 `localhost:5000` 접속

3. 주소창 오른쪽에 설치 아이콘(+) 확인

4. "설치" 클릭

### 프로덕션 배포

```bash
# 웹 서버에 배포 (예: Heroku, Vercel, Railway)
git push heroku main

# 또는 Docker 사용
docker build -t grocery-tracker .
docker run -p 5000:5000 grocery-tracker
```

---

## ✅ 체크리스트

### Google Play Store 배포 전
- [ ] TWA 프로젝트 생성
- [ ] Digital Asset Links 설정
- [ ] 앱 아이콘 준비 (512x512)
- [ ] 스크린샷 준비 (최소 2개)
- [ ] 앱 설명 작성
- [ ] 개인정보 처리방침 URL
- [ ] 키스토어 생성 및 안전하게 보관
- [ ] Google Play Developer 계정 ($25)

### Apple App Store 배포 전
- [ ] Apple Developer 계정 ($99/년)
- [ ] Xcode 프로젝트 설정
- [ ] 앱 아이콘 준비 (1024x1024)
- [ ] 스크린샷 준비 (다양한 기기 크기)
- [ ] 앱 설명 작성
- [ ] 개인정보 처리방침 URL
- [ ] App Store Connect에서 앱 정보 입력

### PWA 배포 (가장 간단)
- [x] manifest.json 설정 완료
- [x] Service Worker 설정 완료
- [x] 아이콘 준비 완료
- [ ] HTTPS 호스팅 설정
- [ ] 도메인 연결

---

## 🆘 도움말

### TWA 관련
- 공식 문서: https://developer.chrome.com/docs/android/trusted-web-activity/
- Bubblewrap: https://github.com/GoogleChromeLabs/bubblewrap

### PWA 관련
- PWA Builder: https://www.pwabuilder.com
- Google PWA 가이드: https://web.dev/progressive-web-apps/

### Capacitor 관련
- 공식 문서: https://capacitorjs.com/docs
- iOS 가이드: https://capacitorjs.com/docs/ios
- Android 가이드: https://capacitorjs.com/docs/android

---

## 🚀 빠른 시작 (권장)

**가장 빠르고 저렴한 방법: PWA 배포**

1. 웹 호스팅 서비스 선택 (Heroku, Vercel, Railway 등)
2. 앱 배포
3. HTTPS 활성화
4. 사용자에게 URL 공유
5. 사용자가 브라우저에서 "홈 화면에 추가"

**완료!** 앱 스토어 승인 없이 즉시 배포 가능합니다.
