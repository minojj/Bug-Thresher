# 토큰 로드(Fixture) 및 공통 설정 정의
import pytest

@pytest.fixture(scope="session")
def auth_token():
    with open("token.txt") as f:
        return f.read().strip()
