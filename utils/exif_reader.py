"""
EXIF 데이터 읽기 모듈
"""

import piexif
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import logging
from typing import Dict, Any, Optional
from fractions import Fraction

logger = logging.getLogger(__name__)

class ExifReader:
    def __init__(self):
        """EXIF 리더 초기화"""
        pass
    
    def read_exif(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        이미지 파일에서 EXIF 데이터 읽기
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            EXIF 데이터 딕셔너리 또는 None
        """
        try:
            # PIL로 이미지 열기
            image = Image.open(image_path)
            
            # EXIF 데이터 가져오기
            exif_data = image._getexif()
            
            if not exif_data:
                return None
            
            # EXIF 데이터 파싱
            parsed_exif = {}
            
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                
                # GPS 정보 처리
                if tag == 'GPSInfo':
                    gps_data = {}
                    for gps_tag_id, gps_value in value.items():
                        gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_data[gps_tag] = gps_value
                    parsed_exif['GPSInfo'] = gps_data
                else:
                    # 일반 EXIF 데이터 처리
                    parsed_exif[tag] = self._format_value(tag, value)
            
            # 주요 정보 추가 처리
            parsed_exif = self._process_common_tags(parsed_exif)
            
            return parsed_exif
            
        except Exception as e:
            logger.error(f"EXIF 읽기 오류: {e}")
            return None
    
    def _format_value(self, tag: str, value: Any) -> Any:
        """EXIF 값 포맷팅"""
        try:
            # 바이트 문자열 디코딩
            if isinstance(value, bytes):
                return value.decode('utf-8', errors='ignore').strip()
            
            # 튜플 처리 (주로 분수 값)
            elif isinstance(value, tuple):
                if len(value) == 2 and isinstance(value[0], int):
                    # 분수를 실수로 변환
                    if value[1] != 0:
                        return value[0] / value[1]
                    return value[0]
                return str(value)
            
            # MakerNote 등 복잡한 데이터는 무시
            elif tag in ['MakerNote', 'UserComment']:
                return '[Binary Data]'
            
            return value
            
        except Exception:
            return str(value)
    
    def _process_common_tags(self, exif_data: Dict[str, Any]) -> Dict[str, Any]:
        """주요 EXIF 태그 처리 및 형식 개선"""
        
        # ISO 값 처리
        if 'ISOSpeedRatings' in exif_data:
            exif_data['ISO'] = exif_data['ISOSpeedRatings']
        
        # 노출 시간 처리
        if 'ExposureTime' in exif_data:
            exposure = exif_data['ExposureTime']
            if isinstance(exposure, (int, float)):
                if exposure < 1:
                    # 1초 미만인 경우 분수로 표시
                    exif_data['ExposureTime'] = f"1/{int(1/exposure)}"
                else:
                    exif_data['ExposureTime'] = f"{exposure}s"
        
        # 조리개 값 처리
        if 'FNumber' in exif_data:
            f_number = exif_data['FNumber']
            if isinstance(f_number, (int, float)):
                exif_data['FNumber'] = f"f/{f_number}"
        
        # 초점 거리 처리
        if 'FocalLength' in exif_data:
            focal = exif_data['FocalLength']
            if isinstance(focal, (int, float)):
                exif_data['FocalLength'] = f"{focal}mm"
        
        # GPS 좌표 변환
        if 'GPSInfo' in exif_data:
            gps_info = exif_data['GPSInfo']
            lat = self._convert_gps_coordinate(
                gps_info.get('GPSLatitude'),
                gps_info.get('GPSLatitudeRef')
            )
            lon = self._convert_gps_coordinate(
                gps_info.get('GPSLongitude'),
                gps_info.get('GPSLongitudeRef')
            )
            
            if lat and lon:
                exif_data['GPSCoordinates'] = {
                    'latitude': lat,
                    'longitude': lon,
                    'formatted': f"{lat:.6f}, {lon:.6f}"
                }
        
        return exif_data
    
    def _convert_gps_coordinate(self, coord_data: Any, ref: str) -> Optional[float]:
        """GPS 좌표를 십진수로 변환"""
        if not coord_data or not ref:
            return None
        
        try:
            # 도, 분, 초 추출
            if len(coord_data) == 3:
                degrees = coord_data[0]
                minutes = coord_data[1]
                seconds = coord_data[2]
                
                # 각 값이 튜플인 경우 처리
                if isinstance(degrees, tuple):
                    degrees = degrees[0] / degrees[1]
                if isinstance(minutes, tuple):
                    minutes = minutes[0] / minutes[1]
                if isinstance(seconds, tuple):
                    seconds = seconds[0] / seconds[1]
                
                # 십진수로 변환
                decimal = degrees + minutes/60 + seconds/3600
                
                # 남반구/서반구인 경우 음수로
                if ref in ['S', 'W']:
                    decimal = -decimal
                
                return decimal
                
        except Exception as e:
            logger.error(f"GPS 좌표 변환 오류: {e}")
            return None 