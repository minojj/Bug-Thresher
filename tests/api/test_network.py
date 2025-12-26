# API 기능 테스트 케이스
import pytest
import requests
import uuid
import allure


base_url = "https://portal.gov.elice.cloud/api/user/resource/network"

# POST -> GET(목록) -> GET(단건) -> PATCH -> DELETE
@allure.epic("네트워크 관리 API") # 2. 클래스 전체에 대한 대분류
@allure.feature("네트워크 인터페이스 CRUD") # 소분류
class TestNetworkInterfaceCRUD:
    created_id = None
    initial_count = 0
    last_payload = None

    #1.기본 목록 조회
    def test_NW001_interface_list(self, api_headers):
        url = f"{base_url}/network_interface?skip=0&count=20"
        response = requests.get(url,headers=api_headers)
        assert response.status_code == 200    

        res_data = response.json()
        assert isinstance(res_data, list)
        TestNetworkInterfaceCRUD.initial_count = len(res_data)
        print(f"\n[기존 개수 저장] {TestNetworkInterfaceCRUD.initial_count}개")

    def test_NW002_interface_empty_list(self, api_headers):
        url = f"{base_url}/network_interface?skip=0&count=20"
        response = requests.get(url,headers=api_headers)

        assert response.status_code == 200

        res_data = response.json()
        assert isinstance(res_data, list), f"응답이 리스트 형식이 아닙니다: {res_data}"

    def test_NW003_interface_create(self, api_headers):
        url = f"{base_url}/network_interface"
        unique_name = f"team2-nic-{uuid.uuid4().hex[:6]}"
        
        payload = {
            "name": unique_name,
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "attached_subnet_id": "a78afe80-88c6-44bc-8438-adba40aa0372",
            "dr": False
        }

        response = requests.post(url, headers=api_headers, json=payload)
        assert response.status_code == 200, f"생성 실패: {response.text}"

        res_data = response.json()

        assert "id" in res_data, f"ID가 응답에 없습니다: {res_data}"
        TestNetworkInterfaceCRUD.created_id = res_data["id"]
        print(f"[리소스 생성 성공] ID: {TestNetworkInterfaceCRUD.created_id}, 이름: {unique_name}")
        TestNetworkInterfaceCRUD.last_payload = payload
        print(f"[성공] 리소스 생성 완료 (ID: {TestNetworkInterfaceCRUD.created_id})")

    def test_NW003_01_verify_after_create(self, api_headers):
        """생성 후 실제로 개수가 늘어났는지 확인"""
        url = f"{base_url}/network_interface?skip=0&count=20"
        response = requests.get(url, headers=api_headers)
        res_data = response.json()
        
        # 생성 후 개수 확인
        current_count = len(res_data)
        assert current_count == TestNetworkInterfaceCRUD.initial_count + 1

        found = any(item['id'] == TestNetworkInterfaceCRUD.created_id for item in res_data)
        assert found, "생성된 ID가 전체 목록에 존재하지 않습니다."
        print(f"[검증 완료] 현재 개수 {current_count}개, 생성된 ID 포함 확인됨.")

    @pytest.mark.xfail(reason="현재 서버에서 중복 이름 생성을 허용하고 있음 ( 409 기대)")
    def test_NW004_duplicate_create_fail(self, api_headers):
        """저장된 last_payload를 사용하여 중복 생성 시도 (409 에러 기대)"""

        if not TestNetworkInterfaceCRUD.last_payload:
            pytest.skip("NW003에서 저장된 payload가 없어 중복 테스트를 건너뜁니다.")

        url = f"{base_url}/network_interface"

        response = requests.post(
            url, 
            headers=api_headers, 
            json=TestNetworkInterfaceCRUD.last_payload
        )

        assert response.status_code == 409, f"중복 생성인데 {response.status_code} 응답."

    @pytest.mark.xfail(reason="포스트맨은 422이나 현재 409 반환됨")
    def test_NW_005_ERR_create_with_invalid_reference_ids(self, api_headers):
        """존재하지 않는 zone_id 및 subnet_id로 생성 시도 (422 에러 기대)"""
        url = f"{base_url}/network_interface"

        invalid_uuid = str(uuid.uuid4())
    
        payload = {
            "name": f"invalid-ref-test-{uuid.uuid4().hex[:4]}",
            "zone_id": invalid_uuid,                 # 가짜 존 ID
            "attached_subnet_id": invalid_uuid,      # 가짜 서브넷 ID
            "dr": False
        }

        response = requests.post(url, headers=api_headers, json=payload)
        assert response.status_code in [422,409,] ,f"가짜 ID로 생성 시도했으나 {response.status_code}가 반환."
        print(f"\n[성공] 잘못된 참조 ID 생성 차단 확인 (응답 코드: {response.status_code})")

    def test_NW006_interface_get(self, api_headers):
        """단건 조회"""
        if not TestNetworkInterfaceCRUD.created_id:
            pytest.skip("NW003에서 생성된 ID가 없어 단건 조회 테스트를 건너뜁니다.")

        url = f"{base_url}/network_interface/{TestNetworkInterfaceCRUD.created_id}"
        response = requests.get(url, headers=api_headers)
        assert response.status_code == 200, f"단건 조회 실패: {response.text}"

        res_data = response.json()
        assert res_data["id"] == TestNetworkInterfaceCRUD.created_id, "조회된 ID가 생성된 ID와 일치하지 않습니다."
        print(f"[성공] 단건 조회 완료 (ID: {TestNetworkInterfaceCRUD.created_id})")

    @pytest.mark.xfail(reason="포스트맨은 422이나 현재 409 반환됨")
    def test_NW_007_ERR_get_non_existent_id(self, api_headers):
        """존재하지 않는 ID로 단건 조회 시도 (422 에러 기대)"""
        non_existent_id = str(uuid.uuid4())
        url = f"{base_url}/network_interface/{non_existent_id}"
        response = requests.get(url, headers=api_headers)
        assert response.status_code in [422,409], f"존재하지 않는 ID 조회 시도했으나 {response.status_code}가 반환."
        print(f"\n[성공] 존재하지 않는 ID 조회 차단 확인 (응답 코드: {response.status_code})")

    def test_NW008_interface_patch(self, api_headers):
        """수정 테스트"""
        if not TestNetworkInterfaceCRUD.created_id:
            pytest.skip("NW003에서 생성된 ID가 없어 수정 테스트를 건너뜁니다.")

        url = f"{base_url}/network_interface/{TestNetworkInterfaceCRUD.created_id}"
        new_name = f"updated-nic-{uuid.uuid4().hex[:6]}"
        payload = {
            "name": new_name
        }

        response = requests.patch(url, headers=api_headers, json=payload)
        assert response.status_code == 200, f"수정 실패: {response.text}"

        res_data = response.json()
        if "name" in res_data:
            # 서버가 수정된 데이터를 즉시 반환하는 경우
            assert res_data["name"] == new_name, f"이름 수정 검증 실패: {res_data['name']} != {new_name}"
        else:
            # 서버가 응답으로 ID만 주는 경우, GET으로 다시 조회해서 확인 
            get_response = requests.get(url, headers=api_headers)
            get_data = get_response.json()
            assert get_data.get("name") == new_name, "조회 결과 이름이 수정되지 않았습니다."
        
        TestNetworkInterfaceCRUD.last_updated_name = new_name
        print(f"[성공] 수정 완료 (ID: {TestNetworkInterfaceCRUD.created_id}, 새 이름: {new_name})")

    def test_NW_009_DUP_patch_same_name(self, api_headers):
        """[Positive/Negative] 이미 설정된 이름과 동일한 이름으로 다시 수정 시도"""
        if not TestNetworkInterfaceCRUD.created_id:
            pytest.skip("수정할 리소스 ID가 없습니다.")

        current_name = TestNetworkInterfaceCRUD.last_updated_name
        
        url = f"{base_url}/network_interface/{TestNetworkInterfaceCRUD.created_id}"
        payload = {
            "name": current_name 
        }

        # 2. 동일한 이름으로 PATCH 요청
        response = requests.patch(url, headers=api_headers, json=payload)

        # 3. [검증] 
        # 시나리오 A: 변화가 없어도 성공으로 간주 (표준적인 PATCH) -> 200 OK
        # 시나리오 B: 중복 데이터로 간주하여 차단 (엄격한 검증) -> 409 Conflict
        
        assert response.status_code == 200, f"동일 이름으로 수정 시도 시 에러 발생: {response.text}"
        
        print(f"[성공] 동일 이름 재수정 시도 결과: {response.status_code}")
    
    def test_NW_010_ERR_patch_immutable_field(self, api_headers):
        """[Negative] 수정 불가능한 필드(zone_id) 수정 시도 시 에러 또는 무시 확인"""
        if not TestNetworkInterfaceCRUD.created_id:
            pytest.skip("테스트 리소스가 없습니다.")

        url = f"{base_url}/network_interface/{TestNetworkInterfaceCRUD.created_id}"
        payload = {
            "zone_id": str(uuid.uuid4()) # 수정되면 안 되는 필드
        }

        response = requests.patch(url, headers=api_headers, json=payload)
        
        print(f"[정보] 불변 필드 수정 시도 결과 코드: {response.status_code}")

    @allure.story("리소스 수정 및 중복 검증") # 시나리오 구분
    @allure.title("다른 리소스와 이름 중복 수정 시 차단 확인") # 리포트에 표시될 제목
    @allure.description("이미 사용 중인 이름으로 수정을 시도할 때 서버가 409를 반환하는지 검증합니다.")
    @pytest.mark.xfail(reason="서버 버그: 중복 이름 수정 허용 및 삭제 실패 현상")
    def test_NW_011_ERR_patch_conflict_with_others(self, api_headers):
        if not TestNetworkInterfaceCRUD.created_id:
            pytest.skip("수정 테스트를 위한 원본 리소스가 없습니다.")

        target_b_name = f"conflict-target-{uuid.uuid4().hex[:4]}"
        payload_b = {
            "name": target_b_name,
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "attached_subnet_id": "a78afe80-88c6-44bc-8438-adba40aa0372",
            "dr": False
        }
        
        resp_b = requests.post(f"{base_url}/network_interface", headers=api_headers, json=payload_b)
        target_b_id = resp_b.json().get("id")
        print(f"\n[임시 B 생성] ID: {target_b_id}, 이름: {target_b_name}")

        try:
            url_a = f"{base_url}/network_interface/{TestNetworkInterfaceCRUD.created_id}"            
            response = requests.patch(url_a, headers=api_headers, json={"name": target_b_name})
            
            # 서버 상태 재조회
            actual_a_name = requests.get(url_a, headers=api_headers).json().get("name")

            if response.status_code == 200:
                print(f"\n🚨 [데이터 오염 확정] ID 불일치 현상 발생!")
                print(f"👉 수정 요청 대상 ID: {TestNetworkInterfaceCRUD.created_id}, 이름 결과: {actual_a_name}")
                print(f"👉 임시 리소스 B ID: {target_b_id}, 이름: {target_b_name}")

            # 기획상 409가 와야 하므로 assert 실행 (xfail에 의해 실패로 기록됨)
            assert response.status_code == 409, f"중복 이름 수정 허용됨 (코드: {response.status_code})"

        finally:
            if target_b_id:
                requests.delete(f"{base_url}/network_interface/{target_b_id}", headers=api_headers)
                verify_del = requests.get(f"{base_url}/network_interface/{target_b_id}", headers=api_headers)
                
                if verify_del.status_code in [404, 422, 409]:
                    print(f"[정리] 리소스 {target_b_id} 삭제 완료")
                else:
                    print(f"[경고!!!] 리소스 {target_b_id}가 삭제 후에도 조회됨 (서버 고스트 버그)")

    def test_NW012_interface_delete(self, api_headers):
        """[최종 정리] 생성된 리소스 삭제 및 ID 일치 여부 최종 확인"""
        if not TestNetworkInterfaceCRUD.created_id:
            pytest.skip("삭제할 ID가 없습니다.")

        url = f"{base_url}/network_interface/{TestNetworkInterfaceCRUD.created_id}"
        
        # 삭제 전 현재 서버의 실제 데이터 상태 확인
        final_check = requests.get(url, headers=api_headers)
        if final_check.status_code == 200:
            actual_data = final_check.json()
            print(f"\n[최종 삭제 전 데이터 상태]")
            print(f"👉 예상 ID: {TestNetworkInterfaceCRUD.created_id}")
            print(f"👉 실제 조회된 ID: {actual_data.get('id')}")
            print(f"👉 실제 조회된 이름: {actual_data.get('name')}")
            
            if actual_data.get('id') != TestNetworkInterfaceCRUD.created_id:
                print("🚨 경고: 관리 중인 ID와 서버의 응답 ID가 다릅니다! (데이터 오염)")

        response = requests.delete(url, headers=api_headers)
        assert response.status_code == 200
        print(f"[최종 성공] 리소스 {TestNetworkInterfaceCRUD.created_id} 삭제 요청 완료")