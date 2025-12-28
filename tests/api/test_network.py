import pytest
import requests
import uuid
import allure
import random
from loguru import logger

@allure.epic("네트워크 관리 API")
@allure.feature("네트워크 인터페이스 CRUD")
class TestNetworkInterfaceCRUD:

    # --- 헬퍼 메서드 ---
    def get_nic_payload(self):
        return {
            "name": f"team2-nic-{uuid.uuid4().hex[:6]}",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "attached_subnet_id": "a78afe80-88c6-44bc-8438-adba40aa0372",
            "dr": False
        }

    # 1. 목록 조회
    @allure.story("목록 조회")
    def test_NW001_interface_list(self, api_headers, base_url_network):
        url = f"{base_url_network}/network_interface?skip=0&count=20"
        response = requests.get(url, headers=api_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @allure.story("목록 조회")
    @allure.title("네트워크 인터페이스 목록 조회 시 응답 형식(List) 검증")
    def test_NW002_interface_list_format(self, api_headers, base_url_network):
        """
        목록 조회 시 데이터의 유무와 상관없이 서버가 항상 
        리스트(List) 형식을 반환하며 200 OK를 응답하는지 검증합니다.
        (데이터가 없을 경우 빈 리스트 [] 반환 확인)
        """
        url = f"{base_url_network}/network_interface?skip=0&count=20"
        response = requests.get(url, headers=api_headers)
        
        # 1. 상태 코드 검증
        assert response.status_code == 200, f"목록 조회 실패: {response.text}"
        
        # 2. 응답 데이터 타입 검증
        res_data = response.json()
        assert isinstance(res_data, list), f"⛔ [FAIL] 응답 데이터가 리스트 형식이 아닙니다: {type(res_data)}"
        
        # 3. 빈 리스트인 경우에도 성공으로 간주 (데이터가 없을 때의 정상 응답이므로)
        if len(res_data) == 0:
            allure.step("현재 리소스가 없어 빈 리스트([])가 반환되었습니다.")
        else:
            allure.step(f"현재 {len(res_data)}개의 리소스가 리스트로 반환되었습니다.")

    # 3. 생성 및 단건 조회 (테스크케이스 NW003, NW006 통합)
    @allure.story("생성 및 조회")
    def test_NW003_interface_create_and_get(self, resource_factory, api_headers, base_url_network):
        payload = self.get_nic_payload()
        resource = resource_factory(f"{base_url_network}/network_interface", payload)
        
        get_url = f"{base_url_network}/network_interface/{resource['id']}"
        response = requests.get(get_url, headers=api_headers)
        assert response.status_code == 200
        assert response.json()["name"] == payload["name"]

    # 4. 중복 생성 실패 (테스크케이스 NW004)
    @allure.story("예외 케이스")
    @pytest.mark.xfail(reason="서버 중복 이름 허용 버그")
    def test_NW004_duplicate_create_fail(self, resource_factory, api_headers, base_url_network):
        payload = self.get_nic_payload()
        resource_factory(f"{base_url_network}/network_interface", payload)
        
        response = requests.post(f"{base_url_network}/network_interface", headers=api_headers, json=payload)
        assert response.status_code == 409

    # 5. 존재하지 않는 참조 ID로 생성 실패 (테스크케이스 NW005)
    @allure.story("예외 케이스")
    @allure.title("존재하지 않는 zone_id 등으로 생성 시도 시 실패")
    def test_NW_005_ERR_invalid_ids(self, api_headers, base_url_network):
        invalid_uuid = str(uuid.uuid4())
        payload = {
            "name": f"invalid-ref-{uuid.uuid4().hex[:4]}",
            "zone_id": invalid_uuid,
            "attached_subnet_id": invalid_uuid,
            "dr": False
        }
        response = requests.post(f"{base_url_network}/network_interface", headers=api_headers, json=payload)
        assert response.status_code in [409, 422]

    # 6. 이름 수정 (테스크케이스 NW008)
    @allure.story("수정")
    def test_NW008_interface_patch(self, resource_factory, api_headers, base_url_network):
        resource = resource_factory(f"{base_url_network}/network_interface", self.get_nic_payload())
        url = f"{base_url_network}/network_interface/{resource['id']}"
        new_name = f"updated-{uuid.uuid4().hex[:4]}"
        
        requests.patch(url, headers=api_headers, json={"name": new_name})
        assert requests.get(url, headers=api_headers).json()["name"] == new_name

    # 7. 불변 필드 수정 시도 (테스크케이스 NW010)
    @allure.story("예외 케이스")
    @allure.title("불변 필드(zone_id) 수정 시도 시 값 유지 또는 에러 확인")
    def test_NW_010_ERR_patch_immutable_field(self, resource_factory, api_headers, base_url_network):
        resource = resource_factory(f"{base_url_network}/network_interface", self.get_nic_payload())
        url = f"{base_url_network}/network_interface/{resource['id']}"
        
        original_zone = requests.get(url, headers=api_headers).json()["zone_id"]
        response = requests.patch(url, headers=api_headers, json={"zone_id": str(uuid.uuid4())})
        
        if response.status_code == 200:
            assert requests.get(url, headers=api_headers).json()["zone_id"] == original_zone
        else:
            assert response.status_code in [400, 422, 409]

    # 8. 중복 이름으로 수정 차단 (테스크케이스 NW011)
    @allure.story("수정")
    @pytest.mark.xfail(reason="서버 중복 수정 허용 버그")
    def test_NW_011_ERR_patch_conflict(self, resource_factory, api_headers, base_url_network):
        res_a = resource_factory(f"{base_url_network}/network_interface", self.get_nic_payload())
        res_b = resource_factory(f"{base_url_network}/network_interface", self.get_nic_payload())
        
        url_a = f"{base_url_network}/network_interface/{res_a['id']}"
        response = requests.patch(url_a, headers=api_headers, json={"name": res_b["name"]})
        assert response.status_code == 409

    @allure.story("삭제")
    @allure.title("네트워크 인터페이스 삭제 프로세스 및 상태 변경 검증")
    def test_NW012_interface_delete_process(self, api_headers, base_url_network, api_helpers):
        """
        시나리오:
        1. 새 리소스를 생성한다.
        2. 생성된 리소스에 대해 삭제(DELETE)를 요청한다.
        3. 헬퍼 함수를 사용하여 리소스 상태가 'deleted'로 변할 때까지 대기하며 검증한다.
        """
        # 1. 테스트 리소스 생성
        url = f"{base_url_network}/network_interface"
        payload = self.get_nic_payload()
        res_data = requests.post(url, headers=api_headers, json=payload).json()
        res_id = res_data["id"]
        target_url = f"{url}/{res_id}"
        
        allure.step(f"대상 리소스 생성 완료: {res_id}")

        # 2. 삭제 요청 (성공 시 200 응답 기대)
        with allure.step("삭제 요청 전송"):
            delete_resp = requests.delete(target_url, headers=api_headers)
            assert delete_resp.status_code == 200, f"삭제 요청 실패: {delete_resp.text}"

        # 3. 상태 변경 폴링 검증 (src/utils/api_util.py의 로직 사용)
        with allure.step("리소스 상태가 'deleted'로 변경될 때까지 대기"):
            success = api_helpers.wait_for_status(
                url=target_url, 
                headers=api_headers, 
                expected_status="deleted",
                timeout=10  # 최대 10초 대기
            )

        # 4. 최종 결과 검증
        assert success, (
            f"⛔ [FAIL] 삭제 요청 후 10초 이내에 리소스 상태가 'deleted'로 변하지 않았습니다.\n"
            f"ID: {res_id}"
        )
        

    # 10. 연결 리소스 존재 시 삭제 차단 (테스크케이스 NW013)  
    # @allure.story("연결")
    # @allure.title("네트워크 인터페이스를 머신에 연결하는 프로세스 검증")
    # def test_NW_013_attach_interface_to_instance(self, api_headers, base_url_network, base_url_compute, api_helpers):
    #     """
    #     시나리오:
    #     1. 테스트용 가상 머신(Server)을 생성한다.
    #     2. 테스트용 네트워크 인터페이스(NIC)를 생성한다.
    #     3. NIC를 머신에 연결(Attach) 요청을 보낸다.
    #     4. 헬퍼를 통해 NIC 상태가 'active'가 되고 머신 ID가 매핑될 때까지 대기한다.
    #     """
        
    #     # 1. 가상 머신 생성
    #     with allure.step("단계 1: 테스트용 머신 생성"):
    #         instance_url = f"{base_url_compute}/server"
    #         instance_payload = {
    #             "name": f"test-vm-{uuid.uuid4().hex[:4]}",
    #             "image_id": "여기에_실제_이미지_ID",
    #             "spec_id": "여기에_실제_스펙_ID"
    #         }
    #         instance_res = requests.post(instance_url, headers=api_headers, json=instance_payload)
    #         assert instance_res.status_code == 200, f"머신 생성 실패: {instance_res.text}"
    #         instance_id = instance_res.json()["id"]
    #         logger.info(f"✅ 머신 생성 완료 (ID: {instance_id})")

    #     # 2. 네트워크 인터페이스 생성
    #     with allure.step("단계 2: 테스트용 NIC 생성"):
    #         nic_url = f"{base_url_network}/network_interface"
    #         nic_payload = {
    #             "name": f"attach-nic-{uuid.uuid4().hex[:4]}",
    #             "attached_subnet_id": "여기에_실제_서브넷_ID"
    #         }
    #         nic_res = requests.post(nic_url, headers=api_headers, json=nic_payload)
    #         assert nic_res.status_code == 200, f"NIC 생성 실패: {nic_res.text}"
    #         nic_id = nic_res.json()["id"]
    #         target_nic_url = f"{nic_url}/{nic_id}"
    #         logger.info(f"✅ NIC 생성 완료 (ID: {nic_id})")

    #     # 3. NIC를 머신에 연결 (보통 PATCH를 사용하여 attached_machine_id 업데이트)
    #     with allure.step("단계 3: NIC를 머신에 연결 요청"):
    #         logger.info(f"🔗 NIC({nic_id})를 머신({instance_id})에 연결 시도...")
    #         attach_payload = {"attached_machine_id": instance_id}
    #         attach_res = requests.patch(target_nic_url, headers=api_headers, json=attach_payload)
    #         assert attach_res.status_code == 200, f"연결 요청 실패: {attach_res.text}"

    #     # 4. 연결 상태 폴링 대기 (api_helpers 활용)
    #     with allure.step("단계 4: 연결 완료 상태 대기 (Polling)"):
    #         # src/utils/api_util.py에 정의한 함수 호출
    #         success = api_helpers.wait_for_status(
    #             url=target_nic_url,
    #             headers=api_headers,
    #             expected_status="active", # 서버 규격에 맞는 연결 완료 상태값
    #             timeout=30 # 연결은 생성보다 시간이 더 걸릴 수 있음
    #         )
        
    #     # 5. 최종 데이터 검증
    #     with allure.step("단계 5: 최종 데이터 정합성 확인"):
    #         final_nic_data = requests.get(target_nic_url, headers=api_headers).json()
            
    #         assert success, "⛔ [FAIL] 시간 내에 NIC 상태가 'active'로 변경되지 않았습니다."
    #         assert final_nic_data["attached_machine_id"] == instance_id, "⛔ [FAIL] 연결된 머신 ID가 일치하지 않습니다."
            
    #         logger.success(f"🎉 리소스 연결 및 검증 성공! (NIC: {nic_id} -> Server: {instance_id})")

    @allure.story("삭제")
    @allure.title("이미 삭제된 리소스 재삭제 시도 시 409 에러 확인")
    def test_NW_014_ERR_delete_already_deleted(self, api_headers, base_url_network):
        """
        시나리오:
        1. 리소스를 생성하고 즉시 삭제한다 (status: deleted 상태 유도).
        2. 'deleted' 상태인 리소스에 다시 DELETE 요청을 보낸다.
        3. 서버가 409 Conflict와 함께 'unexpected_status' 메시지를 반환하는지 확인한다.
        """
        url = f"{base_url_network}/network_interface"
        
        # 1. 생성 및 1차 삭제
        res_data = requests.post(url, headers=api_headers, json=self.get_nic_payload()).json()
        res_id = res_data["id"]
        target_url = f"{url}/{res_id}"
        
        requests.delete(target_url, headers=api_headers)
        allure.step(f"리소스 1차 삭제 완료 (ID: {res_id})")

        # 2. 2차 삭제 시도 (이미 삭제된 상태)
        response = requests.delete(target_url, headers=api_headers)
        res_body = response.json()

        # 3. 검증
        with allure.step("409 Conflict 및 에러 메시지 검증"):
            assert response.status_code == 409
            assert res_body["code"] == "unexpected_status"
            assert "should be active" in res_body["message"]
            
            # 상세 필드 내의 status가 deleted인지 확인
            actual_status = res_body["detail"]["resource_network_interface"]["status"]
            assert actual_status == "deleted", f"예상 상태는 deleted이나 {actual_status}가 반환됨"

    @allure.story("삭제")
    @allure.title("존재하지 않는 ID로 삭제 시도 시 409 에러 확인")
    def test_NW_015_ERR_delete_non_existent_id(self, api_headers, base_url_network):
        """
        시나리오:
        1. 서버에 존재하지 않는 무작위 UUID를 생성한다.
        2. 해당 ID를 경로에 넣어 DELETE 요청을 보낸다.
        3. 서버가 409 Conflict를 반환하는지 확인한다.
        """
        # 1. 존재하지 않는 가짜 ID 생성
        fake_id = str(uuid.uuid4())
        target_url = f"{base_url_network}/network_interface/{fake_id}"
        
        # 2. 삭제 시도
        response = requests.delete(target_url, headers=api_headers)
        
        # 3. 검증
        with allure.step(f"존재하지 않는 ID({fake_id}) 삭제 시도 결과 검증"):
            # 요청하신 대로 409 응답 코드를 명확히 검증
            assert response.status_code == 409, (
                f"⛔ [FAIL] 존재하지 않는 ID 삭제 시 409가 아닌 다른 코드 반환: {response.status_code}"
            )
            
            res_body = response.json()
            # 서버가 보내주는 에러 메시지도 함께 기록
            allure.attach(str(res_body), name="서버 응답 내용")

@allure.epic("서브넷 관리 API")
@allure.feature("서브넷 CRUD")
class TestSubNetCRUD:

    # --- 헬퍼 메서드 ---
    def get_subnet_payload(self):
        random_ip_sub = random.randint(1, 30) 
        return {
            "name": f"team2-subnet-{uuid.uuid4().hex[:6]}",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "attached_network_id": "c0c99a0a-9aca-4e73-a601-81dfb2ba7284",
            "network_gw": f"192.168.{random_ip_sub}.1/24"
            }

    @allure.story("목록 조회")
    def test_NW16_subnet_list(self, api_headers, base_url_network):
        url = f"{base_url_network}/subnet?skip=0&count=20"
        response = requests.get(url, headers=api_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @allure.story("생성 및 조회")
    def test_NW17_subnet_create_and_get(self, resource_factory, api_headers, base_url_network):
        payload = self.get_subnet_payload()
        resource = resource_factory(f"{base_url_network}/subnet", payload)
        
        get_url = f"{base_url_network}/subnet/{resource['id']}"
        response = requests.get(get_url, headers=api_headers)
        assert response.status_code == 200
        assert response.json()["name"] == payload["name"]