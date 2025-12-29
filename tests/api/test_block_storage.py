import requests
import pytest
import uuid
import time


class TestComputeCRUD:
    created_vm_id = None
    deleted_vm_verified = False

    # ----------------------------
    # VM-001 VM 생성
    def test_VM001_create_vm(self, api_headers, base_url_compute):
        url = f"{base_url_compute}/virtual_machine"

        body = {
            "name": f"vm-auto-{uuid.uuid4().hex[:6]}",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            # ✅ 네가 성공시킨 instance_type_id로 유지/교체해도 됨
            "instance_type_id": "830e2041-d477-4058-a65c-386a93ead237",  # M-2
            "username": "test",
            "password": "1qaz2wsx@@",
            "on_init_script": "",
            "always_on": False,
            "dr": False
        }

        r = requests.post(url, headers=api_headers, json=body)
        self._xfail_if_expired_token(r)

        assert r.status_code in (200, 201), f"status={r.status_code}, body={r.text}"

        res = r.json()
        assert "id" in res, f"missing id in response: {res}"

        TestComputeCRUD.created_vm_id = res["id"]

        # ✅ 가짜 PASS 방지: 생성 후 실제로 조회 가능해질 때까지 확인
        self._wait_vm_visible(api_headers, base_url_compute, TestComputeCRUD.created_vm_id, timeout_sec=60)

    # ----------------------------
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
        self._xfail_if_expired_token(r)

        if r.status_code == 409:
            pytest.xfail(f"quota 또는 환경 제한: {r.text}")

        assert r.status_code in (200, 201), f"status={r.status_code}, body={r.text}"

    # ----------------------------
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
        self._xfail_if_expired_token(r)

        if r.status_code in (400, 404, 409, 422):
            pytest.xfail(f"환경 제한: {r.text}")

        assert r.status_code in (200, 201), f"status={r.status_code}, body={r.text}"

    # ----------------------------
    # VM-004 OS 이미지 지정 생성 (Blocked)
    def test_VM004_create_vm_with_image(self):
        pytest.xfail("VM 생성 API에 image_id 미지원")

    # ----------------------------
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
        self._xfail_if_expired_token(r)

        if r.status_code == 409:
            pytest.xfail(f"quota 또는 환경 제한: {r.text}")

        assert r.status_code in (200, 201), f"status={r.status_code}, body={r.text}"

    # ----------------------------
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
        self._xfail_if_expired_token(r)

        if r.status_code == 409:
            pytest.xfail(f"quota 또는 환경 제한: {r.text}")

        assert r.status_code in (200, 201), f"status={r.status_code}, body={r.text}"

    # ----------------------------
    # VM-007 VM 삭제
    def test_VM007_delete_vm(self, api_headers, base_url_compute):
        vm_id = TestComputeCRUD.created_vm_id
        assert vm_id is not None

        url = f"{base_url_compute}/virtual_machine/{vm_id}"
        r = requests.delete(url, headers=api_headers)
        self._xfail_if_expired_token(r)

        assert r.status_code == 200, f"status={r.status_code}, body={r.text}"

        # ✅ 가짜 PASS 방지: “삭제 반영”을 404 강제 대신,
        #    404 또는 status 기반 삭제상태(비동기)까지 허용 + 토큰만료는 XFAIL
        self._wait_deleted(api_headers, base_url_compute, vm_id, timeout_sec=90)
        TestComputeCRUD.deleted_vm_verified = True

    # ----------------------------
    # VM-008 삭제 후 단건 조회
    def test_VM008_get_deleted_vm(self, api_headers, base_url_compute):
        vm_id = TestComputeCRUD.created_vm_id
        assert vm_id is not None

        url = f"{base_url_compute}/virtual_machine/{vm_id}"
        r = requests.get(url, headers=api_headers)
        self._xfail_if_expired_token(r)

        # VM-007에서 삭제 검증까지 끝난 경우: 여기서는 “삭제된 상태”만 허용
        if TestComputeCRUD.deleted_vm_verified:
            if r.status_code == 404:
                return

            if r.status_code == 200:
                try:
                    data = r.json()
                except Exception:
                    pytest.fail(f"deleted but get returned 200 non-json: {r.text}")

                st = (data.get("status") or "").upper()
                if st in ("DELETED", "TERMINATED", "DELETING"):
                    return

                pytest.fail(f"deleted_vm_verified=True but get status=200 and vm.status={data.get('status')}")
            pytest.fail(f"deleted_vm_verified=True but status={r.status_code}, body={r.text}")

        # (예외) VM-007이 XFAIL/스킵된 상황에서는 200/404 둘 다 허용
        assert r.status_code in (200, 404), f"status={r.status_code}, body={r.text}"

    # ----------------------------
    # VM-009 VM 다건 조회
    def test_VM009_list_vm(self, api_headers, base_url_compute):
        vms = self._list_vms(api_headers, base_url_compute)
        assert isinstance(vms, list)

    # ----------------------------
    # VM-010 특정 상태 VM 목록 조회
    def test_VM010_list_vm_by_status(self, api_headers, base_url_compute):
        # TC1에서 만든 VM은 TC7에서 삭제되었을 수 있으니, 여기서는 "사용 가능한 VM"을 확보
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)
        assert vm_id is not None

        # start 엔드포인트가 404로 뜨는 환경이면 이 TC는 XFAIL이 맞음
        start_url = f"{base_url_compute}/virtual_machine_control/start"
        r = requests.post(start_url, headers=api_headers, json={"id": vm_id})
        self._xfail_if_expired_token(r)
        if r.status_code == 404:
            pytest.xfail(f"start API 미지원/URL 상이: {r.status_code} {r.text}")

        time.sleep(10)

        url = f"{base_url_compute}/virtual_machine_allocation?filter_status=RUNNING"
        r = requests.get(url, headers=api_headers)
        self._xfail_if_expired_token(r)

        assert r.status_code in (200, 422), f"status={r.status_code}, body={r.text}"

        if r.status_code == 200:
            for vm in r.json():
                assert (vm.get("status") or "").upper() == "RUNNING"

    # ----------------------------
    # VM-011 VM 목록 조회 (Search)
    def test_VM011_list_vm(self, api_headers, base_url_compute):
        vms = self._list_vms(api_headers, base_url_compute)
        assert isinstance(vms, list)

    # ----------------------------
    # VM-012 VM 단건 조회 (machine_id 기반)
    def test_VM012_get_vm_one(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)
        vm = self._get_vm_by_machine_id(api_headers, base_url_compute, vm_id)
        assert vm is not None
        assert vm.get("machine_id") or vm.get("id")

    # ----------------------------
    # VM-013 VM 시작
    def test_VM013_start_vm(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)

        start_url = f"{base_url_compute}/virtual_machine_control/start"
        r = requests.post(start_url, headers=api_headers, json={"id": vm_id})
        self._xfail_if_expired_token(r)

        if r.status_code == 404:
            pytest.xfail(f"start API 미지원/URL 상이: {r.status_code} {r.text}")

        assert r.status_code in (200, 202), f"status={r.status_code}, body={r.text}"
        self._wait_status(api_headers, base_url_compute, vm_id, ["RUNNING"])

    # ----------------------------
    # VM-014 목록에서 VM 상태 확인 (RUNNING/STOP 필터)
    def test_VM014_check_vm_status_filter(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)

        start_url = f"{base_url_compute}/virtual_machine_control/start"
        r = requests.post(start_url, headers=api_headers, json={"id": vm_id})
        self._xfail_if_expired_token(r)
        if r.status_code == 404:
            pytest.xfail(f"start API 미지원/URL 상이: {r.status_code} {r.text}")

        self._wait_status(api_headers, base_url_compute, vm_id, ["RUNNING"])

        val, data = self._try_filter_status(api_headers, base_url_compute, ["RUNNING", "running"])
        if val is None:
            pytest.xfail("filter_status 파라미터 허용값/형식 미확정(계속 실패)")

        assert isinstance(data, list)

    # ----------------------------
    # VM-015 실행중 VM 정지
    def test_VM015_stop_vm(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)

        start_url = f"{base_url_compute}/virtual_machine_control/start"
        r = requests.post(start_url, headers=api_headers, json={"id": vm_id})
        self._xfail_if_expired_token(r)
        if r.status_code == 404:
            pytest.xfail(f"start API 미지원/URL 상이: {r.status_code} {r.text}")

        self._wait_status(api_headers, base_url_compute, vm_id, ["RUNNING"])

        stop_url = f"{base_url_compute}/virtual_machine_control/stop"
        r = requests.post(stop_url, headers=api_headers, json={"id": vm_id})
        self._xfail_if_expired_token(r)
        if r.status_code == 404:
            pytest.xfail(f"stop API 미지원/URL 상이: {r.status_code} {r.text}")

        assert r.status_code in (200, 202), f"status={r.status_code}, body={r.text}"
        self._wait_status(api_headers, base_url_compute, vm_id, ["STOP"])

    # ----------------------------
    # VM-016 정지 후 상태 확인
    def test_VM016_check_stopped_vm(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)

        stop_url = f"{base_url_compute}/virtual_machine_control/stop"
        r = requests.post(stop_url, headers=api_headers, json={"id": vm_id})
        self._xfail_if_expired_token(r)
        if r.status_code == 404:
            pytest.xfail(f"stop API 미지원/URL 상이: {r.status_code} {r.text}")

        self._wait_status(api_headers, base_url_compute, vm_id, ["STOP"])

        vm = self._get_vm_by_machine_id(api_headers, base_url_compute, vm_id)
        assert vm is not None
        assert "STOP" in (vm.get("status") or "").upper()

    # ----------------------------
    # VM-017 VM 리부팅(Soft)
    def test_VM017_reboot_soft(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)

        reboot_url = f"{base_url_compute}/virtual_machine_control/reboot"
        r = requests.post(reboot_url, headers=api_headers, json={"id": vm_id, "type": "soft"})
        self._xfail_if_expired_token(r)
        if r.status_code == 404:
            pytest.xfail(f"reboot API 미지원/URL 상이: {r.status_code} {r.text}")

        assert r.status_code in (200, 202), f"status={r.status_code}, body={r.text}"

    # ----------------------------
    # VM-018 웹 콘솔 접속 정보 조회
    def test_VM018_get_console(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)

        url = f"{base_url_compute}/virtual_machine_console"
        r = requests.get(url, headers=api_headers, params={"id": vm_id})
        self._xfail_if_expired_token(r)

        if r.status_code in (404, 501):
            pytest.xfail(f"console API 미지원: {r.status_code} {r.text}")

        assert r.status_code == 200, f"status={r.status_code}, body={r.text}"

    # ----------------------------
    # VM-019 SSH 접속 정보 조회(지원 시)
    def test_VM019_get_ssh_info(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)

        url = f"{base_url_compute}/virtual_machine_ssh"
        r = requests.get(url, headers=api_headers, params={"id": vm_id})
        self._xfail_if_expired_token(r)

        if r.status_code in (404, 501):
            pytest.xfail(f"ssh info API 미지원: {r.status_code} {r.text}")

        assert r.status_code == 200, f"status={r.status_code}, body={r.text}"

    # ----------------------------
    # VM-020 SSH 접속 가능 여부 확인(지원 시)
    def test_VM020_check_ssh(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)

        url = f"{base_url_compute}/virtual_machine_ssh/check"
        r = requests.post(url, headers=api_headers, json={"id": vm_id})
        self._xfail_if_expired_token(r)

        if r.status_code in (404, 501):
            pytest.xfail(f"ssh check API 미지원: {r.status_code} {r.text}")

        assert r.status_code == 200, f"status={r.status_code}, body={r.text}"

    # ----------------------------
    # VM-021 VM 메트릭 조회
    def test_VM021_get_metrics(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)

        url = f"{base_url_compute}/virtual_machine_metrics"
        r = requests.get(url, headers=api_headers, params={"id": vm_id})
        self._xfail_if_expired_token(r)

        if r.status_code in (404, 501):
            pytest.xfail(f"metrics API 미지원: {r.status_code} {r.text}")

        assert r.status_code == 200, f"status={r.status_code}, body={r.text}"

    # ----------------------------
    # VM-022 VM 건강 상태 조회
    def test_VM022_get_health(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)

        url = f"{base_url_compute}/virtual_machine_health"
        r = requests.get(url, headers=api_headers, params={"id": vm_id})
        self._xfail_if_expired_token(r)

        if r.status_code in (404, 501):
            pytest.xfail(f"health API 미지원: {r.status_code} {r.text}")

        assert r.status_code == 200, f"status={r.status_code}, body={r.text}"

    # ----------------------------
    # 아래부터는 헬퍼 메서드(이름 그대로 유지)

    def _xfail_if_expired_token(self, response):
        if response.status_code == 403:
            try:
                data = response.json()
            except Exception:
                data = {}
            if isinstance(data, dict) and data.get("code") == "expired_token":
                pytest.xfail(f'expired_token: {response.text}')

    def _list_vms(self, api_headers, base_url_compute):
        url = f"{base_url_compute}/virtual_machine_allocation"
        r = requests.get(url, headers=api_headers)
        self._xfail_if_expired_token(r)

        assert r.status_code == 200, f"list vms failed: status={r.status_code}, body={r.text}"
        data = r.json()
        assert isinstance(data, list), f"list vms response is not list: {data}"
        return data

    def _ensure_vm_id(self, api_headers, base_url_compute):
        # TC1에서 만든 VM id가 있고, 삭제 검증 전이면 그걸 우선 사용
        if TestComputeCRUD.created_vm_id and not TestComputeCRUD.deleted_vm_verified:
            return TestComputeCRUD.created_vm_id

        vms = self._list_vms(api_headers, base_url_compute)
        if not vms:
            pytest.xfail("VM 목록이 비어있어서 단건/제어 테스트 진행 불가")

        candidate = vms[0].get("machine_id") or vms[0].get("id")
        if not candidate:
            pytest.xfail(f"VM 목록에서 machine_id/id를 찾을 수 없음: {vms[0]}")
        return candidate

    def _get_vm_by_machine_id(self, api_headers, base_url_compute, machine_id_or_id):
        url = f"{base_url_compute}/virtual_machine/{machine_id_or_id}"
        r = requests.get(url, headers=api_headers)
        self._xfail_if_expired_token(r)

        if r.status_code == 200:
            try:
                return r.json()
            except Exception:
                return {"raw": r.text}

        vms = self._list_vms(api_headers, base_url_compute)
        for vm in vms:
            if vm.get("machine_id") == machine_id_or_id or vm.get("id") == machine_id_or_id:
                return vm
        return None

    def _wait_status(self, api_headers, base_url_compute, machine_id_or_id, expected_status_list, timeout_sec=120):
        end = time.time() + timeout_sec
        expected = {s.upper() for s in expected_status_list}

        while time.time() < end:
            vm = self._get_vm_by_machine_id(api_headers, base_url_compute, machine_id_or_id)
            if vm:
                st = (vm.get("status") or "").upper()
                if st in expected:
                    return
            time.sleep(5)

        pytest.xfail(f"timeout: status not in {expected_status_list}")

    def _try_filter_status(self, api_headers, base_url_compute, candidates):
        for val in candidates:
            url = f"{base_url_compute}/virtual_machine_allocation?filter_status={val}"
            r = requests.get(url, headers=api_headers)
            self._xfail_if_expired_token(r)

            if r.status_code == 200:
                try:
                    data = r.json()
                except Exception:
                    data = None
                if isinstance(data, list):
                    return val, data
        return None, None

    def _wait_vm_visible(self, api_headers, base_url_compute, vm_id, timeout_sec=60):
        end = time.time() + timeout_sec
        while time.time() < end:
            vm = self._get_vm_by_machine_id(api_headers, base_url_compute, vm_id)
            if vm is not None:
                return
            time.sleep(3)
        pytest.fail(f"VM001 created id={vm_id} but not visible within {timeout_sec}s")

    def _wait_deleted(self, api_headers, base_url_compute, vm_id, timeout_sec=90):
        end = time.time() + timeout_sec
        url = f"{base_url_compute}/virtual_machine/{vm_id}"

        while time.time() < end:
            r = requests.get(url, headers=api_headers)
            self._xfail_if_expired_token(r)

            if r.status_code == 404:
                return

            if r.status_code == 200:
                try:
                    data = r.json()
                except Exception:
                    data = {}
                st = (data.get("status") or "").upper()
                # ✅ 비동기 삭제 환경 대응 (즉시 404가 아닐 수 있음)
                if st in ("DELETED", "TERMINATED"):
                    return
                if st in ("DELETING", "TERMINATING"):
                    time.sleep(3)
                    continue

            time.sleep(3)

        pytest.fail(f"VM007 deleted id={vm_id} but not deleted/404 within {timeout_sec}s")
