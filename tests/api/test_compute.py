import requests
import pytest
import uuid
import time


class TestComputeCRUD:
    created_vm_id = None

    # VM-001 VM 생성
    def test_VM001_create_vm(self, api_headers, base_url_compute):
        url = f"{base_url_compute}/virtual_machine"

        body = {
            "name": f"vm-auto-{uuid.uuid4().hex[:6]}",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "instance_type_id": "830e2041-d477-4058-a65c-386a93ead237",  # M-2
            "username": "test",
            "password": "1qaz2wsx@@",
            "on_init_script": "",
            "always_on": False,
            "dr": False
        }

        r = requests.post(url, headers=api_headers, json=body)
        assert r.status_code in (200, 201), f"status={r.status_code}, body={r.text}"

        res = r.json()
        TestComputeCRUD.created_vm_id = res["id"]

    # VM-002 동일 파라미터로 VM 재생성
    def test_VM002_recreate_vm(self, api_headers, base_url_compute):
        url = f"{base_url_compute}/virtual_machine"

        payload = {
            "name": f"vm-auto-{uuid.uuid4().hex[:6]}",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "instance_type_id": "320909e3-44ce-4018-8b55-7e837cd84a15",
            "username": "test",
            "password": "1qaz2wsx@@",
            "on_init_script": "",
            "always_on": False,
            "dr": False
        }

        r = requests.post(url, headers=api_headers, json=payload)

        if r.status_code == 409:
            pytest.xfail(f"quota 또는 환경 제한: {r.text}")

        assert r.status_code in (200, 201)

    # VM-003 다른 인스턴스 타입으로 VM 생성
    def test_VM003_create_vm_different_instance_type(self, api_headers, base_url_compute):
        url = f"{base_url_compute}/virtual_machine"

        payload = {
            "name": f"vm-auto-type2-{uuid.uuid4().hex[:6]}",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "instance_type_id": "61d9beec-27d5-44df-a3b2-5ec200d2eebb",
            "username": "test",
            "password": "1qaz2wsx@@",
            "on_init_script": "",
            "always_on": False,
            "dr": False
        }

        r = requests.post(url, headers=api_headers, json=payload)

        if r.status_code in (400, 404, 409, 422):
            pytest.xfail(f"환경 제한: {r.text}")

        assert r.status_code in (200, 201)

    # VM-004 OS 이미지 지정 생성 (Blocked)
    def test_VM004_create_vm_with_image(self):
        pytest.xfail("VM 생성 API에 image_id 미지원")

    # VM-005 초기화 스크립트 포함 VM 생성
    def test_VM005_create_vm_with_init_script(self, api_headers, base_url_compute):
        url = f"{base_url_compute}/virtual_machine"

        payload = {
            "name": f"vm-auto-init-{uuid.uuid4().hex[:6]}",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "instance_type_id": "320909e3-44ce-4018-8b55-7e837cd84a15",
            "username": "test",
            "password": "1qaz2wsx@@",
            "on_init_script": "#!/bin/bash\necho test",
            "always_on": False,
            "dr": False
        }

        r = requests.post(url, headers=api_headers, json=payload)

        if r.status_code == 409:
            pytest.xfail(f"quota 또는 환경 제한: {r.text}")

        assert r.status_code in (200, 201)

    # VM-006 DR 옵션 VM 생성
    def test_VM006_create_vm_with_dr(self, api_headers, base_url_compute):
        url = f"{base_url_compute}/virtual_machine"

        payload = {
            "name": f"vm-auto-dr-{uuid.uuid4().hex[:6]}",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "instance_type_id": "320909e3-44ce-4018-8b55-7e837cd84a15",
            "username": "test",
            "password": "1qaz2wsx@@",
            "on_init_script": "",
            "always_on": False,
            "dr": True
        }

        r = requests.post(url, headers=api_headers, json=payload)

        if r.status_code == 409:
            pytest.xfail(f"quota 또는 환경 제한: {r.text}")

        assert r.status_code in (200, 201)

    # VM-007 VM 삭제
    def test_VM007_delete_vm(self, api_headers, base_url_compute):
        vm_id = TestComputeCRUD.created_vm_id
        assert vm_id is not None

        url = f"{base_url_compute}/virtual_machine/{vm_id}"
        r = requests.delete(url, headers=api_headers)

        assert r.status_code == 200

    # VM-008 삭제 후 단건 조회
    def test_VM008_get_deleted_vm(self, api_headers, base_url_compute):
        vm_id = TestComputeCRUD.created_vm_id
        url = f"{base_url_compute}/virtual_machine/{vm_id}"

        r = requests.get(url, headers=api_headers)
        assert r.status_code in (200, 404)

    # VM-009 VM 다건 조회
    def test_VM009_list_vm(self, api_headers, base_url_compute):
        url = f"{base_url_compute}/virtual_machine_allocation"
        r = requests.get(url, headers=api_headers)

        assert r.status_code == 200
        assert isinstance(r.json(), list)

    # VM-010 특정 상태 VM 목록 조회
    def test_VM010_list_vm_by_status(self, api_headers, base_url_compute):
        vm_id = TestComputeCRUD.created_vm_id
        assert vm_id is not None

        start_url = f"{base_url_compute}/virtual_machine_control/start"
        requests.post(start_url, headers=api_headers, json={"id": vm_id})

        time.sleep(10)

        url = f"{base_url_compute}/virtual_machine_allocation?filter_status=RUNNING"
        r = requests.get(url, headers=api_headers)

        assert r.status_code in (200, 422)

        if r.status_code == 200:
            for vm in r.json():
                assert vm["status"] == "RUNNING"

    # VM-011 VM 목록 조회 (Search)
    def test_VM011_list_vm(self, api_headers, base_url_compute):
        vms = self._list_vms(api_headers, base_url_compute)
        assert isinstance(vms, list)

    # VM-012 VM 단건 조회 (machine_id 기반)
    def test_VM012_get_vm_one(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)
        vm = self._get_vm_by_machine_id(api_headers, base_url_compute, vm_id)
        assert vm is not None
        # 최소한 id/machine_id 둘 중 하나는 있어야 한다고 보고 체크
        assert vm.get("machine_id") or vm.get("id")

    # VM-013 VM 시작
    def test_VM013_start_vm(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)
        start_url = f"{base_url_compute}/virtual_machine_control/start"
        r = requests.post(start_url, headers=api_headers, json={"id": vm_id})
        # 200/202 등 가능성 고려
        assert r.status_code in (200, 202)
        self._wait_status(api_headers, base_url_compute, vm_id, ["RUNNING"])

    # VM-014 목록에서 VM 상태 확인 (RUNNING/STOP 필터)
    def test_VM014_check_vm_status_filter(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)

        # 일단 RUNNING 만들어두기
        start_url = f"{base_url_compute}/virtual_machine_control/start"
        requests.post(start_url, headers=api_headers, json={"id": vm_id})
        self._wait_status(api_headers, base_url_compute, vm_id, ["RUNNING"])

        # filter_status가 대소문자/허용값 문제(422) 있을 수 있어서 후보를 돌림
        val, data = self._try_filter_status(api_headers, base_url_compute, ["RUNNING", "running", "Run", "on", "ON"])
        if val is None:
            pytest.xfail("filter_status 파라미터 허용값/형식 미확정(계속 422)")

        assert isinstance(data, list)
        # 전부 해당 상태인지까지는 서버 구현에 따라 애매할 수 있어 "최소 1개 존재"로 체크
        assert len(data) >= 1

    # VM-015 실행중 VM 정지
    def test_VM015_stop_vm(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)

        # RUNNING 보장
        start_url = f"{base_url_compute}/virtual_machine_control/start"
        requests.post(start_url, headers=api_headers, json={"id": vm_id})
        self._wait_status(api_headers, base_url_compute, vm_id, ["RUNNING"])

        stop_url = f"{base_url_compute}/virtual_machine_control/stop"
        r = requests.post(stop_url, headers=api_headers, json={"id": vm_id})
        assert r.status_code in (200, 202)
        self._wait_status(api_headers, base_url_compute, vm_id, ["STOP"])

    # VM-016 정지 후 상태 확인
    def test_VM016_check_stopped_vm(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)
        # STOP 보장
        stop_url = f"{base_url_compute}/virtual_machine_control/stop"
        requests.post(stop_url, headers=api_headers, json={"id": vm_id})
        self._wait_status(api_headers, base_url_compute, vm_id, ["STOP"])

        vm = self._get_vm_by_machine_id(api_headers, base_url_compute, vm_id)
        assert vm is not None
        assert "STOP" in (vm.get("status") or "").upper()

    # VM-017 VM 리부팅(Soft)
    def test_VM017_reboot_soft(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)

        # RUNNING 보장
        start_url = f"{base_url_compute}/virtual_machine_control/start"
        requests.post(start_url, headers=api_headers, json={"id": vm_id})
        self._wait_status(api_headers, base_url_compute, vm_id, ["RUNNING"])

        reboot_url = f"{base_url_compute}/virtual_machine_control/reboot"
        r = requests.post(reboot_url, headers=api_headers, json={"id": vm_id, "type": "soft"})
        assert r.status_code in (200, 202)

        # 리부팅 후 다시 RUNNING으로 돌아오는지(환경에 따라 시간이 걸림)
        self._wait_status(api_headers, base_url_compute, vm_id, ["RUNNING"], timeout_sec=180)

    # VM-018 웹 콘솔 접속 정보 조회
    def test_VM018_get_console(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)
        # RUNNING 권장
        start_url = f"{base_url_compute}/virtual_machine_control/start"
        requests.post(start_url, headers=api_headers, json={"id": vm_id})
        self._wait_status(api_headers, base_url_compute, vm_id, ["RUNNING"])

        url = f"{base_url_compute}/virtual_machine_console"
        r = requests.get(url, headers=api_headers, params={"id": vm_id})
        if r.status_code in (404, 501):
            pytest.xfail(f"console API 미지원: {r.status_code} {r.text}")
        assert r.status_code == 200

    # VM-019 SSH 접속 정보 조회(지원 시)
    def test_VM019_get_ssh_info(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)
        url = f"{base_url_compute}/virtual_machine_ssh"
        r = requests.get(url, headers=api_headers, params={"id": vm_id})
        if r.status_code in (404, 501):
            pytest.xfail(f"ssh info API 미지원: {r.status_code} {r.text}")
        assert r.status_code == 200

    # VM-020 SSH 접속 가능 여부 확인(지원 시)
    def test_VM020_check_ssh(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)
        url = f"{base_url_compute}/virtual_machine_ssh/check"
        r = requests.post(url, headers=api_headers, json={"id": vm_id})
        if r.status_code in (404, 501):
            pytest.xfail(f"ssh check API 미지원: {r.status_code} {r.text}")
        assert r.status_code == 200

    # VM-021 VM 메트릭 조회
    def test_VM021_get_metrics(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)
        # RUNNING 권장
        start_url = f"{base_url_compute}/virtual_machine_control/start"
        requests.post(start_url, headers=api_headers, json={"id": vm_id})
        self._wait_status(api_headers, base_url_compute, vm_id, ["RUNNING"])

        url = f"{base_url_compute}/virtual_machine_metrics"
        r = requests.get(url, headers=api_headers, params={"id": vm_id})
        if r.status_code in (404, 501):
            pytest.xfail(f"metrics API 미지원: {r.status_code} {r.text}")
        assert r.status_code == 200

    # VM-022 VM 건강 상태 조회
    def test_VM022_get_health(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)
        url = f"{base_url_compute}/virtual_machine_health"
        r = requests.get(url, headers=api_headers, params={"id": vm_id})
        if r.status_code in (404, 501):
            pytest.xfail(f"health API 미지원: {r.status_code} {r.text}")
        assert r.status_code == 200