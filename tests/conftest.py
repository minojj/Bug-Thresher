# 토큰 로드(Fixture) 및 공통 설정 정의
import pytest

@pytest.fixture(scope="session")
def auth_token():
    with open("token.txt") as f:
        return f.read().strip()

@pytest.fixture(scope="session")
def api_headers(auth_token):
       return {
        "Authorization": f"Bearer {auth_token}",
        "Host": "portal.gov.elice.cloud",
        "Content-Type": "application/json",
        # "Accept": "application/json"
    }