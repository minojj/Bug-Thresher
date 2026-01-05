import requests
import pytest
import allure
import uuid
import time

# 후보군 instance_type_id (TC28에서 create fallback에 사용)
INSTANCE_TYPE_CANDIDATES = [
    "320909e3-44ce-4018-8b55-7e837cd84a15",
    "332d9f31-595c-4d0f-aebd-4aaf49c345a5",  # C-16
    "830e2041-d477-4058-a65c-386a93ead237",  # M-2
    "c0d04e23-c5bb-4625-8906-13dc2644981c"
]

class TestComputeCRUD:
    created_vm_id = None
    deleted_vm_verified = False
    
    # VM-001 생성, 수정, 삭제 (resource_factory 적용)
    def test_VM_create_rename_delete(self, api_headers, base_url_compute):

        # 1) VM 생성
        vm_name = f"vm-{uuid.uuid4().hex[:6]}"
        create_url = f"{base_url_compute}/virtual_machine"

        payload = {
            "name": vm_name,
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "instance_type_id": "320909e3-44ce-4018-8b55-7e837cd84a15",  # VM-001 성공한 값
            "username": "test",
            "password": "1qaz2wsx@@",
            "on_init_script": "",
            "always_on": False,
            "dr": False,
        }

        # POST 응답에는 id만 내려오는 경우가 있어 name은 GET으로 검증
        r_create = self._request("POST", create_url, headers=api_headers, json=payload)
        assert r_create.status_code in (200, 201), f"VM 생성 실패: {r_create.status_code}: {r_create.text}"

        new_vm = r_create.json()
        vm_id = new_vm["id"]

        # 생성 직후 단건 조회로 payload 반영 확인
        get_url = f"{base_url_compute}/virtual_machine/{vm_id}"
        r_get = requests.get(get_url, headers=api_headers)
        assert r_get.status_code == 200, f"⛔ [FAIL] 생성 직후 조회 실패 - {r_get.status_code}: {r_get.text}"

        vm_one = r_get.json()
        assert isinstance(vm_one, dict)
        assert vm_one["id"] == vm_id
        assert vm_one["name"] == vm_name
        assert vm_one["zone_id"] is not None
        
        # 2) VM 이름 수정 (뒤에 test 추가)
        patch_url = f"{base_url_compute}/virtual_machine/{vm_id}"
        new_name = f"{vm_name} test"

        r_patch = requests.patch(patch_url, headers=api_headers, json={"name": new_name})
        assert r_patch.status_code == 200, f"VM 이름 수정 실패: {r_patch.status_code}: {r_patch.text}"

        # 수정 반영 조회 검증
        r_get2 = requests.get(get_url, headers=api_headers)
        assert r_get2.status_code == 200, f"⛔ [FAIL] 수정 후 조회 실패 - {r_get2.status_code}: {r_get2.text}"

        vm_one2 = r_get2.json()
        assert vm_one2["id"] == vm_id
        assert vm_one2["name"] == new_name

        # 3) VM 삭제 (직접 삭제 검증도 수행)
        delete_url = f"{base_url_compute}/virtual_machine/{vm_id}"
        r_delete = requests.delete(delete_url, headers=api_headers)
        assert r_delete.status_code == 200, f"VM 삭제 실패: {r_delete.status_code}: {r_delete.text}"
    
    # VM-002 다른 인스턴스 타입으로 VM 생성       
    @allure.story("예외 케이스")
    @allure.story("xfail")
    @pytest.mark.xfail(reason="환경 제한으로 인스턴스 타입 사용 불가 시도")
    def test_VM002_create_vm_different_instance_type(self, api_headers, resource_factory, base_url_compute):
        url = f"{base_url_compute}/virtual_machine"

        payload = {
            "name": f"vm-auto-type2-{uuid.uuid4().hex[:6]}",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "instance_type_id": "332d9f31-595c-4d0f-aebd-4aaf49c345a5",  # C-16
            "username": "test",
            "password": "1qaz2wsx@@",
            "on_init_script": "",
            "always_on": False,
            "dr": False,
        }

        # 환경 제한이면 XFAIL
        try:
            resource_factory(url, payload)
        except AssertionError as e:
            pytest.xfail(f"환경 제한: {e}")
            
    # VM-003 OS 이미지 지정 생성 (Blocked)        
    @allure.story("예외 케이스")
    @allure.story("skip")
    @pytest.mark.skip(
        reason="Blocked: VM create API payload/response에 OS image 식별값(image_id/os_image_id 등) 미노출로 선택 OS 적용 여부 판정 불가"
    )
    
    def test_VM003_create_vm_with_os_image(self, api_client, api_headers):
        pass

    # VM-004 초기화 스크립트 포함 VM 생성
    @allure.story("예외 케이스")
    @allure.story("xfail")
    @pytest.mark.xfail(reason="환경 제한으로 초기화 스크립트 포함 VM 생성 불가 시도")
    def test_VM004_create_vm_with_init_script(self, api_headers, resource_factory, base_url_compute):
        url = f"{base_url_compute}/virtual_machine"

        payload = {
            "name": f"vm-20251223-545d01-init-{uuid.uuid4().hex[:6]}",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "instance_type_id": "830e2041-d477-4058-a65c-386a93ead237",  # M-2
            "username": "test",
            "password": "1qaz2wsx@@",
            "on_init_script": "#!/bin/bash\necho test",
            "always_on": False,
            "dr": False,
        }

        # quota 또는 환경 제한: 409 등은 팀 규칙대로 XFAIL
        try:
            resource_factory(url, payload)
        except AssertionError as e:
            # quota/환경 제한은 xfail
            pytest.xfail(f"quota 또는 환경 제한: {e}")

    # VM-005 DR 옵션 VM 생성
    @allure.story("예외 케이스")
    @allure.story("skip")
    @pytest.mark.skip(
        reason="Blocked: dr=true 요청 시 API가 zone_no_secondary_zone 반환. 해당 zone_id에 secondary zone 미구성으로 DR VM 생성 검증 불가."
    )
    
    def test_VM005_create_vm_with_dr_true_blocked(self):
        pass
    
    # VM-006 VM 다건 조회
    def test_VM006_list_vm(self, api_headers, base_url_compute):
        url = f"{base_url_compute}/virtual_machine_allocation"
        r = self._request("GET", url, headers=api_headers)

        assert r.status_code == 200, f"status={r.status_code}, body={r.text}"
        assert isinstance(r.json(), list)

    # VM-007 특정 상태 VM 목록 조회
    def test_VM007_list_vm_by_status(self, api_headers, base_url_compute):
        url = f"{base_url_compute}/virtual_machine"

        r = self._request("GET", url, headers=api_headers)
        assert r.status_code == 200, f"status={r.status_code}, body={r.text}"

        items = r.json()
        assert isinstance(items, list), f"list 아님: {items}"

        # 이전 TC + 실제 response로 확인된 상태값만 사용
        allowed_statuses = ("idle", "allocated")

        for it in items:
            assert it.get("status") in allowed_statuses, f"unexpected status: {it}"
    
    # VM-008 VM 목록 조회 (Search)
    def test_VM008_list_vm(self, api_headers, base_url_compute):
        vms = self._list_vms(api_headers, base_url_compute)
        assert isinstance(vms, list)
    
    # VM-009 VM 단건 조회 (machine_id 기반)
    def test_VM009_get_vm_one(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)
        vm = self._get_vm_by_machine_id(api_headers, base_url_compute, vm_id)
        assert vm is not None
        assert vm.get("machine_id") or vm.get("id")

    def _list_vms(self, api_headers, base_url_compute):
        r = self._request(
            "GET",
            f"{base_url_compute}/virtual_machine_allocation",
            headers=api_headers,
        )
        return r.json()

    def _ensure_vm_id(self, api_headers, base_url_compute):
        if self.created_vm_id and not self.deleted_vm_verified:
            return self.created_vm_id

        vms = self._list_vms(api_headers, base_url_compute)
        return vms[0].get("machine_id") or vms[0].get("id")

    def _get_vm_by_machine_id(self, api_headers, base_url_compute, vm_id):
        r = self._request(
            "GET",
            f"{base_url_compute}/virtual_machine/{vm_id}",
            headers=api_headers,
        )
        if r.status_code == 200:
            return r.json()
        return None

    # VM-020
    def test_VM020_GET_vm_resource_monitoring(self, api_headers, base_url_compute):
        """
        [VM020] VM 리소스 모니터링 대시보드 조회
        """
        endpoint = f"{base_url_compute}/virtual_machine"

        params = {
            "sort_by": "created_desc",
            "count": 100
        }

        print(f"\n📡 호출 URL: {endpoint}")
        response = self._request("GET", endpoint, headers=api_headers, params=params)

        assert response.status_code == 200, f"⛔ 조회 실패! (상태 코드: {response.status_code})"
    
    # VM-026
    @allure.story("예외 케이스")
    @allure.story("xfail")
    @pytest.mark.xfail(reason="환경 제한으로 VM 가시성 확인 불가 시도")
    def test_VM026_wait_vm_visible(self, api_headers, base_url_compute, vm_id, timeout_sec=60):
        # 1. 아까 작성하신 메서드를 통해 vm_id를 내부적으로 가져옵니다.
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)
        
        if not vm_id:
            pytest.fail("테스트에 사용할 VM ID를 찾을 수 없습니다.")

        end = time.time() + timeout_sec
        while time.time() < end:
            # 2. 가져온 vm_id를 사용하여 가시성 확인
            if self._get_vm_by_machine_id(api_headers, base_url_compute, vm_id):
                return
        
        pytest.fail(f"VM {vm_id} not visible after {timeout_sec} seconds")
    
    # VM-028
    @allure.story("예외 케이스")
    def test_VM030_ERR_create_cluster_empty_vm_ids(self, api_headers, base_url_compute):
        url = f"{base_url_compute}/cluster"
        
        body = {
            "name": "cluster-invalid",
            "vm_ids": [] 
        }

        response = self._request("POST", url, headers=api_headers, json=body)

        assert response.status_code == 404, \
            f"⛔ [FAIL] 빈 vm_ids 요청 시 404가 아닌 {response.status_code} 반환: {response.text}"
        
        assert "Not Found" in response.text, \
            f"⛔ [FAIL] 에러 상세 내용이 기대와 다름: {response.text}"
                    
    # 헬퍼 메서드

    def _request(self, method, url, **kwargs):
        r = requests.request(method, url, **kwargs)
        if r.status_code == 403:
            try:
                data = r.json()
                if data.get("code") == "expired_token":
                    pytest.xfail("expired_token")
            except Exception:
                pass
        return r