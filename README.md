# Jusawi - 사진 EXIF 데이터 분석 도구

사진의 EXIF 데이터를 분석하고 시각화하는 Python 기반 데스크톱 애플리케이션입니다.

## 주요 기능

- 사진 EXIF 데이터 추출 및 표시
- GPS 좌표 기반 지도 표시
- 히스토그램 분석
- 장소 추정 (GPT 활용)
- EXIF 데이터 복사/붙여넣기
- 데이터 CSV/Excel 내보내기

## 설치 방법

1. 저장소 클론:
```bash
git clone https://github.com/yourusername/jusawi.git
cd jusawi
```

2. 가상환경 생성 및 활성화:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 의존성 설치:
```bash
pip install -r requirements.txt
```

## 실행 방법

```bash
python app.py
```

## 사용된 기술

- Python
- Tkinter (GUI)
- PIL (이미지 처리)
- Pandas (데이터 처리)
- GPT API (장소 추정)

## 라이선스

MIT License 