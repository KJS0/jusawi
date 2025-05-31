#!/usr/bin/env python3
"""
AI 기반 스마트 사진 뷰어
EXIF 데이터 표시 및 AI 분석 기능을 갖춘 사진 뷰어

메인 애플리케이션 진입점
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import logging
from pathlib import Path
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_photo_viewer.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def check_dependencies():
    """필수 의존성 확인"""
    required_modules = [
        ('PIL', 'Pillow'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('piexif', 'piexif'),
        ('openai', 'openai'),
        ('dotenv', 'python-dotenv')
    ]
    
    missing_modules = []
    for module_name, pip_name in required_modules:
        try:
            __import__(module_name)
        except ImportError:
            missing_modules.append(pip_name)
    
    if missing_modules:
        error_msg = f"다음 모듈이 설치되지 않았습니다: {', '.join(missing_modules)}\n"
        error_msg += "pip install -r requirements.txt 명령으로 필요한 라이브러리를 설치해주세요."
        messagebox.showerror("의존성 오류", error_msg)
        return False
    
    return True

def check_api_key():
    """OpenAI API 키 확인"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        error_msg = "OpenAI API 키가 설정되지 않았습니다.\n"
        error_msg += ".env 파일을 생성하고 OPENAI_API_KEY=your_api_key 형식으로 키를 설정해주세요."
        messagebox.showwarning("API 키 미설정", error_msg)
        # API 키가 없어도 기본 기능은 사용할 수 있도록 함
        return False
    return True

def main():
    """메인 함수"""
    try:
        logger.info("스마트 사진 뷰어 시작")
        
        # 의존성 확인
        if not check_dependencies():
            sys.exit(1)
        
        # API 키 확인
        has_api_key = check_api_key()
        
        # GUI 애플리케이션 시작
        from gui.photo_viewer import PhotoViewer
        
        root = tk.Tk()
        app = PhotoViewer(root, has_api_key=has_api_key)
        
        logger.info("사진 뷰어 애플리케이션 시작")
        root.mainloop()
        
    except Exception as e:
        logger.error(f"애플리케이션 시작 오류: {e}")
        messagebox.showerror("시작 오류", f"애플리케이션을 시작할 수 없습니다:\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 