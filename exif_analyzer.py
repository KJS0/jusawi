"""
EXIF 데이터 분석 모듈
캡스톤 디자인 프로젝트 - 핵심 분석 엔진
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import pandas as pd
import numpy as np
from PIL import Image, ExifTags
import piexif

logger = logging.getLogger(__name__)

class ExifAnalyzer:
    """EXIF 데이터 추출 및 분석 클래스"""
    
    def __init__(self):
        """분석기 초기화"""
        self.supported_formats = ['.jpg', '.jpeg', '.tiff', '.tif']
        self.exif_tags = {
            'DateTime': '촬영 시간',
            'Make': '카메라 제조사',
            'Model': '카메라 모델',
            'LensModel': '렌즈 모델',
            'ExposureTime': '셔터 속도',
            'FNumber': '조리개 값',
            'ISOSpeedRatings': 'ISO 감도',
            'FocalLength': '초점 거리',
            'Flash': '플래시 사용',
            'WhiteBalance': '화이트 밸런스',
            'ExposureMode': '노출 모드',
            'MeteringMode': '측광 모드',
            'ColorSpace': '색공간',
            'ExposureProgram': '노출 프로그램',
            'SceneCaptureType': '장면 모드'
        }
    
    def extract_exif_data(self, image_path: Path) -> Dict[str, Any]:
        """
        이미지에서 EXIF 데이터 추출
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            추출된 EXIF 데이터 딕셔너리
        """
        try:
            logger.info(f"EXIF 데이터 추출 시작: {image_path}")
            
            with Image.open(image_path) as img:
                if 'exif' not in img.info:
                    logger.warning(f"EXIF 데이터가 없습니다: {image_path}")
                    return {}
                
                exif_dict = piexif.load(img.info['exif'])
                extracted_data = {}
                
                # 기본 정보 추출
                if '0th' in exif_dict:
                    extracted_data.update(self._extract_basic_info(exif_dict['0th']))
                
                # 촬영 정보 추출
                if 'Exif' in exif_dict:
                    extracted_data.update(self._extract_shooting_info(exif_dict['Exif']))
                
                # GPS 정보 추출
                if 'GPS' in exif_dict:
                    extracted_data.update(self._extract_gps_info(exif_dict['GPS']))
                
                # 파일 정보 추가
                extracted_data['FileName'] = image_path.name
                extracted_data['FileSize'] = image_path.stat().st_size
                extracted_data['ImageWidth'] = img.width
                extracted_data['ImageHeight'] = img.height
                
                # 35mm 등가 초점거리 계산
                if 'FocalLength' in extracted_data and 'Model' in extracted_data:
                    extracted_data['FocalLength35mm'] = self._calculate_35mm_equivalent(
                        extracted_data['FocalLength'], extracted_data['Model']
                    )
                
                logger.info(f"EXIF 데이터 추출 완료: {len(extracted_data)}개 항목")
                return extracted_data
                
        except Exception as e:
            logger.error(f"EXIF 데이터 추출 오류: {e}")
            return {}
    
    def _extract_basic_info(self, ifd_dict: Dict) -> Dict[str, Any]:
        """기본 정보 추출"""
        data = {}
        
        # 카메라 제조사
        if piexif.ImageIFD.Make in ifd_dict:
            data['Make'] = self._decode_value(ifd_dict[piexif.ImageIFD.Make])
        
        # 카메라 모델
        if piexif.ImageIFD.Model in ifd_dict:
            data['Model'] = self._decode_value(ifd_dict[piexif.ImageIFD.Model])
        
        # 촬영 시간
        if piexif.ImageIFD.DateTime in ifd_dict:
            date_str = self._decode_value(ifd_dict[piexif.ImageIFD.DateTime])
            try:
                data['DateTime'] = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
            except ValueError:
                data['DateTime'] = date_str
        
        return data
    
    def _extract_shooting_info(self, exif_dict: Dict) -> Dict[str, Any]:
        """촬영 정보 추출"""
        data = {}
        
        # 노출 시간
        if piexif.ExifIFD.ExposureTime in exif_dict:
            exposure = exif_dict[piexif.ExifIFD.ExposureTime]
            if isinstance(exposure, tuple) and len(exposure) == 2:
                data['ExposureTime'] = f"1/{int(exposure[1]/exposure[0])}" if exposure[0] != 0 else "0"
            else:
                data['ExposureTime'] = str(exposure)
        
        # 조리개 값
        if piexif.ExifIFD.FNumber in exif_dict:
            fnumber = exif_dict[piexif.ExifIFD.FNumber]
            if isinstance(fnumber, tuple) and len(fnumber) == 2:
                data['FNumber'] = f"f/{fnumber[0]/fnumber[1]:.1f}"
            else:
                data['FNumber'] = f"f/{fnumber}"
        
        # ISO 감도
        if piexif.ExifIFD.ISOSpeedRatings in exif_dict:
            data['ISOSpeedRatings'] = exif_dict[piexif.ExifIFD.ISOSpeedRatings]
        
        # 초점 거리
        if piexif.ExifIFD.FocalLength in exif_dict:
            focal = exif_dict[piexif.ExifIFD.FocalLength]
            if isinstance(focal, tuple) and len(focal) == 2:
                data['FocalLength'] = f"{focal[0]/focal[1]:.0f}mm"
            else:
                data['FocalLength'] = f"{focal}mm"
        
        # 렌즈 모델
        if piexif.ExifIFD.LensModel in exif_dict:
            data['LensModel'] = self._decode_value(exif_dict[piexif.ExifIFD.LensModel])
        
        # 플래시
        if piexif.ExifIFD.Flash in exif_dict:
            flash_value = exif_dict[piexif.ExifIFD.Flash]
            data['Flash'] = '사용' if flash_value & 1 else '미사용'
        
        # 화이트 밸런스
        if piexif.ExifIFD.WhiteBalance in exif_dict:
            wb_value = exif_dict[piexif.ExifIFD.WhiteBalance]
            data['WhiteBalance'] = '자동' if wb_value == 0 else '수동'
        
        # 노출 모드
        if piexif.ExifIFD.ExposureMode in exif_dict:
            exp_mode = exif_dict[piexif.ExifIFD.ExposureMode]
            modes = {0: '자동', 1: '수동', 2: '자동 브라케팅'}
            data['ExposureMode'] = modes.get(exp_mode, '알 수 없음')
        
        return data
    
    def _extract_gps_info(self, gps_dict: Dict) -> Dict[str, Any]:
        """GPS 정보 추출"""
        data = {}
        
        try:
            if piexif.GPSIFD.GPSLatitude in gps_dict and piexif.GPSIFD.GPSLongitude in gps_dict:
                # 위도
                lat = self._convert_to_degrees(gps_dict[piexif.GPSIFD.GPSLatitude])
                if piexif.GPSIFD.GPSLatitudeRef in gps_dict:
                    if gps_dict[piexif.GPSIFD.GPSLatitudeRef] == b'S':
                        lat = -lat
                
                # 경도
                lon = self._convert_to_degrees(gps_dict[piexif.GPSIFD.GPSLongitude])
                if piexif.GPSIFD.GPSLongitudeRef in gps_dict:
                    if gps_dict[piexif.GPSIFD.GPSLongitudeRef] == b'W':
                        lon = -lon
                
                data['GPSLatitude'] = lat
                data['GPSLongitude'] = lon
                
                # 고도
                if piexif.GPSIFD.GPSAltitude in gps_dict:
                    alt_data = gps_dict[piexif.GPSIFD.GPSAltitude]
                    if isinstance(alt_data, tuple) and len(alt_data) == 2:
                        data['GPSAltitude'] = alt_data[0] / alt_data[1]
        
        except Exception as e:
            logger.warning(f"GPS 정보 추출 오류: {e}")
        
        return data
    
    def _decode_value(self, value: Any) -> str:
        """바이트 값을 문자열로 디코딩"""
        if isinstance(value, bytes):
            try:
                return value.decode('utf-8').strip('\x00')
            except UnicodeDecodeError:
                return str(value)
        return str(value)
    
    def _convert_to_degrees(self, value: Tuple) -> float:
        """GPS 좌표를 도 단위로 변환"""
        if not value or len(value) != 3:
            return 0.0
        
        try:
            d = float(value[0][0]) / float(value[0][1])
            m = float(value[1][0]) / float(value[1][1])
            s = float(value[2][0]) / float(value[2][1])
            return d + (m / 60.0) + (s / 3600.0)
        except (ZeroDivisionError, TypeError, IndexError):
            return 0.0
    
    def _calculate_35mm_equivalent(self, focal_length: str, model: str) -> str:
        """35mm 등가 초점거리 계산"""
        try:
            # 초점거리에서 숫자 추출
            focal_mm = float(focal_length.replace('mm', '').strip())
            
            return f"{focal_mm:.0f}mm"
            
        except (ValueError, AttributeError):
            return focal_length
    
    def analyze_batch(self, image_paths: List[Path]) -> pd.DataFrame:
        """
        다중 이미지 일괄 분석
        
        Args:
            image_paths: 이미지 파일 경로 리스트
            
        Returns:
            분석 결과 DataFrame
        """
        logger.info(f"일괄 분석 시작: {len(image_paths)}개 파일")
        
        results = []
        for path in image_paths:
            if path.suffix.lower() in self.supported_formats:
                exif_data = self.extract_exif_data(path)
                if exif_data:
                    results.append(exif_data)
        
        if results:
            df = pd.DataFrame(results)
            logger.info(f"일괄 분석 완료: {len(df)}개 파일 처리")
            return df
        else:
            logger.warning("분석할 수 있는 이미지가 없습니다")
            return pd.DataFrame()
    
    def get_shooting_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        촬영 통계 분석
        
        Args:
            df: EXIF 데이터 DataFrame
            
        Returns:
            통계 분석 결과
        """
        if df.empty:
            return {}
        
        stats = {}
        
        # 카메라 사용 빈도
        if 'Model' in df.columns:
            stats['camera_usage'] = df['Model'].value_counts().to_dict()
        
        # 렌즈 사용 빈도
        if 'LensModel' in df.columns:
            stats['lens_usage'] = df['LensModel'].value_counts().to_dict()
        
        # 조리개 사용 빈도
        if 'FNumber' in df.columns:
            stats['aperture_usage'] = df['FNumber'].value_counts().to_dict()
        
        # ISO 사용 빈도
        if 'ISOSpeedRatings' in df.columns:
            stats['iso_usage'] = df['ISOSpeedRatings'].value_counts().to_dict()
        
        # 초점거리 사용 빈도
        if 'FocalLength' in df.columns:
            stats['focal_length_usage'] = df['FocalLength'].value_counts().to_dict()
        
        # 촬영 시간 분석
        if 'DateTime' in df.columns:
            df_time = df[df['DateTime'].notna()].copy()
            if not df_time.empty:
                df_time['Hour'] = pd.to_datetime(df_time['DateTime']).dt.hour
                stats['shooting_hours'] = df_time['Hour'].value_counts().to_dict()
        
        # 플래시 사용률
        if 'Flash' in df.columns:
            stats['flash_usage'] = df['Flash'].value_counts().to_dict()
        
        logger.info(f"촬영 통계 분석 완료: {len(stats)}개 항목")
        return stats 