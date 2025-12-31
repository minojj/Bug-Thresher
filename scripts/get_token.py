# Selenium을 실행하여 인증 토큰을 추출/저장하는 스크립트
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from dotenv import load_dotenv

load_dotenv()

driver = webdriver.Chrome()
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

if token:
    print(f"Access Token: {token}")
else:
    print("토큰을 찾을 수 없습니다. localStorage 확인:")
    all_storage = driver.execute_script("return JSON.stringify(window.localStorage);")
    print(all_storage)

with open("token.txt", "w") as f:
    f.write(token)

driver.quit()
