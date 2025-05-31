"""
OpenAI GPT Vision API를 사용한 이미지 분석 모듈
"""

import os
import base64
from openai import OpenAI
from typing import Dict, List, Optional
import logging
from dotenv import load_dotenv
import json

logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

class AIImageAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        """AI 이미지 분석기 초기화"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API 키가 필요합니다. 환경 변수 OPENAI_API_KEY를 설정하세요.")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def encode_image(self, image_path: str) -> str:
        """이미지를 base64로 인코딩"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def analyze_image(self, image_path: str, has_exif: bool = True, 
                     has_location: bool = True) -> Dict:
        """
        이미지를 분석하여 해시태그, 촬영 정보, 위치 정보 추출
        
        Args:
            image_path: 분석할 이미지 경로
            has_exif: EXIF 데이터 존재 여부
            has_location: 위치 정보 존재 여부
            
        Returns:
            분석 결과 딕셔너리
        """
        try:
            # 이미지 인코딩
            base64_image = self.encode_image(image_path)
            
            # 프롬프트 구성
            prompt = self._build_prompt(has_exif, has_location)
            
            # API 호출
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            # 응답 파싱
            result = self._parse_response(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"이미지 분석 중 오류 발생: {e}")
            return {
                "hashtags": [],
                "camera_settings": {},
                "location": "",
                "error": str(e)
            }
    
    def _build_prompt(self, has_exif: bool, has_location: bool) -> str:
        """분석을 위한 프롬프트 생성"""
        prompt = """이 이미지를 분석하여 다음 정보를 JSON 형식으로 제공해주세요:

1. hashtags: 이미지와 관련된 대표적인 해시태그 5개 (한글 가능)
"""
        
        if not has_exif:
            prompt += """2. camera_settings: 추정되는 카메라 설정
   - shutter_speed: 셔터 속도 (예: "1/125초초")
   - iso: ISO 값 (예: 400)
   - aperture: 조리개 값 (예: "f/2.8")
   - focal_length: 초점 거리 (예: "50mm")
"""
        
        if not has_location:
            prompt += """3. location: 추정되는 촬영 위치 (도시명, 랜드마크 등)
"""
        
        prompt += """
응답은 다음과 같은 JSON 형식으로만 제공해주세요:
{
    "hashtags": ["해시태그1", "해시태그2", "해시태그3", "해시태그4", "해시태그5"],
    "camera_settings": {
        "shutter_speed": "추정값",
        "iso": 추정값,
        "aperture": "추정값"
    },
    "location": "추정 위치"
}
"""
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict:
        """GPT 응답을 파싱"""
        try:
            # JSON 형식 추출
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # JSON을 찾을 수 없는 경우 기본값 반환
                return {
                    "hashtags": [],
                    "camera_settings": {},
                    "location": ""
                }
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            return {
                "hashtags": [],
                "camera_settings": {},
                "location": ""
            } 