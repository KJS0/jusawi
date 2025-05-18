import os
import logging
from typing import Optional, Dict, Any
import piexif
from PIL import Image

def copy_exif(source_path: str, target_path: str, output_path: Optional[str] = None) -> str:
    """
    소스 이미지에서 대상 이미지로 EXIF 메타데이터를 복사합니다.
    
    Args:
        source_path (str): 소스 이미지 파일 경로
        target_path (str): 대상 이미지 파일 경로
        output_path (str, optional): 출력 파일 경로. None이면 대상 파일을 덮어씁니다.
    
    Returns:
        str: 최종 출력 파일 경로
        
    Raises:
        FileNotFoundError: 소스 또는 대상 파일이 존재하지 않는 경우
        ValueError: 지원되지 않는 파일 형식 또는 메타데이터 형식 오류
        IOError: 파일 입출력 오류
    """
    # 파일 존재 확인
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"소스 파일을 찾을 수 없습니다: {source_path}")
    if not os.path.exists(target_path):
        raise FileNotFoundError(f"대상 파일을 찾을 수 없습니다: {target_path}")
    
    try:
        # 소스 이미지에서 EXIF 메타데이터 로드
        exif_dict = piexif.load(source_path)
        
        # 로드된 EXIF 데이터 검증
        if not exif_dict:
            logging.warning(f"소스 파일에 EXIF 데이터가 없습니다: {source_path}")
        
        # EXIF 데이터를 바이트로 직렬화
        exif_bytes = piexif.dump(exif_dict)
        
        # 출력 경로 결정
        out_path = output_path or target_path
        
        # EXIF 메타데이터 삽입
        piexif.insert(exif_bytes, target_path, out_path)
        
        logging.info(f"EXIF 메타데이터 복사 완료: {source_path} -> {out_path}")
        return out_path
        
    except piexif.InvalidImageDataError:
        raise ValueError(f"유효하지 않은 이미지 데이터: {source_path} 또는 {target_path}")
    except ValueError as e:
        raise ValueError(f"EXIF 데이터 처리 오류: {e}")
    except Exception as e:
        raise IOError(f"EXIF 복사 중 오류 발생: {e}")

def get_exif_summary(image_path: str) -> Dict[str, Any]:
    """
    이미지 파일의 EXIF 메타데이터 요약을 반환합니다.
    
    Args:
        image_path (str): 이미지 파일 경로
        
    Returns:
        Dict[str, Any]: EXIF 메타데이터 요약
    """
    try:
        # EXIF 로드
        exif_dict = piexif.load(image_path)
        
        # 요약 데이터 준비
        summary = {}
        
        # 카메라 모델 (0th 그룹, 모델 태그)
        if "0th" in exif_dict and piexif.ImageIFD.Model in exif_dict["0th"]:
            model_bytes = exif_dict["0th"][piexif.ImageIFD.Model]
            try:
                summary["카메라"] = model_bytes.decode("utf-8").strip("\x00")
            except UnicodeDecodeError:
                summary["카메라"] = model_bytes.decode("latin-1").strip("\x00")
        
        # 렌즈 정보 (Exif 그룹, 렌즈 모델 태그)
        if "Exif" in exif_dict and piexif.ExifIFD.LensModel in exif_dict["Exif"]:
            lens_bytes = exif_dict["Exif"][piexif.ExifIFD.LensModel]
            try:
                summary["렌즈"] = lens_bytes.decode("utf-8").strip("\x00")
            except UnicodeDecodeError:
                summary["렌즈"] = lens_bytes.decode("latin-1").strip("\x00")
        
        # GPS 정보
        if "GPS" in exif_dict and exif_dict["GPS"]:
            has_lat = piexif.GPSIFD.GPSLatitude in exif_dict["GPS"]
            has_lon = piexif.GPSIFD.GPSLongitude in exif_dict["GPS"]
            
            if has_lat and has_lon:
                summary["GPS"] = "있음"
            else:
                summary["GPS"] = "불완전"
        else:
            summary["GPS"] = "없음"
            
        return summary
        
    except Exception as e:
        logging.warning(f"EXIF 요약 생성 실패: {e}")
        return {"오류": f"EXIF 데이터 읽기 실패: {e}"}

def remove_all_exif(image_path: str, output_path: Optional[str] = None) -> str:
    """
    이미지에서 모든 EXIF 메타데이터를 제거합니다.
    
    Args:
        image_path (str): 이미지 파일 경로
        output_path (str, optional): 출력 파일 경로. None이면 원본 파일을 덮어씁니다.
        
    Returns:
        str: 출력 파일 경로
    """
    try:
        # 출력 경로 결정
        out_path = output_path or image_path
        
        # 이미지 로드 및 저장 (EXIF 제거됨)
        with Image.open(image_path) as img:
            # 메타데이터 없이 저장
            img.save(out_path)
        
        logging.info(f"EXIF 메타데이터 제거 완료: {image_path} -> {out_path}")
        return out_path
        
    except Exception as e:
        logging.error(f"EXIF 제거 중 오류 발생: {e}")
        raise IOError(f"EXIF 제거 중 오류 발생: {e}")