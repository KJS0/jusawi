# AI 스마트 사진 뷰어

OpenAI GPT를 활용한 지능형 사진 뷰어 애플리케이션

## 주요 기능

- 📸 **사진 뷰어**: 폴더 내 이미지를 쉽게 탐색
- 📊 **EXIF 데이터 표시**: 사진의 메타데이터 확인
- 🤖 **AI 기반 분석**:
  - 이미지에서 자동 해시태그 생성 (5개)
  - EXIF가 없을 경우 촬영 정보 추정 (셔터 속도, ISO, 조리개)
  - 위치 정보가 없을 경우 촬영 위치 추정

## 설치 방법

### 1. 요구사항

- Python 3.8 이상
- OpenAI API 키 (AI 기능 사용 시)

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. OpenAI API 키 설정

프로젝트 루트에 `.env` 파일을 생성하고 API 키를 추가:

```
OPENAI_API_KEY=your_openai_api_key_here
```

## 사용 방법

### 프로그램 실행

```bash
python main.py
```

### 주요 기능 사용법

1. **이미지 열기**: 
   - "열기" 버튼 클릭 또는 `Ctrl+O`
   - 폴더를 열면 해당 폴더의 모든 이미지를 순회 가능

2. **이미지 탐색**:
   - 이전/다음 버튼 또는 좌우 화살표 키 사용

3. **EXIF 정보 확인**:
   - 우측 "EXIF 정보" 탭에서 자동으로 표시

4. **AI 분석**:
   - 우측 "AI 분석" 탭에서 "AI 분석 실행" 버튼 클릭
   - 해시태그, 촬영 정보, 위치 추정 결과 확인

## 프로젝트 구조

```
├── main.py              # 메인 진입점
├── gui/
│   └── photo_viewer.py  # 사진 뷰어 GUI
├── utils/
│   ├── ai_analyzer.py   # OpenAI API 연동
│   └── exif_reader.py   # EXIF 데이터 읽기
├── requirements.txt     # 의존성 목록
└── README.md           # 프로젝트 문서
```

## 라이선스

MIT License 