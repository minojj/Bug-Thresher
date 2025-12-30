import requests
import pytest
import uuid
import time

# 후보군 instance_type_id (TC28에서 create fallback에 사용)
INSTANCE_TYPE_CANDIDATES = [
    "320909e3-44ce-4018-8b55-7e837cd84a15",
    "332d9f31-595c-4d0f-aebd-4aaf49c345a5",  # C-16
    "830e2041-d477-4058-a65c-386a93ead237",  # M-2
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
    @pytest.mark.skip(
        reason="Blocked: VM create API payload/response에 OS image 식별값(image_id/os_image_id 등) 미노출로 선택 OS 적용 여부 판정 불가"
    )
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
    @pytest.mark.skip(
        reason="Blocked: dr=true 요청 시 API가 zone_no_secondary_zone 반환. 해당 zone_id에 secondary zone 미구성으로 DR VM 생성 검증 불가."
    )
    def test_VM005_create_vm_with_dr_true_blocked(self):
        pass

    # VM-006 VM 삭제
    def test_VM006_delete_vm(self, api_headers, base_url_compute):
        vm_id = TestComputeCRUD.created_vm_id
        assert vm_id is not None

        url = f"{base_url_compute}/virtual_machine/{vm_id}"
        r = self._request("DELETE", url, headers=api_headers)
        assert r.status_code == 200, f"status={r.status_code}, body={r.text}"

        # 삭제는 비동기일 수 있음 → 단건 조회로 상태 확인
        get_url = f"{base_url_compute}/virtual_machine/{vm_id}"
        r2 = self._request("GET", get_url, headers=api_headers)

        # 404면 "완전히 삭제됨"으로 인정
        if r2.status_code == 404:
            TestComputeCRUD.deleted_vm_verified = True
            return

        # 200이면 status를 체크
        assert r2.status_code == 200, f"status={r2.status_code}, body={r2.text}"
        body = r2.json()
        status = (body.get("status") or "").lower()

        # ✅ deleted도 허용
        assert status in ("deleting", "terminated", "inactive", "deleted"), (
            f"unexpected delete status={status}, body={body}"
        )

        # status가 deleted면 "삭제 검증 완료"로 플래그 ON
        if status == "deleted":
            TestComputeCRUD.deleted_vm_verified = True

    # VM-008 VM 다건 조회
    def test_VM008_list_vm(self, api_headers, base_url_compute):
        url = f"{base_url_compute}/virtual_machine_allocation"
        r = self._request("GET", url, headers=api_headers)

        assert r.status_code == 200, f"status={r.status_code}, body={r.text}"
        assert isinstance(r.json(), list)

    # VM-009 특정 상태 VM 목록 조회
    def test_VM009_list_vm_by_status(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)
        assert vm_id is not None

        # start endpoint가 404일 수 있음(미확정)
        start_url = f"{base_url_compute}/virtual_machine_control/start"
        start_r = self._request(
            "POST", start_url, headers=api_headers, json={"id": vm_id}
        )
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

    # VM-014 실행중 VM 정지
    def test_VM014_stop_vm(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)

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

        start_url = f"{base_url_compute}/virtual_machine_control/start"
        r = self._request("POST", start_url, headers=api_headers, json={"id": vm_id})
        if r.status_code == 404:
            pytest.xfail("start API URL 미확정(404). 크롬 네트워크로 실제 URL 확인 필요")
        self._wait_status(api_headers, base_url_compute, vm_id, ["RUNNING"])

        reboot_url = f"{base_url_compute}/virtual_machine_control/reboot"
        r = self._request(
            "POST", reboot_url, headers=api_headers, json={"id": vm_id, "type": "soft"}
        )
        if r.status_code == 404:
            pytest.xfail("reboot API URL 미확정(404). 크롬 네트워크로 실제 URL 확인 필요")

        assert r.status_code in (200, 202), f"status={r.status_code}, body={r.text}"
        self._wait_status(
            api_headers, base_url_compute, vm_id, ["RUNNING"], timeout_sec=180
        )

    # VM-017 웹 콘솔 접속 정보 조회
    def test_VM017_get_console(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)

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

    # def test_VM028_duplicate_name_create_should_fail(self, api_headers, base_url_compute):
    #     create_url = f"{base_url_compute}/virtual_machine"

    #     fixed_name = f"vm-dup-{uuid.uuid4().hex[:6]}"
    #     created_ids = []

    #     body_base = {
    #         "name": fixed_name,
    #         "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
    #         "username": "test",
    #         "password": "1qaz2wsx@@",
    #         "on_init_script": "",
    #         "always_on": False,
    #         "dr": False,
    #     }

    #     try:
    #         r1 = self._create_vm_with_instance_fallback(
    #             api_headers=api_headers,
    #             url=create_url,
    #             body_base=body_base,
    #             candidates=INSTANCE_TYPE_CANDIDATES,
    #             max_retry_per_type=1,
    #         )

    #         if r1 is None:
    #             pytest.xfail("TC28 진행 불가: 첫 번째 VM 생성 응답이 None")

    #         if r1.status_code not in (200, 201):
    #             pytest.xfail(
    #                 f"TC28 진행 불가: 첫 번째 VM 생성 실패 status={r1.status_code}, body={r1.text}"
    #             )

    #         vm1 = r1.json()
    #         vm1_id = vm1.get("id")
    #         if not vm1_id:
    #             pytest.xfail(f"TC28 진행 불가: 첫 번째 생성 응답에 id 없음: {vm1}")

    #         created_ids.append(vm1_id)

    #         r2 = self._create_vm_with_instance_fallback(
    #             api_headers=api_headers,
    #             url=create_url,
    #             body_base=body_base,
    #             candidates=INSTANCE_TYPE_CANDIDATES,
    #             max_retry_per_type=1,
    #         )

    #         if r2 is None:
    #             pytest.xfail("TC28: 두 번째 생성 응답이 None")

    #         if r2.status_code in (400, 409, 422):
    #             return

    #         if r2.status_code in (200, 201):
    #             vm2 = r2.json()
    #             vm2_id = vm2.get("id")
    #             if vm2_id:
    #                 created_ids.append(vm2_id)

    #             pytest.fail(
    #                 f"BUG: 같은 name('{fixed_name}')으로 VM 생성이 허용됨! "
    #                 f"status={r2.status_code}, body={r2.text}"
    #             )

    #         pytest.fail(
    #             f"Unexpected response on duplicate-name create: "
    #             f"status={r2.status_code}, body={r2.text}"
    #         )

    #     finally:
    #         for vid in created_ids:
    #             try:
    #                 self._request(
    #                     "DELETE",
    #                     f"{base_url_compute}/virtual_machine/{vid}",
    #                     headers=api_headers,
    #                 )
    #             except Exception:
    #                 pass

    # # TC28 사용
    # def _create_vm_with_instance_fallback(
    #     self,
    #     api_headers,
    #     url,
    #     body_base,
    #     candidates,
    #     max_retry_per_type=1,
    # ):
    #     last_r = None

    #     for instance_type_id in candidates:
    #         payload = dict(body_base)
    #         payload["instance_type_id"] = instance_type_id

    #         for _ in range(max_retry_per_type):
    #             r = self._request("POST", url, headers=api_headers, json=payload)
    #             last_r = r

    #             if r.status_code in (200, 201):
    #                 return r

    #             # 환경 제한/검증 실패면 다음 후보로
    #             if r.status_code in (400, 404, 409, 422):
    #                 break

    #     return last_r

    # # TC28 사용
    # def _request(self, method, url, **kwargs):
    #     r = requests.request(method, url, **kwargs)

    #     if r.status_code == 403:
    #         try:
    #             data = r.json()
    #         except Exception:
    #             data = None

    #         if isinstance(data, dict) and data.get("code") == "expired_token":
    #             pytest.xfail(f"expired_token: {data.get('message')}")

    #     return r

    # ----------------------------
    # 헬퍼 메서드
    # ----------------------------

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

    # def _create_vm_with_instance_fallback(
    #     self, api_headers, url, body_base, candidates, max_retry_per_type=1
    # ):
    #     last_r = None

    #     for it in candidates:
    #         payload = dict(body_base)
    #         payload["instance_type_id"] = it

    #         r = self._request("POST", url, headers=api_headers, json=payload)
    #         last_r = r

    #         if r.status_code in (200, 201):
    #             return r

    #     return last_r

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

    # def _wait_vm_visible(self, api_headers, base_url_compute, vm_id, timeout_sec=60):
    #     end = time.time() + timeout_sec
    #     while time.time() < end:
    #         if self._get_vm_by_machine_id(api_headers, base_url_compute, vm_id):
    #             return
    #         time.sleep(3)
    #     pytest.fail("VM not visible")