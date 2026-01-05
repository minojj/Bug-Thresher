from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
import json
import time

# 로그인
LOGIN_URL = "https://qatrack.elice.io/eci/home"
EMAIL = "qa2team02@elicer.com"
PASSWORD = "qa2team02!!"

# Chrome 옵션 (Network 로그 활성화)

options = webdriver.ChromeOptions()
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

driver = webdriver.Chrome(options=options)
driver.get(LOGIN_URL)
time.sleep(2)

# 로그인 자동화

driver.find_element(By.NAME, "loginId").send_keys(EMAIL)

pw = driver.find_element(By.NAME, "password")
pw.send_keys(PASSWORD)
pw.send_keys(Keys.ENTER)

print("로그인 진행 중... Network 요청 대기")

# 토큰이 나올 때까지 기다리는 함수

def wait_for_token(driver):
    logs = driver.get_log("performance")
    for entry in logs:
        message = json.loads(entry["message"])["message"]

        if message.get("method") == "Network.requestWillBeSent":
            headers = message.get("params", {}) \
                             .get("request", {}) \
                             .get("headers", {})

            auth = headers.get("Authorization")
            if auth and auth.startswith("Bearer "):
                return auth.replace("Bearer ", "")

    return False

# WebDriverWait으로 최대 30초 대기

wait = WebDriverWait(driver, 30)
token = wait.until(wait_for_token)

# 토큰 저장

with open("token.txt", "w", encoding="utf-8") as f:
    f.write(token)

print("토큰 자동 추출 성공")
print(token[:30] + "...")

# 종료 제어

input("확인 후 엔터 누르면 브라우저 종료")
driver.quit()
