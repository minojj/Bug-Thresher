import pytest
import requests
import uuid


class TestBucketCRUD:

    def test_OS001_post_new_bucket(self, api_headers, resource_factory, base_url_object_storage):
        payload = {
            "name": f"team2-{uuid.uuid4().hex[:6]}",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "size_gib": 10,
            "tags": {}
        }
        new_bucket = resource_factory(base_url_object_storage, payload)
        # 응답 바디 검증
        assert isinstance(new_bucket, dict)
        assert "id" in new_bucket
        assert new_bucket["id"] is not None


        # 동일 이름 버킷 재생성(예외)
    def test_OS002_post_duplicate_bucket(self, api_headers, existing_bucket, base_url_object_storage):
        bucket_name = existing_bucket["name"]
        payload = {
            "name": bucket_name,
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "size_gib": 10,
            "tags": {}
        }
        response = requests.post(base_url_object_storage, headers=api_headers, json=payload)
        # 상태 코드 검증
        assert response.status_code == 409, f"⛔ [FAIL] 409와 다른 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_json = response.json()
        assert isinstance(response_json, dict)
        assert "already exists" in response_json["message"]


        # 요청 바디 값 누락 생성(예외)
    def test_OS003_post_with_missing_body(self, api_headers, base_url_object_storage):
        payload = {
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "size_gib": 10,
            "tags": {}
        }
        response = requests.post(base_url_object_storage, headers=api_headers, json=payload)
        # 상태 코드 검증
        assert response.status_code == 422, f"⛔ [FAIL] 422와 다른 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_json = response.json()
        assert isinstance(response_json, dict)
        assert "not valid" in response_json["message"]


    def test_OS004_get_all_list(self, api_headers, base_url_object_storage):
        url = f"{base_url_object_storage}?count=50"
        response = requests.get(url, headers=api_headers)
        # 상태 코드 검증
        assert response.status_code == 200, f"⛔ [FAIL] 버킷 목록 조회 실패 - 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_list = response.json()
        assert isinstance(response_list, list)
        assert len(response_list) > 0
        assert response_list[0]["id"] is not None


        # 잘못된 URL 입력 조회(예외))
    def test_OS005_get_with_wrong_url(self, api_headers, base_url_object_storage):
        url = f"{base_url_object_storage}?count=50.."
        response = requests.get(url, headers=api_headers)
        # 상태 코드 검증
        assert response.status_code == 422, f"⛔ [FAIL] 422와 다른 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_json = response.json()
        assert isinstance(response_json, dict)
        assert "not valid" in response_json["message"]


    def test_OS006_get_new_bucket(self, api_headers, existing_bucket, base_url_object_storage):
        bucket_id = existing_bucket["id"]
        bucket_name = existing_bucket["name"]

        url = f"{base_url_object_storage}/{bucket_id}"
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


    def test_OS007_patch_bucket_name(self, api_headers, existing_bucket, base_url_object_storage):
        bucket_id = existing_bucket["id"]
        bucket_name = existing_bucket["name"]
        url = f"{base_url_object_storage}/{bucket_id}"
        payload = {"name": "team2-01"}

        response = requests.patch(url, headers=api_headers, json=payload)
        assert response.status_code == 200, f"⛔ [FAIL] 버킷 수정 실패 - 상태 코드: {response.status_code}"
        response_json = response.json()
        # 응답 바디 검증
        assert isinstance(response_json, dict)
        assert response_json["id"] == bucket_id
        assert response_json["id"] is not None
        # 수정된 이름 검증
        response = requests.get(url, headers=api_headers)
        assert response.status_code == 200, f"⛔ [FAIL] 버킷 이름 재수정 실패 - 상태 코드: {response.status_code}"
        response_json = response.json()
        assert response_json["name"] == "team2-01"
        assert response_json["id"] == bucket_id


        # default 값이 아닌 필드로 수정(예외)
    @pytest.mark.xfail(reason="PATCH 요청에서 잘못된 필드 전달 시 200 OK 반환되는 문제")
    def test_OS008_patch_invalid_field(self, api_headers, existing_bucket, base_url_object_storage):
        bucket_id = existing_bucket["id"]
        url = f"{base_url_object_storage}/{bucket_id}"
        payload = {"id": "team2-01"}

        response = requests.patch(url, headers=api_headers, json=payload)
        # 상태 코드 검증
        assert response.status_code == 422, f"⛔ [FAIL] 422와 다른 상태 코드: {response.status_code}"
        response_json = response.json()
        # 응답 바디 검증
        assert isinstance(response_json, dict)
        assert "not valid" in response_json["message"]


    def test_OS009_delete_bucket(self, api_headers, existing_bucket, base_url_object_storage):
        bucket_id = existing_bucket["id"]
        url = f"{base_url_object_storage}/{bucket_id}"

        response = requests.delete(url, headers=api_headers)
        assert response.status_code == 200, f"⛔ [FAIL] 버킷 삭제 실패 - 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_json = response.json()
        assert isinstance(response_json, dict)
        assert response_json["id"] == bucket_id
        assert response_json["status"] == "deleting"


        # 동일 버킷 재삭제(예외)
    def test_OS010_delete_bucket_again(self, api_headers, existing_bucket, base_url_object_storage):
        bucket_id = existing_bucket["id"]
        # 삭제 후 재삭제 시도
        requests.delete(f"{base_url_object_storage}/{bucket_id}", headers=api_headers)
        response = requests.delete(f"{base_url_object_storage}/{bucket_id}", headers=api_headers)
        # 상태 코드 검증
        assert response.status_code == 409, f"⛔ [FAIL] 409와 다른 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_json = response.json()
        assert isinstance(response_json, dict)
        assert response_json["code"] == "unexpected_status"
        assert "unexpected status" in response_json["message"]



class TestUserCRUD:

    def test_OS019_post_new_user(self, api_headers, resource_factory, base_url_object_storage):
        payload = {
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "name": f"team2-{uuid.uuid4().hex[:6]}",
            "tags": {}
            }
        new_user = resource_factory(f"{base_url_object_storage}/user", payload)
        # 응답 바디 검증
        assert isinstance(new_user, dict)
        assert "id" in new_user
        assert new_user["id"] is not None


        # 동일 사용자 재생성(예외)
    def test_OS020_post_duplicate_user(self, api_headers, existing_user, base_url_object_storage):
        user_name = existing_user["name"]
        payload = {
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "name": user_name,
            "tags": {}
        }
        response = requests.post(f"{base_url_object_storage}/user", headers=api_headers, json=payload)
        # 상태 코드 검증
        assert response.status_code == 409, f"⛔ [FAIL] 409와 다른 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_json = response.json()
        assert isinstance(response_json, dict)
        assert "already exists" in response_json["message"]


    def test_OS021_get_all_list(self, api_headers, base_url_object_storage):
        url = f"{base_url_object_storage}/user?count=50"
        response = requests.get(url, headers=api_headers)
        # 상태 코드 검증
        assert response.status_code == 200, f"⛔ [FAIL] 사용자 목록 조회 실패 - 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_list = response.json()
        assert isinstance(response_list, list)
        assert len(response_list) > 0
        assert response_list[0]["id"] is not None


    def test_OS022_get_new_user(self, api_headers, existing_user, base_url_object_storage):
        user_id = existing_user["id"]
        user_name = existing_user["name"]
        url = f"{base_url_object_storage}/user/{user_id}"

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
        # assert response_json["status"] == "activated", f"⛔ [FAIL] 예상과 다른 상태: {response.text}"


    def test_OS023_patch_user_name(self, api_headers, existing_user, base_url_object_storage):
        user_id = existing_user["id"]
        user_name = existing_user["name"]
        url = f"{base_url_object_storage}/user/{user_id}"
        payload = {"name": "team2-01"}

        response = requests.patch(url, headers=api_headers, json=payload)
        assert response.status_code == 200, f"⛔ [FAIL] 사용자 수정 실패 - 상태 코드: {response.status_code}"
        response_json = response.json()
        # 응답 바디 검증
        assert isinstance(response_json, dict)
        assert response_json["id"] == user_id
        assert response_json["id"] is not None
        # 수정 확인
        response = requests.get(url, headers=api_headers)
        assert response.status_code == 200, f"⛔ [FAIL] 사용자 생성 실패 - 상태 코드: {response.status_code}"
        response_json = response.json()
        assert response_json["name"] == "team2-01"
        assert response_json["id"] == user_id


    @pytest.mark.xfail(reason="PATCH 요청에서 잘못된 필드 전달 시 200 OK 반환되는 문제")
    def test_OS024_patch_invalid_field(self, api_headers, existing_user, base_url_object_storage):
        user_id = existing_user["id"]
        url = f"{base_url_object_storage}/user/{user_id}"
        payload = {"id": "team2-01"}

        response = requests.patch(url, headers=api_headers, json=payload)
        # 상태 코드 검증
        assert response.status_code == 422, f"⛔ [FAIL] 422와 다른 상태 코드: {response.status_code}"
        response_json = response.json()
        # 응답 바디 검증
        assert isinstance(response_json, dict)
        assert "not valid" in response_json["message"]


    def test_OS025_delete_user(self, api_headers, existing_user, base_url_object_storage):
        user_id = existing_user["id"]
        url = f"{base_url_object_storage}/user/{user_id}"

        response = requests.delete(url, headers=api_headers)
        # 상태 코드 검증
        assert response.status_code == 200, f"⛔ [FAIL] 사용자 삭제 실패 - 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_json = response.json()
        assert isinstance(response_json, dict)
        assert response_json["id"] == user_id
        assert response_json["status"] == "deleting"


class TestUserGrantCRUD:

    @pytest.fixture
    def existing_user_grant(self, api_headers, existing_bucket, existing_user, base_url_object_storage):
        payload = {
            "object_storage_id": existing_bucket["id"],
            "object_storage_user_id": existing_user["id"],
            "permission": "read_write",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0"
            }
        
        response = requests.post(f"{base_url_object_storage}/user_grant", headers=api_headers, json=payload)
        assert response.status_code == 200, f"⛔ [FAIL] 사용자 권한 생성 실패 - {response.status_code}: {response.text}"
        grant_id = response.json()["id"]
        yield {"id": grant_id, "payload": payload}
        requests.delete(f"{base_url_object_storage}/user_grant/{grant_id}", headers=api_headers)

    # def test_OS011_post_user_grant(self, api_headers, existing_bucket, existing_user, base_url_object_storage):
    #     bucket_id = existing_bucket["id"]
    #     user_id = existing_user["id"]
    #     payload = {
    #         "object_storage_id": bucket_id,
    #         "object_storage_user_id": user_id,
    #         "permission": "read_write",
    #         "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0"
    #         }

    #     response = requests.post(f"{base_url_object_storage}/user_grant", headers=api_headers, json=payload)
    #     # 상태 코드 검증
    #     assert response.status_code == 200, f"⛔ [FAIL] 사용자 권한 생성 실패 - {response.status_code}: {response.text}"
    #     # 응답 바디 검증
    #     response_json = response.json()
    #     assert isinstance(response_json, dict)
    #     assert "id" in response_json
    #     assert response_json["id"] is not None
    #     requests.delete(f"{base_url_object_storage}/user_grant/{response_json['id']}", headers=api_headers)


    def test_OS012_post_duplicate_user_grant(self, api_headers, existing_user_grant,base_url_object_storage):
        payload = existing_user_grant["payload"]

        response = requests.post(f"{base_url_object_storage}/user_grant", headers=api_headers, json=payload)
        # 상태 코드 검증
        assert response.status_code == 409, f"⛔ [FAIL] 409와 다른 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_json = response.json()
        assert isinstance(response_json, dict)
        assert "already exists" in response_json["message"]


    def test_OS013_get_all_user(self, api_headers, existing_bucket, existing_user, base_url_object_storage):
        url = f"{base_url_object_storage}/user?count=100"

        response = requests.get(url, headers=api_headers)
        # 상태 코드 검증
        assert response.status_code == 200, f"⛔ [FAIL] 사용자 권한 목록 조회 실패 - 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_list = response.json()
        assert isinstance(response_list, list)
        assert len(response_list) > 0
        assert response_list[0]["id"] is not None


    def test_OS014_get_user_by_name(self, api_headers, existing_bucket, existing_user, base_url_object_storage):
        user_id = existing_user["id"]
        user_name = existing_user["name"]
        url = f"{base_url_object_storage}/user?filter_name_like=%25{user_name}%25&count=100"

        response = requests.get(url, headers=api_headers)
        # 상태 코드 검증
        assert response.status_code == 200, f"⛔ [FAIL] 사용자 권한 단건 조회 실패 - 상태 코드: {response.status_code}"
        # 응답 바디 검증
        response_json = response.json()
        assert isinstance(response_json, list)
        # 조회 사용자 검증
        exact_user = [user for user in response_json if user["name"].stripi() == user_name]
        assert len(exact_user) == 1
        assert exact_user[0]["id"] == user_id
        assert exact_user[0]["name"] == user_name
        assert exact_user[0]["zone_id"] is not None
        assert exact_user[0]["status"] == "activated"