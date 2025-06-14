import sys
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
import logging
import time
import random
from dateutil import parser  # 날짜 파싱을 위해 추가

# 절대 경로 import를 위한 경로 설정
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent
sys.path.append(str(backend_dir))

from app.database import Base, get_db
from app.model import TrumpStatement

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TruthSocialScraper:
    def __init__(self):
        # Chrome 브라우저 설정
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')  # 테스트할 때는 주석 처리
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 20)
        self.base_url = "https://truthsocial.com/@realDonaldTrump"
    
    def wait_for_page_load(self, delay=15):
        """페이지 로딩을 기다림"""
        logger.info(f"{delay}초 동안 페이지 로딩 대기...")
        time.sleep(delay)
    
    def random_delay(self, min_delay=5, max_delay=10):
        """랜덤 딜레이"""
        delay = random.uniform(min_delay, max_delay)
        logger.info(f"{delay:.1f}초 대기 중...")
        time.sleep(delay)
    
    def parse_date(self, date_str):
        """Truth Social 날짜 문자열을 datetime 객체로 변환"""
        try:
            return parser.parse(date_str)
        except Exception as e:
            logger.error(f"날짜 파싱 오류: {str(e)}")
            return datetime.utcnow()
    
    def smooth_scroll(self, scroll_pause_time=1.0):
        """부드러운 스크롤 구현"""
        current_height = 0
        step = 300  # 한 번에 스크롤할 픽셀 수
        
        # 현재 전체 높이 가져오기
        total_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while current_height < total_height:
            # 점진적으로 스크롤
            current_height += step
            self.driver.execute_script(f"window.scrollTo(0, {current_height});")
            time.sleep(scroll_pause_time)
            
            # 새로운 전체 높이 확인
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            
        logger.info("스크롤 완료")

    def get_trump_posts(self, max_scrolls=5):
        try:
            logger.info(f"Truth Social 접속 시도: {self.base_url}")
            self.driver.get(self.base_url)
            time.sleep(15)  # 초기 로딩 대기
            
            collected_posts = []
            processed_indices = set()
            scroll_count = 0
            
            while scroll_count < max_scrolls:
                # 현재 화면에 보이는 게시글들 찾기 (새로운 선택자 사용)
                current_posts = self.driver.find_elements(
                    By.XPATH,
                    "//div[@data-index][@data-item-index]"
                )
                
                logger.info(f"현재 화면에서 발견된 게시글 컨테이너: {len(current_posts)}개")
                
                # 현재 보이는 게시글들 처리
                for post_container in current_posts:
                    try:
                        # data-index 확인
                        data_index = post_container.get_attribute('data-index')
                        if data_index in processed_indices:
                            continue
                        
                        # 게시글 내용 찾기 (새로운 구조에 맞춤)
                        try:
                            # 먼저 data-markup="true"인 p 태그를 찾고, 그 안의 p 태그에서 텍스트 추출
                            content_wrapper = post_container.find_element(
                                By.XPATH,
                                ".//p[@data-markup='true']"
                            )
                            content_element = content_wrapper.find_element(
                                By.XPATH,
                                ".//p"
                            )
                            content = content_element.text
                            
                        except NoSuchElementException:
                            # 위에서 실패하면 다른 방법 시도
                            try:
                                content_element = post_container.find_element(
                                    By.XPATH,
                                    ".//p[@data-markup='true']"
                                )
                                content = content_element.text
                            except NoSuchElementException:
                                logger.warning(f"게시글 내용을 찾을 수 없음 (index: {data_index})")
                                continue
                        
                        if not content or content.strip() == "":
                            logger.warning(f"빈 게시글 건너뜀 (index: {data_index})")
                            continue
                        
                        # 시간 정보 찾기
                        try:
                            time_element = post_container.find_element(
                                By.XPATH,
                                ".//time[@title]"
                            )
                            time_str = time_element.get_attribute('title')
                            parsed_date = self.parse_date(time_str)
                        except NoSuchElementException:
                            logger.warning(f"시간 정보를 찾을 수 없음 (index: {data_index}), 현재 시간 사용")
                            parsed_date = datetime.utcnow()
                        
                        logger.info(f"새 게시글 수집 (index: {data_index}): {content[:100]}...")
                        logger.info(f"작성 시간: {parsed_date}")
                        
                        collected_posts.append({
                            'content': content,
                            'timestamp': parsed_date,
                            'data_index': data_index
                        })
                        
                        processed_indices.add(data_index)
                        
                        # 각 게시글 처리 후 짧은 대기
                        time.sleep(random.uniform(0.3, 0.7))
                        
                    except Exception as e:
                        logger.error(f"게시글 처리 중 오류 (index: {data_index}): {str(e)}")
                        continue
                
                logger.info(f"현재까지 수집된 총 게시글: {len(collected_posts)}개")
                if processed_indices:
                    sorted_indices = sorted([int(x) for x in processed_indices])
                    logger.info(f"처리된 인덱스: {sorted_indices}")
                
                # 다음 스크롤 수행
                if scroll_count < max_scrolls - 1:
                    logger.info(f"스크롤 {scroll_count + 1}/{max_scrolls} 실행 중...")
                    
                    # 부드러운 스크롤
                    window_height = self.driver.execute_script("return window.innerHeight;")
                    current_position = self.driver.execute_script("return window.pageYOffset;")
                    scroll_step = window_height // 2
                    new_position = current_position + scroll_step
                    
                    self.driver.execute_script(f"window.scrollTo({{top: {new_position}, behavior: 'smooth'}});")
                    
                    # 새로운 컨텐츠 로딩 대기
                    time.sleep(random.uniform(4, 6))
                
                scroll_count += 1
            
            logger.info(f"최종 수집된 게시글: {len(collected_posts)}개")
            if processed_indices:
                sorted_indices = sorted([int(x) for x in processed_indices])
                logger.info(f"수집된 인덱스 범위: {min(sorted_indices)} ~ {max(sorted_indices)}")
            
            return collected_posts
            
        except Exception as e:
            logger.error(f"스크래핑 중 오류 발생: {str(e)}")
            return []
            
        finally:
            self.driver.quit()
        
    def save_to_db(self, posts):
        """수집한 게시글을 데이터베이스에 저장"""
        if not posts:
            logger.warning("저장할 게시글이 없습니다.")
            return
            
        db = next(get_db())
        saved_count = 0
        
        try:
            for post in posts:
                # 중복 체크
                existing = db.query(TrumpStatement).filter_by(
                    original_text=post['content']
                ).first()
                
                if not existing:
                    statement = TrumpStatement(
                        original_text=post['content'],
                        source=f"Truth Social (index: {post.get('data_index', 'unknown')})",
                        posted_at=post['timestamp'],
                    )
                    db.add(statement)
                    saved_count += 1
            
            db.commit()
            logger.info(f"{saved_count}개의 새로운 게시글이 저장되었습니다.")
            
        except Exception as e:
            logger.error(f"데이터베이스 저장 중 오류: {str(e)}")
            db.rollback()
        finally:
            db.close()

def main():
    try:
        scraper = TruthSocialScraper()
        # 스크롤 5번만 실행
        posts = scraper.get_trump_posts(max_scrolls=1000)
        
        if posts:
            print("\n=== 수집된 게시글 ===")
            for i, post in enumerate(posts, 1):
                print(f"\n[게시글 {i}]")
                print(f"내용: {post['content']}")
                print(f"시간: {post['timestamp']}")
                print("-" * 50)
            
            # 저장 전 추가 대기
            time.sleep(5)
            scraper.save_to_db(posts)
        else:
            print("수집된 게시글이 없습니다.")
            
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}")

if __name__ == "__main__":
    main()