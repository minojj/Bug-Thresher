# 토큰 로드(Fixture) 및 공통 설정 정의
import pytest
import os
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def generate_fresh_token():
    """새로운 토큰을 자동으로 생성"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://qatrack.elice.io/eci")
        wait = WebDriverWait(driver, 10)
        
        email_field = wait.until(EC.presence_of_element_located((By.NAME, "loginId")))
        email_field.send_keys("qa2team02@elicer.com")
        
        password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        password_field.send_keys("qa2team02!!")
        
        login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        login_button.click()
        
        time.sleep(5)
        
        token = driver.execute_script("return window.localStorage.getItem('accessToken');")
        
        if token:
            # 프로젝트 루트에 token.txt 저장
            token_path = Path(__file__).parent.parent / "token.txt"
            with open(token_path, "w") as f:
                f.write(token)
            return token
        else:
            raise Exception("토큰을 찾을 수 없습니다.")
    finally:
        driver.quit()

@pytest.fixture(scope="session")
def auth_token():
    """토큰을 자동으로 생성하고 반환"""
    return generate_fresh_token()

@pytest.fixture(scope="session")
def api_headers(auth_token):
       return {
        "Authorization": f"Bearer {auth_token}",
        "Host": "portal.gov.elice.cloud",
        "Content-Type": "application/json",
        # "Accept": "application/json"
    }