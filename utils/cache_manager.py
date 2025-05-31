"""
AI 분석 결과 캐싱 관리 모듈
"""

import json
import hashlib
import os
from pathlib import Path
from typing import Dict, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, cache_dir: str = "cache"):
        """캐시 관리자 초기화"""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # 메모리 캐시 (세션 중 빠른 접근)
        self.memory_cache = {}
        
        # 캐시 파일 경로
        self.cache_file = self.cache_dir / "ai_analysis_cache.json"
        
        # 캐시 로드
        self._load_cache()
    
    def _load_cache(self):
        """디스크에서 캐시 로드"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.memory_cache.update(cache_data)
                logger.info(f"캐시 로드 완료: {len(self.memory_cache)}개 항목")
            else:
                logger.info("캐시 파일이 없습니다. 새로 생성됩니다.")
        except Exception as e:
            logger.error(f"캐시 로드 오류: {e}")
            self.memory_cache = {}
    
    def _save_cache(self):
        """캐시를 디스크에 저장"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory_cache, f, ensure_ascii=False, indent=2)
            logger.info(f"캐시 저장 완료: {len(self.memory_cache)}개 항목")
        except Exception as e:
            logger.error(f"캐시 저장 오류: {e}")
    
    def _get_file_hash(self, file_path: str) -> str:
        """파일의 해시값 계산 (크기 + 수정시간 기반)"""
        try:
            stat = os.stat(file_path)
            # 파일 크기와 수정시간을 조합해서 해시 생성 (빠른 방법)
            hash_input = f"{file_path}_{stat.st_size}_{stat.st_mtime}"
            return hashlib.md5(hash_input.encode()).hexdigest()
        except Exception as e:
            logger.error(f"파일 해시 계산 오류: {e}")
            return None
    
    def get_cached_result(self, file_path: str) -> Optional[Dict]:
        """캐시된 분석 결과 가져오기"""
        file_hash = self._get_file_hash(file_path)
        if not file_hash:
            return None
        
        if file_hash in self.memory_cache:
            cached_data = self.memory_cache[file_hash]
            logger.info(f"캐시에서 결과 찾음: {os.path.basename(file_path)}")
            return cached_data.get('result')
        
        return None
    
    def save_result(self, file_path: str, result: Dict):
        """분석 결과를 캐시에 저장"""
        file_hash = self._get_file_hash(file_path)
        if not file_hash:
            return
        
        cache_entry = {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'result': result,
            'timestamp': datetime.now().isoformat(),
            'version': '1.0'  # 향후 캐시 형식 변경 시 호환성
        }
        
        self.memory_cache[file_hash] = cache_entry
        logger.info(f"캐시에 결과 저장: {os.path.basename(file_path)}")
        
        # 주기적으로 디스크에 저장 (10개마다)
        if len(self.memory_cache) % 10 == 0:
            self._save_cache()
    
    def clear_cache(self):
        """캐시 초기화"""
        self.memory_cache.clear()
        if self.cache_file.exists():
            self.cache_file.unlink()
        logger.info("캐시가 초기화되었습니다.")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보"""
        return {
            'total_entries': len(self.memory_cache),
            'cache_file_exists': self.cache_file.exists(),
            'cache_dir': str(self.cache_dir),
            'memory_cache_size': len(self.memory_cache)
        }
    
    def cleanup_old_entries(self, days: int = 30):
        """오래된 캐시 항목 정리"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        old_keys = []
        
        for key, entry in self.memory_cache.items():
            try:
                entry_date = datetime.fromisoformat(entry.get('timestamp', ''))
                if entry_date < cutoff_date:
                    old_keys.append(key)
            except:
                old_keys.append(key)  # 잘못된 타임스탬프도 제거
        
        for key in old_keys:
            del self.memory_cache[key]
        
        if old_keys:
            logger.info(f"{len(old_keys)}개의 오래된 캐시 항목을 삭제했습니다.")
            self._save_cache()
    
    def __del__(self):
        """소멸자에서 캐시 저장"""
        try:
            self._save_cache()
        except:
            pass 