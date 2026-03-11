# 🎫 티켓팅 매크로 — GitHub Actions 빌드 가이드

## 📁 폴더 구조
```
ticketing_gh/
├── .github/
│   └── workflows/
│       └── build.yml      ← GitHub Actions 자동 빌드
├── image/                 ← 이미지 리소스 폴더 (비어있어도 됨)
├── ticketing.py           ← 메인 소스
├── requirements.txt       ← 패키지 목록
└── README.md
```

---

## 🚀 EXE 빌드 방법 (GitHub 계정만 있으면 무료!)

### 1단계 — GitHub 저장소 만들기
1. [github.com](https://github.com) 로그인
2. 우측 상단 **`+`** → **`New repository`** 클릭
3. Repository name: `ticketing-macro` (아무 이름 OK)
4. **Public** 또는 **Private** 선택 후 **`Create repository`** 클릭

### 2단계 — 파일 올리기
1. 저장소 페이지에서 **`uploading an existing file`** 클릭
2. 이 ZIP 안의 **모든 파일과 폴더**를 드래그하여 업로드
   - ⚠️ `.github/workflows/build.yml` 폴더 구조 포함해서 올려야 합니다
3. **`Commit changes`** 클릭

### 3단계 — EXE 다운로드
1. 저장소 상단 탭 **`Actions`** 클릭
2. 좌측 **`Build Ticketing EXE`** 클릭
3. 최신 실행 항목 클릭 → 하단 **`Artifacts`** 섹션에서
4. **`티켓팅매크로`** 다운로드 → `티켓팅매크로.exe` 완성! 🎉

---

## 🎮 단축키
| 키 | 기능 |
|----|------|
| **F1** | 날짜/회차 선택 |
| **F2** | 티켓팅 실행 |
| **F8** | 범위 좌표↖ 등록 |
| **F9** | 범위 좌표↘ 등록 |
| **F10** | 선택완료 좌표 등록 |

> 💡 **관리자 권한으로 실행**하면 단축키가 더 안정적으로 동작합니다.
