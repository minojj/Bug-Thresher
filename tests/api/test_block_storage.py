from email import errors
import requests
import pytest
import uuid
import allure


def get_prepared_block_storage_id(api_headers, base_url_block_storage):
    """
    prepared 상태의 block storage ID를 찾아 반환
    없으면 새로 생성
    """
    response = requests.get(base_url_block_storage, headers=api_headers)
    if response.status_code == 200:
        block_storages = response.json()
        # prepared 상태의 block storage 찾기
        for bs in block_storages:
            if bs.get("status") == "prepared":
                return bs["id"]
    
    # prepared 상태가 없으면 새로 생성
    payload = {
        "name": f"test-bs-{uuid.uuid4().hex[:6]}",
        "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
        "size_gib": 10,
        "dr": False,
        "image_id": None,
        "snapshot_id": None
    }
    create_response = requests.post(base_url_block_storage, headers=api_headers, json=payload)
    if create_response.status_code == 200:
        new_bs = create_response.json()
        return new_bs["id"]
    
    # 생성 실패시 기본값 반환 (테스트 실패하도록)
    raise Exception(f"prepared block storage를 찾거나 생성할 수 없습니다: {create_response.text}")


class TestBlockStorageCRUD:
    """블록 스토리지 API 테스트 클래스"""

    def test_BS001_list_exists_look_up(self, api_headers, base_url_block_storage):
        """BS-001: 데이터가 있는 경우 목록 조회"""
        headers = api_headers
        url = f"{base_url_block_storage}?skip=0&count=20"
        
        response = requests.get(url, headers=headers)
        res_data = response.json()

        assert response.status_code == 200
        assert isinstance(res_data, list)
        assert len(res_data) > 0, "데이터가 존재해야 하지만 빈 리스트가 반환되었습니다."
        assert "id" in res_data[0]
        assert "name" in res_data[0]
        
    @allure.story("빈 목록 조회")    
    @pytest.mark.xfail(reason="실제 환경에서는 목록을 비워둘 수 없음")
    def test_BS002_list_emptylook_up(self, api_headers, base_url_block_storage):
        """BS-002: 데이터가 없는 경우 조회"""
        headers = api_headers
        url = f"{base_url_block_storage}?skip=0&count=20"
        
        response = requests.get(url, headers=headers)
        res_data = response.json()

        assert response.status_code == 200
        assert res_data == [], f"데이터가 비어있어야 하지만 {len(res_data)}개의 데이터가 반환되었습니다."

    def test_BS003_create_success(self, resource_factory, api_headers, base_url_block_storage):
        """BS-003: 블록 스토리지 생성 성공 및 검증"""
        url = base_url_block_storage
        headers = api_headers
        payload = {
                        "name": f"team2-{uuid.uuid4().hex[:6]}",
                        "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
                        "size_gib": 10,
                        "dr": False,
                        "image_id": None,
                        "snapshot_id": None
        }

        # 1. 블록 스토리지 생성 (resource_factory 사용)
        created_resource = resource_factory(url, payload)
        created_id = created_resource["id"]
        
        # 2. 생성된 블록 스토리지 상세 조회 (GET)
        detail_url = f"{url}/{created_id}"
        detail_response = requests.get(detail_url, headers=headers)
        detail_data = detail_response.json()
        
        # 3. 상세 조회 검증
        assert detail_response.status_code == 200, f"상세 조회 실패: {detail_data}"
        
        # 4. 생성 요청 데이터와 실제 생성된 데이터 비교
        assert detail_data["name"] == payload["name"], f"name 불일치: 요청={payload['name']}, 응답={detail_data.get('name')}"
        assert detail_data["zone_id"] == payload["zone_id"], f"zone_id 불일치: 요청={payload['zone_id']}, 응답={detail_data.get('zone_id')}"
        assert detail_data["size_gib"] == payload["size_gib"], f"size_gib 불일치: 요청={payload['size_gib']}, 응답={detail_data.get('size_gib')}"
        
        #5. 스토리지 상태 확인 (정상적인 생성 프로세스 상태여야 함)
        status = detail_data.get("status", "")
        valid_statuses = ["queued", "creating", "available", "active", "assigned"]
        assert status in valid_statuses, f"예상치 못한 상태: {status} (허용: {valid_statuses})"

    def test_BS004_create_fail_missing_parameters(self, api_headers, base_url_block_storage):
        """BS-004: 필수 파라미터 일부 누락 시 422 에러 검증"""
        url = base_url_block_storage
        headers = api_headers
        
        # 이미지의 예시와 유사하게 size_gib 등을 null로 보내거나 일부 누락한 페이로드
        # 이미지 우측 하단 JSON 예시를 참고하여 구성
        payload = {
            "name": "disk-2ec50c",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "size_gib": None,  # 필수 파라미터가 null이거나 누락된 상황 가정
            "dr": False,
            "image_id": None,
            "snapshot_id": None
        }

        # 1. 블록 스토리지 생성 요청 (실패 예상)
        response = requests.post(url, headers=headers, json=payload)
        res_data = response.json()
        
        # 2. 상태 코드 검증 (이미지 상의 422 확인)
        assert response.status_code == 422, f"예상치 못한 상태 코드: {response.status_code}"
        
        # 3. 에러 메시지 상세 검증 (이미지 상의 JSON 구조와 매칭)
        assert res_data["code"] == "invalid_parameters"
        assert "requested parameters are not valid" in res_data["message"]
        
        # 4. 세부 에러 내용(detail) 확인
        # 이미지에는 "JSON decode error"가 찍혀있으므로 해당 문구가 포함되어 있는지 확인
        found_json_error = any(
            error.get("msg") == "Input should be a valid integer" or error.get("type") == "json_invalid" 
            for error in res_data.get("detail", {}).get("errors", [])
        )
        assert found_json_error, f"상세 에러 내용에 'JSON decode error'가 없습니다: {res_data}"

    def test_BS005_create_fail_invalid_data_type(self, api_headers, base_url_block_storage):
        """BS-005: 필수 파라미터에 잘못된 데이터 타입 입력 시 에러 검증"""
        url = base_url_block_storage
        headers = api_headers.copy()
        headers["Content-Type"] = "application/json"

        # json=payload 대신, 문법이 틀린 raw string을 직접 작성합니다.
        # size_gib: aaa (따옴표 없음) 형태로 만들어 JSON 디코드 에러를 유도합니다.
        invalid_raw_body = """
        {
            "name": "disk-2ec50c",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "size_gib": aaa,
            "dr": false,
            "image_id": null,
            "snapshot_id": null
        }
        """

        # data 파라미터로 문자열을 직접 전송
        response = requests.post(url, headers=headers, data=invalid_raw_body)
        res_data = response.json()

        # 1. 상태 코드 검증
        assert response.status_code == 422
        
        # 2. 공통 응답 구조 검증
        assert res_data["code"] == "invalid_parameters"
        assert res_data["message"] == "requested parameters are not valid"

        # 3. 상세 에러(detail) 검증 - Postman 결과와 매칭
        errors = res_data.get("detail", {}).get("errors", [])
        assert len(errors) > 0
        
        error_detail = errors[0]
        assert error_detail["type"] == "json_invalid" # 이제 정상적으로 통과합니다.
        assert error_detail["msg"] == "JSON decode error"
        assert error_detail["ctx"]["error"] == "Expecting value"

    def test_BS007_get_fail_non_existent_id(self, api_headers, base_url_block_storage):
        """BS-007: 존재하지 않는 ID로 블록 스토리지 조회 시 404 에러 검증"""
        
        # 1. 존재하지 않는 임의의 ID 설정 (이미지 예시 참고)
        invalid_id = "d3012bbe-11f3-44e6-9cd6-f485753914e"
        url = f"{base_url_block_storage}/{invalid_id}"
        
        headers = api_headers.copy()
        headers["Content-Type"] = "application/json"

        # 2. 상세 조회 요청 (GET)
        response = requests.get(url, headers=headers)
        
        # 3. 상태 코드 검증 (404 Not Found)
        assert response.status_code == 404, f"예상치 못한 상태 코드: {response.status_code}"
        
        # 4. 응답 바디 검증
        res_data = response.json()
        assert res_data["detail"] == "Not Found", f"에러 메시지 불일치: {res_data.get('detail')}"

    def test_BS008_update_resource_name(self, resource_factory, api_headers, base_url_block_storage):
        """BS-008: 블록 스토리지 이름 수정 검증"""
        # 테스트용 블록 스토리지 생성
        payload = {
            "name": f"team2-{uuid.uuid4().hex[:6]}",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "size_gib": 10,
            "dr": False,
            "image_id": None,
            "snapshot_id": None
        }
        created_resource = resource_factory(base_url_block_storage, payload)
        resource_id = created_resource["id"]
        
        url = f"{base_url_block_storage}/{resource_id}"
        headers = api_headers
        
        # 수정할 데이터 (이미지 기반)
        update_payload = {
            "name": "test-team22"
        }

        # PATCH 또는 PUT 요청 (API 명세에 따라 선택, 이미지 흐름상 수정 요청)
        response = requests.patch(url, headers=headers, json=update_payload)
        res_data = response.json()

        assert response.status_code == 200
        assert res_data["id"] == resource_id
        
        # 실제로 이름이 변경되었는지 상세 조회를 통해 재확인
        get_response = requests.get(url, headers=headers)
        assert get_response.json()["name"] == "test-team22"

    def test_BS009_update_fail_invalid_tag_format(self, api_headers, base_url_block_storage):
        """BS-009: 올바르지 않은 태그 형식(JSON 문법 오류)으로 수정 시 422 에러 검증"""
        resource_id = "d3012bbe-11f3-44e6-9cd6-f485753914ee"
        url = f"{base_url_block_storage}/{resource_id}"
        headers = api_headers.copy()
        headers["Content-Type"] = "application/json"

        # 이미지 예시: "tags": {}ss, 처럼 문법이 깨진 상태 유도
        invalid_raw_body = """
        {
            "id": "d3012bbe-11f3-44e6-9cd6-f485753914ee",
            "tags": {}ss
        }
        """

        # JSON 문법 오류를 보내기 위해 data= 파라미터 사용
        response = requests.patch(url, headers=headers, data=invalid_raw_body)
        res_data = response.json()

        # 1. 상태 코드 검증
        assert response.status_code == 422
        
        # 2. 에러 상세 정보 검증 (이미지 매칭)
        error_detail = res_data["detail"]["errors"][0]
        assert error_detail["type"] == "json_invalid"
        assert "JSON decode error" in error_detail["msg"]
        assert "Expecting ',' delimiter" in error_detail["ctx"]["error"]

    def test_BS010_delete_resource_success(self, resource_factory, api_headers, base_url_block_storage):
        """BS-010: 블록 스토리지 삭제 요청 성공 검증"""
        # 테스트용 블록 스토리지 생성
        payload = {
            "name": f"team2-{uuid.uuid4().hex[:6]}",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "size_gib": 10,
            "dr": False,
            "image_id": None,
            "snapshot_id": None
        }
        created_resource = resource_factory(base_url_block_storage, payload)
        resource_id = created_resource["id"]
        
        url = f"{base_url_block_storage}/{resource_id}"
        headers = api_headers

        # DELETE 요청 전송
        response = requests.delete(url, headers=headers)
        res_data = response.json()

        # 응답 검증
        assert response.status_code == 200
        assert res_data["id"] == resource_id
        assert res_data["status"] == "deleting"

    def test_BS011_delete_fail_already_deleted(self, resource_factory, api_headers, base_url_block_storage):
        """BS-011: 이미 삭제된 ID 삭제 시도 시 409 Conflict 검증"""
        # 1. 테스트용 블록 스토리지 생성
        payload = {
            "name": f"team2-{uuid.uuid4().hex[:6]}",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "size_gib": 10,
            "dr": False,
            "image_id": None,
            "snapshot_id": None
        }
        created_resource = resource_factory(base_url_block_storage, payload)
        resource_id = created_resource["id"]
        
        url = f"{base_url_block_storage}/{resource_id}"
        headers = api_headers

        # 2. 첫 번째 삭제 요청 (성공해야 함)
        first_delete = requests.delete(url, headers=headers)
        assert first_delete.status_code == 200

        # 3. 두 번째 삭제 요청 (409 Conflict 예상)
        response = requests.delete(url, headers=headers)
        res_data = response.json()

        # 409 Conflict 및 상세 에러 메시지 검증
        assert response.status_code == 409
        assert res_data["code"] == "unexpected_status"
        assert "should be queued, assigned, or prepared" in res_data["message"]
        # 삭제 중이거나 이미 삭제된 상태 모두 허용
        status = res_data["detail"]["resource_block_storage"]["status"]
        assert status in ["deleting", "deleted"], f"예상치 못한 상태: {status}"

class TestSanpshotCRUD:
    """스냅샷 API 테스트 클래스"""

    def test_BS012_list_exists_look_up(self, api_headers, base_url_block_storage):
        """BS-012: 데이터가 있는 경우 목록 조회"""
        headers = api_headers
        url = f"{base_url_block_storage}/snapshot?skip=0&count=20"
        
        response = requests.get(url, headers=headers)
        res_data = response.json()

        assert response.status_code == 200
        assert isinstance(res_data, list)
        assert len(res_data) > 0, "데이터가 존재해야 하지만 빈 리스트가 반환되었습니다."
        assert "id" in res_data[0]
        assert "name" in res_data[0]

    @allure.story("빈 목록 조회")    
    @pytest.mark.xfail(reason="실제 환경에서는 목록을 비워둘 수 없음")
    def test_BS013_list_emptylook_up(self, api_headers, base_url_block_storage):
        """BS-013: 데이터가 없는 경우 조회"""
        headers = api_headers
        url = f"{base_url_block_storage}/snapshot?skip=0&count=20"
        
        response = requests.get(url, headers=headers)
        res_data = response.json()

        assert response.status_code == 200
        assert res_data == [], f"데이터가 비어있어야 하지만 {len(res_data)}개의 데이터가 반환되었습니다."

    def test_BS014_create_success(self, resource_factory, api_headers, base_url_block_storage):
        """BS-014: 스냅샷 생성 성공 및 검증"""
        url = f"{base_url_block_storage}/snapshot"
        headers = api_headers
        payload = {
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "name": "snapshot-878908",
            "block_storage_id": get_prepared_block_storage_id(api_headers, base_url_block_storage),
        }

        # 1. 스냅샷 생성 (resource_factory 사용)
        created_resource = resource_factory(url, payload)
        created_id = created_resource["id"]
        
        # 2. 생성된 스냅샷 상세 조회 (GET)
        detail_url = f"{url}/{created_id}"
        detail_response = requests.get(detail_url, headers=headers)
        detail_data = detail_response.json()
        
        # 3. 상세 조회 검증
        assert detail_response.status_code == 200, f"상세 조회 실패: {detail_data}"
        
        # 4. 생성 요청 데이터와 실제 생성된 데이터 비교 (스냅샷 필드 기준)
        assert detail_data["name"] == payload["name"], f"name 불일치: 요청={payload['name']}, 응답={detail_data.get('name')}"
        assert detail_data["zone_id"] == payload["zone_id"], f"zone_id 불일치: 요청={payload['zone_id']}, 응답={detail_data.get('zone_id')}"
        assert detail_data["block_storage_id"] == payload["block_storage_id"], f"block_storage_id 불일치: 요청={payload['block_storage_id']}, 응답={detail_data.get('block_storage_id')}"
        
        # 5. 스냅샷 상태 확인 (이미지 응답 구조 및 일반적인 상태값 기준)
        status = detail_data.get("status", "")
        # 스냅샷 특성에 맞는 유효 상태 목록
        valid_statuses = ["queued", "creating", "available", "active", "assigned", "prepared"]
        assert status in valid_statuses, f"예상치 못한 상태: {status} (허용: {valid_statuses})"

    def test_BS015_create_fail_missing_parameters(self, api_headers, base_url_block_storage):
        """BS-015: 필수 파라미터 일부 누락 시 422 에러 검증"""
        url = f"{base_url_block_storage}/snapshot"
        headers = api_headers
        
        # 이미지의 예시와 유사하게 size_gib 등을 null로 보내거나 일부 누락한 페이로드
        # 이미지 우측 하단 JSON 예시를 참고하여 구성
        payload = {
                    "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
                    "name": "snapshot-878908",
                    "block_storage_id": None
        }

        # 1. 스냅샷 생성 요청 (실패 예상)
        response = requests.post(url, headers=headers, json=payload)
        res_data = response.json()
        
        # 2. 상태 코드 검증 (이미지 상의 422 확인)
        assert response.status_code == 422, f"예상치 못한 상태 코드: {response.status_code}"
        
        # 3. 에러 메시지 상세 검증 (이미지 상의 JSON 구조와 매칭)
        assert res_data["code"] == "invalid_parameters"
        assert "requested parameters are not valid" in res_data["message"]
        
        # 4. 세부 에러 내용(detail) 확인
        # 이미지에는 "uuid_type" 에러와 "UUID input should be a string..." 메시지가 찍혀있음
        errors = res_data.get("detail", {}).get("errors", [])
        
        found_uuid_error = any(
            error.get("type") == "uuid_type" and 
            "UUID input should be a string" in error.get("msg", "")
            for error in errors
        )
        
        assert found_uuid_error, f"상세 에러 내용에 'uuid_type' 관련 메시지가 없습니다: {res_data}"
        
        # 추가 검증: 에러가 발생한 위치(loc)가 block_storage_id인지 확인
        error_loc = errors[0].get("loc", [])
        assert "block_storage_id" in error_loc, f"에러 위치가 올바르지 않습니다: {error_loc}"
    
    def test_BS016_create_fail_invalid_data_type(self, api_headers, base_url_block_storage):
        """BS-016: 필수 파라미터에 잘못된 데이터 타입 입력 시 에러 검증"""
        url = f"{base_url_block_storage}/snapshot"
        headers = api_headers.copy()
        headers["Content-Type"] = "application/json"

        # 잘못된 UUID 형식(너무 짧음)을 사용하여 uuid_parsing 에러 유도
        invalid_raw_body = """
        {
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "name": "snapshot-878908",
            "block_storage_id": "invalid-uuid-format"
        }
        """

        # data 파라미터로 문자열을 직접 전송
        response = requests.post(url, headers=headers, data=invalid_raw_body)
        res_data = response.json()

        # 1. 상태 코드 검증
        assert response.status_code == 422
        
        # 2. 공통 응답 구조 검증
        assert res_data["code"] == "invalid_parameters"
        assert res_data["message"] == "requested parameters are not valid"

        # 3. 상세 에러(detail) 검증 - Postman 결과와 매칭
        errors = res_data.get("detail", {}).get("errors", [])
        assert len(errors) > 0
        
        error_detail = errors[0]
        assert error_detail["type"] == "uuid_parsing"
        assert "block_storage_id" in error_detail["loc"]
        # 이미지에 나온 구체적인 에러 메시지 확인
        assert "Input should be a valid UUID" in error_detail["msg"]
    
    def test_BS018_get_fail_non_existent_id(self, api_headers, base_url_block_storage):
        """BS-018: 존재하지 않는 ID로 스냅샷 조회 시 404 에러 검증"""
        
        # 1. 존재하지 않는 임의의 ID 설정 (이미지 예시 참고)
        invalid_id = "d3012bbe-11f3-44e6-9cd6-f485753914e"
        url = f"{base_url_block_storage}/snapshot/{invalid_id}"
        
        headers = api_headers.copy()
        headers["Content-Type"] = "application/json"

        # 2. 상세 조회 요청 (GET)
        response = requests.get(url, headers=headers)
        
        # 3. 상태 코드 검증 (404 Not Found)
        assert response.status_code == 404, f"예상치 못한 상태 코드: {response.status_code}"
        
        # 4. 응답 바디 검증
        res_data = response.json()
        assert res_data["detail"] == "Not Found", f"에러 메시지 불일치: {res_data.get('detail')}"
    
    def test_BS019_update_resource_name(self, resource_factory, api_headers, base_url_block_storage):
        """BS-019: 스냅샷 이름 수정 검증"""
        # 테스트용 스냅샷 생성
        url = f"{base_url_block_storage}/snapshot"
        payload = {
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "name": "snapshot-original",
            "block_storage_id": get_prepared_block_storage_id(api_headers, base_url_block_storage),
        }
        created_resource = resource_factory(url, payload)
        resource_id = created_resource["id"]
        
        url = f"{base_url_block_storage}/snapshot/{resource_id}"
        headers = api_headers
        
        # 수정할 데이터 (이미지 기반)
        update_payload = {
            "name": "test-team22"
        }

        # PATCH 또는 PUT 요청 (API 명세에 따라 선택, 이미지 흐름상 수정 요청)
        response = requests.patch(url, headers=headers, json=update_payload)
        res_data = response.json()

        assert response.status_code == 200
        assert res_data["id"] == resource_id
        
        # 실제로 이름이 변경되었는지 상세 조회를 통해 재확인
        get_response = requests.get(url, headers=headers)
        assert get_response.json()["name"] == "test-team22"

    def test_BS020_update_fail_invalid_tag_format(self, api_headers, base_url_block_storage):
        """BS-020: 올바르지 않은 태그 형식(JSON 문법 오류)으로 수정 시 422 에러 검증"""
        resource_id = "d3012bbe-11f3-44e6-9cd6-f485753914ee"
        url = f"{base_url_block_storage}/snapshot/{resource_id}"
        headers = api_headers.copy()
        headers["Content-Type"] = "application/json"

        # 이미지 예시: "tags": {}ss, 처럼 문법이 깨진 상태 유도
        invalid_raw_body = """
        {
          "id": "603fc40b-e42c-420b-9d75-332e48d7a965",
          "tags": {}22
        }
        """

        # JSON 문법 오류를 보내기 위해 data= 파라미터 사용
        response = requests.patch(url, headers=headers, data=invalid_raw_body)
        res_data = response.json()

        # 1. 상태 코드 검증
        assert response.status_code == 422
        
        # 공통 에러 응답 구조 검증
        assert res_data["code"] == "invalid_parameters"
        assert res_data["message"] == "requested parameters are not valid"

        # 상세 에러(detail) 검증
        errors = res_data.get("detail", {}).get("errors", [])
        assert len(errors) > 0
    
        error_detail = errors[0]
        # 이미지 결과: "type": "json_invalid"
        assert error_detail["type"] == "json_invalid"
        # 이미지 결과: "msg": "JSON decode error"
        assert "JSON decode error" in error_detail["msg"]
    
        # loc 정보 검증 (이미지 결과: ["body", 64])
        assert "body" in error_detail["loc"]
    
    def test_BS021_delete_resource_success(self, resource_factory, api_headers, base_url_block_storage):
        """BS-021: 블록 스토리지 삭제 요청 성공 검증"""
        # 테스트용 스냅샷 생성
        url = f"{base_url_block_storage}/snapshot"
        payload = {
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "name": "snapshot-to-delete",
            "block_storage_id": get_prepared_block_storage_id(api_headers, base_url_block_storage),
        }
        created_resource = resource_factory(url, payload)
        resource_id = created_resource["id"]
        
        url = f"{base_url_block_storage}/snapshot/{resource_id}"
        headers = api_headers

        # DELETE 요청 전송
        response = requests.delete(url, headers=headers)
        res_data = response.json()

        # 응답 검증
        assert response.status_code == 200
        assert res_data["id"] == resource_id
        assert res_data["status"] == "deleting"

    def test_BS022_delete_fail_already_deleted(self, resource_factory, api_headers, base_url_block_storage):
        """BS-022: 이미 삭제된 ID 삭제 시도 시 409 Conflict 검증"""
        # 1. 테스트용 스냅샷 생성
        url = f"{base_url_block_storage}/snapshot"
        payload = {
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "name": "snapshot-double-delete",
            "block_storage_id": get_prepared_block_storage_id(api_headers, base_url_block_storage),
        }
        created_resource = resource_factory(url, payload)
        resource_id = created_resource["id"]
        
        url = f"{base_url_block_storage}/snapshot/{resource_id}"
        headers = api_headers

        # 2. 첫 번째 삭제 요청 (성공해야 함)
        first_delete = requests.delete(url, headers=headers)
        assert first_delete.status_code == 200

        # 3. 두 번째 삭제 요청 (409 Conflict 예상)
        response = requests.delete(url, headers=headers)
        res_data = response.json()

        # 409 Conflict 및 상세 에러 메시지 검증
        assert response.status_code == 409
        assert res_data["code"] == "unexpected_status"
        assert "should be queued, assigned, or prepared" in res_data["message"]
        # 삭제 중이거나 이미 삭제된 상태 모두 허용
        status = res_data["detail"]["resource_block_storage_snapshot"]["status"]
        assert status in ["deleting", "deleted"], f"예상치 못한 상태: {status}"

class Testsnapshot_schedulerCRUD:
    """스냅샷 스케쥴러API 테스트 클래스"""

    def test_BS023_list_exists_look_up(self, api_headers, base_url_block_storage):
        """BS-023: snapshot_scheduler 목록 조회 (빈 리스트 허용)"""
        headers = api_headers
        url = f"{base_url_block_storage}/snapshot_scheduler?skip=0&count=20"
    
        response = requests.get(url, headers=headers)
        res_data = response.json()

        assert response.status_code == 200
        assert isinstance(res_data, list)
        # 빈 리스트도 정상 응답으로 간주
        if len(res_data) > 0:
            assert "id" in res_data[0]
            assert "name" in res_data[0]   

    @allure.story("빈 목록 조회")    
    @pytest.mark.xfail(reason="실제 환경에서는 목록을 비워둘 수 없음")
    def test_BS024_list_emptylook_up(self, api_headers, base_url_block_storage):
        """BS-024: 데이터가 없는 경우 조회"""
        headers = api_headers
        url = f"{base_url_block_storage}/snapshot_scheduler?skip=0&count=20"
        
        response = requests.get(url, headers=headers)
        res_data = response.json()

        assert response.status_code == 200
        assert res_data == [], f"데이터가 비어있어야 하지만 {len(res_data)}개의 데이터가 반환되었습니다."
    
    def test_BS025_create_success(self, resource_factory, api_headers, base_url_block_storage):
        """BS-025: 스냅샷 생성 성공 및 검증"""
        url = f"{base_url_block_storage}/snapshot_scheduler"
        headers = api_headers
        payload = {
          "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
          "name": "snapshot-scheduler-ea550f",
          "block_storage_id": get_prepared_block_storage_id(api_headers, base_url_block_storage),
          "cron_expression": "2 4 * * *",
          "max_snapshots": 7,
          "tags": {}
        }

        # 1. 스냅샷 생성 (resource_factory 내부에서 POST 호출)
        created_resource = resource_factory(url, payload)
        
        # [검증] 이미지 1처럼 'code'가 포함되어 있다면 생성이 실패한 것임
        assert "code" not in created_resource, f"생성 실패: {created_resource.get('message')}"
        assert "id" in created_resource, "응답에 생성된 ID가 없습니다."
        
        created_id = created_resource["id"]
        
        # 2. 생성된 스냅샷 상세 조회 (GET)
        detail_url = f"{url}/{created_id}"
        detail_response = requests.get(detail_url, headers=api_headers)
        detail_data = detail_response.json()
        
        # 3. 상세 조회 기본 검증
        assert detail_response.status_code == 200, f"상세 조회 실패: {detail_data}"
        
        # 4. 요청 데이터와 응답 데이터 비교 (이미지 2의 구조 반영)
        assert detail_data["name"] == payload["name"]
        assert detail_data["block_storage_id"] == payload["block_storage_id"]
        
        # 5. 상태 값 검증
        # 스냅샷 스케줄러가 'active' 혹은 'prepared' 상태인지 확인
        status = detail_data.get("status")
        valid_statuses = ["active", "available", "prepared"]
        assert status in valid_statuses, f"부적절한 상태값: {status}"

    def test_BS026_create_fail_missing_parameters(self, api_headers, base_url_block_storage):
        """BS-026: 필수 파라미터 일부 누락 시 422 에러 검증"""
        url = f"{base_url_block_storage}/snapshot_scheduler"
        headers = api_headers
        
        # 이미지의 예시와 유사하게 size_gib 등을 null로 보내거나 일부 누락한 페이로드
        # 이미지 우측 하단 JSON 예시를 참고하여 구성
        payload = {
                    "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
                    "name": "snapshot-scheduler-ea550f",
                    "block_storage_id": get_prepared_block_storage_id(api_headers, base_url_block_storage),
                    "cron_expression": None,
                    "max_snapshots": 7,
                    "tags": {}
        }

        # 1. 생성 요청 (422 예상)
        response = requests.post(url, headers=api_headers, json=payload)
        res_data = response.json()
        
        # 2. 상태 코드 검증
        assert response.status_code == 422, f"예상치 못한 상태 코드: {response.status_code}"
        
        # 3. 에러 코드 및 구조 검증
        # 실제 구조: {"code": "invalid_parameters", "detail": {"errors": [...], "query_params": ""}, "message": "..."}
        assert res_data["code"] == "invalid_parameters"
        assert "detail" in res_data, "응답에 'detail' 필드가 없습니다."
        assert "errors" in res_data["detail"], "응답에 'errors' 필드가 없습니다."
        
        # 4. 세부 에러 내용 검증
        errors = res_data["detail"]["errors"]
        
        # 에러 구조: {"input": None, "loc": ["body", "cron_expression"], "msg": "Input should be a valid string", "type": "string_type"}
        found_cron_error = any(
            "cron_expression" in error.get("loc", []) and 
            "Input should be a valid string" in error.get("msg", "")
            for error in errors
        )
        
        assert found_cron_error, f"cron_expression 관련 에러 메시지가 없습니다: {res_data}"

    def test_BS027_create_fail_invalid_data_type(self, api_headers, base_url_block_storage):
        """BS-027: 필수 파라미터에 잘못된 데이터 타입(JSON 문법 오류) 입력 시 에러 검증"""
        url = f"{base_url_block_storage}/snapshot_scheduler"
        headers = api_headers.copy()
        headers["Content-Type"] = "application/json"

        # 이미지 4, 5번 예시: "tags": {}22 처럼 문법을 깨뜨려 JSON 디코드 에러 유도
        invalid_raw_body = """
        {
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "name": "snapshot-scheduler-e9838b",
            "block_storage_id": "e0abb783-493b-432e-bdcc-69ecfb858f",
            "cron_expression": "2 4 * * *",
            "max_snapshots": 7,
            "tags": {}22
        }
        """

        # json= 대신 data=를 사용하여 가공되지 않은 raw string 전송
        response = requests.post(url, headers=headers, data=invalid_raw_body)
        res_data = response.json()

        # 1. 상태 코드 검증 (이미지 상 422 Unprocessable Entity)
        assert response.status_code == 422
        
        # 2. 공통 응답 구조 검증 (code: invalid_parameters)
        assert res_data["code"] == "invalid_parameters"
        assert "detail" in res_data, "응답에 'detail' 필드가 없습니다."
        assert "errors" in res_data["detail"], "응답에 'errors' 필드가 없습니다."

        # 3. 상세 에러(errors) 검증 - 실제 구조에 맞게
        errors = res_data["detail"]["errors"]
        assert len(errors) > 0
        
        error_detail = errors[0]
        
        # 실제 에러 구조: {"ctx": {"error": "..."}, "input": {}, "loc": ["body", 291], "msg": "JSON decode error", "type": "json_invalid"}
        assert error_detail["type"] == "json_invalid"
        assert error_detail["msg"] == "JSON decode error"
        # "Expecting ',' delimiter" 또는 "Expecting value" 등 상세 원인 확인
        assert "ctx" in error_detail
        assert "error" in error_detail["ctx"]
        assert "Expecting" in error_detail["ctx"]["error"]

    def test_BS029_get_fail_non_existent_id(self, api_headers, base_url_block_storage):
        """BS-029: 존재하지 않는 ID로 블록 스토리지 조회 시 404 에러 검증"""
        
        # 1. 존재하지 않는 임의의 ID 설정 (이미지 예시 참고)
        invalid_id = "2bbe3e69-7a41-4b2c-936c-057d79303a6"
        url = f"{base_url_block_storage}/snapshot_scheduler/{invalid_id}"
        
        headers = api_headers.copy()
        headers["Content-Type"] = "application/json"

        # 2. 상세 조회 요청 (GET)
        response = requests.get(url, headers=headers)
        
        # 3. 상태 코드 검증 (404 Not Found)
        assert response.status_code == 404, f"예상치 못한 상태 코드: {response.status_code}"
        
        # 4. 응답 바디 검증
        res_data = response.json()
        assert res_data["detail"] == "Not Found", f"에러 메시지 불일치: {res_data.get('detail')}"

    def test_BS030_update_resource_name(self, resource_factory, api_headers, base_url_block_storage):
        """BS-030: 스냅샷 스케줄러 이름 수정 검증"""
        
        # 1. 테스트용 스냅샷 스케줄러 생성
        snapshot_scheduler_url = f"{base_url_block_storage}/snapshot_scheduler"
        payload = {
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "name": f"before-update-{uuid.uuid4().hex[:6]}",
            "block_storage_id": get_prepared_block_storage_id(api_headers, base_url_block_storage),
            "cron_expression": "2 4 * * *",
            "max_snapshots": 7,
            "tags": {}
        }
        # resource_factory를 통해 생성 (종료 후 자동 삭제됨)
        created_resource = resource_factory(snapshot_scheduler_url, payload)
        resource_id = created_resource["id"]
        
        # 2. 이름 변경 요청 설정
        url = f"{base_url_block_storage}/snapshot_scheduler/{resource_id}"
        
        # 요청 바디: {"name": "team2"}
        update_payload = {
            "name": "team2"
        }

        # 3. 수정 요청 전송 (PATCH)
        response = requests.patch(url, headers=api_headers, json=update_payload)
        res_data = response.json()

        # [검증] 상태 코드 200 및 반환된 ID 일치 여부
        assert response.status_code == 200, f"수정 실패: {res_data}"
        assert res_data["id"] == resource_id, "반환된 ID가 기존 ID와 다릅니다."
        
        # 4. 실제로 이름이 변경되었는지 상세 조회(GET)로 최종 확정
        get_response = requests.get(url, headers=api_headers)
        get_data = get_response.json()
        
        assert get_data["name"] == "team2", f"이름이 변경되지 않음: {get_data.get('name')}"
    
    def test_BS031_update_fail_invalid_tag_format(self, api_headers, base_url_block_storage):
        """BS-031: 올바르지 않은 태그 형식(JSON 문법 오류)으로 수정 시 422 에러 검증"""
        # 이미지 9번 예시 ID 반영
        resource_id = "2bbe3e69-7a41-4b2c-936c-057d79303a68" 
        url = f"{base_url_block_storage}/snapshot_scheduler/{resource_id}"
        
        headers = api_headers.copy()
        headers["Content-Type"] = "application/json"

        # 이미지 9번 우측 하단 예시: "tags": {}22 처럼 문법이 깨진 상태 유도
        # (작성하신 {}ss 대신 이미지와 동일한 {}22로 맞춤)
        invalid_raw_body = """
        {
            "id": "2bbe3e69-7a41-4b2c-936c-057d79303a68",
            "tags": {}22
        }
        """

        # JSON 문법 오류를 보내기 위해 data= 파라미터 사용
        response = requests.patch(url, headers=headers, data=invalid_raw_body)
        res_data = response.json()

        # 1. 상태 코드 검증 (이미지 상 422 Unprocessable Entity)
        assert response.status_code == 422
        
        # 2. 공통 응답 구조 검증
        assert res_data["code"] == "invalid_parameters"
        assert res_data["message"] == "requested parameters are not valid"

        # 3. 상세 에러 정보 검증 (이미지 9번 중앙 응답 데이터 매칭)
        # 이미지 구조: res_data["detail"]["errors"][0]
        errors = res_data.get("detail", {}).get("errors", [])
        assert len(errors) > 0
        
        error_detail = errors[0]
        assert error_detail["type"] == "json_invalid" #
        assert error_detail["msg"] == "JSON decode error" # 이미지 상 키값은 'msg'임
        
        # 4. 에러 위치 정보 검증
        assert "body" in error_detail.get("loc", [])

    def test_BS032_delete_resource_success(self, resource_factory, api_headers, base_url_block_storage):
        """BS-032: 스냅샷 스케줄러 삭제 요청 성공 검증"""
        
        # 1. 테스트용 스냅샷 스케줄러 생성
        snapshot_scheduler_url = f"{base_url_block_storage}/snapshot_scheduler"
        payload = {
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "name": f"to-delete-{uuid.uuid4().hex[:6]}",
            "block_storage_id": get_prepared_block_storage_id(api_headers, base_url_block_storage),
            "cron_expression": "2 4 * * *",
            "max_snapshots": 7,
            "tags": {}
        }
        created_resource = resource_factory(snapshot_scheduler_url, payload)
        resource_id = created_resource["id"]
        
        # 2. 삭제 요청 설정
        url = f"{base_url_block_storage}/snapshot_scheduler/{resource_id}"
        
        # 3. DELETE 요청 전송
        response = requests.delete(url, headers=api_headers)
        res_data = response.json()

        # 4. 응답 데이터 검증
        assert response.status_code == 200, f"삭제 실패: {res_data}"
        assert res_data["id"] == resource_id, "반환된 ID가 요청한 ID와 일치하지 않습니다."
        assert res_data["status"] == "deleted", f"상태값이 'deleted'가 아닙니다: {res_data.get('status')}"


    def test_BS033_delete_fail_already_deleted(self, resource_factory, api_headers, base_url_block_storage):
        """BS-033: 존재하지 않는 스냅샷 스케줄러 삭제 시도 시 409 Conflict 검증"""

        # 1. 존재하지 않는 UUID로 삭제 시도
        fake_id = str(uuid.uuid4())
        snapshot_scheduler_url = f"{base_url_block_storage}/snapshot_scheduler"
        target_url = f"{snapshot_scheduler_url}/{fake_id}"

        # 2. 존재하지 않는 리소스 삭제 요청
        response = requests.delete(target_url, headers=api_headers)
        res_data = response.json()

        # 3. 409 Conflict 검증
        assert response.status_code == 409, f"예상치 못한 상태 코드: {response.status_code}"
        
        # 에러 코드 확인 (not_found 또는 snapshot_scheduler_not_found)
        assert res_data["code"] in ["not_found", "snapshot_scheduler_not_found"], \
            f"예상치 못한 에러 코드: {res_data.get('code')}"
        
        # 에러 메시지 확인
        assert "snapshot scheduler" in res_data["message"].lower(), \
            f"에러 메시지에 'snapshot scheduler' 언급이 없습니다: {res_data.get('message')}"