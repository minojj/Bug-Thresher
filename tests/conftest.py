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
from dotenv import load_dotenv
load_dotenv()

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
        
        # .env의 LOGIN_ID 사용
        email_field = wait.until(EC.presence_of_element_located((By.NAME, "loginId")))
        email_field.send_keys(os.getenv("LOGIN_ID"))

        # .env의 PASSWORD 사용
        password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        password_field.send_keys(os.getenv("PASSWORD"))
        
        login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        login_button.click()
        wait.until(EC.url_contains("/eci/home"))
        
        token = driver.execute_script("return window.localStorage.getItem('accessToken');")
        
        return token
        
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