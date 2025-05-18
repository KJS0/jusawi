# GPT-4o Vision 기반 이미지 분석 유틸리티 모듈
import os
import base64
import logging
import json
from typing import Optional, Dict, Any, List, Union
import openai
from config import OPENAI_API_KEY

class GPTVisionAnalyzer:
    """GPT-4o Vision 모델을 사용한 이미지 분석 클래스"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        초기화
        
        Args:
            api_key (str, optional): OpenAI API 키. 지정하지 않으면 환경 변수에서 가져옵니다.
            model (str, optional): 사용할 모델. 기본값은 'gpt-4o'
        
        Raises:
            ValueError: API 키가 없는 경우
        """
        # API 키 설정
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API 키가 필요합니다. config.py에 설정하거나 환경 변수로 제공하세요.")
        
        openai.api_key = self.api_key
        self.model = model
    
    def encode_image(self, image_path: str) -> str:
        """
        이미지 파일을 Base64로 인코딩합니다
        
        Args:
            image_path (str): 이미지 파일 경로
            
        Returns:
            str: Base64 인코딩된 이미지 문자열
            
        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
            IOError: 파일을 읽을 수 없는 경우
        """
        try:
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except FileNotFoundError:
            logging.error(f"파일을 찾을 수 없음: {image_path}")
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
        except Exception as e:
            logging.error(f"이미지 인코딩 오류: {e}")
            raise IOError(f"이미지 파일을 읽을 수 없습니다: {e}")
    
    def predict_location(self, image_path: str, detail_level: str = "high") -> str:
        """
        이미지 속 위치를 추정합니다
        
        Args:
            image_path (str): 이미지 파일 경로
            detail_level (str, optional): 이미지 분석 상세도 ('high', 'low'). 기본값 'high'
            
        Returns:
            str: GPT 모델이 추정한 위치 정보
            
        Raises:
            Exception: API 호출 오류 등
        """
        try:
            # 이미지 인코딩
            img64 = self.encode_image(image_path)
            
            # API 요청 메시지 구성
            messages = [
                {"role": "system", "content": "당신은 사진 속 장소를 추정하는 전문가입니다. 특징적인 랜드마크, 건축물, 자연환경, 간판 등을 분석하여 정확한 위치를 식별합니다."},
                {"role": "user", "content": [
                    {"type": "text", "text": "이 사진 촬영 장소(도시·랜드마크)를 한국어로 알려주세요. 가능하면 구체적인 위치도 포함해주세요."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img64}", "detail": detail_level}}
                ]}
            ]
            
            # API 호출
            response = openai.ChatCompletion.create(
                model=self.model,
                max_tokens=350,
                messages=messages
            )
            
            # 결과 추출
            location = response["choices"][0]["message"]["content"].strip()
            return location
            
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API 오류: {e}")
            raise Exception(f"OpenAI API 호출 중 오류 발생: {e}")
        except Exception as e:
            logging.error(f"장소 추정 오류: {e}")
            raise
    
    def analyze_photo_settings(self, image_path: str) -> Dict[str, Any]:
        """
        사진의 촬영 설정을 분석합니다 (EXIF가 부족한 경우 유용)
        
        Args:
            image_path (str): 이미지 파일 경로
            
        Returns:
            Dict[str, Any]: 예상 촬영 설정
            {
                'focal_length': '예상 초점 거리',
                'aperture': '예상 조리개',
                'shutter_speed': '예상 셔터 속도',
                'iso': '예상 ISO',
                'explanation': '설명'
            }
        """
        try:
            # 이미지 인코딩
            img64 = self.encode_image(image_path)
            
            # API 요청 메시지 구성
            messages = [
                {"role": "system", "content": "당신은 사진 기술 분석 전문가입니다. 카메라 설정과 촬영 기법을 분석할 수 있습니다."},
                {"role": "user", "content": [
                    {"type": "text", "text": "이 사진의 촬영 설정(초점 거리, 조리개, 셔터 속도, ISO)을 추정해주세요. JSON 형식으로 focal_length, aperture, shutter_speed, iso, explanation 필드를 포함하여 응답해주세요."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img64}", "detail": "high"}}
                ]}
            ]
            
            # API 호출
            response = openai.ChatCompletion.create(
                model=self.model,
                max_tokens=500,
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            # 결과 추출 및 JSON 파싱
            content = response["choices"][0]["message"]["content"].strip()
            settings = json.loads(content)
            return settings
            
        except (json.JSONDecodeError, KeyError) as e:
            logging.error(f"JSON 파싱 오류: {e}")
            return {
                "focal_length": "알 수 없음",
                "aperture": "알 수 없음", 
                "shutter_speed": "알 수 없음",
                "iso": "알 수 없음",
                "explanation": "분석 과정에서 오류가 발생했습니다."
            }
        except Exception as e:
            logging.error(f"설정 분석 오류: {e}")
            raise


# 편의를 위한 함수 (기존 호환성 유지)
def predict_location(image_path: str) -> str:
    """
    이미지 속 위치를 추정합니다. (편의 함수)
    
    Args:
        image_path (str): 이미지 파일 경로
        
    Returns:
        str: 추정된 위치
    
    Raises:
        Exception: 처리 오류
    """
    try:
        analyzer = GPTVisionAnalyzer()
        return analyzer.predict_location(image_path)
    except Exception as e:
        logging.error(f"위치 추정 오류: {e}")
        raise
