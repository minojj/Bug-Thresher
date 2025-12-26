import pytest
import requests
import uuid


base_url = "https://portal.gov.elice.cloud/api/user/resource/storage/object_storage"


class TestBucketCRUD:

    @pytest.fixture
    def setup_bucket(self, api_headers):
        random_name = f"team2-{uuid.uuid4().hex[:6]}"
        payload = {
            "name": random_name,
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "size_gib": 10,
            "tags": {}
        }
        response = requests.post(base_url, headers=api_headers, json=payload)
        assert response.status_code == 200, f"⛔ [FAIL] Setup 실패, {response.status_code}: {response.text}"
        response_json = response.json()
        yield {"id": response_json["id"], "name": random_name}

        requests.delete(f"{base_url}/{response_json['id']}", headers=api_headers)


    def test_OS001_post_new_bucket(self, api_headers):
        payload = {
            "name": "team2",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "size_gib": 10,
            "tags": {}
        }
        response = requests.post(base_url, headers=api_headers, json=payload)
        # 상태 코드 검증
        assert response.status_code == 200, f"⛔ [FAIL] 버킷 생성 실패 - 상태 코드: {response.status_code}"
        response_json = response.json()
        # 응답 바디 검증
        assert isinstance(response_json, dict)
        assert "id" in response_json 
        assert response_json["id"] is not None

        requests.delete(f"{base_url}/{response_json['id']}", headers=api_headers)


        # 동일 이름 버킷 생성(예외)
    def test_OS002_post_duplicate_bucket(self, api_headers, setup_bucket):
        bucket_name = setup_bucket["name"]
        payload = {
            "name": bucket_name,
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "size_gib": 10,
            "tags": {}
        }
        response = requests.post(base_url, headers=api_headers, json=payload)
        # 상태 코드 검증
        assert response.status_code == 409, f"⛔ [FAIL] 409와 다른 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_json = response.json()
        assert isinstance(response_json, dict)
        assert "already exists" in response_json["message"]


        # 요청 바디 값 누락 생성(예외)
    def test_OS003_post_with_missing_body(self, api_headers):
        payload = {
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "size_gib": 10,
            "tags": {}
        }
        response = requests.post(base_url, headers=api_headers, json=payload)
        # 상태 코드 검증
        assert response.status_code == 422, f"⛔ [FAIL] 422와 다른 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_json = response.json()
        assert isinstance(response_json, dict)
        assert "not valid" in response_json["message"]


    def test_OS004_get_all_list(self, api_headers):
        url = f"{base_url}?count=50"
        response = requests.get(url, headers=api_headers)
        # 상태 코드 검증
        assert response.status_code == 200, f"⛔ [FAIL] 버킷 목록 조회 실패 - 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_list = response.json()
        assert isinstance(response_list, list)
        assert len(response_list) > 0
        assert response_list[0]["id"] is not None


        # 잘못된 URL 입력 조회(예외))
    def test_OS005_get_with_wrong_url(self, api_headers):
        url = f"{base_url}?count=50.."
        response = requests.get(url, headers=api_headers)
        # 상태 코드 검증
        assert response.status_code == 422, f"⛔ [FAIL] 422와 다른 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_json = response.json()
        assert isinstance(response_json, dict)
        assert "not valid" in response_json["message"]


    def test_OS006_get_new_bucket(self, api_headers, setup_bucket):
        bucket_id = setup_bucket["id"]
        bucket_name = setup_bucket["name"]

        url = f"{base_url}/{bucket_id}"
        response = requests.get(url, headers=api_headers)
        assert response.status_code == 200, f"⛔ [FAIL] 버킷 단건 조회 실패 - 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_json = response.json()
        assert isinstance(response_json, dict)
        assert "id" in response_json
        assert "name" in response_json
        assert "zone_id" in response_json
        assert "size_gib" in response_json
        assert response_json["id"] == bucket_id
        assert response_json["name"] == bucket_name
        assert response_json["zone_id"] is not None
        assert response_json["size_gib"] == 10


    def test_OS007_patch_bucket_name(self, api_headers, setup_bucket):
        bucket_id = setup_bucket["id"]
        url = f"{base_url}/{bucket_id}"
        payload = {"name": "team2-01"}

        response = requests.patch(url, headers=api_headers, json=payload)
        # 상태 코드 검증
        assert response.status_code == 200, f"⛔ [FAIL] 버킷 수정 실패 - 상태 코드: {response.status_code}"
        response_json = response.json()
        # 응답 바디 검증
        assert isinstance(response_json, dict)
        assert response_json["id"] == bucket_id
        assert response_json["id"] is not None


        # default 값이 아닌 필드로 수정(예외)
    @pytest.mark.xfail(reason="PATCH 요청에서 잘못된 필드 전달 시 200 OK 반환되는 문제")
    def test_OS008_patch_invalid_field(self, api_headers, setup_bucket):
        bucket_id = setup_bucket["id"]
        url = f"{base_url}/{bucket_id}"
        payload = {"id": "team2-01"}

        response = requests.patch(url, headers=api_headers, json=payload)
        # 상태 코드 검증
        assert response.status_code == 422, f"⛔ [FAIL] 422와 다른 상태 코드: {response.status_code}"
        response_json = response.json()
        # 응답 바디 검증
        assert isinstance(response_json, dict)
        assert "not valid" in response_json["message"]


    def test_OS009_delete_bucket(self, api_headers, setup_bucket):
        bucket_id = setup_bucket["id"]
        url = f"{base_url}/{bucket_id}"

        response = requests.delete(url, headers=api_headers)
        # 상태 코드 검증
        assert response.status_code == 200, f"⛔ [FAIL] 버킷 삭제 실패 - 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_json = response.json()
        assert isinstance(response_json, dict)
        assert response_json["id"] == bucket_id
        assert response_json["status"] == "deleting"


        # 동일 버킷 재삭제(예외)
    def test_OS010_delete_bucket_again(self, api_headers, setup_bucket):
        bucket_id = setup_bucket["id"]
        # 삭제 후 재삭제 시도
        requests.delete(f"{base_url}/{bucket_id}", headers=api_headers)
        response = requests.delete(f"{base_url}/{bucket_id}", headers=api_headers)

        # 상태 코드 검증
        assert response.status_code == 409, f"⛔ [FAIL] 409와 다른 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_json = response.json()
        assert isinstance(response_json, dict)
        assert response_json["code"] == "unexpected_status"
        assert "unexpected status" in response_json["message"]



class TestUserCRUD:

    @pytest.fixture
    def setup_user(self, api_headers):
        random_name = f"team2-{uuid.uuid4().hex[:6]}"
        payload = {
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "name": random_name,
            "tags": {}
            }
        response = requests.post(f"{base_url}/user", headers=api_headers, json=payload)
        assert response.status_code == 200, f"⛔ [FAIL] Setup 실패, {response.status_code}: {response.text}"
        response_json = response.json()
        yield {"id": response_json["id"], "name": random_name}

        requests.delete(f"{base_url}/{response_json['id']}", headers=api_headers)


    def test_OS019_post_new_user(self, api_headers):
        payload = {
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "name": "team2",
            "tags": {}
            }
        url = f"{base_url}/user"
        response = requests.post(url, headers=api_headers, json=payload)
        # 상태 코드 검증
        assert response.status_code == 200, f"⛔ [FAIL] 사용자 생성 실패 - 상태 코드: {response.status_code}"
        response_json = response.json()
        # 응답 바디 검증
        assert isinstance(response_json, dict)
        assert "id" in response_json 
        assert response_json["id"] is not None

        requests.delete(f"{base_url}/user/{response_json['id']}", headers=api_headers)


        # 동일 사용자 생성(예외)
    def test_OS020_post_duplicate_user(self, api_headers, setup_user):
        user_name = setup_user["name"]
        payload = {
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "name": user_name,
            "tags": {}
        }
        response = requests.post(f"{base_url}/user", headers=api_headers, json=payload)
        # 상태 코드 검증
        assert response.status_code == 409, f"⛔ [FAIL] 409와 다른 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_json = response.json()
        assert isinstance(response_json, dict)
        assert "already exists" in response_json["message"]


    def test_OS021_get_all_list(self, api_headers):
        url = f"{base_url}/user?count=50"
        response = requests.get(url, headers=api_headers)
        # 상태 코드 검증
        assert response.status_code == 200, f"⛔ [FAIL] 사용자 목록 조회 실패 - 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_list = response.json()
        assert isinstance(response_list, list)
        assert len(response_list) > 0
        assert response_list[0]["id"] is not None


    def test_OS022_get_new_user(self, api_headers, setup_user):
        user_id = setup_user["id"]
        user_name = setup_user["name"]

        url = f"{base_url}/user/{user_id}"
        response = requests.get(url, headers=api_headers)
        assert response.status_code == 200, f"⛔ [FAIL] 사용자 단건 조회 실패 - 상태 코드: {response.status_code}, 내용: {response.text}"
        # 응답 바디 검증
        response_json = response.json()
        assert isinstance(response_json, dict)
        assert "id" in response_json
        assert "name" in response_json
        assert "zone_id" in response_json
        assert "status" in response_json
        assert response_json["id"] == user_id
        assert response_json["name"] == user_name
        assert response_json["zone_id"] is not None
        assert response_json["status"] == "activated", f"⛔ [FAIL] 예상과 다른 상태: {response.text}"


    def test_OS023_patch_user_name(self, api_headers, setup_user):
        user_id = setup_user["id"]
        url = f"{base_url}/user/{user_id}"
        payload = {"name": "team2-01"}

        response = requests.patch(url, headers=api_headers, json=payload)
        # 상태 코드 검증
        assert response.status_code == 200, f"⛔ [FAIL] 사용자 수정 실패 - 상태 코드: {response.status_code}"
        response_json = response.json()
        # 응답 바디 검증
        assert isinstance(response_json, dict)
        assert response_json["id"] == user_id
        assert response_json["id"] is not None


    def test_OS024_delete_user(self, api_headers, setup_user):
        user_id = setup_user["id"]
        url = f"{base_url}/user/{user_id}"

        response = requests.delete(url, headers=api_headers)
        # 상태 코드 검증
        assert response.status_code == 200, f"⛔ [FAIL] 사용자 삭제 실패 - 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_json = response.json()
        assert isinstance(response_json, dict)
        assert response_json["id"] == user_id
        assert response_json["status"] == "deleting"