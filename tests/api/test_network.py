from urllib import response
import pytest
import requests
import uuid
import allure
import random
from loguru import logger

from tests.conftest import api_headers

class TestNetworkInterfaceCRUD:

    # --- 헬퍼 메서드 ---
    def get_nic_payload(self):
        return {
            "name": f"team2-nic-{uuid.uuid4().hex[:6]}",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "attached_subnet_id": "a78afe80-88c6-44bc-8438-adba40aa0372",
            "dr": False
        }
    
    def test_NW001_interface_list(self, api_headers, base_url_network):
        url = f"{base_url_network}/network_interface?skip=0&count=20"
        response = requests.get(url, headers=api_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_NW002_interface_list_format(self, api_headers, base_url_network):
        url = f"{base_url_network}/network_interface?skip=0&count=20"
        response = requests.get(url, headers=api_headers)
        
        assert response.status_code == 200, f"목록 조회 실패: {response.text}"
        
        res_data = response.json()
        assert isinstance(res_data, list), f"⛔ [FAIL] 응답 데이터가 리스트 형식이 아닙니다: {type(res_data)}"
        
        # 빈 리스트인 경우에도 성공으로 간주
        if len(res_data) == 0:
            allure.step("현재 리소스가 없어 빈 리스트([])가 반환되었습니다.")
        else:
            allure.step(f"현재 {len(res_data)}개의 리소스가 리스트로 반환되었습니다.")

    def test_NW003_NW006_interface_create_and_get(self, resource_factory, api_headers, base_url_network):
        payload = self.get_nic_payload()
        resource = resource_factory(f"{base_url_network}/network_interface", payload)
        
        get_url = f"{base_url_network}/network_interface/{resource['id']}"
        response = requests.get(get_url, headers=api_headers)
        assert response.status_code == 200, f"⛔ [FAIL] 200과 다른 상태 코드: {response.status_code}"
        assert response.json()["name"] == payload["name"]

    @allure.story("예외 케이스:중복 서버생성")
    @pytest.mark.xfail(reason="서버 중복 이름 허용 버그")
    def test_NW004_duplicate_create_fail(self, resource_factory, api_headers, base_url_network):
        payload = self.get_nic_payload()
        resource_factory(f"{base_url_network}/network_interface", payload)
        
        response = requests.post(f"{base_url_network}/network_interface", headers=api_headers, json=payload)
        assert response.status_code == 409, f"⛔ [FAIL] 409와 다른 상태 코드: {response.status_code}"

    @allure.story("예외 케이스:존재하지 않는 zone_id 등으로 생성 시도 시 실패")
    def test_NW_005_ERR_invalid_ids(self, api_headers, base_url_network):
        invalid_uuid = str(uuid.uuid4())
        payload = {
            "name": f"invalid-ref-{uuid.uuid4().hex[:4]}",
            "zone_id": invalid_uuid,
            "attached_subnet_id": invalid_uuid,
            "dr": False
        }
        response = requests.post(f"{base_url_network}/network_interface", headers=api_headers, json=payload)
        assert response.status_code == 409

    def test_NW008_interface_patch(self, resource_factory, api_headers, base_url_network):
        resource = resource_factory(f"{base_url_network}/network_interface", self.get_nic_payload())
        url = f"{base_url_network}/network_interface/{resource['id']}"
        new_name = f"updated-{uuid.uuid4().hex[:4]}"
        
        requests.patch(url, headers=api_headers, json={"name": new_name})
        assert requests.get(url, headers=api_headers).json()["name"] == new_name

    @allure.story("예외 케이스:불변 필드(zone_id) 수정 시도 시 값 유지 확인")
    def test_NW_010_ERR_patch_immutable_field(self, resource_factory, api_headers, base_url_network):
        resource = resource_factory(f"{base_url_network}/network_interface", self.get_nic_payload())
        url = f"{base_url_network}/network_interface/{resource['id']}"
        
        original_zone = requests.get(url, headers=api_headers).json()["zone_id"]
        new_zone_id = str(uuid.uuid4())
        response = requests.patch(url, headers=api_headers, json={"zone_id": new_zone_id})
    
        # [검증] 시나리오 A: 서버는 요청을 수락(200)해야 함
        assert response.status_code == 200, f"불변 필드 수정 시 200 OK를 기대했으나 {response.status_code}가 반환됨"

        # [검증] 응답은 성공이었지만, 실제로 조회를 해봤을 때 값은 바뀌지 않았어야 함
        current_zone = requests.get(url, headers=api_headers).json()["zone_id"]
        assert current_zone == original_zone, f"불변 필드인 zone_id가 {original_zone}에서 {current_zone}으로 변경됨"

    def test_NW_011_ERR_patch_conflict(self, resource_factory, api_headers, base_url_network):
        res_a = resource_factory(f"{base_url_network}/network_interface", self.get_nic_payload())
        res_b = resource_factory(f"{base_url_network}/network_interface", self.get_nic_payload())
        
        url_a = f"{base_url_network}/network_interface/{res_a['id']}"
        response = requests.patch(url_a, headers=api_headers, json={"name": res_b["name"]})
        assert response.status_code == 200, f"⛔ [FAIL] 200과 다른 상태 코드: {response.status_code}"
    
    def test_NW_012_NW007_network_full_cycle(self, resource_factory, api_headers, base_url_network, api_helpers):
        zone_id = "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0"

        # --- 단계 1: 가상 네트워크 생성 ---
        with allure.step("단계 1: 가상 네트워크 생성"):
            vn_payload = {
                "name": f"team2-vn-{uuid.uuid4().hex[:6]}",
                "zone_id": zone_id,
                "network_cidr": "192.168.0.0/16"
            }
            vn = resource_factory(f"{base_url_network}/virtual_network", vn_payload)
            vn_id = vn["id"]
            logger.info(f"✅ 가상 네트워크 생성 완료 (ID: {vn_id})")

        # --- 단계 2: 서브넷 생성 ---
        with allure.step("단계 2: 서브넷 생성"):
            random_ip_sub = random.randint(1, 30)
            sub_payload = {
                "name": f"team2-sub-{uuid.uuid4().hex[:4]}",
                "zone_id": zone_id,
                "attached_network_id": vn_id,
                "network_gw": f"192.168.{random_ip_sub}.1/24"
            }
            subnet = resource_factory(f"{base_url_network}/subnet", sub_payload)
            subnet_id = subnet["id"]
            logger.info(f"✅ 서브넷 생성 완료 (ID: {subnet_id})")

        # --- 단계 3: NIC 생성 (클래스 헬퍼 메서드 활용) ---
        with allure.step("단계 3: NIC 생성 및 서브넷 연결 확인"):
            # 기존 헬퍼 메서드에서 페이로드를 가져옵니다.
            nic_payload = self.get_nic_payload()
            # 생성된 서브넷 ID로 덮어쓰기 (핵심!)
            nic_payload["attached_subnet_id"] = subnet_id
            
            nic = resource_factory(f"{base_url_network}/network_interface", nic_payload)
            nic_id = nic["id"]
            target_nic_url = f"{base_url_network}/network_interface/{nic_id}"

            # 연결 상태 폴링 확인
            success = api_helpers.wait_for_status(
                url=target_nic_url,
                headers=api_headers,
                expected_status=subnet_id,
                status_key="attached_subnet_id",
                timeout=20
            )
            assert success, "⛔ [FAIL] NIC가 서브넷에 정상적으로 연결되지 않았습니다."
            logger.success(f"✅ NIC 생성 및 연결 확인 완료")

        # --- 단계 4: 연결 해제 (Detach) ---
        with allure.step("단계 4: NIC에서 머신(또는 상위 리소스) 연결 해제"):
            logger.info(f"🔓 NIC({nic_id}) 해제 시도 (포스트맨 방식 적용)...")

            detach_payload = {"attached_machine_id": None}

            res = requests.patch(target_nic_url, headers=api_headers, json=detach_payload)
            assert res.status_code == 200, f"⛔ [FAIL] PATCH 요청 실패: {res.text}"

            is_detached = api_helpers.wait_for_status(
                url=target_nic_url,
                headers=api_headers,
                expected_status=None,
                status_key="attached_machine_id", 
                timeout=20
            )

            final_data = requests.get(target_nic_url, headers=api_headers).json()
            actual_machine = final_data.get("attached_machine_id")

            assert is_detached, f"⛔ [FAIL] NIC 해제 실패 (현재 머신 ID: {actual_machine})"
            logger.success("🎉 가상 네트워크 생성부터 NIC 해제까지 전체 시나리오 성공!")

    def test_NW013_nic_delete(self, api_headers, base_url_network, api_helpers):
        """삭제 테스트: resource_factory 사용하지 않고 직접 생성"""
        url = f"{base_url_network}/network_interface"
        payload = self.get_nic_payload()
        
        response = requests.post(url, headers=api_headers, json=payload)
        assert response.status_code == 200, f"⛔ [FAIL] 생성 실패: {response.text}"
        resource_id = response.json()["id"]
        target_url = f"{url}/{resource_id}"

        logger.info(f"🗑️ [NW13] NIC 삭제 요청: {target_url}")
        assert requests.delete(target_url, headers=api_headers).status_code == 200

        # api_helpers를 사용하여 스마트 대기 (지수 백오프 적용됨)
        success = api_helpers.wait_for_status(target_url, api_headers, expected_status="deleted")
        assert success, "⛔ [FAIL] 시간 이내에 NIC가 삭제되지 않았습니다."
        logger.success("✅ [NW13] NIC 삭제 확인 완료")


    @allure.story("예외 케이스:이미 삭제된 리소스 재삭제 시도 시 409 에러 확인")
    def test_NW_014_ERR_delete_already_deleted(self, api_headers, base_url_network):
        """재삭제 테스트: resource_factory 사용하지 않고 직접 생성"""
        url = f"{base_url_network}/network_interface"
        payload = self.get_nic_payload()
        
        # 1. 직접 생성
        response = requests.post(url, headers=api_headers, json=payload)
        assert response.status_code == 200, f"⛔ [FAIL] 생성 실패: {response.text}"
        resource_id = response.json()["id"]
        target_url = f"{url}/{resource_id}"
        
        # 2. 1차 삭제
        requests.delete(target_url, headers=api_headers)
        allure.step(f"리소스 1차 삭제 완료 (ID: {resource_id})")

        # 3. 2차 삭제 시도 (이미 삭제된 상태)
        response = requests.delete(target_url, headers=api_headers)
        res_body = response.json()

        # 4. 검증
        with allure.step("409 Conflict 및 에러 메시지 검증"):
            assert response.status_code == 409, f"⛔ [FAIL] 409와 다른 상태 코드: {response.status_code}"
            assert res_body["code"] == "unexpected_status"
            assert "should be active" in res_body["message"]
            
            # 상세 필드 내의 status가 deleted인지 확인
            actual_status = res_body["detail"]["resource_network_interface"]["status"]
            assert actual_status == "deleted", f"예상 상태는 deleted이나 {actual_status}가 반환됨"

    @allure.story("예외 케이스:존재하지 않는 ID로 삭제 시도 시 409 에러 확인")
    def test_NW_015_ERR_delete_non_existent_id(self, api_headers, base_url_network):
        # 1. 존재하지 않는 가짜 ID 생성
        fake_id = str(uuid.uuid4())
        target_url = f"{base_url_network}/network_interface/{fake_id}"
        
        # 2. 삭제 시도
        response = requests.delete(target_url, headers=api_headers)
        
        # 3. 검증
        with allure.step(f"존재하지 않는 ID({fake_id}) 삭제 시도 결과 검증"):
            assert response.status_code == 409, (
                f"⛔ [FAIL] 존재하지 않는 ID 삭제 시 409가 아닌 다른 코드 반환: {response.status_code}"
            )
            
            res_body = response.json()
            allure.attach(str(res_body), name="서버 응답 내용")


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

    def test_NW16_subnet_list(self, api_headers, base_url_network):
        url = f"{base_url_network}/subnet?skip=0&count=20"
        response = requests.get(url, headers=api_headers)
        assert response.status_code == 200, f"⛔ [FAIL] 생성 실패: {response.text}"
        assert isinstance(response.json(), list)

    def test_NW017_subnet_create_and_get(self, resource_factory, api_headers, base_url_network):
        payload = self.get_subnet_payload()
        resource = resource_factory(f"{base_url_network}/subnet", payload)
        
        get_url = f"{base_url_network}/subnet/{resource['id']}"
        response = requests.get(get_url, headers=api_headers)
        assert response.status_code == 200, f"⛔ [FAIL] 생성 실패: {response.text}"
        assert response.json()["name"] == payload["name"]

    @allure.story("예외 케이스:중복 서브넷생성")
    def test_NW018_ERR_duplicate_subnet_create_fail(self, resource_factory, api_headers, base_url_network):
        payload = self.get_subnet_payload()
        resource_factory(f"{base_url_network}/subnet", payload)
        
        response = requests.post(f"{base_url_network}/subnet", headers=api_headers, json=payload)
        assert response.status_code == 409, f"⛔ [FAIL] 409와 다른 상태 코드: {response.status_code}"

    @allure.story("예외케이스: 존재하지 않는 서브넷 ID 조회 시 409 응답 확인")
    def test_NW020_ERR_get_non_existent_subnet(self, api_headers, base_url_network):
        fake_id = str(uuid.uuid4()) 
        url = f"{base_url_network}/subnet/{fake_id}"
        response = requests.get(url, headers=api_headers)
        assert response.status_code == 409, f"⛔ [FAIL] 409와 다른 상태 코드: {response.status_code}"

    def test_NW021_subnet_patch(self, resource_factory, api_headers, base_url_network):
        resource = resource_factory(f"{base_url_network}/subnet", self.get_subnet_payload())
        url = f"{base_url_network}/subnet/{resource['id']}"
        new_name = f"updated-{uuid.uuid4().hex[:4]}"
        
        requests.patch(url, headers=api_headers, json={"name": new_name})
        assert requests.get(url, headers=api_headers).json()["name"] == new_name

    def test_NW022_subnet_repeated_patch(self, resource_factory, api_headers, base_url_network):
        resource = resource_factory(f"{base_url_network}/subnet", self.get_subnet_payload())
        url = f"{base_url_network}/subnet/{resource['id']}"
        
        for i in range(3):
            new_name = f"repeated-{i}-{uuid.uuid4().hex[:4]}"
            with allure.step(f"수정 시도 {i+1}: 이름을 '{new_name}'(으)로 변경"):
                requests.patch(url, headers=api_headers, json={"name": new_name})
                current_name = requests.get(url, headers=api_headers).json()["name"]
                assert current_name == new_name, f"⛔ [FAIL] 수정 {i+1} 실패: 현재 이름은 '{current_name}'"
                logger.info(f"✅ 수정 {i+1} 성공: 이름이 '{current_name}'(으)로 변경됨")

    
    def test_NW023_subnet_delete(self, api_headers, base_url_network, api_helpers):
        url = f"{base_url_network}/subnet"
        payload = self.get_subnet_payload()
        
        response = requests.post(url, headers=api_headers, json=payload)
        assert response.status_code == 200, f"⛔ [FAIL] 생성 실패: {response.text}"
        resource_id = response.json()["id"]
        target_url = f"{url}/{resource_id}"

        logger.info(f"🗑️ [NW23] 서브넷 삭제 요청: {target_url}")
        assert requests.delete(target_url, headers=api_headers).status_code == 200

        # api_helpers를 사용하여 스마트 대기
        success = api_helpers.wait_for_status(target_url, api_headers, expected_status="deleted")
        assert success, "⛔ [FAIL] 시간 이내에 서브넷이 삭제되지 않았습니다."
        logger.success("✅ [NW23] 서브넷 삭제 확인 완료")

    @allure.story("예외 케이스: 연결된 NIC 존재 시 서브넷 삭제 차단 검증")
    def test_NW024_ERR_delete_subnet_with_attached_nic(self, resource_factory, api_headers, base_url_network):
        # 1. 서브넷 생성
        subnet_payload = self.get_subnet_payload()
        subnet = resource_factory(f"{base_url_network}/subnet", subnet_payload)
        subnet_id = subnet['id']

        # 2. 의존성 리소스(NIC) 생성하여 서브넷 잠금
        with allure.step("의존성 생성: 해당 서브넷을 사용하는 NIC 생성"):
            nic_payload = {
                "name": f"team2-nic-for-lock-{uuid.uuid4().hex[:4]}",
                "zone_id": subnet_payload["zone_id"],
                "attached_subnet_id": subnet_id,
                "dr": False
            }
            resource_factory(f"{base_url_network}/network_interface", nic_payload)

        url = f"{base_url_network}/subnet/{subnet_id}"
        response = requests.delete(url, headers=api_headers)

        with allure.step("삭제 차단 및 에러 메시지 검증"):
            # 응답 코드 확인
            assert response.status_code == 409, (
                f"⛔ [FAIL] NIC가 연결된 서브넷이 삭제되었습니다. (상태 코드: {response.status_code})"
            )

            res_body = response.json()
            assert res_body["code"] == "interface_found", f"⛔ [FAIL] 에러 코드가 일치하지 않습니다: {res_body['code']}"
            assert "interface" in res_body["message"].lower(), f"⛔ [FAIL] 에러 메시지에 원인 설명이 부족합니다: {res_body['message']}"
            logger.success(f"✅ 검증 성공: 서버가 '{res_body['code']}' 코드로 삭제를 정상적으로 차단함")

    @allure.story("예외 케이스: 존재하지 않는 ID로 서브넷 삭제 시도 409 에러 확인")
    def test_NW025_ERR_delete_non_existent_subnet(self, api_headers, base_url_network):
        fake_id = str(uuid.uuid4())
        target_url = f"{base_url_network}/subnet/{fake_id}"
        
        response = requests.delete(target_url, headers=api_headers)
        
        with allure.step(f"존재하지 않는 ID({fake_id}) 삭제 시도 결과 검증"):
            assert response.status_code == 409, (
                f"⛔ [FAIL] 존재하지 않는 ID 삭제 시 409가 아닌 다른 코드 반환: {response.status_code}"
            )
            
            res_body = response.json()
            allure.attach(str(res_body), name="서버 응답 내용")


class TestVirtualNetworkCRUD:
    # 클래스 내부 헬퍼 메서드
    def get_vn_payload(self):
        return {
            "name": f"team2-vn-{uuid.uuid4().hex[:6]}",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "network_cidr": "192.168.0.0/16"
        }
    
    def test_NW026_vn_list(self, api_headers, base_url_network):
        url = f"{base_url_network}/virtual_network?skip=0&count=20"
        response = requests.get(url, headers=api_headers)
        assert response.status_code == 200, f"⛔ [FAIL] 생성 실패: {response.text}"
        assert isinstance(response.json(), list)

    #테스트 케이스 30번 포함
    def test_NW027_NW030_vn_create_and_get(self, resource_factory, api_headers, base_url_network):
        payload = self.get_vn_payload()
        resource = resource_factory(f"{base_url_network}/virtual_network", payload)
        
        get_url = f"{base_url_network}/virtual_network/{resource['id']}"
        response = requests.get(get_url, headers=api_headers)
        assert response.status_code == 200, f"⛔ [FAIL] 생성 실패: {response.text}"
        assert response.json()["name"] == payload["name"]

    @allure.story("예외 케이스:중복 VN생성")
    def test_NW028_ERR_duplicate_vn_create_fail(self, resource_factory, api_headers, base_url_network):
        payload = self.get_vn_payload()
        resource_factory(f"{base_url_network}/virtual_network", payload)
        
        response = requests.post(f"{base_url_network}/virtual_network", headers=api_headers, json=payload)
        assert response.status_code == 200, f"⛔ [FAIL] 200와 다른 상태 코드: {response.status_code}"

        if response.status_code == 200:
            extra_id = response.json().get("id")
            requests.delete(f"{base_url_network}/virtual_network/{extra_id}", headers=api_headers)
        
        assert response.status_code == 200 # 기존 어설션 유지

    @allure.story("예외케이스:필수값 누락시")
    def test_NW029_ERR_create_missing_required_field(self, api_headers, base_url_network):
        payload = {
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "network_cidr": "192.168.0.0/16"
        }
        response = requests.post(f"{base_url_network}/virtual_network", headers=api_headers, json=payload)
        assert response.status_code == 422, f"⛔ [FAIL] 422와 다른 상태 코드: {response.status_code}"   

    @allure.story("예외 케이스:존재하지 않는 데이터 조회")  
    def test_NW031_ERR_get_non_existent_vn(self, api_headers, base_url_network):
        fake_id = str(uuid.uuid4()) 
        url = f"{base_url_network}/virtual_network/{fake_id}"
        response = requests.get(url, headers=api_headers)
        assert response.status_code == 409, f"⛔ [FAIL] 409와 다른 상태 코드: {response.status_code}"

    def test_NW032_vn_patch(self, resource_factory, api_headers, base_url_network):
        resource = resource_factory(f"{base_url_network}/virtual_network", self.get_vn_payload())
        url = f"{base_url_network}/virtual_network/{resource['id']}"
        new_name = f"updated-{uuid.uuid4().hex[:4]}"
        
        requests.patch(url, headers=api_headers, json={"name": new_name})
        assert requests.get(url, headers=api_headers).json()["name"] == new_name

    @allure.story("예외 케이스:반복 수정: 같은 이름 변경 *3번")
    def test_NW033_vn_repeated_patch(self, resource_factory, api_headers,    base_url_network):
        resource = resource_factory(f"{base_url_network}/virtual_network", self.get_vn_payload())
        url = f"{base_url_network}/virtual_network/{resource['id']}"
        
        for i in range(3):
            new_name = f"repeated-{i}-{uuid.uuid4().hex[:4]}"
            with allure.step(f"수정 시도 {i+1}: 이름을 '{new_name}'(으)로 변경"):
                requests.patch(url, headers=api_headers, json={"name": new_name})
                current_name = requests.get(url, headers=api_headers).json()["name"]
                assert current_name == new_name, f"⛔ [FAIL] 수정 {i+1} 실패: 현재 이름은 '{current_name}'"
                logger.info(f"✅ 수정 {i+1} 성공: 이름이 '{current_name}'(으)로 변경됨")

    def test_NW034_vn_delete(self, api_headers, base_url_network, api_helpers):
        url = f"{base_url_network}/virtual_network"
        payload = self.get_vn_payload()
        
        response = requests.post(url, headers=api_headers, json=payload)
        assert response.status_code == 200, f"⛔ [FAIL] 생성 실패: {response.text}"
        resource_id = response.json()["id"]
        target_url = f"{url}/{resource_id}"

        logger.info(f"🗑️ [NW33] 가상 네트워크 삭제 요청: {target_url}")
        assert requests.delete(target_url, headers=api_headers).status_code == 200

        # api_helpers를 사용하여 스마트 대기
        success = api_helpers.wait_for_status(target_url, api_headers,expected_status="deleted")
        assert success, "⛔ [FAIL] 시간 이내에 가상 네트워크가 삭제되지 않았습니다."
        logger.success("✅ [NW33] 가상 네트워크 삭제 확인 완료")

    @allure.story("예외 케이스: 존재하지 않는 ID로 가상 네트워크 삭제 시도 409 에러 확인")
    def test_NW035_ERR_delete_non_existent_vn(self, api_headers, base_url_network):
        fake_id = str(uuid.uuid4())
        target_url = f"{base_url_network}/virtual_network/{fake_id}"
        
        response = requests.delete(target_url, headers=api_headers)
        
        with allure.step(f"존재하지 않는 ID({fake_id}) 삭제 시도 결과 검증"):
            assert response.status_code == 409, (
                f"⛔ [FAIL] 존재하지 않는 ID 삭제 시 409가 아닌 다른 코드 반환: {response.status_code}"
            )
            
            res_body = response.json()
            allure.attach(str(res_body), name="서버 응답 내용") 

    @allure.story("예외 케이스: 이미 삭제된 가상 네트워크 재삭제 시도 시 409 에러 확인")
    def test_NW036_ERR_delete_already_deleted_vn(self, api_headers, base_url_network, api_helpers):  
        """재삭제 테스트: resource_factory 사용하지 않고 직접 생성"""
        url = f"{base_url_network}/virtual_network"
        payload = self.get_vn_payload()
        
        # 1. 직접 생성
        response = requests.post(url, headers=api_headers, json=payload)
        assert response.status_code == 200, f"⛔ [FAIL] 생성 실패: {response.text}"
        resource_id = response.json()["id"]
        target_url = f"{url}/{resource_id}"
        
        # 2. 1차 삭제
        requests.delete(target_url, headers=api_headers)
        allure.step(f"리소스 1차 삭제 완료 (ID: {resource_id})")

        # 3. 2차 삭제 시도 (이미 삭제된 상태)
        response = requests.delete(target_url, headers=api_headers)
        res_body = response.json()

        # 4. 검증
        with allure.step("409 Conflict 및 에러 메시지 검증"):
            assert response.status_code == 409, f"⛔ [FAIL] 409와 다른 상태 코드: {response.status_code}"
            assert res_body["code"] == "unexpected_status"
            assert "should be active" in res_body["message"]    
            # 상세 필드 내의 status가 deleted인지 확인
            actual_status = res_body["detail"]["resource_virtual_network"]["status"]    
            assert actual_status == "deleted", f"예상 상태는 deleted이나 {actual_status}가 반환됨"
            allure.attach(str(res_body), name="서버 응답 내용")
            allure.step("✅ 재삭제 테스트 완료")

    @allure.story("예외 케이스: 연결된 서브넷 존재 시 가상 네트워크 삭제 차단 검증")
    def test_NW037_ERR_delete_vn_with_attached_subnet(self, resource_factory, api_headers, base_url_network):
        # 1. 가상 네트워크(VN) 생성
        vn_payload = self.get_vn_payload()
        vn = resource_factory(f"{base_url_network}/virtual_network", vn_payload)
        vn_id = vn['id']
        
        # 💡 [핵심] 409 에러를 유도하기 위해 해당 VN에 서브넷을 하나 생성합니다.
        with allure.step("의존성 생성: 해당 VN을 부모로 갖는 서브넷 생성"):
            sub_payload = {
                "name": f"team2-sub-lock-{uuid.uuid4().hex[:4]}",
                "zone_id": vn_payload["zone_id"],
                "attached_network_id": vn_id,
                "network_gw": "192.168.10.1/24"
            }
            resource_factory(f"{base_url_network}/subnet", sub_payload)

        # 2. 가상 네트워크 삭제 시도
        url = f"{base_url_network}/virtual_network/{vn_id}"
        response = requests.delete(url, headers=api_headers)
        
        with allure.step("삭제 차단 및 에러 메시지 검증"):
            assert response.status_code == 409, (
                f"⛔ [FAIL] 서브넷이 포함된 VN이 삭제되었습니다. (상태 코드: {response.status_code})"
            )
            
            res_body = response.json()
            
            assert "found" in res_body["code"] or "in_use" in res_body["code"], \
                f"⛔ [FAIL] 에러 코드가 일치하지 않습니다: {res_body['code']}"
            
            allure.attach(str(res_body), name="서버 응답 내용")
            logger.success(f"✅ VN 삭제 차단 검증 완료 (에러 코드: {res_body['code']})")

class TestPublicIpCRUD:

    # --- 헬퍼 메서드 ---
    def get_public_ip_payload(self):
        return {
            "name": f"team2-public-ip-{uuid.uuid4().hex[:6]}",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "ddos": True,
            "dr": False
        }

    def test_NW038_public_ip_list(self, api_headers, base_url_network):
        url = f"{base_url_network}/public_ip?skip=0&count=20"
        with allure.step("공인 IP 목록 조회 API 호출"):
            response = requests.get(url, headers=api_headers)
        
        with allure.step("응답 상태 코드 및 데이터 형식 검증"):
            assert response.status_code == 200, f"⛔ 목록 조회 실패: {response.text}"
            res_data = response.json()
            assert isinstance(res_data, list), f"⛔ 응답이 리스트 형식이 아님: {type(res_data)}"
            logger.info(f"✅ 조회된 공인 IP 개수: {len(res_data)}개")


    @allure.story("예외 케이스: 중복 이름으로 공인 IP 생성 시도 시 200 확인")
    def test_NW039_ERR_duplicate_public_ip_create_fail(self, resource_factory, api_headers, base_url_network):
        payload = self.get_public_ip_payload()
        resource_factory(f"{base_url_network}/public_ip", payload)
        
        response = requests.post(f"{base_url_network}/public_ip", headers=api_headers, json=payload)

        if response.status_code == 200:
            extra_id = response.json().get("id")
            requests.delete(f"{base_url_network}/public_ip/{extra_id}", headers=api_headers)
            
        assert response.status_code == 200

    @allure.story("예외 케이스: 필수 필드 누락 시 공인 IP 생성 실패 검증")
    def test_NW040_ERR_create_public_ip_missing_required_field(self, api_headers, base_url_network):
        payload = {"zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0"} # name 누락
        response = requests.post(f"{base_url_network}/public_ip", headers=api_headers, json=payload)
        assert response.status_code == 422, f"⛔ 예상 코드 422, 실제: {response.status_code}"

    def test_NW041_check_created_public_ip_in_list(self, resource_factory, api_headers, base_url_network):
        payload = self.get_public_ip_payload()
        created_ip = resource_factory(f"{base_url_network}/public_ip", payload)
        target_id = created_ip['id']

        with allure.step("전체 목록에서 생성한 ID 검색"):
            response = requests.get(f"{base_url_network}/public_ip", headers=api_headers)
            ip_list = response.json()
            found = any(ip['id'] == target_id for ip in ip_list)
            assert found, f"⛔ 생성된 공인 IP {target_id}가 목록에 없습니다."
            logger.success(f"✅ 목록 노출 확인 완료")

    def test_NW042_public_ip_patch(self, resource_factory, api_headers, base_url_network):
        """공인 IP의 태그를 수정하고 변경 사항이 반영되는지 확인"""
        # 1. 리소스 생성
        resource = resource_factory(f"{base_url_network}/public_ip", self.get_public_ip_payload())
        url = f"{base_url_network}/public_ip/{resource['id']}"
        
        # 2. 포스트맨에서 성공한 바디값과 동일한 구조로 설정
        patch_payload = {
            "tags": {"env": "prod", "test": "pytest"}
        }

        with allure.step("공인 IP 태그 수정 요청"):
            response = requests.patch(url, headers=api_headers, json=patch_payload)
            assert response.status_code == 200, f"⛔ PATCH 요청 실패: {response.text}"

        with allure.step("수정된 데이터 상세 조회 및 검증"):
            updated_ip = requests.get(url, headers=api_headers).json()
            
            # tags 필드 검증 (KeyError 방지)
            actual_tags = updated_ip.get("tags", {})
            assert actual_tags.get("env") == "prod", f"⛔ 태그 수정 미반영: {updated_ip}"
            assert actual_tags.get("test") == "pytest"
            
            logger.success(f"✅ 공인 IP 태그 수정 및 반영 확인 완료: {actual_tags}")

    @allure.story("예외 케이스: 존재하지 않는 NIC로 공인 IP 연결 시도 시 에러 확인")
    def test_NW043_ERR_attach_public_ip_to_non_existent_nic(self, resource_factory, api_headers, base_url_network):
        public_ip = resource_factory(f"{base_url_network}/public_ip", self.get_public_ip_payload())
        fake_nic_id = str(uuid.uuid4())
        
        url = f"{base_url_network}/public_ip/{public_ip['id']}"
        response = requests.patch(url, headers=api_headers, json={"attached_network_interface_id": fake_nic_id})
        
        # [수정] 서버가 409를 준다면 409로 검증
        assert response.status_code in [409, 422], f"⛔ 예상 코드 409/422, 실제: {response.status_code}"

    @allure.story("예외 케이스: 공인 IP 연결 해제 및 반영 확인") 
    def test_NW044_public_ip_detach(self, resource_factory, api_headers, base_url_network):
        public_ip = resource_factory(f"{base_url_network}/public_ip", self.get_public_ip_payload())
        
        # [수정] NIC 생성 시 필수 필드(attached_subnet_id, dr) 추가
        nic_payload = {
            "name": f"test-nic-{uuid.uuid4().hex[:4]}",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "attached_network_id": "c0c99a0a-9aca-4e73-a601-81dfb2ba7284",
            "attached_subnet_id": "a78afe80-88c6-44bc-8438-adba40aa0372", # 실제 서브넷 ID 권장
            "dr": False
        }
        nic = resource_factory(f"{base_url_network}/network_interface", nic_payload)
        
        url = f"{base_url_network}/public_ip/{public_ip['id']}"
        # 연결 후 해제
        requests.patch(url, headers=api_headers, json={"attached_network_interface_id": nic["id"]})
        requests.patch(url, headers=api_headers, json={"attached_network_interface_id": None})
        
        updated_ip = requests.get(url, headers=api_headers).json()
        val = updated_ip.get("attached_network_interface_id")
        assert val is None or val == "", "⛔ 연결 해제 실패"

    def test_NW045_public_ip_delete(self, api_headers, base_url_network, api_helpers):
        response = requests.post(f"{base_url_network}/public_ip", headers=api_headers, json=self.get_public_ip_payload())
        resource_id = response.json()["id"]
        target_url = f"{base_url_network}/public_ip/{resource_id}"

        requests.delete(target_url, headers=api_headers)

        # [수정] expected_status="deleted" 필수 인자 추가
        success = api_helpers.wait_for_status(target_url, api_headers,expected_status="deleted")
        assert success, "⛔ 삭제 대기 타임아웃"

    @allure.story("예외 케이스: 이미 삭제된 공인 IP 재삭제 시도 시 409 에러 확인")
    def test_NW046_ERR_delete_already_deleted_public_ip(self, api_headers, base_url_network, api_helpers):  
        response = requests.post(f"{base_url_network}/public_ip", headers=api_headers, json=self.get_public_ip_payload())
        resource_id = response.json()["id"]
        target_url = f"{base_url_network}/public_ip/{resource_id}"
        
        # 1차 삭제
        requests.delete(target_url, headers=api_headers)
        api_helpers.wait_for_status(target_url, api_headers, expected_status="deleted")
        allure.step(f"리소스 1차 삭제 완료 (ID: {resource_id})")

        # 2차 삭제 시도 (이미 삭제된 상태)
        response = requests.delete(target_url, headers=api_headers)
        res_body = response.json()

        # 검증
        with allure.step("409 Conflict 및 에러 메시지 검증"):
            assert response.status_code == 409, f"⛔ [FAIL] 409와 다른 상태 코드: {response.status_code}"
            assert res_body["code"] == "unexpected_status"
            assert "should be active" in res_body["message"]    
            # 상세 필드 내의 status가 deleted인지 확인
            actual_status = res_body["detail"]["resource_public_ip"]["status"]    
            assert actual_status == "deleted", f"예상 상태는 deleted이나 {actual_status}가 반환됨"

    @allure.story("예외 케이스: 존재하지 않는 ID로 공인 IP 삭제 시도 409 에러 확인")
    def test_NW047_ERR_delete_non_existent_public_ip(self, api_headers, base_url_network):
        fake_id = str(uuid.uuid4())
        target_url = f"{base_url_network}/public_ip/{fake_id}"
        
        response = requests.delete(target_url, headers=api_headers)
        
        with allure.step(f"존재하지 않는 ID({fake_id}) 삭제 시도 결과 검증"):
            assert response.status_code == 409, (
                f"⛔ [FAIL] 존재하지 않는 ID 삭제 시 409가 아닌 다른 코드 반환: {response.status_code}"
            )
            
            res_body = response.json()
            allure.attach(str(res_body), name="서버 응답 내용")

    def test_NW048_public_ip_nic_integration(self, resource_factory, api_headers, base_url_network, api_helpers):
        public_ip = resource_factory(f"{base_url_network}/public_ip", self.get_public_ip_payload())
        
        # [수정] NIC 생성 시 필수 필드 추가
        nic_payload = {
            "name": f"int-nic-{uuid.uuid4().hex[:4]}",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "attached_network_id": "c0c99a0a-9aca-4e73-a601-81dfb2ba7284",
            "attached_subnet_id": "a78afe80-88c6-44bc-8438-adba40aa0372", # 실제 값 확인 필요
            "dr": False
        }
        nic = resource_factory(f"{base_url_network}/network_interface", nic_payload)
        
        url = f"{base_url_network}/public_ip/{public_ip['id']}"

        try:
            with allure.step("연결 및 해제"):
                requests.patch(url, headers=api_headers, json={"attached_network_interface_id": nic["id"]})
                detach_res = requests.patch(url, headers=api_headers, json={"attached_network_interface_id": None})
                assert detach_res.status_code == 200, "해제 요청 자체가 실패함"

            with allure.step("최종 상태 검증"):
                updated_ip = requests.get(url, headers=api_headers).json()
                assert not updated_ip.get("attached_network_interface_id"), "⛔ 미해제 상태"
        
        finally:
            requests.patch(url, headers=api_headers, json={"attached_network_interface_id": None})

    @allure.story("예외 케이스: 만료된 토큰으로 접근 시 에러 확인")
    def test_NW049_ERR_access_with_expired_token(self, base_url_network):
        expired_headers = {"Authorization": "Bearer expired_token", "Content-Type": "application/json"}
        response = requests.get(f"{base_url_network}/public_ip", headers=expired_headers)
        assert response.status_code in [401, 403], f"⛔ 예상 코드 401/403, 실제: {response.status_code}"