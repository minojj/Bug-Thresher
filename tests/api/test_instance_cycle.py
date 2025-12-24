# API 기능 테스트 케이스
import requests

def test_vm_list(auth_token):
    headers = {
        "Authorization": f"Bearer {auth_token}"
    }

    response = requests.get(
        "https://portal.gov.elice.cloud/api/user/resource/compute/virtual_machine?skip=0&count=50",
        headers=headers
    )

    assert response.status_code == 200
