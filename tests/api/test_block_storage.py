import requests
import pytest


class TestBlockStorageCRUD:
    """블록 스토리지 API 테스트 클래스"""
    created_block_storage_id = None

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


    def test_BS002_list_emptylook_up(self, api_headers, base_url_block_storage):
        """BS-002: 데이터가 없는 경우 조회"""
        headers = api_headers
        url = f"{base_url_block_storage}?skip=0&count=20"
        
        response = requests.get(url, headers=headers)
        res_data = response.json()

        assert response.status_code == 200
        # assert res_data == [], f"데이터가 비어있어야 하지만 {len(res_data)}개의 데이터가 반환되었습니다."

    def test_BS003_create_success(self, api_headers, base_url_block_storage):
        """BS-003: 블록 스토리지 생성 성공 및 검증"""
        url = base_url_block_storage
        headers = api_headers
        payload = {
                        "name": "team2",
                        "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
                        "size_gib": 10,
                        "dr": False,
                        "image_id": None,
                        "snapshot_id": None
        }

        # 1. 블록 스토리지 생성
        response = requests.post(url, headers=headers, json=payload)
        res_data = response.json()
        
        assert response.status_code == 200, f"생성 실패: {res_data}"
        assert "id" in res_data, "생성 응답에 id가 없습니다"
        
        # 2. 생성된 블록 스토리지 상세 조회 (GET)
        created_id = res_data["id"]
        TestBlockStorageCRUD.created_block_storage_id = created_id  # 클래스 변수에 저장
        
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
        """BS-006: 존재하지 않는 ID로 블록 스토리지 조회 시 404 에러 검증"""
        
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

        print(f"테스트 통과: 존재하지 않는 ID({invalid_id}) 조회 시 404 및 'Not Found' 확인")

    def test_BS008_update_resource_name(self, api_headers, base_url_block_storage):
        """BS-008: 블록 스토리지 이름 수정 검증"""
        # test_BS003에서 생성된 블록 스토리지 ID 사용
        assert TestBlockStorageCRUD.created_block_storage_id is not None, "test_BS003이 먼저 실행되어야 합니다."
        resource_id = TestBlockStorageCRUD.created_block_storage_id
        
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

    def test_BS010_delete_resource_success(self, api_headers, base_url_block_storage):
        """BS-010: 블록 스토리지 삭제 요청 성공 검증"""
        # test_BS003에서 생성하고 test_BS008에서 수정한 블록 스토리지 ID 사용
        assert TestBlockStorageCRUD.created_block_storage_id is not None, "test_BS003이 먼저 실행되어야 합니다."
        resource_id = TestBlockStorageCRUD.created_block_storage_id
        
        url = f"{base_url_block_storage}/{resource_id}"
        headers = api_headers

        # DELETE 요청 전송
        response = requests.delete(url, headers=headers)
        res_data = response.json()

        # 응답 검증
        assert response.status_code == 200
        assert res_data["id"] == resource_id
        assert res_data["status"] == "deleting"

    def test_BS011_delete_fail_already_deleted(self, api_headers, base_url_block_storage):
        """BS-011: 이미 삭제된 ID 삭제 시도 시 409 Conflict 검증"""
        # test_BS010에서 삭제한 블록 스토리지를 다시 삭제 시도
        assert TestBlockStorageCRUD.created_block_storage_id is not None, "test_BS010이 먼저 실행되어야 합니다."
        resource_id = TestBlockStorageCRUD.created_block_storage_id
        
        url = f"{base_url_block_storage}/{resource_id}"
        headers = api_headers

        response = requests.delete(url, headers=headers)
        res_data = response.json()

        # 409 Conflict 및 상세 에러 메시지 검증
        assert response.status_code == 409
        assert res_data["code"] == "unexpected_status"
        assert "should be queued, assigned, or prepared" in res_data["message"]
        # 삭제 중이거나 이미 삭제된 상태 모두 허용
        status = res_data["detail"]["resource_block_storage"]["status"]
        assert status in ["deleting", "deleted"], f"예상치 못한 상태: {status}"

class TestSnapshotCRUD:
    """스냅샷 API 테스트 클래스"""
    created_block_storage_id = None

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


    def test_BS002_list_emptylook_up(self, api_headers, base_url_block_storage):
        """BS-002: 데이터가 없는 경우 조회"""
        headers = api_headers
        url = f"{base_url_block_storage}?skip=0&count=20"
        
        response = requests.get(url, headers=headers)
        res_data = response.json()

        assert response.status_code == 200
        # assert res_data == [], f"데이터가 비어있어야 하지만 {len(res_data)}개의 데이터가 반환되었습니다."

    def test_BS003_create_success(self, api_headers, base_url_block_storage):
        """BS-003: 블록 스토리지 생성 성공 및 검증"""
        url = base_url_block_storage
        headers = api_headers
        payload = {
                        "name": "team2",
                        "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
                        "size_gib": 10,
                        "dr": False,
                        "image_id": None,
                        "snapshot_id": None
        }

        # 1. 블록 스토리지 생성
        response = requests.post(url, headers=headers, json=payload)
        res_data = response.json()
        
        assert response.status_code == 200, f"생성 실패: {res_data}"
        assert "id" in res_data, "생성 응답에 id가 없습니다"
        
        # 2. 생성된 블록 스토리지 상세 조회 (GET)
        created_id = res_data["id"]
        TestBlockStorageCRUD.created_block_storage_id = created_id  # 클래스 변수에 저장
        
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
        """BS-006: 존재하지 않는 ID로 블록 스토리지 조회 시 404 에러 검증"""
        
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

        print(f"테스트 통과: 존재하지 않는 ID({invalid_id}) 조회 시 404 및 'Not Found' 확인")

    def test_BS008_update_resource_name(self, api_headers, base_url_block_storage):
        """BS-008: 블록 스토리지 이름 수정 검증"""
        # test_BS003에서 생성된 블록 스토리지 ID 사용
        assert TestBlockStorageCRUD.created_block_storage_id is not None, "test_BS003이 먼저 실행되어야 합니다."
        resource_id = TestBlockStorageCRUD.created_block_storage_id
        
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

    def test_BS010_delete_resource_success(self, api_headers, base_url_block_storage):
        """BS-010: 블록 스토리지 삭제 요청 성공 검증"""
        # test_BS003에서 생성하고 test_BS008에서 수정한 블록 스토리지 ID 사용
        assert TestBlockStorageCRUD.created_block_storage_id is not None, "test_BS003이 먼저 실행되어야 합니다."
        resource_id = TestBlockStorageCRUD.created_block_storage_id
        
        url = f"{base_url_block_storage}/{resource_id}"
        headers = api_headers

        # DELETE 요청 전송
        response = requests.delete(url, headers=headers)
        res_data = response.json()

        # 응답 검증
        assert response.status_code == 200
        assert res_data["id"] == resource_id
        assert res_data["status"] == "deleting"

    def test_BS011_delete_fail_already_deleted(self, api_headers, base_url_block_storage):
        """BS-011: 이미 삭제된 ID 삭제 시도 시 409 Conflict 검증"""
        # test_BS010에서 삭제한 블록 스토리지를 다시 삭제 시도
        assert TestBlockStorageCRUD.created_block_storage_id is not None, "test_BS010이 먼저 실행되어야 합니다."
        resource_id = TestBlockStorageCRUD.created_block_storage_id
        
        url = f"{base_url_block_storage}/{resource_id}"
        headers = api_headers

        response = requests.delete(url, headers=headers)
        res_data = response.json()

        # 409 Conflict 및 상세 에러 메시지 검증
        assert response.status_code == 409
        assert res_data["code"] == "unexpected_status"
        assert "should be queued, assigned, or prepared" in res_data["message"]
        # 삭제 중이거나 이미 삭제된 상태 모두 허용
        status = res_data["detail"]["resource_block_storage"]["status"]
        assert status in ["deleting", "deleted"], f"예상치 못한 상태: {status}"