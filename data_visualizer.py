"""
데이터 시각화 모듈
캡스톤 디자인 프로젝트 - 촬영 데이터 시각화
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from pathlib import Path
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

logger = logging.getLogger(__name__)

class DataVisualizer:
    """EXIF 데이터 시각화 클래스"""
    
    def __init__(self):
        """시각화 도구 초기화"""
        self._setup_matplotlib()
        self.color_palette = sns.color_palette("husl", 10)
        
    def _setup_matplotlib(self):
        """Matplotlib 한글 폰트 설정"""
        try:
            # 한글 폰트 설정
            plt.rcParams['font.family'] = 'DejaVu Sans'
            plt.rcParams['axes.unicode_minus'] = False
            
            # 스타일 설정
            plt.style.use('seaborn-v0_8')
            sns.set_palette("husl")
            
        except Exception as e:
            logger.warning(f"폰트 설정 오류: {e}")
    
    def create_aperture_histogram(self, stats: Dict[str, Any], parent: tk.Widget) -> tk.Frame:
        """
        조리개 사용 빈도 히스토그램 생성
        
        Args:
            stats: 촬영 통계 데이터
            parent: 부모 위젯
            
        Returns:
            차트가 포함된 프레임
        """
        frame = tk.Frame(parent)
        
        if 'aperture_usage' not in stats or not stats['aperture_usage']:
            tk.Label(frame, text="조리개 데이터가 없습니다.", 
                    font=('Arial', 12)).pack(pady=20)
            return frame
        
        try:
            fig = Figure(figsize=(8, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            aperture_data = stats['aperture_usage']
            apertures = list(aperture_data.keys())
            counts = list(aperture_data.values())
            
            # 조리개 값 정렬 (f/1.4, f/2.8, f/4.0 등)
            try:
                aperture_nums = [float(a.replace('f/', '')) for a in apertures]
                sorted_data = sorted(zip(aperture_nums, apertures, counts))
                apertures = [item[1] for item in sorted_data]
                counts = [item[2] for item in sorted_data]
            except ValueError:
                pass  # 정렬 실패 시 원본 순서 유지
            
            bars = ax.bar(apertures, counts, color=self.color_palette[0], alpha=0.7)
            ax.set_title('조리개 사용 빈도', fontsize=14, fontweight='bold')
            ax.set_xlabel('조리개 값', fontsize=12)
            ax.set_ylabel('사용 횟수', fontsize=12)
            
            # 막대 위에 값 표시
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{count}', ha='center', va='bottom')
            
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            fig.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            logger.error(f"조리개 히스토그램 생성 오류: {e}")
            tk.Label(frame, text=f"차트 생성 오류: {e}", 
                    font=('Arial', 10), fg='red').pack(pady=20)
        
        return frame
    
    def create_iso_distribution(self, stats: Dict[str, Any], parent: tk.Widget) -> tk.Frame:
        """
        ISO 감도 분포 차트 생성
        
        Args:
            stats: 촬영 통계 데이터
            parent: 부모 위젯
            
        Returns:
            차트가 포함된 프레임
        """
        frame = tk.Frame(parent)
        
        if 'iso_usage' not in stats or not stats['iso_usage']:
            tk.Label(frame, text="ISO 데이터가 없습니다.", 
                    font=('Arial', 12)).pack(pady=20)
            return frame
        
        try:
            fig = Figure(figsize=(8, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            iso_data = stats['iso_usage']
            isos = list(iso_data.keys())
            counts = list(iso_data.values())
            
            # ISO 값 정렬
            try:
                sorted_data = sorted(zip(isos, counts), key=lambda x: int(x[0]))
                isos = [str(item[0]) for item in sorted_data]
                counts = [item[1] for item in sorted_data]
            except (ValueError, TypeError):
                pass  # 정렬 실패 시 원본 순서 유지
            
            # 파이 차트로 표시
            wedges, texts, autotexts = ax.pie(counts, labels=isos, autopct='%1.1f%%',
                                             colors=self.color_palette[:len(isos)])
            ax.set_title('ISO 감도 사용 분포', fontsize=14, fontweight='bold')
            
            # 범례 추가
            ax.legend(wedges, [f'ISO {iso}: {count}회' for iso, count in zip(isos, counts)],
                     title="ISO 사용 현황", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
            
            fig.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            logger.error(f"ISO 분포 차트 생성 오류: {e}")
            tk.Label(frame, text=f"차트 생성 오류: {e}", 
                    font=('Arial', 10), fg='red').pack(pady=20)
        
        return frame
    
    def create_focal_length_chart(self, stats: Dict[str, Any], parent: tk.Widget) -> tk.Frame:
        """
        초점거리 사용 패턴 차트 생성
        
        Args:
            stats: 촬영 통계 데이터
            parent: 부모 위젯
            
        Returns:
            차트가 포함된 프레임
        """
        frame = tk.Frame(parent)
        
        if 'focal_length_usage' not in stats or not stats['focal_length_usage']:
            tk.Label(frame, text="초점거리 데이터가 없습니다.", 
                    font=('Arial', 12)).pack(pady=20)
            return frame
        
        try:
            fig = Figure(figsize=(10, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            focal_data = stats['focal_length_usage']
            focals = list(focal_data.keys())
            counts = list(focal_data.values())
            
            # 초점거리 값 정렬
            try:
                focal_nums = [float(f.replace('mm', '').strip()) for f in focals]
                sorted_data = sorted(zip(focal_nums, focals, counts))
                focals = [item[1] for item in sorted_data]
                counts = [item[2] for item in sorted_data]
            except ValueError:
                pass  # 정렬 실패 시 원본 순서 유지
            
            bars = ax.bar(range(len(focals)), counts, color=self.color_palette[2], alpha=0.7)
            ax.set_title('초점거리 사용 패턴', fontsize=14, fontweight='bold')
            ax.set_xlabel('초점거리', fontsize=12)
            ax.set_ylabel('사용 횟수', fontsize=12)
            ax.set_xticks(range(len(focals)))
            ax.set_xticklabels(focals, rotation=45, ha='right')
            
            # 막대 위에 값 표시
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{count}', ha='center', va='bottom')
            
            fig.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            logger.error(f"초점거리 차트 생성 오류: {e}")
            tk.Label(frame, text=f"차트 생성 오류: {e}", 
                    font=('Arial', 10), fg='red').pack(pady=20)
        
        return frame
    
    def create_shooting_time_chart(self, stats: Dict[str, Any], parent: tk.Widget) -> tk.Frame:
        """
        촬영 시간대 분석 차트 생성
        
        Args:
            stats: 촬영 통계 데이터
            parent: 부모 위젯
            
        Returns:
            차트가 포함된 프레임
        """
        frame = tk.Frame(parent)
        
        if 'shooting_hours' not in stats or not stats['shooting_hours']:
            tk.Label(frame, text="촬영 시간 데이터가 없습니다.", 
                    font=('Arial', 12)).pack(pady=20)
            return frame
        
        try:
            fig = Figure(figsize=(10, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            hour_data = stats['shooting_hours']
            
            # 24시간 전체 데이터 준비 (없는 시간대는 0으로)
            hours = list(range(24))
            counts = [hour_data.get(hour, 0) for hour in hours]
            
            # 선 그래프로 표시
            ax.plot(hours, counts, marker='o', linewidth=2, markersize=6,
                   color=self.color_palette[3])
            ax.fill_between(hours, counts, alpha=0.3, color=self.color_palette[3])
            
            ax.set_title('시간대별 촬영 빈도', fontsize=14, fontweight='bold')
            ax.set_xlabel('시간 (24시간)', fontsize=12)
            ax.set_ylabel('촬영 횟수', fontsize=12)
            ax.set_xticks(range(0, 24, 2))
            ax.grid(True, alpha=0.3)
            
            # 최대 촬영 시간대 표시
            max_hour = max(hour_data, key=hour_data.get)
            max_count = hour_data[max_hour]
            ax.annotate(f'최대: {max_hour}시 ({max_count}회)',
                       xy=(max_hour, max_count), xytext=(max_hour+2, max_count+1),
                       arrowprops=dict(arrowstyle='->', color='red'),
                       fontsize=10, color='red')
            
            fig.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            logger.error(f"촬영 시간 차트 생성 오류: {e}")
            tk.Label(frame, text=f"차트 생성 오류: {e}", 
                    font=('Arial', 10), fg='red').pack(pady=20)
        
        return frame
    
    def create_camera_usage_chart(self, stats: Dict[str, Any], parent: tk.Widget) -> tk.Frame:
        """
        카메라 사용 빈도 차트 생성
        
        Args:
            stats: 촬영 통계 데이터
            parent: 부모 위젯
            
        Returns:
            차트가 포함된 프레임
        """
        frame = tk.Frame(parent)
        
        if 'camera_usage' not in stats or not stats['camera_usage']:
            tk.Label(frame, text="카메라 데이터가 없습니다.", 
                    font=('Arial', 12)).pack(pady=20)
            return frame
        
        try:
            fig = Figure(figsize=(10, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            camera_data = stats['camera_usage']
            cameras = list(camera_data.keys())
            counts = list(camera_data.values())
            
            # 수평 막대 그래프
            y_pos = np.arange(len(cameras))
            bars = ax.barh(y_pos, counts, color=self.color_palette[4], alpha=0.7)
            
            ax.set_title('카메라 모델별 사용 빈도', fontsize=14, fontweight='bold')
            ax.set_xlabel('사용 횟수', fontsize=12)
            ax.set_ylabel('카메라 모델', fontsize=12)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(cameras)
            
            # 막대 끝에 값 표시
            for i, (bar, count) in enumerate(zip(bars, counts)):
                width = bar.get_width()
                ax.text(width + 0.1, bar.get_y() + bar.get_height()/2.,
                       f'{count}', ha='left', va='center')
            
            fig.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            logger.error(f"카메라 사용 차트 생성 오류: {e}")
            tk.Label(frame, text=f"차트 생성 오류: {e}", 
                    font=('Arial', 10), fg='red').pack(pady=20)
        
        return frame
    
    def create_settings_correlation_chart(self, df: pd.DataFrame, parent: tk.Widget) -> tk.Frame:
        """
        촬영 설정 간 상관관계 분석 차트
        
        Args:
            df: EXIF 데이터 DataFrame
            parent: 부모 위젯
            
        Returns:
            차트가 포함된 프레임
        """
        frame = tk.Frame(parent)
        
        if df.empty:
            tk.Label(frame, text="분석할 데이터가 없습니다.", 
                    font=('Arial', 12)).pack(pady=20)
            return frame
        
        try:
            fig = Figure(figsize=(10, 8), dpi=100)
            ax = fig.add_subplot(111)
            
            # 숫자형 데이터만 추출
            numeric_cols = []
            numeric_data = {}
            
            # ISO 값 추출
            if 'ISOSpeedRatings' in df.columns:
                iso_values = pd.to_numeric(df['ISOSpeedRatings'], errors='coerce')
                if not iso_values.isna().all():
                    numeric_data['ISO'] = iso_values
                    numeric_cols.append('ISO')
            
            # 조리개 값 추출 (f/2.8 -> 2.8)
            if 'FNumber' in df.columns:
                try:
                    f_values = df['FNumber'].str.replace('f/', '').astype(float)
                    numeric_data['Aperture'] = f_values
                    numeric_cols.append('Aperture')
                except:
                    pass
            
            # 초점거리 값 추출 (50mm -> 50)
            if 'FocalLength' in df.columns:
                try:
                    focal_values = df['FocalLength'].str.replace('mm', '').astype(float)
                    numeric_data['FocalLength'] = focal_values
                    numeric_cols.append('FocalLength')
                except:
                    pass
            
            if len(numeric_cols) < 2:
                tk.Label(frame, text="상관관계 분석을 위한 충분한 숫자 데이터가 없습니다.", 
                        font=('Arial', 12)).pack(pady=20)
                return frame
            
            # 상관관계 매트릭스 생성
            corr_df = pd.DataFrame(numeric_data)
            correlation_matrix = corr_df.corr()
            
            # 히트맵 생성
            im = ax.imshow(correlation_matrix, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
            
            # 축 설정
            ax.set_xticks(range(len(numeric_cols)))
            ax.set_yticks(range(len(numeric_cols)))
            ax.set_xticklabels(numeric_cols)
            ax.set_yticklabels(numeric_cols)
            
            # 상관계수 값 표시
            for i in range(len(numeric_cols)):
                for j in range(len(numeric_cols)):
                    text = ax.text(j, i, f'{correlation_matrix.iloc[i, j]:.2f}',
                                 ha="center", va="center", color="black", fontweight='bold')
            
            ax.set_title('촬영 설정 간 상관관계', fontsize=14, fontweight='bold')
            
            # 컬러바 추가
            cbar = fig.colorbar(im, ax=ax)
            cbar.set_label('상관계수', rotation=270, labelpad=15)
            
            fig.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            logger.error(f"상관관계 차트 생성 오류: {e}")
            tk.Label(frame, text=f"차트 생성 오류: {e}", 
                    font=('Arial', 10), fg='red').pack(pady=20)
        
        return frame
    
    def save_chart(self, fig: Figure, filename: str, output_dir: Path = None):
        """
        차트를 파일로 저장
        
        Args:
            fig: Matplotlib Figure 객체
            filename: 저장할 파일명
            output_dir: 출력 디렉토리
        """
        try:
            if output_dir is None:
                output_dir = Path.cwd() / 'charts'
            
            output_dir.mkdir(exist_ok=True)
            filepath = output_dir / filename
            
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
            logger.info(f"차트 저장 완료: {filepath}")
            
        except Exception as e:
            logger.error(f"차트 저장 오류: {e}")
            raise 