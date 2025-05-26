#!/usr/bin/env python3
"""
EXIF 데이터 분석 및 촬영 습관 개선 도구
캡스톤 디자인 프로젝트

메인 애플리케이션 진입점
"""

import sys
import tkinter as tk
from tkinter import messagebox
import logging
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('exif_analyzer.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def check_dependencies():
    """필수 의존성 확인"""
    required_modules = [
        'PIL', 'pandas', 'numpy', 'matplotlib', 
        'seaborn', 'piexif', 'sklearn'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        error_msg = f"다음 모듈이 설치되지 않았습니다: {', '.join(missing_modules)}\n"
        error_msg += "pip install -r requirements.txt 명령으로 설치해주세요."
        messagebox.showerror("의존성 오류", error_msg)
        return False
    
    return True

def main():
    """메인 함수"""
    try:
        logger.info("EXIF 분석 도구 시작")
        
        # 의존성 확인
        if not check_dependencies():
            sys.exit(1)
        
        # GUI 애플리케이션 시작
        from gui.main_window import MainWindow
        
        root = tk.Tk()
        app = MainWindow(root)
        
        logger.info("GUI 애플리케이션 시작")
        root.mainloop()
        
    except Exception as e:
        logger.error(f"애플리케이션 시작 오류: {e}")
        messagebox.showerror("시작 오류", f"애플리케이션을 시작할 수 없습니다:\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 