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
    
    @allure.story("목록 조회")
    def test_NW001_interface_list(self, api_headers, base_url_network):
        url = f"{base_url_network}/network_interface?skip=0&count=20"
        response = requests.get(url, headers=api_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @allure.story("빈 목록 조회")
    @allure.title("네트워크 인터페이스 목록 조회 시 응답 형식(List) 검증")
    def test_NW002_interface_list_format(self, api_headers, base_url_network):

        url = f"{base_url_network}/network_interface?skip=0&count=20"
        response = requests.get(url, headers=api_headers)
        
        assert response.status_code == 200, f"목록 조회 실패: {response.text}"
        
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

    @allure.story("예외 케이스")
    @pytest.mark.xfail(reason="서버 중복 이름 허용 버그")
    def test_NW004_duplicate_create_fail(self, resource_factory, api_headers, base_url_network):
        payload = self.get_nic_payload()
        resource_factory(f"{base_url_network}/network_interface", payload)
        
        response = requests.post(f"{base_url_network}/network_interface", headers=api_headers, json=payload)
        assert response.status_code == 409

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

    @allure.story("수정")
    def test_NW008_interface_patch(self, resource_factory, api_headers, base_url_network):
        resource = resource_factory(f"{base_url_network}/network_interface", self.get_nic_payload())
        url = f"{base_url_network}/network_interface/{resource['id']}"
        new_name = f"updated-{uuid.uuid4().hex[:4]}"
        
        requests.patch(url, headers=api_headers, json={"name": new_name})
        assert requests.get(url, headers=api_headers).json()["name"] == new_name

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

    @allure.story("수정")
    @pytest.mark.xfail(reason="서버 중복 수정 허용 버그")
    def test_NW_011_ERR_patch_conflict(self, resource_factory, api_headers, base_url_network):
        res_a = resource_factory(f"{base_url_network}/network_interface", self.get_nic_payload())
        res_b = resource_factory(f"{base_url_network}/network_interface", self.get_nic_payload())
        
        url_a = f"{base_url_network}/network_interface/{res_a['id']}"
        response = requests.patch(url_a, headers=api_headers, json={"name": res_b["name"]})
        assert response.status_code == 409

    @allure.story("NIC 삭제")
    @allure.title("NW12: NIC 삭제 및 실제 제거 확인")
    def test_NW12_nic_delete(self, resource_factory, api_headers, base_url_network, api_helpers):
        payload = self.get_nic_payload()
        resource = resource_factory(f"{base_url_network}/network_interface", payload, teardown=False)
        url = f"{base_url_network}/network_interface/{resource['id']}"

        logger.info(f"🗑️ [NW12] NIC 삭제 요청: {url}")
        assert requests.delete(url, headers=api_headers).status_code == 200

        # ✅ api_helpers를 사용하여 스마트 대기 (지수 백오프 적용됨)
        success = api_helpers.wait_for_status(url, api_headers)
        assert success, "⛔ [FAIL] 시간 이내에 NIC가 삭제되지 않았습니다."
        logger.success("✅ [NW12] NIC 삭제 확인 완료")
        

    # 10. 연결 리소스 존재 시 삭제 차단 (테스크케이스 NW013)  
    @allure.story("연결")
    @allure.title("네트워크 인터페이스를 머신에 연결하는 프로세스 검증")
    @pytest.mark.skip(reason="API 중복 수정 검증 미구현")
    def test_NW_013_attach_interface_to_instance(self, api_headers, base_url_network, base_url_compute, api_helpers):
        """
        시나리오:
        1. 테스트용 가상 머신(Server)을 생성한다.
        2. 테스트용 네트워크 인터페이스(NIC)를 생성한다.
        3. NIC를 머신에 연결(Attach) 요청을 보낸다.
        4. 헬퍼를 통해 NIC 상태가 'active'가 되고 머신 ID가 매핑될 때까지 대기한다.
        """
        
        # 1. 가상 머신 생성
        with allure.step("단계 1: 테스트용 머신 생성"):
            instance_url = f"{base_url_compute}/server"
            instance_payload = {
                "name": f"test-vm-{uuid.uuid4().hex[:4]}",
                "image_id": "여기에_실제_이미지_ID",
                "spec_id": "여기에_실제_스펙_ID"
            }
            instance_res = requests.post(instance_url, headers=api_headers, json=instance_payload)
            assert instance_res.status_code == 200, f"머신 생성 실패: {instance_res.text}"
            instance_id = instance_res.json()["id"]
            logger.info(f"✅ 머신 생성 완료 (ID: {instance_id})")

        # 2. 네트워크 인터페이스 생성
        with allure.step("단계 2: 테스트용 NIC 생성"):
            nic_url = f"{base_url_network}/network_interface"
            nic_payload = {
                "name": f"attach-nic-{uuid.uuid4().hex[:4]}",
                "attached_subnet_id": "여기에_실제_서브넷_ID"
            }
            nic_res = requests.post(nic_url, headers=api_headers, json=nic_payload)
            assert nic_res.status_code == 200, f"NIC 생성 실패: {nic_res.text}"
            nic_id = nic_res.json()["id"]
            target_nic_url = f"{nic_url}/{nic_id}"
            logger.info(f"✅ NIC 생성 완료 (ID: {nic_id})")

        # 3. NIC를 머신에 연결 (보통 PATCH를 사용하여 attached_machine_id 업데이트)
        with allure.step("단계 3: NIC를 머신에 연결 요청"):
            logger.info(f"🔗 NIC({nic_id})를 머신({instance_id})에 연결 시도...")
            attach_payload = {"attached_machine_id": instance_id}
            attach_res = requests.patch(target_nic_url, headers=api_headers, json=attach_payload)
            assert attach_res.status_code == 200, f"연결 요청 실패: {attach_res.text}"

        # 4. 연결 상태 폴링 대기 (api_helpers 활용)
        with allure.step("단계 4: 연결 완료 상태 대기 (Polling)"):
            # src/utils/api_util.py에 정의한 함수 호출
            success = api_helpers.wait_for_status(
                url=target_nic_url,
                headers=api_headers,
                expected_status="active", # 서버 규격에 맞는 연결 완료 상태값
                timeout=30 # 연결은 생성보다 시간이 더 걸릴 수 있음
            )
        
        # 5. 최종 데이터 검증
        with allure.step("단계 5: 최종 데이터 정합성 확인"):
            final_nic_data = requests.get(target_nic_url, headers=api_headers).json()
            
            assert success, "⛔ [FAIL] 시간 내에 NIC 상태가 'active'로 변경되지 않았습니다."
            assert final_nic_data["attached_machine_id"] == instance_id, "⛔ [FAIL] 연결된 머신 ID가 일치하지 않습니다."
            
            logger.success(f"🎉 리소스 연결 및 검증 성공! (NIC: {nic_id} -> Server: {instance_id})")

    @allure.story("삭제")
    @allure.title("이미 삭제된 리소스 재삭제 시도 시 409 에러 확인")
    def test_NW_014_ERR_delete_already_deleted(self, api_headers, base_url_network):
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

    #테스트케이스 19번 조회 포함
    @allure.story("생성 및 조회")
    def test_NW17_subnet_create_and_get(self, resource_factory, api_headers, base_url_network):
        payload = self.get_subnet_payload()
        resource = resource_factory(f"{base_url_network}/subnet", payload)
        
        get_url = f"{base_url_network}/subnet/{resource['id']}"
        response = requests.get(get_url, headers=api_headers)
        assert response.status_code == 200
        assert response.json()["name"] == payload["name"]

    @allure.story("예외 케이스")
    def test_NW18_ERR_duplicate_subnet_create_fail(self, resource_factory, api_headers, base_url_network):
        payload = self.get_subnet_payload()
        resource_factory(f"{base_url_network}/subnet", payload)
        
        response = requests.post(f"{base_url_network}/subnet", headers=api_headers, json=payload)
        assert response.status_code == 409

    @allure.title("NW20: 존재하지 않는 서브넷 ID 조회 시 404 응답 확인")
    def test_NW20_ERR_get_non_existent_subnet(self, api_headers, base_url_network):
        fake_id = str(uuid.uuid4()) 
        url = f"{base_url_network}/subnet/{fake_id}"
        response = requests.get(url, headers=api_headers)
        assert response.status_code == 404

    @allure.story("수정")
    def test_NW21_subnet_patch(self, resource_factory, api_headers, base_url_network):
        resource = resource_factory(f"{base_url_network}/subnet", self.get_subnet_payload())
        url = f"{base_url_network}/subnet/{resource['id']}"
        new_name = f"updated-{uuid.uuid4().hex[:4]}"
        
        requests.patch(url, headers=api_headers, json={"name": new_name})
        assert requests.get(url, headers=api_headers).json()["name"] == new_name

    @allure.story("반복 수정 :같은 이름 변경 *3번")
    def test_NW22_subnet_repeated_patch(self, resource_factory, api_headers, base_url_network):
        resource = resource_factory(f"{base_url_network}/subnet", self.get_subnet_payload())
        url = f"{base_url_network}/subnet/{resource['id']}"
        
        for i in range(3):
            new_name = f"repeated-{i}-{uuid.uuid4().hex[:4]}"
            with allure.step(f"수정 시도 {i+1}: 이름을 '{new_name}'(으)로 변경"):
                requests.patch(url, headers=api_headers, json={"name": new_name})
                current_name = requests.get(url, headers=api_headers).json()["name"]
                assert current_name == new_name, f"⛔ [FAIL] 수정 {i+1} 실패: 현재 이름은 '{current_name}'"
                logger.info(f"✅ 수정 {i+1} 성공: 이름이 '{current_name}'(으)로 변경됨")

    @allure.story("수정 연결 해제")
    @pytest.mark.skip(reason="API 중복 수정 검증 미구현")
    def test_NW23_subnet_detach_network(self, resource_factory, api_headers, base_url_network):
        resource = resource_factory(f"{base_url_network}/subnet", self.get_subnet_payload())
        url = f"{base_url_network}/subnet/{resource['id']}"
        
        requests.patch(url, headers=api_headers, json={"attached_network_id": None})
        assert requests.get(url, headers=api_headers).json()["attached_network_id"] is None

    @allure.story("서브넷 삭제")
    @allure.title("NW24: 서브넷 삭제 및 실제 제거 확인")
    def test_NW24_subnet_delete(self, resource_factory, api_headers, base_url_network, api_helpers):
        payload = self.get_subnet_payload()
        resource = resource_factory(f"{base_url_network}/subnet", payload, teardown=False)
        url = f"{base_url_network}/subnet/{resource['id']}"

        logger.info(f"🗑️ [NW24] 서브넷 삭제 요청: {url}")
        assert requests.delete(url, headers=api_headers).status_code == 200

        # ✅ api_helpers를 사용하여 스마트 대기
        success = api_helpers.wait_for_status(url, api_headers)
        assert success, "⛔ [FAIL] 시간 이내에 서브넷이 삭제되지 않았습니다."
        logger.success("✅ [NW24] 서브넷 삭제 확인 완료")

    @allure.story("예외 케이스")
    @allure.title("NW25: 연결된 네트워크 존재 시 서브넷 삭제 차단 검증")
    @pytest.mark.skip(reason="API 중복 수정 검증 미구현")
    def test_NW25_ERR_delete_subnet_with_attached_network(self, resource_factory, api_headers, base_url_network):
        resource = resource_factory(f"{base_url_network}/subnet", self.get_subnet_payload())
        url = f"{base_url_network}/subnet/{resource['id']}"
        
        response = requests.delete(url, headers=api_headers)
        
        with allure.step("삭제 차단 및 에러 메시지 검증"):
            assert response.status_code == 409, (
                f"⛔ [FAIL] 연결된 네트워크가 있는 서브넷 삭제 시 409가 아닌 다른 코드 반환: {response.status_code}"
            )
            
            res_body = response.json()
            assert res_body["code"] == "resource_in_use", f"⛔ [FAIL] 에러 코드가 일치하지 않습니다: {res_body['code']}"
            assert "cannot be deleted" in res_body["message"], f"⛔ [FAIL] 에러 메시지가 일치하지 않습니다: {res_body['message']}"

    @allure.story("예외 케이스")
    @allure.title("NW26: 존재하지 않는 ID로 서브넷 삭제 시도 409 에러 확인")
    def test_NW26_ERR_delete_non_existent_subnet(self, api_headers, base_url_network):
        fake_id = str(uuid.uuid4())
        target_url = f"{base_url_network}/subnet/{fake_id}"
        
        response = requests.delete(target_url, headers=api_headers)
        
        with allure.step(f"존재하지 않는 ID({fake_id}) 삭제 시도 결과 검증"):
            assert response.status_code == 409, (
                f"⛔ [FAIL] 존재하지 않는 ID 삭제 시 409가 아닌 다른 코드 반환: {response.status_code}"
            )
            
            res_body = response.json()
            allure.attach(str(res_body), name="서버 응답 내용")    

