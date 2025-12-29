# 토큰 로드(Fixture) 및 공통 설정 정의
import pytest
import requests
import os
import uuid
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.utils.api_util import wait_for_status  # 수정된 유틸 함수 임포트
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

# API Base URL Fixtures
@pytest.fixture(scope="session")
def base_url_infra():
    """인프라 API Base URL"""
    return os.getenv("BASE_URL_INFRA", "https://portal.gov.elice.cloud/api/user")

@pytest.fixture(scope="session")
def base_url_compute():
    """컴퓨트 API Base URL"""
    return os.getenv("BASE_URL_COMPUTE", "https://portal.gov.elice.cloud/api/user/resource/compute")

@pytest.fixture(scope="session")
def base_url_block_storage():
    """블록 스토리지 API Base URL"""
    return os.getenv("BASE_URL_BLOCK_STORAGE", "https://portal.gov.elice.cloud/api/user/resource/storage/block_storage")

@pytest.fixture(scope="session")
def base_url_network():
    """네트워크 API Base URL"""
    return os.getenv("BASE_URL_NETWORK", "https://portal.gov.elice.cloud/api/user/resource/network")

@pytest.fixture(scope="session")
def base_url_object_storage():
    """오브젝트 스토리지 API Base URL"""
    return os.getenv("BASE_URL_OBJECT_STORAGE", "https://portal.gov.elice.cloud/api/user/resource/storage/object_storage")

# Setup/Teardown 공통 Fixture
@pytest.fixture
def resource_factory(api_headers):
    
    """
    1. 리소스 생성/삭제 공통 Fixture
    2. 반환값: {"id": resource_id, "name": resource_name}
    3. 이미 삭제된 리소스는 teardown 단계에서 제외
    """
    created_resources = []

    def _create(base_url, payload):
        data = create_resource(base_url, api_headers, payload)
        resource_id = data["id"]
        resource_name = payload["name"]
        # 나중에 지울 리스트에 저장 (URL과 ID 쌍)
        created_resources.append({"url": base_url, "id": resource_id, "name": resource_name, "deleting": False})
        return {"id": resource_id, "name": resource_name}

    yield _create

    # Teardown: 생성된 역순으로 삭제
    for resource in reversed(created_resources):
            try:
                delete_resource(resource["url"], api_headers, resource["id"])
            except Exception as e:
                pass

def create_resource(url, headers, payload):
    """리소스 생성을 위한 공통 함수"""
    response = requests.post(url, headers=headers, json=payload)
    assert response.status_code == 200, f"⛔ [FAIL] 생성 실패: {response.text}"
    return response.json()

def delete_resource(url, headers,resource_id):
    """리소스 삭제를 위한 공통 함수"""
    response = requests.delete(f"{url}/{resource_id}", headers=headers)
    assert response.status_code == 200, f"⛔ [FAIL] 삭제 실패, {response.status_code}: {response.text}"

# --- Helpers Fixture (유틸 함수 연결) ---
@pytest.fixture
def api_helpers():
    class Helpers:
        # api_util.py에 정의된 지수 백오프 기반 함수를 그대로 사용
        wait_for_status = staticmethod(wait_for_status)
    return Helpers()

# --- 기타 공통 Fixtures (Object Storage 등) ---
@pytest.fixture
def existing_bucket(resource_factory, base_url_object_storage):
    payload = {
        "name": f"team2-{uuid.uuid4().hex[:6]}",
        "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
        "size_gib": 10,
        "tags": {}
    }
    return resource_factory(base_url_object_storage, payload)

@pytest.fixture
def existing_user(resource_factory, base_url_object_storage):
    payload = {
        "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
        "name": f"team2-{uuid.uuid4().hex[:6]}",
        "tags": {}
        }
    return resource_factory(f"{base_url_object_storage}/user", payload)
