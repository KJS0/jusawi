# EXIF 데이터 시각화 유틸리티
import logging
from typing import Dict, List, Union, Optional, Any, Tuple
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter, defaultdict
from utils import sort_key

class ExifGraphGenerator:
    """EXIF 데이터 시각화 그래프 생성 클래스"""
    
    def __init__(self, theme: str = 'default'):
        """
        초기화
        
        Args:
            theme (str, optional): 차트 테마 ('default', 'dark', 'light'). 기본값 'default'
        """
        self.theme = theme
        self._setup_theme()
    
    def _setup_theme(self):
        """테마에 따른 Matplotlib 스타일 설정"""
        if self.theme == 'dark':
            plt.style.use('dark_background')
        elif self.theme == 'light':
            plt.style.use('seaborn-v0_8-whitegrid')
        else:
            plt.style.use('default')
    
    def plot_frequency(self, data: Dict[str, List[str]], title_suffix: str = "빈도", 
                      figsize: Optional[Tuple[int, int]] = None, 
                      save_path: Optional[str] = None):
        """
        EXIF 값 빈도 그래프를 생성합니다.
        
        Args:
            data (Dict[str, List[str]]): 그래프로 표시할 데이터 (태그별 값 리스트)
            title_suffix (str, optional): 그래프 제목 접미사. 기본값 "빈도"
            figsize (Tuple[int, int], optional): 그래프 크기. 기본값 None (자동)
            save_path (str, optional): 그래프 저장 경로. 기본값 None (표시만)
        """
        for tag, items in data.items():
            if not items:
                continue
                
            # 빈도 계산
            counts = Counter(items)
            
            # 데이터 정렬 (태그별 맞춤 정렬)
            sorted_items = sorted(counts.items(), key=lambda x: sort_key(x[0]))
            
            # 데이터가 너무 많으면 상위 항목만 표시
            if len(sorted_items) > 20:
                logging.info(f"{tag}: 데이터가 너무 많아 상위 20개 항목만 표시합니다.")
                sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:20]
            
            labels, vals = zip(*sorted_items)
            
            # 그래프 크기 자동 조정 (항목이 많으면 더 넓게)
            if figsize is None:
                width = max(6, min(12, len(labels) * 0.6))
                height = 4 if len(labels) < 10 else 6
                figsize = (width, height)
            
            # 그래프 생성
            plt.figure(figsize=figsize)
            
            # 바 차트 생성
            bars = plt.bar(labels, vals, color='royalblue', alpha=0.8)
            
            # 막대 위에 값 표시
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        str(int(height)), ha='center', va='bottom')
            
            # 그래프 스타일링
            plt.title(f"{tag} {title_suffix}")
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # 그래프 저장 또는 표시
            if save_path:
                plt.savefig(f"{save_path}_{tag}.png", dpi=150)
                plt.close()
            else:
                plt.show()
    
    def plot_histogram(self, data: Dict[str, List[Union[int, float]]], 
                     bins: int = 10, figsize: Optional[Tuple[int, int]] = None,
                     save_path: Optional[str] = None):
        """
        수치형 EXIF 데이터의 히스토그램을 생성합니다.
        
        Args:
            data (Dict[str, List[Union[int, float]]]): 히스토그램으로 표시할 수치 데이터
            bins (int, optional): 히스토그램 구간 수. 기본값 10
            figsize (Tuple[int, int], optional): 그래프 크기. 기본값 None
            save_path (str, optional): 그래프 저장 경로. 기본값 None
        """
        for tag, values in data.items():
            if not values:
                continue
                
            # 수치형 데이터로 변환
            try:
                numeric_values = [float(v) if isinstance(v, (int, float, str)) else 0 for v in values]
            except (ValueError, TypeError):
                logging.warning(f"{tag}: 수치형 데이터로 변환할 수 없습니다.")
                continue
            
            # 그래프 생성
            if figsize is None:
                figsize = (8, 5)
                
            plt.figure(figsize=figsize)
            
            # 히스토그램 생성
            plt.hist(numeric_values, bins=bins, alpha=0.7, color='royalblue', edgecolor='black')
            
            # 평균선 표시
            mean_val = np.mean(numeric_values)
            plt.axvline(mean_val, color='r', linestyle='dashed', linewidth=1, label=f'평균: {mean_val:.2f}')
            
            # 그래프 스타일링
            plt.title(f"{tag} 분포")
            plt.xlabel(tag)
            plt.ylabel("빈도")
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # 그래프 저장 또는 표시
            if save_path:
                plt.savefig(f"{save_path}_{tag}_hist.png", dpi=150)
                plt.close()
            else:
                plt.show()
    
    def plot_combined_charts(self, data: Dict[str, Dict[str, List[Any]]], 
                          figsize: Tuple[int, int] = (12, 10),
                          save_path: Optional[str] = None):
        """
        여러 EXIF 데이터를 하나의 그림에 결합하여 표시합니다.
        
        Args:
            data (Dict): 다양한 차트에 표시할 데이터
            figsize (Tuple[int, int], optional): 그래프 크기. 기본값 (12, 10)
            save_path (str, optional): 그래프 저장 경로. 기본값 None
        """
        # 데이터 검증
        if not data:
            logging.warning("시각화할 데이터가 없습니다.")
            return
            
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        plt.subplots_adjust(hspace=0.4, wspace=0.3)
        
        # 각 차트 생성
        chart_positions = {
            'FNumber': (0, 0, '조리개 값 분포'),
            'FocalLength': (0, 1, '초점 거리 분포'),
            'ExposureTime': (1, 0, '노출 시간 분포'),
            'ISOSpeedRatings': (1, 1, 'ISO 감도 분포')
        }
        
        # 차트 생성
        for tag, (row, col, title) in chart_positions.items():
            ax = axes[row, col]
            
            if tag in data:
                items = data[tag]
                
                # 빈도 계산
                counts = Counter(items)
                
                # 정렬
                sorted_items = sorted(counts.items(), key=lambda x: sort_key(x[0]))
                
                if sorted_items:
                    labels, vals = zip(*sorted_items)
                    
                    # 바 차트 생성
                    bars = ax.bar(labels, vals, color='royalblue', alpha=0.7)
                    
                    # 차트 스타일링
                    ax.set_title(title)
                    ax.tick_params(axis='x', rotation=45)
                    
                    # 값이 너무 많으면 일부만 표시
                    if len(labels) > 8:
                        every_nth = len(labels) // 8 + 1
                        for n, label in enumerate(ax.xaxis.get_ticklabels()):
                            if n % every_nth != 0:
                                label.set_visible(False)
            else:
                ax.text(0.5, 0.5, f"{tag} 데이터 없음", 
                       ha='center', va='center', transform=ax.transAxes)
        
        # 전체 타이틀 설정
        plt.suptitle("EXIF 데이터 종합 분석", fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.96])  # rect는 suptitle 공간 확보
        
        # 그래프 저장 또는 표시
        if save_path:
            plt.savefig(save_path, dpi=150)
            plt.close()
        else:
            plt.show()


# 편의 함수 (기존 코드와의 호환성 유지)
def plot_frequency(data: Dict[str, List[str]]):
    """
    EXIF 값 빈도 그래프를 생성합니다 (편의 함수).
    
    Args:
        data (Dict[str, List[str]]): 그래프로 표시할 데이터 (태그별 값 리스트)
    """
    generator = ExifGraphGenerator()
    generator.plot_frequency(data)
