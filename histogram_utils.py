# 이미지 히스토그램 처리 및 표시 모듈
import numpy as np
import tkinter as tk
from tkinter import ttk
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import logging

class HistogramViewer:
    """이미지 히스토그램 뷰어 클래스"""
    
    def __init__(self, image_path, parent=None, title="히스토그램 분석"):
        """
        히스토그램 뷰어 초기화
        
        Args:
            image_path (str): 이미지 파일 경로
            parent (tk.Tk, optional): 부모 윈도우 (없으면 새 윈도우 생성)
            title (str, optional): 윈도우 제목
        """
        self.image_path = image_path
        self.title = title
        
        # 이미지 로드 및 배열 변환
        try:
            self.img = Image.open(image_path)
            self.arr = np.array(self.img)
        except Exception as e:
            raise IOError(f"이미지를 히스토그램 분석용으로 로드할 수 없습니다: {e}")
        
        # 윈도우 생성
        self.parent = parent
        self.win = tk.Toplevel(parent)
        self.win.title(title)
        self.win.geometry("580x480")
        self.win.minsize(520, 400)
        
        # 탭 컨트롤 생성
        self.tab_control = ttk.Notebook(self.win)
        self.basic_tab = ttk.Frame(self.tab_control)
        self.advanced_tab = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.basic_tab, text='기본 히스토그램')
        self.tab_control.add(self.advanced_tab, text='고급 분석')
        self.tab_control.pack(expand=1, fill='both')
        
        # 히스토그램 데이터 계산
        self._compute_histograms()
        
        # UI 구성 - 기본 탭
        self._build_basic_ui()
        
        # UI 구성 - 고급 탭
        self._build_advanced_ui()
    
    def _compute_histograms(self):
        """히스토그램 데이터 계산"""
        # 회색조 이미지 또는 RGB 이미지 확인
        if self.arr.ndim == 3 and self.arr.shape[2] >= 3:
            # 회색조 휘도 계산 (BT.709 표준)
            self.gray = np.dot(self.arr[...,:3], [0.2126, 0.7152, 0.0722]).astype(np.uint8)
            
            # 채널별 히스토그램
            self.h_r, _ = np.histogram(self.arr[...,0].flatten(), bins=256, range=(0,255))
            self.h_g, _ = np.histogram(self.arr[...,1].flatten(), bins=256, range=(0,255))
            self.h_b, _ = np.histogram(self.arr[...,2].flatten(), bins=256, range=(0,255))
            
            # 알파 채널 확인
            if self.arr.shape[2] == 4:
                self.h_a, _ = np.histogram(self.arr[...,3].flatten(), bins=256, range=(0,255))
            else:
                self.h_a = None
        else:
            # 이미 회색조 이미지인 경우
            self.gray = self.arr
            self.h_r = self.h_g = self.h_b = self.h_a = None
        
        # 회색조 히스토그램
        self.h_gray, self.bins = np.histogram(self.gray.flatten(), bins=256, range=(0,255))
        
        # 이미지 통계 계산
        self.mean = np.mean(self.gray)
        self.median = np.median(self.gray)
        self.std = np.std(self.gray)
        self.min = np.min(self.gray)
        self.max = np.max(self.gray)
    
    def _build_basic_ui(self):
        """기본 히스토그램 UI 구성"""
        # 캔버스 생성
        canvas = tk.Canvas(self.basic_tab, width=560, height=440, bg='white')
        canvas.pack(fill='both', expand=True)
        
        # 히스토그램 그리기
        colors = {
            'brightness': ('gray', '휘도'),
            'red': ('red', '빨강'),
            'green': ('green', '초록'),
            'blue': ('blue', '파랑')
        }
        
        # 화면 분할에 사용할 파라미터
        margin = 20
        width, height = 250, 180
        
        # 각 히스토그램 그리기
        self._draw_histogram(canvas, self.h_gray, margin, margin, width, height, 'gray', '휘도')
        
        if self.h_r is not None:
            self._draw_histogram(canvas, self.h_r, margin + width + 20, margin, width, height, 'red', '빨강')
            self._draw_histogram(canvas, self.h_g, margin, margin + height + 20, width, height, 'green', '초록')
            self._draw_histogram(canvas, self.h_b, margin + width + 20, margin + height + 20, width, height, 'blue', '파랑')
        
        # 통계 정보 표시
        stats_x = margin + width + 20
        stats_y = margin + height * 2 + 40
        self._draw_statistics(canvas, stats_x, stats_y)
    
    def _build_advanced_ui(self):
        """고급 분석 UI 구성"""
        # Matplotlib 사용 (더 정교한 그래프)
        fig = plt.Figure(figsize=(10, 8), dpi=80)
        fig.subplots_adjust(hspace=0.4, wspace=0.3)
        
        # 휘도 히스토그램 (더 자세한 통계 포함)
        ax1 = fig.add_subplot(2, 1, 1)
        ax1.hist(self.gray.flatten(), bins=256, range=(0,255), color='gray', alpha=0.8)
        ax1.set_title("휘도 히스토그램")
        ax1.axvline(self.mean, color='r', linestyle='dashed', linewidth=1, label=f'평균: {self.mean:.1f}')
        ax1.axvline(self.median, color='g', linestyle='dashed', linewidth=1, label=f'중앙값: {self.median:.1f}')
        ax1.legend()
        
        # RGB 통합 히스토그램
        if self.h_r is not None:
            ax2 = fig.add_subplot(2, 1, 2)
            bins = np.arange(256)
            ax2.fill_between(bins, 0, self.h_r, color='r', alpha=0.3, label='빨강')
            ax2.fill_between(bins, 0, self.h_g, color='g', alpha=0.3, label='초록')
            ax2.fill_between(bins, 0, self.h_b, color='b', alpha=0.3, label='파랑')
            ax2.legend()
            ax2.set_title("RGB 채널 히스토그램")
        
        # Matplotlib 캔버스를 Tkinter에 임베드
        canvas = FigureCanvasTkAgg(fig, self.advanced_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def _draw_histogram(self, canvas, hist, x, y, w, h, color, label):
        """
        히스토그램 그리기
        
        Args:
            canvas: Tkinter 캔버스
            hist: 히스토그램 데이터
            x, y: 시작 좌표
            w, h: 너비와 높이
            color: 색상
            label: 라벨
        """
        if hist is None:
            return
            
        # 최대값 계산
        maxv = hist.max()
        if maxv == 0:  # 0으로 나누기 방지
            maxv = 1
        
        # 히스토그램 막대 그리기
        for i, v in enumerate(hist):
            x0 = x + i * (w / 256)
            y0 = y + h
            x1 = x0 + (w / 256)
            y1 = y + h - (v / maxv) * h
            canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline='')
        
        # 라벨 그리기
        canvas.create_text(x, y - 15, anchor='nw', text=label, fill='black', font=('Arial', 10, 'bold'))
        
        # 축 그리기
        canvas.create_line(x, y+h, x+w, y+h, fill='black')  # X축
        canvas.create_line(x, y, x, y+h, fill='black')     # Y축
        
        # 눈금 그리기 (0, 128, 255)
        for i, val in enumerate([0, 128, 255]):
            tick_x = x + (val/255) * w
            canvas.create_line(tick_x, y+h, tick_x, y+h+5, fill='black')
            canvas.create_text(tick_x, y+h+5, text=str(val), anchor='n', font=('Arial', 8))
    
    def _draw_statistics(self, canvas, x, y):
        """이미지 통계 정보 표시"""
        stats = [
            f"평균 밝기: {self.mean:.1f}",
            f"중앙값: {self.median:.1f}",
            f"표준 편차: {self.std:.1f}",
            f"최소값: {self.min}",
            f"최대값: {self.max}",
            f"다이나믹 레인지: {self.max - self.min}"
        ]
        
        canvas.create_text(x, y, anchor='nw', text="이미지 통계", fill='black', font=('Arial', 12, 'bold'))
        
        for i, stat in enumerate(stats):
            canvas.create_text(x, y + 25 + i*20, anchor='nw', text=stat, fill='black', font=('Arial', 10))


def show_histogram(image_path):
    """
    이미지 히스토그램을 보여주는 함수
    
    Args:
        image_path (str): 이미지 파일 경로
    
    Returns:
        HistogramViewer: 히스토그램 뷰어 인스턴스
    """
    try:
        viewer = HistogramViewer(image_path)
        return viewer
    except Exception as e:
        logging.error(f"히스토그램 생성 오류: {e}")
        raise 