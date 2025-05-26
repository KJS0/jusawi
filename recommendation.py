"""
촬영 설정 추천 시스템 모듈
캡스톤 디자인 프로젝트 - AI 기반 촬영 습관 개선 추천
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

class RecommendationEngine:
    """촬영 설정 추천 엔진"""
    
    def __init__(self):
        """추천 엔진 초기화"""
        self.scaler = StandardScaler()
        self.kmeans = None
        self.user_clusters = None
        
        # 촬영 상황별 권장 설정
        self.situation_recommendations = {
            '인물 촬영': {
                'aperture': ['f/1.4', 'f/1.8', 'f/2.8'],
                'iso': [100, 200, 400],
                'focal_length': ['85mm', '105mm', '135mm'],
                'tips': ['배경 흐림을 위해 큰 조리개 사용', '자연스러운 피부톤을 위해 낮은 ISO 권장']
            },
            '풍경 촬영': {
                'aperture': ['f/8', 'f/11', 'f/16'],
                'iso': [100, 200],
                'focal_length': ['14mm', '24mm', '35mm'],
                'tips': ['선명한 전체 화면을 위해 작은 조리개 사용', '삼각대 사용으로 낮은 ISO 유지']
            },
            '스포츠 촬영': {
                'aperture': ['f/2.8', 'f/4', 'f/5.6'],
                'iso': [800, 1600, 3200],
                'focal_length': ['70mm', '200mm', '300mm'],
                'tips': ['빠른 셔터 속도를 위해 높은 ISO 허용', '망원 렌즈로 피사체에 집중']
            },
            '야간 촬영': {
                'aperture': ['f/1.4', 'f/2.8', 'f/4'],
                'iso': [1600, 3200, 6400],
                'focal_length': ['24mm', '35mm', '50mm'],
                'tips': ['충분한 빛 확보를 위해 큰 조리개 사용', '삼각대 필수, 노이즈 감소 기능 활용']
            },
            '매크로 촬영': {
                'aperture': ['f/8', 'f/11', 'f/16'],
                'iso': [100, 200, 400],
                'focal_length': ['60mm', '100mm', '180mm'],
                'tips': ['피사계 심도 확보를 위해 작은 조리개', '매크로 전용 렌즈 또는 접사링 사용']
            }
        }
        
        # 카메라별 최적 ISO 범위
        self.camera_iso_limits = {
            'Canon': {'crop': 1600, 'full_frame': 3200},
            'Nikon': {'crop': 1600, 'full_frame': 3200},
            'Sony': {'crop': 1600, 'full_frame': 6400},
            'Fujifilm': {'crop': 1600, 'full_frame': 3200},
            'Olympus': {'crop': 800, 'full_frame': 1600}
        }
    
    def analyze_shooting_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        사용자의 촬영 패턴 분석
        
        Args:
            df: EXIF 데이터 DataFrame
            
        Returns:
            촬영 패턴 분석 결과
        """
        if df.empty:
            return {}
        
        logger.info("촬영 패턴 분석 시작")
        
        patterns = {}
        
        try:
            # 가장 많이 사용하는 설정 분석
            patterns['preferred_settings'] = self._get_preferred_settings(df)
            
            # 촬영 스타일 분류
            patterns['shooting_style'] = self._classify_shooting_style(df)
            
            # 설정 다양성 분석
            patterns['diversity_score'] = self._calculate_diversity_score(df)
            
            # 시간대별 촬영 패턴
            patterns['time_patterns'] = self._analyze_time_patterns(df)
            
            # 기술적 숙련도 평가
            patterns['skill_level'] = self._assess_skill_level(df)
            
            logger.info("촬영 패턴 분석 완료")
            return patterns
            
        except Exception as e:
            logger.error(f"촬영 패턴 분석 오류: {e}")
            return {}
    
    def _get_preferred_settings(self, df: pd.DataFrame) -> Dict[str, Any]:
        """선호하는 촬영 설정 분석"""
        preferred = {}
        
        # 가장 많이 사용하는 조리개
        if 'FNumber' in df.columns:
            aperture_counts = df['FNumber'].value_counts()
            preferred['aperture'] = {
                'most_used': aperture_counts.index[0] if len(aperture_counts) > 0 else None,
                'usage_rate': aperture_counts.iloc[0] / len(df) if len(aperture_counts) > 0 else 0,
                'variety': len(aperture_counts)
            }
        
        # 가장 많이 사용하는 ISO
        if 'ISOSpeedRatings' in df.columns:
            iso_counts = df['ISOSpeedRatings'].value_counts()
            preferred['iso'] = {
                'most_used': iso_counts.index[0] if len(iso_counts) > 0 else None,
                'usage_rate': iso_counts.iloc[0] / len(df) if len(iso_counts) > 0 else 0,
                'variety': len(iso_counts)
            }
        
        # 가장 많이 사용하는 초점거리
        if 'FocalLength' in df.columns:
            focal_counts = df['FocalLength'].value_counts()
            preferred['focal_length'] = {
                'most_used': focal_counts.index[0] if len(focal_counts) > 0 else None,
                'usage_rate': focal_counts.iloc[0] / len(df) if len(focal_counts) > 0 else 0,
                'variety': len(focal_counts)
            }
        
        return preferred
    
    def _classify_shooting_style(self, df: pd.DataFrame) -> str:
        """촬영 스타일 분류"""
        try:
            # 조리개 값 분석
            aperture_analysis = self._analyze_aperture_preference(df)
            
            # 초점거리 분석
            focal_analysis = self._analyze_focal_length_preference(df)
            
            # ISO 분석
            iso_analysis = self._analyze_iso_preference(df)
            
            # 스타일 점수 계산
            style_scores = {
                '인물 촬영': 0,
                '풍경 촬영': 0,
                '스포츠 촬영': 0,
                '야간 촬영': 0,
                '매크로 촬영': 0
            }
            
            # 조리개 기반 점수
            if aperture_analysis['prefers_wide']:
                style_scores['인물 촬영'] += 2
                style_scores['야간 촬영'] += 1
            elif aperture_analysis['prefers_narrow']:
                style_scores['풍경 촬영'] += 2
                style_scores['매크로 촬영'] += 1
            
            # 초점거리 기반 점수
            if focal_analysis['prefers_telephoto']:
                style_scores['인물 촬영'] += 1
                style_scores['스포츠 촬영'] += 2
            elif focal_analysis['prefers_wide_angle']:
                style_scores['풍경 촬영'] += 2
            
            # ISO 기반 점수
            if iso_analysis['uses_high_iso']:
                style_scores['스포츠 촬영'] += 1
                style_scores['야간 촬영'] += 2
            elif iso_analysis['uses_low_iso']:
                style_scores['풍경 촬영'] += 1
                style_scores['매크로 촬영'] += 1
            
            # 가장 높은 점수의 스타일 반환
            return max(style_scores, key=style_scores.get)
            
        except Exception as e:
            logger.warning(f"촬영 스타일 분류 오류: {e}")
            return '일반 촬영'
    
    def _analyze_aperture_preference(self, df: pd.DataFrame) -> Dict[str, bool]:
        """조리개 선호도 분석"""
        if 'FNumber' not in df.columns:
            return {'prefers_wide': False, 'prefers_narrow': False}
        
        try:
            # f/ 제거하고 숫자만 추출
            aperture_values = []
            for aperture in df['FNumber'].dropna():
                try:
                    value = float(str(aperture).replace('f/', ''))
                    aperture_values.append(value)
                except ValueError:
                    continue
            
            if not aperture_values:
                return {'prefers_wide': False, 'prefers_narrow': False}
            
            avg_aperture = np.mean(aperture_values)
            wide_count = sum(1 for a in aperture_values if a <= 2.8)
            narrow_count = sum(1 for a in aperture_values if a >= 8.0)
            
            total_count = len(aperture_values)
            wide_ratio = wide_count / total_count
            narrow_ratio = narrow_count / total_count
            
            return {
                'prefers_wide': wide_ratio > 0.5,
                'prefers_narrow': narrow_ratio > 0.5
            }
            
        except Exception:
            return {'prefers_wide': False, 'prefers_narrow': False}
    
    def _analyze_focal_length_preference(self, df: pd.DataFrame) -> Dict[str, bool]:
        """초점거리 선호도 분석"""
        if 'FocalLength' not in df.columns:
            return {'prefers_wide_angle': False, 'prefers_telephoto': False}
        
        try:
            focal_values = []
            for focal in df['FocalLength'].dropna():
                try:
                    value = float(str(focal).replace('mm', ''))
                    focal_values.append(value)
                except ValueError:
                    continue
            
            if not focal_values:
                return {'prefers_wide_angle': False, 'prefers_telephoto': False}
            
            wide_count = sum(1 for f in focal_values if f <= 35)
            tele_count = sum(1 for f in focal_values if f >= 85)
            
            total_count = len(focal_values)
            wide_ratio = wide_count / total_count
            tele_ratio = tele_count / total_count
            
            return {
                'prefers_wide_angle': wide_ratio > 0.5,
                'prefers_telephoto': tele_ratio > 0.5
            }
            
        except Exception:
            return {'prefers_wide_angle': False, 'prefers_telephoto': False}
    
    def _analyze_iso_preference(self, df: pd.DataFrame) -> Dict[str, bool]:
        """ISO 선호도 분석"""
        if 'ISOSpeedRatings' not in df.columns:
            return {'uses_low_iso': False, 'uses_high_iso': False}
        
        try:
            iso_values = pd.to_numeric(df['ISOSpeedRatings'], errors='coerce').dropna()
            
            if iso_values.empty:
                return {'uses_low_iso': False, 'uses_high_iso': False}
            
            low_count = sum(1 for iso in iso_values if iso <= 400)
            high_count = sum(1 for iso in iso_values if iso >= 1600)
            
            total_count = len(iso_values)
            low_ratio = low_count / total_count
            high_ratio = high_count / total_count
            
            return {
                'uses_low_iso': low_ratio > 0.6,
                'uses_high_iso': high_ratio > 0.3
            }
            
        except Exception:
            return {'uses_low_iso': False, 'uses_high_iso': False}
    
    def _calculate_diversity_score(self, df: pd.DataFrame) -> float:
        """설정 다양성 점수 계산"""
        try:
            diversity_scores = []
            
            # 조리개 다양성
            if 'FNumber' in df.columns:
                unique_apertures = df['FNumber'].nunique()
                total_apertures = len(df['FNumber'].dropna())
                if total_apertures > 0:
                    diversity_scores.append(unique_apertures / total_apertures)
            
            # ISO 다양성
            if 'ISOSpeedRatings' in df.columns:
                unique_isos = df['ISOSpeedRatings'].nunique()
                total_isos = len(df['ISOSpeedRatings'].dropna())
                if total_isos > 0:
                    diversity_scores.append(unique_isos / total_isos)
            
            # 초점거리 다양성
            if 'FocalLength' in df.columns:
                unique_focals = df['FocalLength'].nunique()
                total_focals = len(df['FocalLength'].dropna())
                if total_focals > 0:
                    diversity_scores.append(unique_focals / total_focals)
            
            return np.mean(diversity_scores) if diversity_scores else 0.0
            
        except Exception:
            return 0.0
    
    def _analyze_time_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """시간대별 촬영 패턴 분석"""
        if 'DateTime' not in df.columns:
            return {}
        
        try:
            df_time = df[df['DateTime'].notna()].copy()
            if df_time.empty:
                return {}
            
            df_time['Hour'] = pd.to_datetime(df_time['DateTime']).dt.hour
            hour_counts = df_time['Hour'].value_counts()
            
            # 주요 촬영 시간대 분류
            morning_count = sum(hour_counts.get(h, 0) for h in range(6, 12))
            afternoon_count = sum(hour_counts.get(h, 0) for h in range(12, 18))
            evening_count = sum(hour_counts.get(h, 0) for h in range(18, 22))
            night_count = sum(hour_counts.get(h, 0) for h in list(range(22, 24)) + list(range(0, 6)))
            
            total = morning_count + afternoon_count + evening_count + night_count
            
            if total == 0:
                return {}
            
            return {
                'morning_ratio': morning_count / total,
                'afternoon_ratio': afternoon_count / total,
                'evening_ratio': evening_count / total,
                'night_ratio': night_count / total,
                'peak_hour': hour_counts.index[0] if len(hour_counts) > 0 else None
            }
            
        except Exception:
            return {}
    
    def _assess_skill_level(self, df: pd.DataFrame) -> str:
        """기술적 숙련도 평가"""
        try:
            skill_indicators = []
            
            # 수동 모드 사용률
            if 'ExposureMode' in df.columns:
                manual_count = sum(1 for mode in df['ExposureMode'].dropna() if '수동' in str(mode))
                manual_ratio = manual_count / len(df['ExposureMode'].dropna()) if len(df['ExposureMode'].dropna()) > 0 else 0
                skill_indicators.append(manual_ratio)
            
            # 설정 다양성
            diversity = self._calculate_diversity_score(df)
            skill_indicators.append(diversity)
            
            # 극한 설정 사용 (매우 높은 ISO, 매우 작은 조리개 등)
            extreme_usage = self._calculate_extreme_settings_usage(df)
            skill_indicators.append(extreme_usage)
            
            if not skill_indicators:
                return '초급'
            
            avg_skill = np.mean(skill_indicators)
            
            if avg_skill >= 0.7:
                return '고급'
            elif avg_skill >= 0.4:
                return '중급'
            else:
                return '초급'
                
        except Exception:
            return '초급'
    
    def _calculate_extreme_settings_usage(self, df: pd.DataFrame) -> float:
        """극한 설정 사용률 계산"""
        try:
            extreme_count = 0
            total_count = 0
            
            # 높은 ISO 사용 (3200 이상)
            if 'ISOSpeedRatings' in df.columns:
                iso_values = pd.to_numeric(df['ISOSpeedRatings'], errors='coerce').dropna()
                if not iso_values.empty:
                    extreme_count += sum(1 for iso in iso_values if iso >= 3200)
                    total_count += len(iso_values)
            
            # 매우 작은 조리개 사용 (f/11 이상)
            if 'FNumber' in df.columns:
                for aperture in df['FNumber'].dropna():
                    try:
                        value = float(str(aperture).replace('f/', ''))
                        if value >= 11:
                            extreme_count += 1
                        total_count += 1
                    except ValueError:
                        continue
            
            return extreme_count / total_count if total_count > 0 else 0.0
            
        except Exception:
            return 0.0
    
    def generate_recommendations(self, patterns: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """
        개인화된 촬영 설정 추천 생성
        
        Args:
            patterns: 촬영 패턴 분석 결과
            df: EXIF 데이터 DataFrame
            
        Returns:
            추천 결과
        """
        logger.info("개인화된 추천 생성 시작")
        
        recommendations = {}
        
        try:
            # 촬영 스타일 기반 추천
            shooting_style = patterns.get('shooting_style', '일반 촬영')
            recommendations['style_recommendations'] = self.situation_recommendations.get(
                shooting_style, self.situation_recommendations['인물 촬영']
            )
            
            # 개선 제안
            recommendations['improvements'] = self._generate_improvement_suggestions(patterns, df)
            
            # 새로운 기법 제안
            recommendations['new_techniques'] = self._suggest_new_techniques(patterns)
            
            # 장비 추천
            recommendations['equipment_suggestions'] = self._suggest_equipment(patterns, df)
            
            # 학습 자료 추천
            recommendations['learning_resources'] = self._recommend_learning_resources(patterns)
            
            logger.info("개인화된 추천 생성 완료")
            return recommendations
            
        except Exception as e:
            logger.error(f"추천 생성 오류: {e}")
            return {}
    
    def _generate_improvement_suggestions(self, patterns: Dict[str, Any], df: pd.DataFrame) -> List[str]:
        """개선 제안 생성"""
        suggestions = []
        
        try:
            # 다양성 부족 시 제안
            diversity = patterns.get('diversity_score', 0)
            if diversity < 0.3:
                suggestions.append("다양한 촬영 설정을 시도해보세요. 새로운 조리개 값이나 ISO 설정을 실험해보는 것이 좋습니다.")
            
            # 선호 설정 기반 제안
            preferred = patterns.get('preferred_settings', {})
            
            # 조리개 관련 제안
            if 'aperture' in preferred:
                aperture_variety = preferred['aperture'].get('variety', 0)
                if aperture_variety < 3:
                    suggestions.append("조리개 설정을 더 다양하게 사용해보세요. 배경 흐림 효과와 피사계 심도를 조절할 수 있습니다.")
            
            # ISO 관련 제안
            if 'iso' in preferred:
                most_used_iso = preferred['iso'].get('most_used')
                if most_used_iso and int(most_used_iso) > 1600:
                    suggestions.append("높은 ISO 사용이 많습니다. 삼각대나 더 밝은 렌즈 사용을 고려해보세요.")
            
            # 시간대 관련 제안
            time_patterns = patterns.get('time_patterns', {})
            if time_patterns.get('night_ratio', 0) > 0.5:
                suggestions.append("야간 촬영이 많습니다. 노이즈 감소 기법과 장노출 촬영을 학습해보세요.")
            
            return suggestions[:5]  # 최대 5개 제안
            
        except Exception:
            return ["촬영 기법을 다양화하고 새로운 설정을 시도해보세요."]
    
    def _suggest_new_techniques(self, patterns: Dict[str, Any]) -> List[str]:
        """새로운 기법 제안"""
        techniques = []
        
        skill_level = patterns.get('skill_level', '초급')
        shooting_style = patterns.get('shooting_style', '일반 촬영')
        
        if skill_level == '초급':
            techniques.extend([
                "조리개 우선 모드(A/Av)로 피사계 심도 조절 연습",
                "셔터 우선 모드(S/Tv)로 움직임 표현 연습",
                "ISO 자동 설정의 최대값 조절하기"
            ])
        elif skill_level == '중급':
            techniques.extend([
                "수동 모드에서의 노출 삼각형 마스터하기",
                "히스토그램을 활용한 정확한 노출 측정",
                "브라케팅을 이용한 HDR 촬영"
            ])
        else:  # 고급
            techniques.extend([
                "포커스 스태킹 기법으로 피사계 심도 확장",
                "장노출을 이용한 창의적 표현",
                "플래시와 자연광의 조화"
            ])
        
        # 촬영 스타일별 추가 기법
        if shooting_style == '인물 촬영':
            techniques.append("자연스러운 포즈 유도와 감정 표현 포착")
        elif shooting_style == '풍경 촬영':
            techniques.append("골든 아워와 블루 아워 활용하기")
        elif shooting_style == '스포츠 촬영':
            techniques.append("연속 촬영과 예측 포커스 활용")
        
        return techniques[:4]  # 최대 4개 기법
    
    def _suggest_equipment(self, patterns: Dict[str, Any], df: pd.DataFrame) -> List[str]:
        """장비 추천"""
        suggestions = []
        
        try:
            shooting_style = patterns.get('shooting_style', '일반 촬영')
            
            # 촬영 스타일별 장비 추천
            if shooting_style == '인물 촬영':
                suggestions.extend([
                    "85mm f/1.8 또는 f/1.4 인물 전용 렌즈",
                    "반사판과 디퓨저로 자연스러운 조명 연출"
                ])
            elif shooting_style == '풍경 촬영':
                suggestions.extend([
                    "견고한 삼각대로 안정적인 촬영",
                    "ND 필터로 장노출 효과 연출",
                    "초광각 렌즈(14-24mm)로 웅장한 풍경 담기"
                ])
            elif shooting_style == '스포츠 촬영':
                suggestions.extend([
                    "70-200mm f/2.8 망원 줌 렌즈",
                    "빠른 연속 촬영이 가능한 카메라 바디"
                ])
            elif shooting_style == '야간 촬영':
                suggestions.extend([
                    "f/1.4 대구경 렌즈로 더 많은 빛 확보",
                    "견고한 삼각대는 필수"
                ])
            
            # ISO 사용 패턴 기반 추천
            preferred = patterns.get('preferred_settings', {})
            if 'iso' in preferred:
                most_used_iso = preferred['iso'].get('most_used')
                if most_used_iso and int(most_used_iso) > 3200:
                    suggestions.append("풀프레임 카메라로 고감도 성능 향상")
            
            return suggestions[:3]  # 최대 3개 추천
            
        except Exception:
            return ["촬영 목적에 맞는 렌즈 선택이 중요합니다."]
    
    def _recommend_learning_resources(self, patterns: Dict[str, Any]) -> List[str]:
        """학습 자료 추천"""
        resources = []
        
        skill_level = patterns.get('skill_level', '초급')
        shooting_style = patterns.get('shooting_style', '일반 촬영')
        
        # 스킬 레벨별 학습 자료
        if skill_level == '초급':
            resources.extend([
                "카메라 기본 조작법과 노출 삼각형 이해",
                "구도의 기본 원칙 (삼분할 법칙, 황금비율)",
                "빛의 방향과 질감 이해하기"
            ])
        elif skill_level == '중급':
            resources.extend([
                "고급 구도 기법과 시각적 균형",
                "색채 이론과 색온도 조절",
                "후보정 기초 (라이트룸, 포토샵)"
            ])
        else:  # 고급
            resources.extend([
                "창의적 표현 기법과 개인 스타일 개발",
                "상업 사진과 포트폴리오 구성",
                "고급 후보정 기법과 워크플로우"
            ])
        
        # 촬영 스타일별 전문 자료
        style_resources = {
            '인물 촬영': "인물 사진의 조명과 포즈 연출법",
            '풍경 촬영': "자연광 활용과 계절별 풍경 촬영",
            '스포츠 촬영': "액션 포착과 연속 촬영 기법",
            '야간 촬영': "야경과 천체 사진 촬영법",
            '매크로 촬영': "접사 촬영과 미시 세계 표현"
        }
        
        if shooting_style in style_resources:
            resources.append(style_resources[shooting_style])
        
        return resources[:4]  # 최대 4개 자료 