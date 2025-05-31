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

from utils.exif_reader import ExifReader
from utils.ai_analyzer import AIImageAnalyzer

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
        
        # EXIF 리더 초기화
        self.exif_reader = ExifReader()
        
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
        
        # 현재 파일 정보
        self.file_label = ttk.Label(toolbar, text="파일을 선택하세요")
        self.file_label.pack(side=tk.LEFT, padx=20)
        
        # 이미지 표시 캔버스
        self.canvas = tk.Canvas(left_frame, bg='gray20')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
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
        self.notebook.add(ai_frame, text="AI 분석")
        
        # AI 분석 결과 표시
        ai_scroll = ttk.Scrollbar(ai_frame)
        ai_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.ai_text = tk.Text(ai_frame, wrap=tk.WORD, yscrollcommand=ai_scroll.set)
        self.ai_text.pack(fill=tk.BOTH, expand=True)
        ai_scroll.config(command=self.ai_text.yview)
        
        # AI 분석 버튼
        if self.has_api_key:
            ttk.Button(ai_frame, text="AI 분석 실행", command=self.analyze_with_ai).pack(pady=5)
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
            self.load_image(file_path)
            # 선택한 파일의 폴더에서 이미지 목록 생성
            self._build_image_list(os.path.dirname(file_path))
    
    def open_folder(self):
        """폴더 열기"""
        folder_path = filedialog.askdirectory(title="폴더 선택")
        
        if folder_path:
            self._build_image_list(folder_path)
            if self.image_list:
                self.current_index = 0
                self.load_image(self.image_list[0])
    
    def _build_image_list(self, folder_path: str):
        """폴더 내 이미지 목록 생성"""
        self.image_list = []
        extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
        
        for file in Path(folder_path).iterdir():
            if file.suffix.lower() in extensions:
                self.image_list.append(str(file))
        
        self.image_list.sort()
        
        # 현재 이미지의 인덱스 찾기
        if self.current_image_path in self.image_list:
            self.current_index = self.image_list.index(self.current_image_path)
    
    def load_image(self, file_path: str):
        """이미지 로드 및 표시"""
        try:
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
            self.ai_text.insert(tk.END, "AI 분석을 실행하려면 버튼을 클릭하세요.")
            
            self.status_bar.config(text=f"이미지 로드 완료: {file_path}")
            
        except Exception as e:
            logger.error(f"이미지 로드 오류: {e}")
            messagebox.showerror("오류", f"이미지를 로드할 수 없습니다:\n{e}")
    
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
        """AI를 사용한 이미지 분석"""
        if not self.current_image_path or not self.ai_analyzer:
            return
        
        # 로딩 메시지 표시
        self.ai_text.delete(1.0, tk.END)
        self.ai_text.insert(tk.END, "AI 분석 중... 잠시만 기다려주세요.")
        self.status_bar.config(text="AI 분석 중...")
        
        # 백그라운드에서 분석 실행
        threading.Thread(target=self._run_ai_analysis, daemon=True).start()
    
    def _run_ai_analysis(self):
        """백그라운드에서 AI 분석 실행"""
        try:
            # EXIF 정보 확인
            exif_data = self.exif_reader.read_exif(self.current_image_path)
            has_exif = bool(exif_data and any(tag in exif_data for tag in ['ExposureTime', 'FNumber', 'ISO']))
            has_location = bool(exif_data and 'GPSInfo' in exif_data)
            
            # AI 분석 실행
            result = self.ai_analyzer.analyze_image(
                self.current_image_path, 
                has_exif=has_exif,
                has_location=has_location
            )
            
            # 결과를 메인 스레드에서 표시
            self.root.after(0, self._display_ai_results, result)
            
        except Exception as e:
            logger.error(f"AI 분석 오류: {e}")
            self.root.after(0, lambda: self.ai_text.insert(tk.END, f"\n\n오류: {e}"))
            self.root.after(0, lambda: self.status_bar.config(text="AI 분석 실패"))
    
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
            self.ai_text.insert(tk.END, "\n")
        
        # 위치 정보
        if result.get('location'):
            self.ai_text.insert(tk.END, "📍 추정 촬영 위치:\n")
            self.ai_text.insert(tk.END, f"  {result['location']}\n")
        
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