# 일반 유틸리티 함수 모듈
import os
import re
import logging
from datetime import datetime
from fractions import Fraction
from typing import Union, Any, Optional, Dict

def format_exposure(val: Union[float, str, Fraction]) -> str:
    """
    노출 시간을 사람이 읽기 쉬운 형식으로 변환합니다.
    
    Args:
        val: 노출 시간 값 (실수, 문자열 또는 Fraction)
        
    Returns:
        str: 포맷된 노출 시간 (예: '1/60s', '2.5s')
    """
    try:
        # 문자열이 들어오면 숫자로 변환
        if isinstance(val, str):
            # 이미 형식화된 문자열인지 확인
            if val.endswith('s') and ('/' in val or val[0].isdigit()):
                return val
            
            # 분수 형태 문자열 변환
            if '/' in val:
                num, denom = map(int, val.split('/'))
                sec = num / denom
            else:
                sec = float(val)
        elif isinstance(val, Fraction):
            sec = float(val)
        else:
            sec = val
        
        # 노출 시간 포맷팅
        if sec >= 1:
            return f"{sec:.1f}s"
        else:
            frac = Fraction(sec).limit_denominator()
            return f"1/{frac.denominator}s"
    except (ValueError, TypeError, ZeroDivisionError) as e:
        logging.warning(f"노출 시간 포맷팅 실패: {e}")
        return str(val)

def sort_key(value: str) -> float:
    """
    EXIF 값을 정렬하기 위한 키 함수입니다.
    
    Args:
        value: 정렬할 값 (문자열)
        
    Returns:
        float: 정렬 키 값
    """
    try:
        # 노출 시간 처리 (예: '1/60s')
        if isinstance(value, str) and value.endswith('s'):
            u = value[:-1]  # 's' 제거
            if u.startswith('1/'):
                # 분수 형태 (예: '1/60s')
                return 1 / int(u.split('/')[1])
            else:
                # 정수/실수 형태 (예: '2.5s')
                return float(u)
        
        # ISO 처리 (예: 'ISO 100')
        if isinstance(value, str) and value.startswith('ISO'):
            match = re.search(r'ISO\s+(\d+)', value)
            if match:
                return float(match.group(1))
        
        # 조리개 값 처리 (예: 'f/2.8')
        if isinstance(value, str) and value.startswith('f/'):
            return float(value[2:])
    except (ValueError, IndexError, ZeroDivisionError):
        pass
    
    # 숫자로 변환 불가능한 경우 무한대 반환
    return float('inf')

def format_timestamp(timestamp: Optional[str] = None) -> str:
    """
    타임스탬프를 사람이 읽기 쉬운 형식으로 변환합니다.
    
    Args:
        timestamp (str, optional): 형식화할 타임스탬프. None이면 현재 시간 사용
        
    Returns:
        str: 포맷된 타임스탬프
    """
    if timestamp is None:
        dt = datetime.now()
    else:
        try:
            # EXIF 날짜 시간 문자열 파싱 (예: '2023:05:18 15:30:45')
            dt = datetime.strptime(timestamp, '%Y:%m:%d %H:%M:%S')
        except ValueError:
            try:
                # 일반 ISO 형식 파싱
                dt = datetime.fromisoformat(timestamp)
            except (ValueError, TypeError):
                return timestamp
    
    # 형식화된 날짜 반환
    return dt.strftime('%Y년 %m월 %d일 %H시 %M분')

def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    파일 정보를 반환합니다.
    
    Args:
        file_path (str): 파일 경로
        
    Returns:
        Dict[str, Any]: 파일 정보 딕셔너리
    """
    try:
        stat = os.stat(file_path)
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()
        
        return {
            'name': file_name,
            'extension': file_ext,
            'size': stat.st_size,
            'size_human': format_file_size(stat.st_size),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'modified_str': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        logging.warning(f"파일 정보 조회 실패: {e}")
        return {'name': os.path.basename(file_path), 'error': str(e)}

def format_file_size(size_bytes: int) -> str:
    """
    파일 크기를 사람이 읽기 쉬운 형식으로 변환합니다.
    
    Args:
        size_bytes (int): 바이트 단위 파일 크기
        
    Returns:
        str: 형식화된 파일 크기 (예: '1.5 MB')
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024 or unit == 'TB':
            if unit == 'B':
                return f"{size_bytes} {unit}"
            return f"{size_bytes/1024:.1f} {unit}"
        size_bytes /= 1024
