# 지도 유틸리티 모듈 - 정적 및 동적 지도 표시
import os
import requests
import folium
import webbrowser
import tempfile
import logging
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from config import MAP_SIZE

def fetch_static_map(lat, lon, zoom=15, marker_color='red', marker_size='m'):
    """
    Yandex Static Maps API를 사용하여 정적 지도 이미지를 가져옵니다.
    
    Args:
        lat (float): 위도
        lon (float): 경도
        zoom (int, optional): 확대 레벨 (0-19). 기본값 15
        marker_color (str, optional): 마커 색상. 기본값 'red'
        marker_size (str, optional): 마커 크기 ('s', 'm', 'l'). 기본값 'm'
        
    Returns:
        PIL.Image: 지도 이미지
        
    Raises:
        ConnectionError: API 연결 실패 시
        Exception: 기타 오류 발생 시
    """
    try:
        # 지도 크기 구성
        width, height = MAP_SIZE
        
        # 마커 스타일 조정
        marker_style = {
            'red': 'pm2rd', 
            'blue': 'pm2bl', 
            'green': 'pm2gn',
            'yellow': 'pm2yw'
        }.get(marker_color, 'pm2rd')
        
        # 마커 크기 조정
        if marker_size == 's':
            marker_style = marker_style.replace('2', '1')
        elif marker_size == 'l':
            marker_style = marker_style.replace('2', '3')
        
        # API URL 구성
        url = (
            "https://static-maps.yandex.ru/1.x/"
            f"?ll={lon},{lat}&size={width},{height}&z={zoom}&l=map"
            f"&pt={lon},{lat},{marker_style}m"
        )
        
        # 요청 및 응답 처리
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        
        # 이미지 로드 및 좌표 정보 추가
        img = Image.open(BytesIO(resp.content))
        img = _add_coordinate_info(img, lat, lon)
        
        return img
        
    except requests.exceptions.RequestException as e:
        logging.error(f"지도 서버 연결 실패: {e}")
        raise ConnectionError(f"지도 서버에 연결할 수 없습니다: {e}")
    except Exception as e:
        logging.error(f"정적 지도 생성 오류: {e}")
        raise

def _add_coordinate_info(img, lat, lon):
    """
    이미지에 좌표 정보를 추가합니다.
    
    Args:
        img (PIL.Image): 원본 이미지
        lat (float): 위도
        lon (float): 경도
        
    Returns:
        PIL.Image: 좌표 정보가 추가된 이미지
    """
    try:
        # 이미지 복사본 작업
        img_with_info = img.copy()
        draw = ImageDraw.Draw(img_with_info)
        
        # 텍스트 정보 설정
        text = f"위도: {lat:.5f}, 경도: {lon:.5f}"
        fill_color = (255, 255, 255)  # 흰색
        shadow_color = (0, 0, 0)      # 검정색
        
        # 텍스트 폰트 설정 (폰트 없으면 기본 폰트 사용)
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()
            
        # 텍스트 위치 계산 (하단 중앙)
        w, h = img.size
        text_width, text_height = draw.textsize(text, font=font) if hasattr(draw, 'textsize') else (100, 15)
        x = (w - text_width) // 2
        y = h - text_height - 10
        
        # 텍스트 배경 박스
        box_padding = 4
        draw.rectangle(
            [(x - box_padding, y - box_padding), 
             (x + text_width + box_padding, y + text_height + box_padding)],
            fill=(0, 0, 0, 160)  # 반투명 검정 배경
        )
        
        # 그림자 효과로 텍스트 그리기
        draw.text((x+1, y+1), text, font=font, fill=shadow_color)
        draw.text((x, y), text, font=font, fill=fill_color)
        
        return img_with_info
    except Exception:
        # 오류 발생 시 원본 이미지 반환
        return img

def open_interactive_map(lat, lon, zoom=15, map_type='OpenStreetMap'):
    """
    Folium 라이브러리를 사용하여 동적 지도를 생성하고 웹 브라우저에서 엽니다.
    
    Args:
        lat (float): 위도
        lon (float): 경도
        zoom (int, optional): 확대 레벨 (0-18). 기본값 15
        map_type (str, optional): 지도 타일 유형. 기본값 'OpenStreetMap'
            - 'OpenStreetMap', 'CartoDB Positron', 'CartoDB Dark_Matter', 'Stamen Terrain'
        
    Returns:
        str: 생성된 임시 HTML 파일 경로
    """
    try:
        # 지도 타일 설정
        tiles = map_type
        if map_type not in ['OpenStreetMap', 'CartoDB Positron', 'CartoDB Dark_Matter', 'Stamen Terrain']:
            tiles = 'OpenStreetMap'
        
        # 지도 생성
        m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles=tiles)
        
        # 마커 추가 및 팝업 정보 설정
        popup_text = f"위도: {lat:.5f}<br>경도: {lon:.5f}"
        folium.Marker(
            [lat, lon], 
            popup=popup_text,
            tooltip="좌표 정보",
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)
        
        # 원형 영역 표시 (200m 반경)
        folium.Circle(
            [lat, lon],
            radius=200,
            color='blue',
            fill=True,
            fill_color='blue',
            fill_opacity=0.2
        ).add_to(m)
        
        # 임시 HTML 파일 생성
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
        m.save(tmp.name)
        
        # 웹 브라우저에서 파일 열기
        webbrowser.open(f"file://{tmp.name}")
        
        return tmp.name
    except Exception as e:
        logging.error(f"동적 지도 생성 오류: {e}")
        raise
