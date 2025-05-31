# AI 스마트 사진 뷰어 설치 가이드

## 빠른 시작

### 1. 프로젝트 클론
```bash
git clone https://github.com/your-username/smart-photo-viewer.git
cd smart-photo-viewer
```

### 2. 가상 환경 생성 (권장)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. OpenAI API 키 설정

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 다음 내용을 추가:

```env
# OpenAI API 키
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**중요**: 
- `.env` 파일은 절대 Git에 커밋하지 마세요
- API 키는 https://platform.openai.com/api-keys 에서 발급받을 수 있습니다
- API 사용에는 요금이 부과될 수 있습니다

### 5. 프로그램 실행
```bash
python main.py
```

## API 키 없이 사용하기

OpenAI API 키가 없어도 기본적인 사진 뷰어 기능과 EXIF 데이터 확인은 가능합니다.
단, AI 기반 분석 기능(해시태그 생성, 촬영 정보 추정, 위치 추정)은 사용할 수 없습니다.

## 문제 해결

### 1. ModuleNotFoundError
```bash
# requirements.txt의 모든 패키지가 설치되었는지 확인
pip list

# 특정 패키지만 재설치
pip install --force-reinstall package-name
```

### 2. OpenAI API 오류
- API 키가 올바른지 확인
- API 사용량 한도 확인
- 인터넷 연결 상태 확인

### 3. 이미지가 표시되지 않음
- 지원 형식: JPG, JPEG, PNG, GIF, BMP, TIFF
- 파일이 손상되지 않았는지 확인 