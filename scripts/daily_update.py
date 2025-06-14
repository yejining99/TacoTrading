#!/usr/bin/env python3
"""
TACO Trading 일일 자동 업데이트 스크립트
매일 실행하여 트럼프 SNS 크롤링, LLM 분석, ETF 업데이트를 수행합니다.
"""

import os
import sys
import logging
import subprocess
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 경로 설정
script_dir = Path(__file__).parent
project_root = script_dir.parent
backend_dir = project_root / "backend"
app_dir = backend_dir / "app"

# 로깅 설정
log_dir = script_dir / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"daily_update_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_script(script_path, description):
    """스크립트를 실행하고 결과를 로깅합니다."""
    try:
        logger.info(f"시작: {description}")
        
        # Python 가상환경 활성화
        venv_python = backend_dir / "venv" / "Scripts" / "python.exe"
        if not venv_python.exists():
            venv_python = sys.executable  # 가상환경이 없으면 시스템 Python 사용
        
        result = subprocess.run(
            [str(venv_python), str(script_path)],
            cwd=str(app_dir),
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            logger.info(f"성공: {description}")
            if result.stdout:
                logger.info(f"출력: {result.stdout}")
        else:
            logger.error(f"실패: {description}")
            logger.error(f"에러: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"예외 발생 - {description}: {str(e)}")
        return False
    
    return True

def main():
    """메인 실행 함수"""
    logger.info("=" * 50)
    logger.info("TACO Trading 일일 업데이트 시작")
    logger.info("=" * 50)
    
    # 실행할 스크립트들 (순서 중요)
    scripts = [
        (app_dir / "crowling.py", "트럼프 SNS 크롤링"),
        (app_dir / "trump_analyzer.py", "LLM 분석"),
        (app_dir / "etf_updater.py", "ETF 데이터 업데이트")
    ]
    
    success_count = 0
    total_count = len(scripts)
    
    for script_path, description in scripts:
        if script_path.exists():
            if run_script(script_path, description):
                success_count += 1
            else:
                logger.warning(f"스크립트 실행 실패: {script_path}")
        else:
            logger.error(f"스크립트 파일을 찾을 수 없습니다: {script_path}")
    
    # 결과 요약
    logger.info("=" * 50)
    logger.info(f"업데이트 완료: {success_count}/{total_count} 성공")
    logger.info("=" * 50)
    
    if success_count == total_count:
        logger.info("모든 작업이 성공적으로 완료되었습니다!")
        return 0
    else:
        logger.warning("일부 작업이 실패했습니다. 로그를 확인해주세요.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 