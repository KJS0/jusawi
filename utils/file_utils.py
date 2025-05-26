"""
파일 처리 유틸리티
캡스톤 디자인 프로젝트 - 파일 및 디렉토리 관련 유틸리티
"""

import os
import logging
from pathlib import Path
from typing import List, Set, Optional
import mimetypes

logger = logging.getLogger(__name__)

class FileUtils:
    """파일 처리 유틸리티 클래스"""
    
    # 지원하는 이미지 확장자
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.tiff', '.tif', '.png', '.bmp'}
    
    @staticmethod
    def is_image_file(file_path: Path) -> bool:
        """
        파일이 지원하는 이미지 파일인지 확인
        
        Args:
            file_path: 확인할 파일 경로
            
        Returns:
            이미지 파일 여부
        """
        try:
            return file_path.suffix.lower() in FileUtils.SUPPORTED_EXTENSIONS
        except Exception:
            return False
    
    @staticmethod
    def get_image_files(directory: Path, recursive: bool = False) -> List[Path]:
        """
        디렉토리에서 이미지 파일 목록 가져오기
        
        Args:
            directory: 검색할 디렉토리
            recursive: 하위 디렉토리 포함 여부
            
        Returns:
            이미지 파일 경로 리스트
        """
        image_files = []
        
        try:
            if not directory.exists() or not directory.is_dir():
                logger.warning(f"디렉토리가 존재하지 않습니다: {directory}")
                return image_files
            
            pattern = "**/*" if recursive else "*"
            
            for file_path in directory.glob(pattern):
                if file_path.is_file() and FileUtils.is_image_file(file_path):
                    image_files.append(file_path)
            
            logger.info(f"디렉토리에서 {len(image_files)}개 이미지 파일 발견: {directory}")
            return sorted(image_files)
            
        except Exception as e:
            logger.error(f"이미지 파일 검색 오류: {e}")
            return []
    
    @staticmethod
    def get_file_size_mb(file_path: Path) -> float:
        """
        파일 크기를 MB 단위로 반환
        
        Args:
            file_path: 파일 경로
            
        Returns:
            파일 크기 (MB)
        """
        try:
            size_bytes = file_path.stat().st_size
            return size_bytes / (1024 * 1024)
        except Exception:
            return 0.0
    
    @staticmethod
    def create_output_directory(base_path: Path, dir_name: str) -> Path:
        """
        출력 디렉토리 생성
        
        Args:
            base_path: 기본 경로
            dir_name: 디렉토리 이름
            
        Returns:
            생성된 디렉토리 경로
        """
        try:
            output_dir = base_path / dir_name
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"출력 디렉토리 생성: {output_dir}")
            return output_dir
        except Exception as e:
            logger.error(f"디렉토리 생성 오류: {e}")
            raise
    
    @staticmethod
    def validate_file_access(file_path: Path) -> bool:
        """
        파일 접근 가능성 확인
        
        Args:
            file_path: 확인할 파일 경로
            
        Returns:
            접근 가능 여부
        """
        try:
            return (file_path.exists() and 
                   file_path.is_file() and 
                   os.access(file_path, os.R_OK))
        except Exception:
            return False
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """
        안전한 파일명 생성 (특수문자 제거)
        
        Args:
            filename: 원본 파일명
            
        Returns:
            안전한 파일명
        """
        import re
        
        # 특수문자를 언더스코어로 대체
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # 연속된 언더스코어를 하나로 줄임
        safe_name = re.sub(r'_+', '_', safe_name)
        
        # 앞뒤 공백 및 언더스코어 제거
        safe_name = safe_name.strip(' _')
        
        return safe_name if safe_name else 'unnamed'
    
    @staticmethod
    def backup_file(file_path: Path, backup_suffix: str = '.bak') -> Optional[Path]:
        """
        파일 백업 생성
        
        Args:
            file_path: 백업할 파일 경로
            backup_suffix: 백업 파일 접미사
            
        Returns:
            백업 파일 경로 (실패 시 None)
        """
        try:
            if not file_path.exists():
                return None
            
            backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)
            
            # 기존 백업 파일이 있으면 번호 추가
            counter = 1
            while backup_path.exists():
                backup_path = file_path.with_suffix(
                    f"{file_path.suffix}{backup_suffix}.{counter}"
                )
                counter += 1
            
            # 파일 복사
            import shutil
            shutil.copy2(file_path, backup_path)
            
            logger.info(f"파일 백업 생성: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"파일 백업 오류: {e}")
            return None 