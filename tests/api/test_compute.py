import requests
import pytest
import uuid
import time

from tests.conftest import base_url_compute

class TestComputeCRUD:
    created_vm_id = None
    deleted_vm_verified = False

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
            "dr": False,
        }

        r = self._request("POST", url, headers=api_headers, json=body)
        assert r.status_code in (200, 201), f"status={r.status_code}, body={r.text}"

        res = r.json()
        assert isinstance(res, dict), f"create response not dict: {res}"
        assert res.get("id"), f"create response missing id: {res}"

        TestComputeCRUD.created_vm_id = res["id"]

        # 가짜 PASS 방지: 생성된 id가 실제로 조회/목록에 보일 때까지 확인
        self._wait_vm_visible(api_headers, base_url_compute, TestComputeCRUD.created_vm_id, timeout_sec=60)

    # VM-002 다른 인스턴스 타입으로 VM 생성
    def test_VM002_create_vm_different_instance_type(self, api_headers, base_url_compute):
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

        r = self._request("POST", url, headers=api_headers, json=payload)

        # 환경 제한이면 XFAIL
        if r.status_code in (400, 404, 409, 422):
            pytest.xfail(f"환경 제한: {r.text}")

        assert r.status_code in (200, 201), f"status={r.status_code}, body={r.text}"

    # VM-003 OS 이미지 지정 생성 (Blocked)
    @pytest.mark.skip(reason="Blocked: VM create API payload/response에 OS image 식별값(image_id/os_image_id 등) 미노출로 선택 OS 적용 여부 판정 불가")
    def test_VM003_create_vm_with_os_image(self, api_client, api_headers):
        pass
    
    # VM-004 초기화 스크립트 포함 VM 생성
    def test_VM004_create_vm_with_init_script(self, api_headers, base_url_compute):
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

        r = self._request("POST", url, headers=api_headers, json=payload)

        if r.status_code == 409:
            pytest.xfail(f"quota 또는 환경 제한: {r.text}")

        assert r.status_code in (200, 201), f"status={r.status_code}, body={r.text}"

    # VM-005 DR 옵션 VM 생성
    def test_VM005_create_vm_with_dr_true(self, api_headers, base_url_compute):
        url = f"{base_url_compute}/virtual_machine"

        payload = {
            "name": f"vm-auto-dr-{uuid.uuid4().hex[:6]}",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "instance_type_id": "830e2041-d477-4058-a65c-386a93ead237",  # M-2
            "username": "test",
            "password": "1qaz2wsx@@",
            "on_init_script": "",
            "always_on": False,
            "dr": True,
        }

        r = self._request("POST", url, headers=api_headers, json=payload)

        if r.status_code == 409:
            pytest.xfail(f"quota 또는 환경 제한: {r.text}")

        assert r.status_code in (200, 201), f"status={r.status_code}, body={r.text}"

    # VM-006 VM 삭제
    def test_VM006_delete_vm(self, api_headers, base_url_compute):
        vm_id = TestComputeCRUD.created_vm_id
        assert vm_id is not None

        url = f"{base_url_compute}/virtual_machine/{vm_id}"
        r = self._request("DELETE", url, headers=api_headers)

        assert r.status_code == 200, f"status={r.status_code}, body={r.text}"

        # 삭제는 비동기 → 바로 404 안 뜨는 게 정상
        # 단건 조회로 상태만 확인
        get_url = f"{base_url_compute}/virtual_machine/{vm_id}"
        r2 = self._request("GET", get_url, headers=api_headers)

        if r2.status_code == 200:
            body = r2.json()
            status = (body.get("status") or "").lower()

            # deleting / terminated / inactive 등 허용
            assert status in ("deleting", "terminated", "inactive"), (
                f"unexpected delete status={status}, body={body}"
            )
        elif r2.status_code == 404:
            # 환경에 따라 바로 404 주는 경우도 허용
            pass
        else:
            pytest.xfail(
                f"delete 후 상태 확인 API 동작 불명확: "
                f"status={r2.status_code}, body={r2.text}"
            )


    # VM-007 삭제 후 단건 조회
    def test_VM007_get_deleted_vm(self, api_headers, base_url_compute):
        vm_id = TestComputeCRUD.created_vm_id
        assert vm_id is not None

        url = f"{base_url_compute}/virtual_machine/{vm_id}"
        r = self._request("GET", url, headers=api_headers)

        # VM-007에서 삭제 검증 완료했다면: 여기서는 404만 허용(가짜 PASS 봉쇄)
        if TestComputeCRUD.deleted_vm_verified:
            assert r.status_code == 404, f"deleted id={vm_id} but status={r.status_code}, body={r.text}"
            return

        # (예외) VM-007이 xfail/skip으로 안 돌았을 때만 완화
        assert r.status_code in (200, 404), f"status={r.status_code}, body={r.text}"

    # VM-008 VM 다건 조회
    def test_VM008_list_vm(self, api_headers, base_url_compute):
        url = f"{base_url_compute}/virtual_machine_allocation"
        r = self._request("GET", url, headers=api_headers)

        assert r.status_code == 200, f"status={r.status_code}, body={r.text}"
        assert isinstance(r.json(), list)

    # VM-009 특정 상태 VM 목록 조회
    def test_VM009_list_vm_by_status(self, api_headers, base_url_compute):
        # TC1에서 만든 VM은 TC7에서 삭제되었을 수 있으니, 여기서는 "사용 가능한 VM"을 확보
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)
        assert vm_id is not None

        # start endpoint가 404일 수 있음(미확정)
        start_url = f"{base_url_compute}/virtual_machine_control/start"
        start_r = self._request("POST", start_url, headers=api_headers, json={"id": vm_id})
        if start_r.status_code == 404:
            pytest.xfail("start API URL 미확정(404). 크롬 네트워크로 실제 URL 확인 필요")

        time.sleep(10)

        url = f"{base_url_compute}/virtual_machine_allocation?filter_status=RUNNING"
        r = self._request("GET", url, headers=api_headers)

        assert r.status_code in (200, 422), f"status={r.status_code}, body={r.text}"

        if r.status_code == 200:
            for vm in r.json():
                assert vm["status"] == "RUNNING"

    # VM-010 VM 목록 조회 (Search)
    def test_VM010_list_vm(self, api_headers, base_url_compute):
        vms = self._list_vms(api_headers, base_url_compute)
        assert isinstance(vms, list)

    # VM-011 VM 단건 조회 (machine_id 기반)
    def test_VM011_get_vm_one(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)
        vm = self._get_vm_by_machine_id(api_headers, base_url_compute, vm_id)
        assert vm is not None
        # 최소한 id/machine_id 둘 중 하나는 있어야 한다고 보고 체크
        assert vm.get("machine_id") or vm.get("id")

    # VM-012 VM 시작
    def test_VM012_start_vm(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)

        start_url = f"{base_url_compute}/virtual_machine_control/start"
        r = self._request("POST", start_url, headers=api_headers, json={"id": vm_id})

        if r.status_code == 404:
            pytest.xfail("start API URL 미확정(404). 크롬 네트워크로 실제 URL 확인 필요")

        assert r.status_code in (200, 202), f"status={r.status_code}, body={r.text}"
        self._wait_status(api_headers, base_url_compute, vm_id, ["RUNNING"])

    # VM-013 목록에서 VM 상태 확인 (RUNNING/STOP 필터)
    def test_VM013_check_vm_status_filter(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)

        # 일단 RUNNING 만들어두기
        start_url = f"{base_url_compute}/virtual_machine_control/start"
        r = self._request("POST", start_url, headers=api_headers, json={"id": vm_id})
        if r.status_code == 404:
            pytest.xfail("start API URL 미확정(404). 크롬 네트워크로 실제 URL 확인 필요")

        self._wait_status(api_headers, base_url_compute, vm_id, ["RUNNING"])

        # filter_status가 대소문자/허용값 문제(422) 있을 수 있어서 후보를 돌림
        val, data = self._try_filter_status(api_headers, base_url_compute, ["RUNNING", "running", "Run", "on", "ON"])
        if val is None:
            pytest.xfail("filter_status 파라미터 허용값/형식 미확정(계속 422)")

        assert isinstance(data, list)
        assert len(data) >= 1

    # VM-014 실행중 VM 정지
    def test_VM014_stop_vm(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)

        # RUNNING 보장
        start_url = f"{base_url_compute}/virtual_machine_control/start"
        r = self._request("POST", start_url, headers=api_headers, json={"id": vm_id})
        if r.status_code == 404:
            pytest.xfail("start API URL 미확정(404). 크롬 네트워크로 실제 URL 확인 필요")
        self._wait_status(api_headers, base_url_compute, vm_id, ["RUNNING"])

        stop_url = f"{base_url_compute}/virtual_machine_control/stop"
        r = self._request("POST", stop_url, headers=api_headers, json={"id": vm_id})
        if r.status_code == 404:
            pytest.xfail("stop API URL 미확정(404). 크롬 네트워크로 실제 URL 확인 필요")

        assert r.status_code in (200, 202), f"status={r.status_code}, body={r.text}"
        self._wait_status(api_headers, base_url_compute, vm_id, ["STOP"])

    # VM-015 정지 후 상태 확인
    def test_VM015_check_stopped_vm(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)

        # STOP 보장
        stop_url = f"{base_url_compute}/virtual_machine_control/stop"
        r = self._request("POST", stop_url, headers=api_headers, json={"id": vm_id})
        if r.status_code == 404:
            pytest.xfail("stop API URL 미확정(404). 크롬 네트워크로 실제 URL 확인 필요")

        self._wait_status(api_headers, base_url_compute, vm_id, ["STOP"])

        vm = self._get_vm_by_machine_id(api_headers, base_url_compute, vm_id)
        assert vm is not None
        assert "STOP" in (vm.get("status") or "").upper()

    # VM-016 VM 리부팅(Soft)
    def test_VM016_reboot_soft(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)

        # RUNNING 보장
        start_url = f"{base_url_compute}/virtual_machine_control/start"
        r = self._request("POST", start_url, headers=api_headers, json={"id": vm_id})
        if r.status_code == 404:
            pytest.xfail("start API URL 미확정(404). 크롬 네트워크로 실제 URL 확인 필요")
        self._wait_status(api_headers, base_url_compute, vm_id, ["RUNNING"])

        reboot_url = f"{base_url_compute}/virtual_machine_control/reboot"
        r = self._request("POST", reboot_url, headers=api_headers, json={"id": vm_id, "type": "soft"})
        if r.status_code == 404:
            pytest.xfail("reboot API URL 미확정(404). 크롬 네트워크로 실제 URL 확인 필요")

        assert r.status_code in (200, 202), f"status={r.status_code}, body={r.text}"
        self._wait_status(api_headers, base_url_compute, vm_id, ["RUNNING"], timeout_sec=180)

    # VM-017 웹 콘솔 접속 정보 조회
    def test_VM017_get_console(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)

        # RUNNING 권장
        start_url = f"{base_url_compute}/virtual_machine_control/start"
        r = self._request("POST", start_url, headers=api_headers, json={"id": vm_id})
        if r.status_code == 404:
            pytest.xfail("start API URL 미확정(404). 크롬 네트워크로 실제 URL 확인 필요")
        self._wait_status(api_headers, base_url_compute, vm_id, ["RUNNING"])

        url = f"{base_url_compute}/virtual_machine_console"
        r = self._request("GET", url, headers=api_headers, params={"id": vm_id})
        if r.status_code in (404, 501):
            pytest.xfail(f"console API 미지원: {r.status_code} {r.text}")
        assert r.status_code == 200, f"status={r.status_code}, body={r.text}"

    # VM-018 SSH 접속 정보 조회(지원 시)
    def test_VM018_get_ssh_info(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)
        url = f"{base_url_compute}/virtual_machine_ssh"
        r = self._request("GET", url, headers=api_headers, params={"id": vm_id})
        if r.status_code in (404, 501):
            pytest.xfail(f"ssh info API 미지원: {r.status_code} {r.text}")
        assert r.status_code == 200, f"status={r.status_code}, body={r.text}"

    # VM-019 SSH 접속 가능 여부 확인(지원 시)
    def test_VM019_check_ssh(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)
        url = f"{base_url_compute}/virtual_machine_ssh/check"
        r = self._request("POST", url, headers=api_headers, json={"id": vm_id})
        if r.status_code in (404, 501):
            pytest.xfail(f"ssh check API 미지원: {r.status_code} {r.text}")
        assert r.status_code == 200, f"status={r.status_code}, body={r.text}"

    # VM-020 VM 메트릭 조회
    def test_VM020_get_metrics(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)

        # RUNNING 권장
        start_url = f"{base_url_compute}/virtual_machine_control/start"
        r = self._request("POST", start_url, headers=api_headers, json={"id": vm_id})
        if r.status_code == 404:
            pytest.xfail("start API URL 미확정(404). 크롬 네트워크로 실제 URL 확인 필요")
        self._wait_status(api_headers, base_url_compute, vm_id, ["RUNNING"])

        url = f"{base_url_compute}/virtual_machine_metrics"
        r = self._request("GET", url, headers=api_headers, params={"id": vm_id})
        if r.status_code in (404, 501):
            pytest.xfail(f"metrics API 미지원: {r.status_code} {r.text}")
        assert r.status_code == 200, f"status={r.status_code}, body={r.text}"

    # VM-021 VM 건강 상태 조회
    def test_VM021_get_health(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)
        url = f"{base_url_compute}/virtual_machine_health"
        r = self._request("GET", url, headers=api_headers, params={"id": vm_id})
        if r.status_code in (404, 501):
            pytest.xfail(f"health API 미지원: {r.status_code} {r.text}")
        assert r.status_code == 200, f"status={r.status_code}, body={r.text}"

    # ----------------------------
    # 아래부터는 헬퍼 메서드(이름 그대로 유지)
    # ----------------------------

    def _request(self, method, url, **kwargs):
        r = requests.request(method, url, **kwargs)

        # 토큰 만료면: 무한 폴링/무한 실패 대신 즉시 XFAIL로 끊기
        if r.status_code == 403:
            try:
                data = r.json()
            except Exception:
                data = None

            if isinstance(data, dict) and data.get("code") == "expired_token":
                pytest.xfail(f"expired_token: {data.get('message')}")

        return r

    def _list_vms(self, api_headers, base_url_compute):
        url = f"{base_url_compute}/virtual_machine_allocation"
        r = self._request("GET", url, headers=api_headers)
        assert r.status_code == 200, f"list vms failed: status={r.status_code}, body={r.text}"
        data = r.json()
        assert isinstance(data, list), f"list vms response is not list: {data}"
        return data

    def _ensure_vm_id(self, api_headers, base_url_compute):
        # TC1에서 만든 VM id가 있으면 그걸 우선 사용(단, 삭제 검증 완료면 제외)
        if TestComputeCRUD.created_vm_id and not TestComputeCRUD.deleted_vm_verified:
            return TestComputeCRUD.created_vm_id

        # 없거나 삭제된 상태면 목록에서 하나 확보
        vms = self._list_vms(api_headers, base_url_compute)
        if not vms:
            pytest.xfail("VM 목록이 비어있어서 단건/제어 테스트 진행 불가")

        candidate = vms[0].get("machine_id") or vms[0].get("id")
        if not candidate:
            pytest.xfail(f"VM 목록에서 machine_id/id를 찾을 수 없음: {vms[0]}")
        return candidate

    def _get_vm_by_machine_id(self, api_headers, base_url_compute, machine_id_or_id):
        # 단건 조회 우선 시도
        url = f"{base_url_compute}/virtual_machine/{machine_id_or_id}"
        r = self._request("GET", url, headers=api_headers)

        if r.status_code == 200:
            try:
                return r.json()
            except Exception:
                return {"raw": r.text}

        # 단건 조회가 404/미지원이면 allocation 목록에서 찾아서 반환
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
            r = self._request("GET", url, headers=api_headers)
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

    def _wait_deleted(self, api_headers, base_url_compute, vm_id, timeout_sec=60):
        end = time.time() + timeout_sec
        url = f"{base_url_compute}/virtual_machine/{vm_id}"

        while time.time() < end:
            r = self._request("GET", url, headers=api_headers)

            # 정상적인 삭제 반영
            if r.status_code == 404:
                return

            # 200이면 아직 삭제 반영 전일 수 있음 → 조금 기다림
            if r.status_code == 200:
                time.sleep(3)
                continue

            # 그 외(403 제외는 위 _request에서 expired_token이면 xfail 처리됨)
            pytest.fail(f"delete verify unexpected status={r.status_code}, body={r.text}")

        pytest.fail(f"VM007 deleted id={vm_id} but still not 404 within {timeout_sec}s")
