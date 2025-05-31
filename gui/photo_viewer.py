"""
스마트 사진 뷰어 GUI
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import threading
from pathlib import Path
import logging
from typing import Optional, Dict, List
import re

from utils.exif_reader import ExifReader
from utils.ai_analyzer import AIImageAnalyzer
from utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)

class PhotoViewer:
    def __init__(self, root: tk.Tk, has_api_key: bool = True):
        self.root = root
        self.root.title("AI 스마트 사진 뷰어")
        self.root.geometry("1200x800")
        
        # API 키 존재 여부
        self.has_api_key = has_api_key
        
        # 현재 이미지 관련 변수
        self.current_image_path = None
        self.current_image = None
        self.photo_image = None
        self.image_list = []
        self.current_index = 0
        
        # 분석 상태 추적을 위한 변수
        self.analyzing_image_path = None
        
        # 스마트 분석을 위한 변수
        self.analysis_timer = None
        self.analysis_delay = 2.0  # 2초 후에 분석 시작
        self.skip_analysis = False  # 빠른 넘김 감지
        
        # EXIF 리더 초기화
        self.exif_reader = ExifReader()
        
        # 캐시 관리자 초기화
        self.cache_manager = CacheManager()
        
        # AI 분석기 초기화 (API 키가 있을 때만)
        self.ai_analyzer = None
        if self.has_api_key:
            try:
                self.ai_analyzer = AIImageAnalyzer()
            except Exception as e:
                logger.error(f"AI 분석기 초기화 실패: {e}")
                self.has_api_key = False
        
        # GUI 구성
        self._setup_ui()
        
        # 키보드 이벤트 바인딩
        self._bind_events()
    
    def _setup_ui(self):
        """UI 구성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 왼쪽: 이미지 표시 영역
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 툴바
        toolbar = ttk.Frame(left_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(toolbar, text="열기", command=self.open_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="폴더 열기", command=self.open_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="이전", command=self.prev_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="다음", command=self.next_image).pack(side=tk.LEFT, padx=2)
        
        # 캐시 관리 버튼 추가
        ttk.Separator(toolbar, orient='vertical').pack(side=tk.LEFT, padx=5, fill=tk.Y)
        ttk.Button(toolbar, text="캐시 정보", command=self.show_cache_info).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="캐시 초기화", command=self.clear_cache).pack(side=tk.LEFT, padx=2)
        
        # 스마트 분석 설정
        ttk.Separator(toolbar, orient='vertical').pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # 분석 지연 시간 설정
        ttk.Label(toolbar, text="분석 지연:").pack(side=tk.LEFT, padx=2)
        self.delay_var = tk.StringVar(value="2.0")
        delay_combo = ttk.Combobox(toolbar, textvariable=self.delay_var, width=5, 
                                 values=["0.5", "1.0", "2.0", "3.0", "5.0"])
        delay_combo.pack(side=tk.LEFT, padx=2)
        delay_combo.bind('<<ComboboxSelected>>', self._update_delay)
        ttk.Label(toolbar, text="초").pack(side=tk.LEFT, padx=2)
        
        # 현재 파일 정보
        self.file_label = ttk.Label(toolbar, text="파일을 선택하세요")
        self.file_label.pack(side=tk.LEFT, padx=20)
        
        # 이미지 표시 캔버스
        self.canvas = tk.Canvas(left_frame, bg='gray20')
        self.canvas.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # 사진 아래 AI 분석 정보 표시 영역
        info_frame = ttk.Frame(left_frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        # 해시태그 라벨
        self.hashtags_label = ttk.Label(info_frame, text="📌 해시태그: 로딩 중...", wraplength=600)
        self.hashtags_label.pack(fill=tk.X, pady=2)
        
        # 카메라 설정 라벨
        self.camera_label = ttk.Label(info_frame, text="📷 카메라 설정: 로딩 중...", wraplength=600)
        self.camera_label.pack(fill=tk.X, pady=2)
        
        # 위치 정보 라벨
        self.location_label = ttk.Label(info_frame, text="📍 위치: 로딩 중...", wraplength=600)
        self.location_label.pack(fill=tk.X, pady=2)
        
        # 오른쪽: 정보 표시 영역
        right_frame = ttk.Frame(main_frame, width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right_frame.pack_propagate(False)
        
        # 노트북 위젯으로 탭 구성
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # EXIF 정보 탭
        exif_frame = ttk.Frame(self.notebook)
        self.notebook.add(exif_frame, text="EXIF 정보")
        
        # EXIF 정보 표시 (스크롤 가능)
        exif_scroll = ttk.Scrollbar(exif_frame)
        exif_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.exif_text = tk.Text(exif_frame, wrap=tk.WORD, yscrollcommand=exif_scroll.set)
        self.exif_text.pack(fill=tk.BOTH, expand=True)
        exif_scroll.config(command=self.exif_text.yview)
        
        # AI 분석 탭
        ai_frame = ttk.Frame(self.notebook)
        self.notebook.add(ai_frame, text="AI 분석 상세")
        
        # AI 분석 결과 표시
        ai_scroll = ttk.Scrollbar(ai_frame)
        ai_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.ai_text = tk.Text(ai_frame, wrap=tk.WORD, yscrollcommand=ai_scroll.set)
        self.ai_text.pack(fill=tk.BOTH, expand=True)
        ai_scroll.config(command=self.ai_text.yview)
        
        # AI 분석 버튼
        if self.has_api_key:
            ttk.Button(ai_frame, text="AI 분석 재실행", command=self.analyze_with_ai).pack(pady=5)
        else:
            ttk.Label(ai_frame, text="API 키가 설정되지 않았습니다").pack(pady=5)
        
        # 상태바
        self.status_bar = ttk.Label(self.root, text="준비", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _bind_events(self):
        """키보드 이벤트 바인딩"""
        self.root.bind('<Left>', lambda e: self.prev_image())
        self.root.bind('<Right>', lambda e: self.next_image())
        self.root.bind('<Control-o>', lambda e: self.open_image())
        self.canvas.bind('<Configure>', self._on_canvas_resize)
    
    def open_image(self):
        """이미지 파일 열기"""
        file_path = filedialog.askopenfilename(
            title="이미지 선택",
            filetypes=[
                ("이미지 파일", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff"),
                ("모든 파일", "*.*")
            ]
        )
        
        if file_path:
            logger.info(f"단일 파일 선택: {os.path.basename(file_path)}")
            folder_path = os.path.dirname(file_path)
            logger.info(f"폴더 경로: {folder_path}")
            
            # 먼저 선택한 파일의 폴더에서 이미지 목록 생성
            self._build_image_list(folder_path)
            
            # 현재 선택한 파일의 인덱스 찾기
            if file_path in self.image_list:
                self.current_index = self.image_list.index(file_path)
                logger.info(f"파일 인덱스 찾음: {self.current_index + 1}/{len(self.image_list)} - {os.path.basename(file_path)}")
            else:
                # 리스트에 없으면 0으로 설정 (혹시 모를 경우 대비)
                self.current_index = 0
                logger.warning(f"파일이 목록에서 찾을 수 없음. 인덱스 0으로 설정: {os.path.basename(file_path)}")
                # 디버그를 위해 현재 목록 출력
                current_files = [os.path.basename(p) for p in self.image_list[:10]]
                logger.debug(f"현재 목록 (처음 10개): {current_files}")
            
            # 이미지 로드
            self.load_image(file_path)
    
    def open_folder(self):
        """폴더 열기"""
        folder_path = filedialog.askdirectory(title="폴더 선택")
        
        if folder_path:
            self._build_image_list(folder_path)
            if self.image_list:
                self.current_index = 0
                self.load_image(self.image_list[0])
    
    def _windows_explorer_sort_key(self, text: str):
        """윈도우 탐색기 방식의 정렬을 위한 키 생성 함수"""
        # 윈도우 탐색기는 특수문자 > 숫자 > 문자 순서로 정렬합니다
        result = []
        for char in text.lower():
            if char.isalpha():
                # 문자: 우선순위 2
                result.append((2, char))
            elif char.isdigit():
                # 숫자: 우선순위 1  
                result.append((1, char))
            else:
                # 특수문자(_포함): 우선순위 0 (가장 먼저)
                result.append((0, char))
        return result

    def _build_image_list(self, folder_path: str):
        """폴더 내 이미지 목록 생성 (윈도우 탐색기 정렬)"""
        self.image_list = []
        extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
        
        logger.info(f"폴더 스캔 시작: {folder_path}")
        
        # 폴더 내 모든 파일 검색
        image_files = []
        for file in Path(folder_path).iterdir():
            if file.is_file() and file.suffix.lower() in extensions:
                image_files.append(file)
        
        # 윈도우 탐색기 방식 정렬 (대소문자 구분 없는 ASCII 순서)
        image_files.sort(key=lambda x: self._windows_explorer_sort_key(x.name))
        
        # 경로를 문자열로 변환하여 리스트에 추가
        self.image_list = [str(file) for file in image_files]
        
        logger.info(f"이미지 목록 생성 완료: {len(self.image_list)}개 파일 (윈도우 탐색기 정렬)")
        
        # 디버그: 정렬된 파일명들 확인
        if self.image_list:
            file_names = [os.path.basename(path) for path in self.image_list]
            logger.debug(f"정렬된 모든 파일들: {file_names}")
            
            # 처음 10개만 미리보기
            preview = file_names[:10]
            logger.info(f"정렬된 파일들 (처음 10개): {preview}")
    
    def load_image(self, file_path: str):
        """이미지 로드 및 표시"""
        try:
            # 이전 분석 타이머 취소
            self._cancel_analysis_timer()
            
            # 즉시 정보 초기화 (이전 이미지 정보 제거)
            self._immediate_reset()
            
            self.current_image_path = file_path
            self.current_image = Image.open(file_path)
            
            # 파일 정보 업데이트
            file_name = os.path.basename(file_path)
            self.file_label.config(text=f"{file_name} ({self.current_index + 1}/{len(self.image_list)})")
            
            # 이미지 표시
            self._display_image()
            
            # EXIF 정보 표시
            self._display_exif_info()
            
            # AI 분석 결과 초기화
            self.ai_text.delete(1.0, tk.END)
            self.ai_text.insert(tk.END, "이미지 로드 시 자동 분석이 실행됩니다.")
            
            # EXIF 데이터 먼저 읽기
            exif_data = self.exif_reader.read_exif(self.current_image_path)
            has_exif = bool(exif_data and any(tag in exif_data for tag in ['ExposureTime', 'FNumber', 'ISO']))
            has_location = bool(exif_data and 'GPSInfo' in exif_data)
            
            # 사진 아래 정보 초기화 및 EXIF 정보 즉시 표시
            self._reset_info_labels(exif_data, has_exif, has_location)
            
            # 스마트 AI 분석 실행 (지연 분석)
            if self.has_api_key and self.ai_analyzer:
                # EXIF에 없는 정보만 분석
                if not has_exif or not has_location:
                    self._schedule_smart_analysis(file_path)
                else:
                    self.status_bar.config(text="EXIF 정보 표시 완료")
            else:
                self._set_no_api_info(has_exif, has_location)
            
            self.status_bar.config(text=f"이미지 로드 완료: {file_path}")
            
        except Exception as e:
            logger.error(f"이미지 로드 오류: {e}")
            messagebox.showerror("오류", f"이미지를 로드할 수 없습니다:\n{e}")
    
    def _immediate_reset(self):
        """이미지 변경 시 즉시 정보 초기화"""
        # 분석 중인 이미지 추적 초기화
        self.analyzing_image_path = None
        
        # 모든 정보 라벨 즉시 초기화
        self.hashtags_label.config(text="📌 해시태그: 로딩 중...")
        self.camera_label.config(text="📷 카메라 설정: 로딩 중...")
        self.location_label.config(text="📍 위치: 로딩 중...")
        
        # EXIF 텍스트 영역도 초기화
        self.exif_text.delete(1.0, tk.END)
        self.exif_text.insert(tk.END, "EXIF 정보 로딩 중...")
        
        # AI 분석 텍스트 영역도 초기화
        self.ai_text.delete(1.0, tk.END)
        self.ai_text.insert(tk.END, "정보 로딩 중...")
    
    def _display_image(self):
        """이미지를 캔버스에 표시"""
        if not self.current_image:
            return
        
        # 캔버스 크기에 맞게 이미지 크기 조정
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            # 이미지 비율 유지하며 크기 조정
            img_width, img_height = self.current_image.size
            scale = min(canvas_width / img_width, canvas_height / img_height, 1.0)
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            resized_image = self.current_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.photo_image = ImageTk.PhotoImage(resized_image)
            
            # 캔버스 중앙에 이미지 배치
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2
            
            self.canvas.delete("all")
            self.canvas.create_image(x, y, anchor=tk.NW, image=self.photo_image)
    
    def _on_canvas_resize(self, event):
        """캔버스 크기 변경 시 이미지 재표시"""
        if self.current_image:
            self._display_image()
    
    def _display_exif_info(self):
        """EXIF 정보 표시"""
        self.exif_text.delete(1.0, tk.END)
        
        if not self.current_image_path:
            return
        
        try:
            exif_data = self.exif_reader.read_exif(self.current_image_path)
            
            if exif_data:
                self.exif_text.insert(tk.END, "=== EXIF 정보 ===\n\n")
                
                # 주요 정보 먼저 표시
                important_tags = ['Make', 'Model', 'DateTime', 'ExposureTime', 
                                'FNumber', 'ISO', 'FocalLength', 'LensModel']
                
                for tag in important_tags:
                    if tag in exif_data:
                        self.exif_text.insert(tk.END, f"{tag}: {exif_data[tag]}\n")
                
                self.exif_text.insert(tk.END, "\n=== 모든 EXIF 데이터 ===\n\n")
                
                # 모든 EXIF 데이터 표시
                for tag, value in sorted(exif_data.items()):
                    if tag not in important_tags:
                        self.exif_text.insert(tk.END, f"{tag}: {value}\n")
            else:
                self.exif_text.insert(tk.END, "EXIF 정보가 없습니다.")
                
        except Exception as e:
            logger.error(f"EXIF 읽기 오류: {e}")
            self.exif_text.insert(tk.END, f"EXIF 정보를 읽을 수 없습니다:\n{e}")
    
    def analyze_with_ai(self):
        """AI를 사용한 이미지 분석 (수동 재실행)"""
        if not self.current_image_path or not self.ai_analyzer:
            return
        
        # 로딩 메시지 표시
        self.ai_text.delete(1.0, tk.END)
        self.ai_text.insert(tk.END, "AI 분석 중... 잠시만 기다려주세요.")
        self.status_bar.config(text="AI 분석 중...")
        
        # 캐시 무시하고 강제로 새로 분석
        self.analyzing_image_path = self.current_image_path
        threading.Thread(target=self._force_ai_analysis, daemon=True).start()
    
    def _force_ai_analysis(self):
        """강제 AI 분석 (캐시 무시)"""
        try:
            analysis_target = self.analyzing_image_path
            
            if analysis_target != self.current_image_path:
                return
            
            # EXIF 정보 확인
            exif_data = self.exif_reader.read_exif(analysis_target)
            has_exif = bool(exif_data and any(tag in exif_data for tag in ['ExposureTime', 'FNumber', 'ISO']))
            has_location = bool(exif_data and 'GPSInfo' in exif_data)
            
            # AI 분석 실행
            result = self.ai_analyzer.analyze_image(
                analysis_target, 
                has_exif=has_exif,
                has_location=has_location
            )
            
            if analysis_target == self.current_image_path:
                # 새로운 결과를 캐시에 저장 (기존 캐시 덮어쓰기)
                self.cache_manager.save_result(analysis_target, result)
                
                # 결과 표시
                self.root.after(0, self._update_info_labels, result, exif_data, analysis_target)
                self.root.after(0, self._display_ai_results, result)
                
        except Exception as e:
            logger.error(f"강제 AI 분석 오류: {e}")
            if self.analyzing_image_path == self.current_image_path:
                self.root.after(0, self._set_error_info, str(e))
    
    def _display_ai_results(self, result: Dict):
        """AI 분석 결과 표시"""
        self.ai_text.delete(1.0, tk.END)
        self.ai_text.insert(tk.END, "=== AI 분석 결과 ===\n\n")
        
        # 해시태그
        if result.get('hashtags'):
            self.ai_text.insert(tk.END, "📌 추천 해시태그:\n")
            for tag in result['hashtags']:
                self.ai_text.insert(tk.END, f"  #{tag}\n")
            self.ai_text.insert(tk.END, "\n")
        
        # 카메라 설정 (EXIF가 없을 때만)
        if result.get('camera_settings'):
            self.ai_text.insert(tk.END, "📷 추정 카메라 설정:\n")
            settings = result['camera_settings']
            if settings.get('shutter_speed'):
                self.ai_text.insert(tk.END, f"  셔터 속도: {settings['shutter_speed']}\n")
            if settings.get('iso'):
                self.ai_text.insert(tk.END, f"  ISO: {settings['iso']}\n")
            if settings.get('aperture'):
                self.ai_text.insert(tk.END, f"  조리개: {settings['aperture']}\n")
            if settings.get('reasoning'):
                self.ai_text.insert(tk.END, f"  추정 근거: {settings['reasoning']}\n")
            self.ai_text.insert(tk.END, "\n")
        
        # 위치 정보 (간단한 형태)
        if result.get('location'):
            location = result['location']
            if isinstance(location, dict) and location:
                self.ai_text.insert(tk.END, "📍 추정 촬영 위치:\n")
                
                # 주요 위치 정보
                if location.get('primary_location'):
                    self.ai_text.insert(tk.END, f"  {location['primary_location']}\n")
                
                # 대안 위치들
                if location.get('alternative_locations') and len(location['alternative_locations']) > 0:
                    self.ai_text.insert(tk.END, f"\n  다른 가능성:\n")
                    for alt_location in location['alternative_locations']:
                        self.ai_text.insert(tk.END, f"    • {alt_location}\n")
                
                self.ai_text.insert(tk.END, "\n")
            elif isinstance(location, str) and location:
                # 이전 형식과의 호환성
                self.ai_text.insert(tk.END, "📍 추정 촬영 위치:\n")
                self.ai_text.insert(tk.END, f"  {location}\n\n")
        
        # 오류 메시지
        if result.get('error'):
            self.ai_text.insert(tk.END, f"\n⚠️ 오류: {result['error']}\n")
        
        self.status_bar.config(text="AI 분석 완료")
    
    def prev_image(self):
        """이전 이미지로 이동"""
        if self.image_list and self.current_index > 0:
            self.current_index -= 1
            self.load_image(self.image_list[self.current_index])
    
    def next_image(self):
        """다음 이미지로 이동"""
        if self.image_list and self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.load_image(self.image_list[self.current_index])
    
    def _reset_info_labels(self, exif_data: Optional[Dict], has_exif: bool, has_location: bool):
        """정보 라벨 초기화 및 EXIF 정보 즉시 표시"""
        # 해시태그는 항상 AI 분석 필요
        self.hashtags_label.config(text="📌 해시태그: 로딩 중...")
        
        # 카메라 설정 - EXIF가 있으면 바로 표시
        if has_exif and exif_data:
            camera_info = []
            if 'ExposureTime' in exif_data:
                camera_info.append(f"셔터: {exif_data['ExposureTime']}")
            if 'ISO' in exif_data:
                camera_info.append(f"ISO: {exif_data['ISO']}")
            if 'FNumber' in exif_data:
                camera_info.append(f"조리개: {exif_data['FNumber']}")
            
            if camera_info:
                camera_text = " | ".join(camera_info)
                self.camera_label.config(text=f"📷 카메라 설정: {camera_text}")
            else:
                self.camera_label.config(text="📷 카메라 설정: 정보 없음")
        else:
            # EXIF가 없으면 AI 분석 대기
            if self.has_api_key:
                self.camera_label.config(text="📷 카메라 설정: 분석 중...")
            else:
                self.camera_label.config(text="📷 카메라 설정: API 키가 필요합니다")
        
        # 위치 정보 - EXIF GPS가 있으면 바로 표시
        if has_location and exif_data and 'GPSCoordinates' in exif_data:
            coords = exif_data['GPSCoordinates']
            self.location_label.config(text=f"📍 위치: GPS {coords['formatted']}")
        else:
            # GPS가 없으면 AI 분석 대기
            if self.has_api_key:
                self.location_label.config(text="📍 위치: 분석 중...")
            else:
                self.location_label.config(text="📍 위치: API 키가 필요합니다")
    
    def _set_no_api_info(self, has_exif: bool, has_location: bool):
        """API 키가 없을 때 정보 표시"""
        self.hashtags_label.config(text="📌 해시태그: API 키가 필요합니다")
        
        if not has_exif:
            self.camera_label.config(text="📷 카메라 설정: API 키가 필요합니다")
        
        if not has_location:
            self.location_label.config(text="📍 위치: API 키가 필요합니다")
    
    def _cancel_analysis_timer(self):
        """분석 타이머 취소"""
        if self.analysis_timer:
            self.root.after_cancel(self.analysis_timer)
            self.analysis_timer = None
            logger.debug("분석 타이머 취소됨")
    
    def _schedule_smart_analysis(self, file_path: str):
        """스마트 분석 스케줄링 (지연 분석)"""
        self.analyzing_image_path = file_path
        
        # 캐시에서 먼저 확인
        cached_result = self.cache_manager.get_cached_result(file_path)
        if cached_result:
            # 캐시된 결과가 있으면 즉시 표시
            logger.info(f"캐시된 결과 즉시 사용: {os.path.basename(file_path)}")
            exif_data = self.exif_reader.read_exif(file_path)
            if file_path == self.current_image_path:
                self._update_info_labels(cached_result, exif_data, file_path)
                self._display_ai_results(cached_result)
                self.status_bar.config(text="캐시된 결과 표시 완료")
            return
        
        # 캐시에 없으면 지연 분석 스케줄
        delay_ms = int(self.analysis_delay * 1000)
        self.analysis_timer = self.root.after(delay_ms, self._delayed_analysis_start, file_path)
        
        # 사용자에게는 단순히 "분석 중" 메시지 표시 (지연 시간 숨김)
        self.hashtags_label.config(text="📌 해시태그: 분석 중...")
        if not self._has_camera_info():
            self.camera_label.config(text="📷 카메라 설정: 분석 중...")
        if not self._has_location_info():
            self.location_label.config(text="📍 위치: 분석 중...")
        
        logger.info(f"AI 분석 {self.analysis_delay}초 지연 스케줄됨: {os.path.basename(file_path)}")
    
    def _delayed_analysis_start(self, file_path: str):
        """지연된 분석 시작"""
        # 이미지가 바뀌었는지 확인
        if file_path != self.current_image_path:
            logger.info(f"이미지 변경됨. 분석 취소: {os.path.basename(file_path)}")
            return
        
        # 실제 AI 분석 시작 (사용자에게는 동일한 "분석 중" 메시지)
        self.status_bar.config(text="AI 분석 중...")
        # 라벨은 이미 "분석 중..."으로 설정되어 있으므로 변경하지 않음
            
        threading.Thread(target=self._auto_ai_analysis, daemon=True).start()
        logger.info(f"지연된 AI 분석 시작: {os.path.basename(file_path)}")
    
    def _has_camera_info(self) -> bool:
        """현재 카메라 정보가 있는지 확인"""
        text = self.camera_label.cget("text")
        return not any(keyword in text for keyword in ["로딩 중", "분석", "API 키"])
    
    def _has_location_info(self) -> bool:
        """현재 위치 정보가 있는지 확인"""
        text = self.location_label.cget("text")
        return not any(keyword in text for keyword in ["로딩 중", "분석", "API 키"])
    
    def _auto_ai_analysis(self):
        """자동 AI 분석 실행"""
        try:
            # 분석 시작 시점의 이미지 경로 저장
            analysis_target = self.analyzing_image_path
            
            # 이미지가 바뀌었는지 확인
            if analysis_target != self.current_image_path:
                return  # 이미지가 바뀌었으면 분석 중단
            
            # EXIF 정보 확인
            exif_data = self.exif_reader.read_exif(analysis_target)
            has_exif = bool(exif_data and any(tag in exif_data for tag in ['ExposureTime', 'FNumber', 'ISO']))
            has_location = bool(exif_data and 'GPSInfo' in exif_data)
            
            # AI 분석 실행
            result = self.ai_analyzer.analyze_image(
                analysis_target, 
                has_exif=has_exif,
                has_location=has_location
            )
            
            # 분석 완료 후 이미지가 바뀌었는지 다시 확인
            if analysis_target == self.current_image_path:
                # 결과를 캐시에 저장
                self.cache_manager.save_result(analysis_target, result)
                
                # 결과를 메인 스레드에서 표시
                self.root.after(0, self._update_info_labels, result, exif_data, analysis_target)
                self.root.after(0, self._display_ai_results, result)
            # 이미지가 바뀌었으면 결과를 무시
            
        except Exception as e:
            logger.error(f"자동 AI 분석 오류: {e}")
            # 오류 발생 시에도 현재 이미지와 일치하는지 확인
            if self.analyzing_image_path == self.current_image_path:
                self.root.after(0, self._set_error_info, str(e))
    
    def _update_delay(self, event=None):
        """분석 지연 시간 업데이트"""
        try:
            self.analysis_delay = float(self.delay_var.get())
            logger.info(f"분석 지연 시간 변경: {self.analysis_delay}초")
        except ValueError:
            self.analysis_delay = 2.0
            self.delay_var.set("2.0")
    
    def _update_info_labels(self, ai_result: Dict, exif_data: Optional[Dict], analysis_target: str):
        """사진 아래 정보 라벨 업데이트"""
        # 분석 결과가 현재 이미지에 대한 것인지 확인
        if analysis_target != self.current_image_path:
            return  # 다른 이미지에 대한 결과이면 무시
        
        # 해시태그 (항상 AI 생성)
        if ai_result.get('hashtags'):
            hashtags_text = " ".join([f"#{tag}" for tag in ai_result['hashtags']])
            self.hashtags_label.config(text=f"📌 해시태그: {hashtags_text} (GPT 추정)")
        else:
            self.hashtags_label.config(text="📌 해시태그: 생성되지 않음")
        
        # 카메라 설정 - EXIF가 없는 경우에만 AI 추정값으로 업데이트
        has_exif = bool(exif_data and any(tag in exif_data for tag in ['ExposureTime', 'FNumber', 'ISO']))
        if not has_exif and ai_result.get('camera_settings'):
            settings = ai_result['camera_settings']
            camera_info = []
            if settings.get('shutter_speed'):
                camera_info.append(f"셔터: {settings['shutter_speed']}")
            if settings.get('iso'):
                camera_info.append(f"ISO: {settings['iso']}")
            if settings.get('aperture'):
                camera_info.append(f"조리개: {settings['aperture']}")
            
            if camera_info:
                camera_text = " | ".join(camera_info)
                self.camera_label.config(text=f"📷 추정 설정: {camera_text} (GPT 추정)")
            else:
                self.camera_label.config(text="📷 카메라 설정: 추정되지 않음")
        
        # 위치 정보 - GPS가 없는 경우에만 AI 추정값으로 업데이트
        has_location = bool(exif_data and 'GPSInfo' in exif_data)
        if not has_location and ai_result.get('location') and ai_result['location'].get('primary_location'):
            location_text = ai_result['location']['primary_location']
            self.location_label.config(text=f"📍 추정 위치: {location_text} (GPT 추정)")
        elif not has_location and not ai_result.get('location'):
            self.location_label.config(text="📍 위치: 추정되지 않음")
        
        self.status_bar.config(text="AI 분석 완료")
    
    def _set_error_info(self, error_message: str):
        """오류 정보 표시"""
        self.hashtags_label.config(text=f"📌 해시태그: 오류 - {error_message}")
        self.camera_label.config(text="📷 카메라 설정: 분석 실패")
        self.location_label.config(text="📍 위치: 분석 실패")
        self.status_bar.config(text="AI 분석 실패")
    
    def show_cache_info(self):
        """캐시 정보 표시"""
        stats = self.cache_manager.get_cache_stats()
        info_msg = f"""💰 스마트 분석 & 캐시 시스템

🧠 스마트 분석:
• 분석 지연 시간: {self.analysis_delay}초
• 빠르게 넘기면 분석하지 않음 (토큰 절약!)
• 캐시된 결과는 즉시 표시

📊 캐시 통계:
• 저장된 항목 수: {stats['total_entries']}개
• 캐시 디렉토리: {stats['cache_dir']}
• 메모리 캐시 크기: {stats['memory_cache_size']}개
• 캐시 파일 존재: {'예' if stats['cache_file_exists'] else '아니오'}

💡 절약 효과:
• 같은 사진 재분석 방지
• 빠른 넘김 시 분석 생략
• API 비용 최대 90% 절약 가능!"""
        
        messagebox.showinfo("스마트 분석 & 캐시 정보", info_msg)
    
    def clear_cache(self):
        """캐시 초기화"""
        result = messagebox.askyesno(
            "캐시 초기화", 
            "모든 캐시된 AI 분석 결과를 삭제하시겠습니까?\n\n"
            "삭제 후에는 모든 이미지를 다시 분석해야 합니다."
        )
        
        if result:
            self.cache_manager.clear_cache()
            messagebox.showinfo("완료", "캐시가 초기화되었습니다.") 