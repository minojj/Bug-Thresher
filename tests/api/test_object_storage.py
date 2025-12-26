import pytest
import requests
import uuid


base_url = "https://portal.gov.elice.cloud/api/user/resource/storage/object_storage"


class TestBucketCRUD:
    created_id = None

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

        # 생성된 버킷 ID 저장
        TestBucketCRUD.created_id = response_json["id"]


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


    def test_OS006_get_new_bucket(self, api_headers):
        bucket_id = TestBucketCRUD.created_id
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
        assert response_json["name"] == "team2"
        assert response_json["zone_id"] is not None
        assert response_json["size_gib"] == 10


    def test_OS007_patch_bucket_name(self, api_headers):
        bucket_id = TestBucketCRUD.created_id
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


    def test_OS009_delete_bucket(self, api_headers):
        bucket_id = TestBucketCRUD.created_id
        url = f"{base_url}/{bucket_id}"

        response = requests.delete(url, headers=api_headers)
        # 상태 코드 검증
        assert response.status_code == 200, f"⛔ [FAIL] 버킷 삭제 실패 - 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_json = response.json()
        assert isinstance(response_json, dict)
        assert response_json["id"] == bucket_id
        assert response_json["status"] == "deleting"



class TestBucketEdgeCases:

    @pytest.fixture
    def setup_bucket(self, api_headers):
        random_name = f"team2-edge-{uuid.uuid4().hex[:6]}"
        payload = {
            "name": random_name,
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "size_gib": 10,
            "tags": {}
        }
        response = requests.post(base_url, headers=api_headers, json=payload)
        self.edge_id = response.json()["id"]
        self.edge_name = random_name
        yield

        requests.delete(f"{base_url}/{self.edge_id}", headers=api_headers)


    # 동일 이름 버킷 생성
    def test_OS002_post_duplicate_bucket(self, api_headers, setup_bucket):
        payload = {
            "name": self.edge_name,
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


    # 요청 바디 값 누락 생성
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


    # 잘못된 URL 입력 조회
    def test_OS005_get_with_wrong_url(self, api_headers):
        url = f"{base_url}?count=50.."
        response = requests.get(url, headers=api_headers)
        # 상태 코드 검증
        assert response.status_code == 422, f"⛔ [FAIL] 422와 다른 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_json = response.json()
        assert isinstance(response_json, dict)
        assert "not valid" in response_json["message"]



    # default 값이 아닌 필드로 수정
    @pytest.mark.xfail(reason="PATCH 요청에서 잘못된 필드 전달 시 200 OK 반환되는 문제")
    def test_OS008_patch_invalid_field(self, api_headers, setup_bucket):
        url = f"{base_url}/{self.edge_id}"
        payload = {"id": "team2-edge-01"}

        response = requests.patch(url, headers=api_headers, json=payload)
        # 상태 코드 검증
        assert response.status_code == 422, f"⛔ [FAIL] 422와 다른 상태 코드: {response.status_code}"
        response_json = response.json()
        # 응답 바디 검증
        assert isinstance(response_json, dict)
        assert "not valid" in response_json["message"]
    

    # 동일 버킷 재삭제
    def test_OS010_delete_bucket_again(self, api_headers, setup_bucket):
        # 삭제 후 재삭제 시도
        requests.delete(f"{base_url}/{self.edge_id}", headers=api_headers)
        response = requests.delete(f"{base_url}/{self.edge_id}", headers=api_headers)
        
        # 상태 코드 검증
        assert response.status_code == 409, f"⛔ [FAIL] 409와 다른 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_json = response.json()
        assert isinstance(response_json, dict)
        assert response_json["code"] == "unexpected_status"
        assert "unexpected status" in response_json["message"]



class 