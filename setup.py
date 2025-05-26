"""
EXIF 데이터 분석 및 촬영 습관 개선 도구
캡스톤 디자인 프로젝트 설치 스크립트
"""

from setuptools import setup, find_packages
from pathlib import Path

# README 파일 읽기
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# 요구사항 파일 읽기
requirements = []
try:
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
except FileNotFoundError:
    requirements = [
        'Pillow>=10.0.0',
        'pandas>=2.0.0',
        'numpy>=1.24.0',
        'matplotlib>=3.7.0',
        'seaborn>=0.12.0',
        'openpyxl>=3.1.0',
        'piexif>=1.1.3',
        'python-dotenv>=1.0.0',
        'scikit-learn>=1.3.0'
    ]

setup(
    name="exif-analyzer",
    version="20250526",
    author="김진수",
    author_email="kjs.fficial@gmail.com",
    description="EXIF 데이터 분석 및 촬영 습관 개선 도구",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/exif-analyzer/capstone",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Graphics :: Capture :: Digital Camera",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'exif-analyzer=main:main',
        ],
        'gui_scripts': [
            'exif-analyzer-gui=main:main',
        ],
    },
    include_package_data=True,
    package_data={
        '': ['*.md', '*.txt', '*.yml', '*.yaml'],
        'data': ['*.jpg', '*.jpeg', '*.tiff', '*.tif'],
    },
    project_urls={
        "Bug Reports": "https://github.com/exif-analyzer/capstone/issues",
        "Source": "https://github.com/exif-analyzer/capstone",
        "Documentation": "https://github.com/exif-analyzer/capstone/wiki",
    },
    keywords=[
        "exif", "photography", "image-analysis", "camera-settings", 
        "photo-metadata", "shooting-habits", "capstone-project"
    ],
) 