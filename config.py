# 주사위 (JUSAWI) EXIF 뷰어 프로그램 설정
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# 기본 설정 정의
class Config:
    """애플리케이션 설정 클래스"""
    
    # EXIF 메타데이터 태그 순서 (표시 순서 유지)
    EXIF_TAGS = [
        'Model',        # 카메라 모델
        'LensModel',    # 렌즈 모델
        'FocalLength',  # 초점 거리
        '35mmEq',       # 35mm 등가 초점 거리
        'FNumber',      # 조리개 값
        'ISOSpeedRatings',  # ISO 감도
        'ExposureTime'  # 노출 시간
    ]
    
    # UI 크기 설정
    CANVAS_SIZE = (340, 340)  # 이미지 캔버스 크기
    MAP_SIZE = (400, 400)     # 지도 크기
    
    # API 키 및 서비스 설정
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # OpenAI API 키
    
    # 애플리케이션 설정
    APP_TITLE = "주.사.위 EXIF Viewer"  # 앱 타이틀
    APP_SIZE = "800x520"  # 기본 창 크기
    USER_CONFIG_PATH = Path.home() / ".jusawi" / "config.json"  # 사용자 설정 파일 경로
    
    # 로깅 설정
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = Path.home() / ".jusawi" / "app.log"

    @classmethod
    def load_user_config(cls) -> Dict[str, Any]:
        """
        사용자 설정 파일을 로드합니다.
        
        Returns:
            Dict[str, Any]: 사용자 설정 또는 빈 딕셔너리
        """
        try:
            if cls.USER_CONFIG_PATH.exists():
                with open(cls.USER_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logging.warning(f"사용자 설정을 로드하지 못했습니다: {e}")
            return {}
    
    @classmethod
    def save_user_config(cls, config: Dict[str, Any]) -> bool:
        """
        사용자 설정을 파일에 저장합니다.
        
        Args:
            config (Dict[str, Any]): 저장할 설정
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # 디렉토리 생성
            cls.USER_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            # 설정 저장
            with open(cls.USER_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logging.error(f"사용자 설정을 저장하지 못했습니다: {e}")
            return False

    @classmethod
    def setup_logging(cls):
        """로깅 시스템을 설정합니다."""
        try:
            # 로그 디렉토리 생성
            cls.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # 로깅 설정
            logging.basicConfig(
                level=cls.LOG_LEVEL,
                format=cls.LOG_FORMAT,
                handlers=[
                    logging.FileHandler(cls.LOG_FILE),
                    logging.StreamHandler()
                ]
            )
        except Exception as e:
            # 기본 로깅만 설정
            logging.basicConfig(level=cls.LOG_LEVEL, format=cls.LOG_FORMAT)
            logging.warning(f"로깅 설정 중 오류 발생: {e}")


# 설정 객체에서 값을 가져오는 대신 모듈 레벨 변수로 노출 (기존 코드와의 호환성 유지)
EXIF_TAGS = Config.EXIF_TAGS
CANVAS_SIZE = Config.CANVAS_SIZE
MAP_SIZE = Config.MAP_SIZE
OPENAI_API_KEY = Config.OPENAI_API_KEY
APP_TITLE = Config.APP_TITLE
APP_SIZE = Config.APP_SIZE

# 애플리케이션 시작 시 로깅 설정
Config.setup_logging()
