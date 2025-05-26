"""
메인 GUI 윈도우
캡스톤 디자인 프로젝트 - EXIF 분석 도구 메인 인터페이스
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
from PIL import Image, ImageTk

from exif_analyzer import ExifAnalyzer
from data_visualizer import DataVisualizer
from recommendation import RecommendationEngine

logger = logging.getLogger(__name__)

class MainWindow:
    """메인 애플리케이션 윈도우"""
    
    def __init__(self, root: tk.Tk):
        """
        메인 윈도우 초기화
        
        Args:
            root: Tkinter 루트 윈도우
        """
        self.root = root
        self.setup_window()
        
        # 핵심 컴포넌트 초기화
        self.exif_analyzer = ExifAnalyzer()
        self.visualizer = DataVisualizer()
        self.recommendation_engine = RecommendationEngine()
        
        # 데이터 저장
        self.current_data = pd.DataFrame()
        self.current_stats = {}
        self.current_patterns = {}
        self.current_recommendations = {}
        
        # GUI 컴포넌트 생성
        self.create_menu()
        self.create_main_interface()
        self.create_status_bar()
        
        logger.info("메인 윈도우 초기화 완료")
    
    def setup_window(self):
        """윈도우 기본 설정"""
        self.root.title("📸 주.사.위")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # 아이콘 설정 (선택사항)
        try:
            # self.root.iconbitmap('icon.ico')  # 아이콘 파일이 있다면
            pass
        except:
            pass
        
        # 윈도우 종료 이벤트
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_menu(self):
        """메뉴바 생성"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 파일 메뉴
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="파일", menu=file_menu)
        file_menu.add_command(label="이미지 파일 열기", command=self.open_single_file)
        file_menu.add_command(label="폴더 열기", command=self.open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="결과 저장", command=self.save_results)
        file_menu.add_separator()
        file_menu.add_command(label="종료", command=self.on_closing)
        
        # 분석 메뉴
        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="분석", menu=analysis_menu)
        analysis_menu.add_command(label="EXIF 데이터 추출", command=self.extract_exif_data)
        analysis_menu.add_command(label="촬영 패턴 분석", command=self.analyze_patterns)
        analysis_menu.add_command(label="추천 생성", command=self.generate_recommendations)
        
        # 시각화 메뉴
        viz_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="시각화", menu=viz_menu)
        viz_menu.add_command(label="조리개 히스토그램", command=self.show_aperture_chart)
        viz_menu.add_command(label="ISO 분포", command=self.show_iso_chart)
        viz_menu.add_command(label="초점거리 패턴", command=self.show_focal_chart)
        viz_menu.add_command(label="촬영 시간 분석", command=self.show_time_chart)
        viz_menu.add_command(label="카메라 사용 빈도", command=self.show_camera_chart)
        
        # 도움말 메뉴
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="도움말", menu=help_menu)
        help_menu.add_command(label="사용법", command=self.show_help)
        help_menu.add_command(label="정보", command=self.show_about)
    
    def create_main_interface(self):
        """메인 인터페이스 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 좌측 패널 (파일 목록 및 컨트롤)
        left_panel = ttk.Frame(main_frame, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # 우측 패널 (결과 표시)
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.create_left_panel(left_panel)
        self.create_right_panel(right_panel)
    
    def create_left_panel(self, parent: ttk.Frame):
        """좌측 패널 생성"""
        # 파일 선택 섹션
        file_frame = ttk.LabelFrame(parent, text="📁 파일 선택", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(file_frame, text="이미지 파일 열기", 
                  command=self.open_single_file, width=20).pack(pady=2)
        ttk.Button(file_frame, text="폴더 열기", 
                  command=self.open_folder, width=20).pack(pady=2)
        
        # 파일 목록
        list_frame = ttk.LabelFrame(parent, text="📋 선택된 파일", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 리스트박스와 스크롤바
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(list_container, yscrollcommand=scrollbar.set)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        # 분석 버튼
        analysis_frame = ttk.LabelFrame(parent, text="🔍 분석 실행", padding=10)
        analysis_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(analysis_frame, text="EXIF 분석 시작", 
                  command=self.start_analysis, width=20).pack(pady=2)
        ttk.Button(analysis_frame, text="결과 저장", 
                  command=self.save_results, width=20).pack(pady=2)
        
        # 진행률 표시
        progress_frame = ttk.LabelFrame(parent, text="📊 진행 상황", padding=10)
        progress_frame.pack(fill=tk.X)
        
        self.progress_var = tk.StringVar(value="대기 중...")
        ttk.Label(progress_frame, textvariable=self.progress_var).pack()
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
    
    def create_right_panel(self, parent: ttk.Frame):
        """우측 패널 생성"""
        # 탭 노트북
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 탭들 생성
        self.create_overview_tab()
        self.create_statistics_tab()
        self.create_visualization_tab()
        self.create_recommendations_tab()
        self.create_raw_data_tab()
    
    def create_overview_tab(self):
        """개요 탭 생성"""
        overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(overview_frame, text="📋 개요")
        
        # 스크롤 가능한 텍스트 위젯
        self.overview_text = scrolledtext.ScrolledText(
            overview_frame, wrap=tk.WORD, height=20, font=('Arial', 11)
        )
        self.overview_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 초기 텍스트
        welcome_text = """
🎯 EXIF 데이터 분석 및 촬영 습관 개선 도구에 오신 것을 환영합니다!

📸 주요 기능:
• EXIF 데이터 자동 추출 및 분석
• 촬영 습관 패턴 분석
• 개인화된 촬영 설정 추천
• 다양한 시각화 차트 제공
• 촬영 기법 개선 제안

🚀 시작하기:
1. 좌측 패널에서 "이미지 파일 열기" 또는 "폴더 열기"를 클릭
2. 분석할 이미지 파일들을 선택
3. "EXIF 분석 시작" 버튼을 클릭하여 분석 실행
4. 각 탭에서 분석 결과를 확인

💡 팁:
• 더 정확한 분석을 위해 다양한 촬영 조건의 이미지를 포함시키세요
• 최소 10장 이상의 이미지를 분석하는 것을 권장합니다
• JPEG 파일에 EXIF 데이터가 포함되어 있어야 합니다

📊 캡스톤 디자인 목표:
• EXIF 데이터 분석률 95% 이상 달성
• 1초당 10장 이상의 이미지 처리 성능
• 사용자 만족도 80% 이상의 추천 정확도
        """
        
        self.overview_text.insert(tk.END, welcome_text)
        self.overview_text.config(state=tk.DISABLED)
    
    def create_statistics_tab(self):
        """통계 탭 생성"""
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="📊 통계")
        
        self.stats_text = scrolledtext.ScrolledText(
            stats_frame, wrap=tk.WORD, height=20, font=('Consolas', 10)
        )
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def create_visualization_tab(self):
        """시각화 탭 생성"""
        viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(viz_frame, text="📈 시각화")
        
        # 차트 선택 프레임
        chart_select_frame = ttk.Frame(viz_frame)
        chart_select_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(chart_select_frame, text="차트 선택:").pack(side=tk.LEFT)
        
        self.chart_var = tk.StringVar(value="조리개 히스토그램")
        chart_combo = ttk.Combobox(chart_select_frame, textvariable=self.chart_var,
                                  values=["조리개 히스토그램", "ISO 분포", "초점거리 패턴", 
                                         "촬영 시간 분석", "카메라 사용 빈도", "설정 상관관계"],
                                  state="readonly")
        chart_combo.pack(side=tk.LEFT, padx=(10, 0))
        chart_combo.bind('<<ComboboxSelected>>', self.on_chart_selected)
        
        # 차트 표시 프레임
        self.chart_frame = ttk.Frame(viz_frame)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    def create_recommendations_tab(self):
        """추천 탭 생성"""
        rec_frame = ttk.Frame(self.notebook)
        self.notebook.add(rec_frame, text="💡 추천")
        
        self.recommendations_text = scrolledtext.ScrolledText(
            rec_frame, wrap=tk.WORD, height=20, font=('Arial', 11)
        )
        self.recommendations_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def create_raw_data_tab(self):
        """원본 데이터 탭 생성"""
        data_frame = ttk.Frame(self.notebook)
        self.notebook.add(data_frame, text="📄 원본 데이터")
        
        # 트리뷰로 테이블 형태 표시
        tree_frame = ttk.Frame(data_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 스크롤바
        tree_scroll_y = ttk.Scrollbar(tree_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 트리뷰
        self.data_tree = ttk.Treeview(tree_frame, 
                                     yscrollcommand=tree_scroll_y.set,
                                     xscrollcommand=tree_scroll_x.set)
        self.data_tree.pack(fill=tk.BOTH, expand=True)
        
        tree_scroll_y.config(command=self.data_tree.yview)
        tree_scroll_x.config(command=self.data_tree.xview)
    
    def create_status_bar(self):
        """상태바 생성"""
        self.status_var = tk.StringVar(value="준비")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def open_single_file(self):
        """단일 이미지 파일 열기"""
        filetypes = [
            ("이미지 파일", "*.jpg *.jpeg *.tiff *.tif"),
            ("JPEG 파일", "*.jpg *.jpeg"),
            ("TIFF 파일", "*.tiff *.tif"),
            ("모든 파일", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="이미지 파일 선택",
            filetypes=filetypes
        )
        
        if filename:
            self.file_listbox.delete(0, tk.END)
            self.file_listbox.insert(tk.END, filename)
            self.status_var.set(f"파일 선택됨: {Path(filename).name}")
            logger.info(f"단일 파일 선택: {filename}")
    
    def open_folder(self):
        """폴더 열기"""
        folder_path = filedialog.askdirectory(title="이미지 폴더 선택")
        
        if folder_path:
            self.load_images_from_folder(folder_path)
    
    def load_images_from_folder(self, folder_path: str):
        """폴더에서 이미지 파일 로드"""
        try:
            folder = Path(folder_path)
            image_extensions = {'.jpg', '.jpeg', '.tiff', '.tif'}
            
            image_files = []
            for ext in image_extensions:
                image_files.extend(folder.glob(f"*{ext}"))
                image_files.extend(folder.glob(f"*{ext.upper()}"))
            
            if not image_files:
                messagebox.showwarning("경고", "선택한 폴더에 이미지 파일이 없습니다.")
                return
            
            # 파일 목록 업데이트
            self.file_listbox.delete(0, tk.END)
            for file_path in sorted(image_files):
                self.file_listbox.insert(tk.END, str(file_path))
            
            self.status_var.set(f"{len(image_files)}개 이미지 파일 로드됨")
            logger.info(f"폴더에서 {len(image_files)}개 파일 로드: {folder_path}")
            
        except Exception as e:
            logger.error(f"폴더 로드 오류: {e}")
            messagebox.showerror("오류", f"폴더를 로드할 수 없습니다:\\n{e}")
    
    def start_analysis(self):
        """분석 시작"""
        if self.file_listbox.size() == 0:
            messagebox.showwarning("경고", "분석할 파일을 먼저 선택해주세요.")
            return
        
        # 백그라운드에서 분석 실행
        threading.Thread(target=self.run_analysis, daemon=True).start()
    
    def run_analysis(self):
        """분석 실행 (백그라운드)"""
        try:
            # 진행률 표시 시작
            self.root.after(0, self.start_progress)
            
            # 파일 목록 가져오기
            file_paths = [Path(self.file_listbox.get(i)) 
                         for i in range(self.file_listbox.size())]
            
            self.root.after(0, lambda: self.progress_var.set("EXIF 데이터 추출 중..."))
            
            # EXIF 데이터 추출
            self.current_data = self.exif_analyzer.analyze_batch(file_paths)
            
            if self.current_data.empty:
                self.root.after(0, lambda: messagebox.showwarning(
                    "경고", "EXIF 데이터를 추출할 수 있는 파일이 없습니다."))
                return
            
            self.root.after(0, lambda: self.progress_var.set("통계 분석 중..."))
            
            # 통계 분석
            self.current_stats = self.exif_analyzer.get_shooting_statistics(self.current_data)
            
            self.root.after(0, lambda: self.progress_var.set("촬영 패턴 분석 중..."))
            
            # 촬영 패턴 분석
            self.current_patterns = self.recommendation_engine.analyze_shooting_patterns(self.current_data)
            
            self.root.after(0, lambda: self.progress_var.set("추천 생성 중..."))
            
            # 추천 생성
            self.current_recommendations = self.recommendation_engine.generate_recommendations(
                self.current_patterns, self.current_data)
            
            # UI 업데이트
            self.root.after(0, self.update_results)
            self.root.after(0, self.stop_progress)
            self.root.after(0, lambda: self.status_var.set(
                f"분석 완료: {len(self.current_data)}개 파일 처리됨"))
            
        except Exception as e:
            logger.error(f"분석 오류: {e}")
            self.root.after(0, lambda: messagebox.showerror("오류", f"분석 중 오류가 발생했습니다:\\n{e}"))
            self.root.after(0, self.stop_progress)
    
    def start_progress(self):
        """진행률 표시 시작"""
        self.progress_bar.start()
    
    def stop_progress(self):
        """진행률 표시 중지"""
        self.progress_bar.stop()
        self.progress_var.set("분석 완료")
    
    def update_results(self):
        """결과 업데이트"""
        try:
            self.update_overview()
            self.update_statistics()
            self.update_recommendations()
            self.update_raw_data()
            self.update_visualization()
            
        except Exception as e:
            logger.error(f"결과 업데이트 오류: {e}")
    
    def update_overview(self):
        """개요 탭 업데이트"""
        if self.current_data.empty:
            return
        
        overview_text = f"""
📊 분석 결과 요약

📁 처리된 파일: {len(self.current_data)}개
📸 주요 카메라: {self.current_stats.get('camera_usage', {}).get(list(self.current_stats.get('camera_usage', {}).keys())[0], 'N/A') if self.current_stats.get('camera_usage') else 'N/A'}
🎯 촬영 스타일: {self.current_patterns.get('shooting_style', 'N/A')}
⭐ 숙련도: {self.current_patterns.get('skill_level', 'N/A')}
📈 설정 다양성: {self.current_patterns.get('diversity_score', 0):.2f}

🔍 주요 설정 분석:
"""
        
        # 선호 설정 정보
        preferred = self.current_patterns.get('preferred_settings', {})
        if 'aperture' in preferred:
            overview_text += f"• 가장 많이 사용하는 조리개: {preferred['aperture'].get('most_used', 'N/A')}\n"
        if 'iso' in preferred:
            overview_text += f"• 가장 많이 사용하는 ISO: {preferred['iso'].get('most_used', 'N/A')}\n"
        if 'focal_length' in preferred:
            overview_text += f"• 가장 많이 사용하는 초점거리: {preferred['focal_length'].get('most_used', 'N/A')}\n"
        
        # 시간 패턴
        time_patterns = self.current_patterns.get('time_patterns', {})
        if time_patterns:
            peak_hour = time_patterns.get('peak_hour')
            if peak_hour is not None:
                overview_text += f"• 주요 촬영 시간: {peak_hour}시\n"
        
        overview_text += f"""

💡 빠른 개선 제안:
"""
        
        # 추천 요약
        improvements = self.current_recommendations.get('improvements', [])
        for i, improvement in enumerate(improvements[:3], 1):
            overview_text += f"{i}. {improvement}\n"
        
        self.overview_text.config(state=tk.NORMAL)
        self.overview_text.delete(1.0, tk.END)
        self.overview_text.insert(tk.END, overview_text)
        self.overview_text.config(state=tk.DISABLED)
    
    def update_statistics(self):
        """통계 탭 업데이트"""
        if not self.current_stats:
            return
        
        stats_text = "📊 상세 촬영 통계\n" + "="*50 + "\n\n"
        
        # 카메라 사용 통계
        if 'camera_usage' in self.current_stats:
            stats_text += "📷 카메라 사용 빈도:\n"
            for camera, count in self.current_stats['camera_usage'].items():
                percentage = (count / len(self.current_data)) * 100
                stats_text += f"  • {camera}: {count}회 ({percentage:.1f}%)\n"
            stats_text += "\n"
        
        # 조리개 사용 통계
        if 'aperture_usage' in self.current_stats:
            stats_text += "🔍 조리개 사용 빈도:\n"
            for aperture, count in list(self.current_stats['aperture_usage'].items())[:10]:
                percentage = (count / len(self.current_data)) * 100
                stats_text += f"  • {aperture}: {count}회 ({percentage:.1f}%)\n"
            stats_text += "\n"
        
        # ISO 사용 통계
        if 'iso_usage' in self.current_stats:
            stats_text += "📈 ISO 사용 빈도:\n"
            for iso, count in list(self.current_stats['iso_usage'].items())[:10]:
                percentage = (count / len(self.current_data)) * 100
                stats_text += f"  • ISO {iso}: {count}회 ({percentage:.1f}%)\n"
            stats_text += "\n"
        
        # 초점거리 사용 통계
        if 'focal_length_usage' in self.current_stats:
            stats_text += "📏 초점거리 사용 빈도:\n"
            for focal, count in list(self.current_stats['focal_length_usage'].items())[:10]:
                percentage = (count / len(self.current_data)) * 100
                stats_text += f"  • {focal}: {count}회 ({percentage:.1f}%)\n"
            stats_text += "\n"
        
        # 시간대별 촬영 통계
        if 'shooting_hours' in self.current_stats:
            stats_text += "🕐 시간대별 촬영 빈도:\n"
            sorted_hours = sorted(self.current_stats['shooting_hours'].items())
            for hour, count in sorted_hours:
                percentage = (count / sum(self.current_stats['shooting_hours'].values())) * 100
                stats_text += f"  • {hour:02d}시: {count}회 ({percentage:.1f}%)\n"
            stats_text += "\n"
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, stats_text)
    
    def update_recommendations(self):
        """추천 탭 업데이트"""
        if not self.current_recommendations:
            return
        
        rec_text = "💡 개인화된 촬영 개선 추천\n" + "="*50 + "\n\n"
        
        # 촬영 스타일 기반 추천
        style_rec = self.current_recommendations.get('style_recommendations', {})
        if style_rec:
            shooting_style = self.current_patterns.get('shooting_style', '일반 촬영')
            rec_text += f"🎯 {shooting_style} 최적 설정:\n"
            
            if 'aperture' in style_rec:
                rec_text += f"  • 권장 조리개: {', '.join(style_rec['aperture'])}\n"
            if 'iso' in style_rec:
                rec_text += f"  • 권장 ISO: {', '.join(map(str, style_rec['iso']))}\n"
            if 'focal_length' in style_rec:
                rec_text += f"  • 권장 초점거리: {', '.join(style_rec['focal_length'])}\n"
            
            if 'tips' in style_rec:
                rec_text += "  💡 팁:\n"
                for tip in style_rec['tips']:
                    rec_text += f"    - {tip}\n"
            rec_text += "\n"
        
        # 개선 제안
        improvements = self.current_recommendations.get('improvements', [])
        if improvements:
            rec_text += "🔧 촬영 습관 개선 제안:\n"
            for i, improvement in enumerate(improvements, 1):
                rec_text += f"  {i}. {improvement}\n"
            rec_text += "\n"
        
        # 새로운 기법 제안
        techniques = self.current_recommendations.get('new_techniques', [])
        if techniques:
            rec_text += "🚀 새로운 촬영 기법:\n"
            for i, technique in enumerate(techniques, 1):
                rec_text += f"  {i}. {technique}\n"
            rec_text += "\n"
        
        # 장비 추천
        equipment = self.current_recommendations.get('equipment_suggestions', [])
        if equipment:
            rec_text += "📷 장비 추천:\n"
            for i, item in enumerate(equipment, 1):
                rec_text += f"  {i}. {item}\n"
            rec_text += "\n"
        
        # 학습 자료 추천
        resources = self.current_recommendations.get('learning_resources', [])
        if resources:
            rec_text += "📚 추천 학습 자료:\n"
            for i, resource in enumerate(resources, 1):
                rec_text += f"  {i}. {resource}\n"
            rec_text += "\n"
        
        self.recommendations_text.delete(1.0, tk.END)
        self.recommendations_text.insert(tk.END, rec_text)
    
    def update_raw_data(self):
        """원본 데이터 탭 업데이트"""
        if self.current_data.empty:
            return
        
        # 기존 데이터 삭제
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
        
        # 컬럼 설정
        columns = list(self.current_data.columns)
        self.data_tree['columns'] = columns
        self.data_tree['show'] = 'headings'
        
        # 헤더 설정
        for col in columns:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=100, minwidth=50)
        
        # 데이터 삽입
        for index, row in self.current_data.iterrows():
            values = [str(row[col]) if pd.notna(row[col]) else '' for col in columns]
            self.data_tree.insert('', tk.END, values=values)
    
    def update_visualization(self):
        """시각화 탭 업데이트"""
        self.show_selected_chart()
    
    def on_chart_selected(self, event=None):
        """차트 선택 이벤트"""
        self.show_selected_chart()
    
    def show_selected_chart(self):
        """선택된 차트 표시"""
        if not self.current_stats and not self.current_data.empty:
            return
        
        chart_type = self.chart_var.get()
        
        # 기존 차트 제거
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        try:
            if chart_type == "조리개 히스토그램":
                chart_frame = self.visualizer.create_aperture_histogram(self.current_stats, self.chart_frame)
            elif chart_type == "ISO 분포":
                chart_frame = self.visualizer.create_iso_distribution(self.current_stats, self.chart_frame)
            elif chart_type == "초점거리 패턴":
                chart_frame = self.visualizer.create_focal_length_chart(self.current_stats, self.chart_frame)
            elif chart_type == "촬영 시간 분석":
                chart_frame = self.visualizer.create_shooting_time_chart(self.current_stats, self.chart_frame)
            elif chart_type == "카메라 사용 빈도":
                chart_frame = self.visualizer.create_camera_usage_chart(self.current_stats, self.chart_frame)
            elif chart_type == "설정 상관관계":
                chart_frame = self.visualizer.create_settings_correlation_chart(self.current_data, self.chart_frame)
            
            chart_frame.pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            logger.error(f"차트 생성 오류: {e}")
            error_label = ttk.Label(self.chart_frame, text=f"차트 생성 오류: {e}")
            error_label.pack(pady=20)
    
    # 메뉴 이벤트 핸들러들
    def extract_exif_data(self):
        """EXIF 데이터 추출 (메뉴)"""
        self.start_analysis()
    
    def analyze_patterns(self):
        """패턴 분석 (메뉴)"""
        if self.current_data.empty:
            messagebox.showwarning("경고", "먼저 EXIF 데이터를 추출해주세요.")
            return
        self.notebook.select(1)  # 통계 탭으로 이동
    
    def generate_recommendations(self):
        """추천 생성 (메뉴)"""
        if not self.current_recommendations:
            messagebox.showwarning("경고", "먼저 분석을 완료해주세요.")
            return
        self.notebook.select(3)  # 추천 탭으로 이동
    
    def show_aperture_chart(self):
        """조리개 차트 표시"""
        self.chart_var.set("조리개 히스토그램")
        self.notebook.select(2)  # 시각화 탭으로 이동
        self.show_selected_chart()
    
    def show_iso_chart(self):
        """ISO 차트 표시"""
        self.chart_var.set("ISO 분포")
        self.notebook.select(2)
        self.show_selected_chart()
    
    def show_focal_chart(self):
        """초점거리 차트 표시"""
        self.chart_var.set("초점거리 패턴")
        self.notebook.select(2)
        self.show_selected_chart()
    
    def show_time_chart(self):
        """시간 차트 표시"""
        self.chart_var.set("촬영 시간 분석")
        self.notebook.select(2)
        self.show_selected_chart()
    
    def show_camera_chart(self):
        """카메라 차트 표시"""
        self.chart_var.set("카메라 사용 빈도")
        self.notebook.select(2)
        self.show_selected_chart()
    
    def save_results(self):
        """결과 저장"""
        if self.current_data.empty:
            messagebox.showwarning("경고", "저장할 데이터가 없습니다.")
            return
        
        try:
            # 저장할 파일 선택
            filename = filedialog.asksaveasfilename(
                title="결과 저장",
                defaultextension=".xlsx",
                filetypes=[
                    ("Excel 파일", "*.xlsx"),
                    ("CSV 파일", "*.csv"),
                    ("모든 파일", "*.*")
                ]
            )
            
            if filename:
                file_path = Path(filename)
                
                if file_path.suffix.lower() == '.xlsx':
                    # Excel 파일로 저장
                    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                        self.current_data.to_excel(writer, sheet_name='EXIF_Data', index=False)
                        
                        # 통계 데이터도 별도 시트로 저장
                        if self.current_stats:
                            stats_df = pd.DataFrame([
                                {'Category': k, 'Data': str(v)} 
                                for k, v in self.current_stats.items()
                            ])
                            stats_df.to_excel(writer, sheet_name='Statistics', index=False)
                else:
                    # CSV 파일로 저장
                    self.current_data.to_csv(filename, index=False, encoding='utf-8-sig')
                
                messagebox.showinfo("완료", f"결과가 저장되었습니다:\\n{filename}")
                logger.info(f"결과 저장 완료: {filename}")
                
        except Exception as e:
            logger.error(f"저장 오류: {e}")
            messagebox.showerror("오류", f"저장 중 오류가 발생했습니다:\\n{e}")
    
    def show_help(self):
        """도움말 표시"""
        help_text = """
📖 EXIF 분석 도구 사용법

🚀 시작하기:
1. "파일" → "이미지 파일 열기" 또는 "폴더 열기"로 분석할 이미지 선택
2. 좌측 패널의 "EXIF 분석 시작" 버튼 클릭
3. 분석 완료 후 각 탭에서 결과 확인

📊 탭 설명:
• 개요: 분석 결과 요약 및 주요 정보
• 통계: 상세한 촬영 설정 사용 빈도
• 시각화: 다양한 차트로 데이터 시각화
• 추천: 개인화된 촬영 개선 제안
• 원본 데이터: 추출된 EXIF 데이터 테이블

💡 팁:
• JPEG 파일에 EXIF 데이터가 포함되어야 분석 가능
• 최소 10장 이상의 이미지 권장
• 다양한 촬영 조건의 이미지 포함 시 더 정확한 분석
        """
        
        messagebox.showinfo("사용법", help_text)
    
    def show_about(self):
        """정보 표시"""
        about_text = """
📸 주.사.위

🎯 캡스톤 디자인 프로젝트
개발자: 김진수

📋 주요 기능:
• EXIF 데이터 자동 추출 및 분석
• 촬영 습관 패턴 분석
• AI 기반 개인화 추천
• 다양한 시각화 차트
• 촬영 기법 개선 제안

© 2025 Kim Jinsoo
        """
        
        messagebox.showinfo("정보", about_text)
    
    def on_closing(self):
        """윈도우 종료 이벤트"""
        if messagebox.askokcancel("종료", "프로그램을 종료하시겠습니까?"):
            logger.info("애플리케이션 종료")
            self.root.destroy() 