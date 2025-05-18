# EXIF reading, GPS extraction, and 35mm equivalent focal length
from PIL import Image, ExifTags
import logging
from utils import format_exposure
from config import EXIF_TAGS

# 카메라 모델별 크롭 팩터 정의
CROP_FACTORS = {
    'D5300':1.5,'D5600':1.5,'D3500':1.5,'D7200':1.5,
    'D610':1.0,'D750':1.0,'D850':1.0
}

def read_exif(path):
    """
    이미지 파일에서 EXIF 데이터를 읽어옵니다.
    
    Args:
        path (str): 이미지 파일 경로
        
    Returns:
        tuple: (exif_data, gps_raw_data) - EXIF 데이터와 GPS 원시 데이터
        
    Raises:
        IOError: 파일 열기 실패 시
        ValueError: EXIF 데이터 처리 실패 시
    """
    try:
        with Image.open(path) as img:
            raw = img._getexif() or {}
    except Exception as e:
        raise IOError(f"이미지 파일을 열 수 없습니다: {e}")
    
    if not raw:
        return {}, None
    
    exif = {}
    gps_raw = None
    
    # EXIF 태그 처리
    for tid, val in raw.items():
        try:
            tag = ExifTags.TAGS.get(tid, tid)
            
            # GPS 정보 처리
            if tag == 'GPSInfo':
                gps_raw = val
            
            # 설정된 EXIF 태그만 처리
            if tag in EXIF_TAGS and tag != '35mmEq':
                if val is None:
                    continue
                    
                # 특별한 형식 처리
                if tag == 'ExposureTime':
                    val = format_exposure(val)
                elif tag == 'FNumber':
                    val = f"f/{float(val):.1f}"
                elif tag == 'ISOSpeedRatings':
                    val = f"ISO {val}"
                    
                exif[tag] = str(val)
        except Exception as e:
            logging.warning(f"EXIF 태그 {tid} 처리 중 오류: {e}")
    
    # 35mm 등가 초점 거리 계산
    model = exif.get('Model', '')
    fl_str = exif.get('FocalLength')
    
    try:
        fl = float(fl_str)
        factor = 1.0
        
        # 기기 모델에 따른 크롭 팩터 적용
        for key, cf in CROP_FACTORS.items():
            if key in model:
                factor = cf
                break
                
        exif['35mmEq'] = f"{fl*factor:.1f}"
    except (ValueError, TypeError):
        exif['35mmEq'] = ''
    
    return exif, gps_raw


def dms_to_deg(dms, ref):
    """
    DMS(Degrees, Minutes, Seconds) 좌표를 십진수 도(Decimal Degrees)로 변환합니다.
    
    Args:
        dms: 도, 분, 초 값이 담긴 튜플
        ref: 방향 참조 ('N', 'S', 'E', 'W')
        
    Returns:
        float: 십진수 도 값
    """
    try:
        deg, mn, sec = (c.numerator / c.denominator for c in dms)
        dec = deg + mn/60 + sec/3600
        return -dec if ref in ('S', 'W') else dec
    except (AttributeError, TypeError, ZeroDivisionError) as e:
        raise ValueError(f"DMS 좌표 변환 오류: {e}")


def gps_to_latlon(gps_raw):
    """
    EXIF GPS 정보를 위도/경도 좌표로 변환합니다.
    
    Args:
        gps_raw: EXIF에서 추출한 원시 GPS 데이터
        
    Returns:
        tuple 또는 None: (위도, 경도) 튜플 또는 GPS 정보가 없을 경우 None
    """
    if not gps_raw:
        return None
    
    try:
        # GPS 태그를 사람이 읽을 수 있는 형태로 변환
        gps = {ExifTags.GPSTAGS.get(k, k): v for k, v in gps_raw.items()}
        
        # 필수 GPS 태그 확인
        required_tags = ['GPSLatitude', 'GPSLatitudeRef', 'GPSLongitude', 'GPSLongitudeRef']
        if not all(tag in gps for tag in required_tags):
            return None
            
        # 위도/경도 변환
        return (
            dms_to_deg(gps['GPSLatitude'], gps['GPSLatitudeRef']),
            dms_to_deg(gps['GPSLongitude'], gps['GPSLongitudeRef'])
        )
    except Exception as e:
        logging.warning(f"GPS 좌표 변환 중 오류: {e}")
        return None


def get_exif_summary(exif_data):
    """
    EXIF 데이터의 간략한 요약을 생성합니다.
    
    Args:
        exif_data (dict): EXIF 데이터 딕셔너리
        
    Returns:
        str: EXIF 데이터 요약 문자열
    """
    if not exif_data:
        return "EXIF 데이터 없음"
        
    summary_items = []
    
    # 카메라 모델
    if 'Model' in exif_data:
        summary_items.append(f"카메라: {exif_data['Model']}")
    
    # 렌즈 정보
    if 'LensModel' in exif_data:
        summary_items.append(f"렌즈: {exif_data['LensModel']}")
    
    # 촬영 설정 (노출, 조리개, ISO)
    settings = []
    if 'FocalLength' in exif_data:
        settings.append(f"{exif_data['FocalLength']}mm")
    if 'FNumber' in exif_data:
        settings.append(exif_data['FNumber'])
    if 'ExposureTime' in exif_data:
        settings.append(exif_data['ExposureTime'])
    if 'ISOSpeedRatings' in exif_data:
        settings.append(exif_data['ISOSpeedRatings'])
    
    if settings:
        summary_items.append(" | ".join(settings))
    
    return " - ".join(summary_items) if summary_items else "EXIF 요약 정보 없음"
