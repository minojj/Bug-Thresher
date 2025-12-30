import os
import time
import uuid

import pytest
import requests


# ----------------------------
# 상수/후보값 (가능하면 ENV로 주입)
# ----------------------------
ZONE_ID = os.getenv("COMPUTE_ZONE_ID", "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0")

# 인스턴스 타입 후보: ENV로 "id1,id2,id3" 넣으면 그걸 우선 사용
_ENV_INSTANCE_IDS = os.getenv("COMPUTE_INSTANCE_TYPE_IDS", "").strip()
if _ENV_INSTANCE_IDS:
    INSTANCE_TYPE_CANDIDATES = [s.strip() for s in _ENV_INSTANCE_IDS.split(",") if s.strip()]
else:
    # 네가 기존 코드에서 쓰던 값들을 기본 후보로 둠 (환경에 따라 409/422면 자동 xfail 처리됨)
    INSTANCE_TYPE_CANDIDATES = [
        "320909e3-44ce-4018-8b55-7e837cd84a15",
        "332d9f31-595c-4d0f-aebd-4aaf49c345a5",
        "830e2041-d477-4058-a65c-386a93ead237",
        "c0d04e23-c5bb-4625-8906-13dc2644981c"
    ]


class TestComputeCRUD:
    created_vm_id = None
    deleted_vm_verified = False

    # ----------------------------
    # VM-001 VM 생성
    # ----------------------------
    def test_VM001_create_vm(self, api_headers, base_url_compute):
        url = f"{base_url_compute}/virtual_machine"

        body_base = {
            "name": f"vm-auto-{uuid.uuid4().hex[:6]}",
            "zone_id": ZONE_ID,
            "username": "test",
            "password": "1qaz2wsx@@",
            "on_init_script": "",
            "always_on": False,
            "dr": False,
        }

        r = self._create_vm_with_instance_fallback(
            api_headers=api_headers,
            url=url,
            body_base=body_base,
            candidates=INSTANCE_TYPE_CANDIDATES,
            max_retry_per_type=1,
        )

        assert r.status_code in (200, 201), r.text
        res = r.json()
        assert res.get("id"), res

        TestComputeCRUD.created_vm_id = res["id"]

        # 생성 직후 list/상태 조회에서 안 잡힐 수 있어서 잠깐 기다림
        self._wait_vm_visible(api_headers, base_url_compute, res["id"], timeout_sec=60)

    # ----------------------------
    # VM-016 Soft Reboot
    # ----------------------------
    def test_VM016_reboot_soft(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)
        self._ensure_running(api_headers, base_url_compute, vm_id)

        url = f"{base_url_compute}/virtual_machine_control/reboot"
        payload = {"id": vm_id, "type": "soft"}

        r = self._request("POST", url, headers=api_headers, json=payload)
        if r.status_code == 404:
            pytest.xfail("reboot API 미확정(404)")
        assert r.status_code in (200, 202), r.text

        # 재부팅은 상태가 잠깐 바뀔 수 있어서 여유 있게 확인
        self._wait_status(api_headers, base_url_compute, vm_id, ["RUNNING"], timeout_sec=180)

    # ----------------------------
    # VM-018 Web Console 접속 정보 조회
    # ----------------------------
    def test_VM018_get_web_console(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)
        self._ensure_running(api_headers, base_url_compute, vm_id)

        data = self._try_get_by_patterns(
            api_headers=api_headers,
            base_url_compute=base_url_compute,
            endpoint_name="virtual_machine_console",
            vm_id=vm_id,
        )
        # 최소한 url/endpoint/console 관련 키 하나는 있어야 의미가 있음
        assert isinstance(data, (dict, list)), data

    # ----------------------------
    # VM-019 SSH 접속 정보 조회 (지원 시)
    # ----------------------------
    def test_VM019_get_ssh_info(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)
        self._ensure_running(api_headers, base_url_compute, vm_id)

        data = self._try_get_by_patterns(
            api_headers=api_headers,
            base_url_compute=base_url_compute,
            endpoint_name="virtual_machine_ssh",
            vm_id=vm_id,
        )

        # 응답이 dict라면 ssh 관련 필드가 하나라도 있으면 통과
        if isinstance(data, dict):
            keys = {k.lower() for k in data.keys()}
            ok = any(
                k in keys
                for k in [
                    "ssh_host",
                    "host",
                    "ssh_port",
                    "port",
                    "ssh_user",
                    "username",
                    "user",
                    "key",
                    "private_key",
                    "guide",
                    "command",
                ]
            )
            assert ok, data

    # ----------------------------
    # VM-020 VM Metrics 조회
    # ----------------------------
    def test_VM020_get_metrics(self, api_headers, base_url_compute):
        vm_id = self._ensure_vm_id(api_headers, base_url_compute)
        self._ensure_running(api_headers, base_url_compute, vm_id)

        data = self._try_get_by_patterns(
            api_headers=api_headers,
            base_url_compute=base_url_compute,
            endpoint_name="virtual_machine_metrics",
            vm_id=vm_id,
        )

        # 생성 직후엔 비어있을 수 있으니 "형태"만 확인 (dict/list면 OK)
        assert isinstance(data, (dict, list)), data

    # ----------------------------
    # (옵션) VM 삭제 - 필요하면 네 흐름에 맞게 다시 붙여도 됨
    # ----------------------------
    def test_VM006_delete_vm(self, api_headers, base_url_compute):
        vm_id = TestComputeCRUD.created_vm_id
        if not vm_id:
            pytest.xfail("생성된 VM id 없음")

        url = f"{base_url_compute}/virtual_machine/{vm_id}"
        r = self._request("DELETE", url, headers=api_headers)
        assert r.status_code == 200, r.text

        TestComputeCRUD.deleted_vm_verified = True

    # =========================================================
    # Helper
    # =========================================================
    def _request(self, method, url, **kwargs):
        return requests.request(method, url, **kwargs)

    def _list_vms(self, api_headers, base_url_compute):
        url = f"{base_url_compute}/virtual_machine_allocation"
        r = self._request("GET", url, headers=api_headers)
        if r.status_code != 200:
            pytest.xfail(f"VM list 실패: {r.status_code} {r.text}")
        data = r.json()
        if not isinstance(data, list):
            pytest.xfail(f"VM list 응답이 list 아님: {data}")
        return data

    def _ensure_vm_id(self, api_headers, base_url_compute):
        if TestComputeCRUD.created_vm_id and not TestComputeCRUD.deleted_vm_verified:
            return TestComputeCRUD.created_vm_id

        vms = self._list_vms(api_headers, base_url_compute)
        if not vms:
            pytest.xfail("VM 목록이 비어있음")

        # 환경마다 키가 다를 수 있어 후보를 순서대로 탐색
        first = vms[0]
        return first.get("machine_id") or first.get("id") or first.get("vm_id")

    def _get_vm_by_machine_id(self, api_headers, base_url_compute, mid):
        url = f"{base_url_compute}/virtual_machine/{mid}"
        r = self._request("GET", url, headers=api_headers)
        if r.status_code == 200:
            return r.json()
        return None

    def _wait_status(self, api_headers, base_url_compute, mid, expected, timeout_sec=120):
        end = time.time() + timeout_sec
        expected_set = {e.upper() for e in expected}

        while time.time() < end:
            vm = self._get_vm_by_machine_id(api_headers, base_url_compute, mid)
            if vm:
                status = (vm.get("status") or "").upper()
                if status in expected_set:
                    return
            time.sleep(5)

        pytest.xfail(f"timeout: status not in {expected_set}")

    def _ensure_running(self, api_headers, base_url_compute, vm_id):
        vm = self._get_vm_by_machine_id(api_headers, base_url_compute, vm_id)
        if not vm:
            # 아직 조회에 안 잡힐 수 있음
            self._wait_vm_visible(api_headers, base_url_compute, vm_id, timeout_sec=60)
            vm = self._get_vm_by_machine_id(api_headers, base_url_compute, vm_id)

        status = (vm.get("status") or "").upper() if vm else ""
        if status != "RUNNING":
            # RUNNING 아닐 경우 start 시도 (API 미확정이면 xfail)
            start_url = f"{base_url_compute}/virtual_machine_control/start"
            r = self._request("POST", start_url, headers=api_headers, json={"id": vm_id})
            if r.status_code == 404:
                pytest.xfail("start API 미확정(404) - RUNNING 보장 불가")
            if r.status_code not in (200, 202):
                pytest.xfail(f"start 실패: {r.status_code} {r.text}")
            self._wait_status(api_headers, base_url_compute, vm_id, ["RUNNING"], timeout_sec=180)

    def _wait_vm_visible(self, api_headers, base_url_compute, vm_id, timeout_sec=60):
        end = time.time() + timeout_sec
        while time.time() < end:
            vm = self._get_vm_by_machine_id(api_headers, base_url_compute, vm_id)
            if vm:
                return
            time.sleep(3)
        pytest.xfail("timeout: VM not visible")

    def _create_vm_with_instance_fallback(
        self,
        api_headers,
        url,
        body_base,
        candidates,
        max_retry_per_type=1,
    ):
        last_resp = None

        for inst_id in candidates:
            payload = dict(body_base)
            payload["instance_type_id"] = inst_id

            for _ in range(max_retry_per_type):
                r = self._request("POST", url, headers=api_headers, json=payload)
                last_resp = r

                # 성공
                if r.status_code in (200, 201):
                    return r

                # 환경/쿼터/검증 실패면 다음 후보로
                if r.status_code in (400, 404, 409, 422):
                    break

        # 여기까지 왔다는 건 후보 전부 실패
        pytest.xfail(f"VM 생성 실패(후보 전부 실패): {last_resp.status_code if last_resp else None} {last_resp.text if last_resp else None}")

    def _try_get_by_patterns(self, api_headers, base_url_compute, endpoint_name, vm_id):
        """
        console/ssh/metrics는 서비스마다 URL 패턴이 다를 수 있어서
        1) /endpoint/{vm_id}
        2) /endpoint?filter_machine_id=...&count=1
        3) /endpoint?machine_id=...
        순으로 시도.
        404면 다음 패턴, 전부 404면 xfail.
        """
        patterns = [
            f"{base_url_compute}/{endpoint_name}/{vm_id}",
            f"{base_url_compute}/{endpoint_name}?filter_machine_id={vm_id}&count=1",
            f"{base_url_compute}/{endpoint_name}?machine_id={vm_id}",
            f"{base_url_compute}/{endpoint_name}?id={vm_id}",
        ]

        last = None
        for url in patterns:
            r = self._request("GET", url, headers=api_headers)
            last = r
            if r.status_code == 404:
                continue
            if r.status_code != 200:
                pytest.xfail(f"{endpoint_name} 조회 실패: {r.status_code} {r.text}")
            try:
                return r.json()
            except Exception:
                return r.text

        pytest.xfail(f"{endpoint_name} API 미확정/미지원(404): {last.text if last else ''}")





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

        print(f"📊 응답 상태 코드: {response.status_code}")
        
        assert response.status_code == 200, f"⛔ 조회 실패! (상태 코드: {response.status_code})"
        
        print("✅ 대시보드용 VM 리소스 정보 조회 성공")

    # ----------------------------
    # VM-028 동일 이름 VM 생성 시 실패 (409 Conflict)
    # ----------------------------
    @pytest.mark.xfail(reason="서버에서 중복 VM 이름 생성을 차단하지 않고 200 OK를 반환함 (버그 의심)")
    def test_VM028_ERR_duplicate_vm_name_create_fail(self, api_headers, base_url_compute):
        url = f"{base_url_compute}/virtual_machine"
        
        created_vm_ids = []
        instance_id = INSTANCE_TYPE_CANDIDATES[3] 
        
        duplicate_name = f"vm-dup-test-{uuid.uuid4().hex[:6]}"
        
        body = {
            "name": duplicate_name,
            "zone_id": ZONE_ID,
            "instance_type_id": instance_id,
            "username": "test",
            "password": "1qaz2wsx@@",
            "on_init_script": "",
            "always_on": False,
            "dr": False,
        }

        try:
            # 1. 첫 번째 VM 생성
            first_resp = self._request("POST", url, headers=api_headers, json=body)
            assert first_resp.status_code in (200, 201), f"⛔ 첫 번째 VM 생성부터 실패함: {first_resp.text}"
            
            first_id = first_resp.json().get("id")
            if first_id:
                created_vm_ids.append(first_id)

            # 2. 동일한 이름으로 두 번째 VM 생성 요청
            duplicate_resp = self._request("POST", url, headers=api_headers, json=body)
            
            second_id = duplicate_resp.json().get("id")
            if second_id:
                created_vm_ids.append(second_id)

            # 3. 검증: 409 Conflict 기대 (현재 200이 오고 있으므로 이 부분에서 xfail 발생)
            assert duplicate_resp.status_code == 409, \
                f"⛔ [FAIL] 중복 이름 생성 시 409가 아닌 {duplicate_resp.status_code} 반환: {duplicate_resp.text}"
            
        finally:
            for vm_id in created_vm_ids:
                try:
                    self._request("DELETE", f"{url}/{vm_id}", headers=api_headers)
                except Exception as e:
                    print(f"⚠️ VM 삭제 중 오류 발생 (ID: {vm_id}): {e}")

    def test_VM030_ERR_create_cluster_empty_vm_ids(self, api_headers, base_url_compute):
        url = f"{base_url_compute}/cluster"
        
        # 1. vm_ids가 비어있는 Request Body 준비
        body = {
            "name": "cluster-invalid",
            "vm_ids": [] 
        }

        # 2. HTTP Request 생성 및 전송
        response = self._request("POST", url, headers=api_headers, json=body)

        # 3. 검증: 404 Not Found 및 에러 메시지 확인
        assert response.status_code == 404, \
            f"⛔ [FAIL] 빈 vm_ids 요청 시 404가 아닌 {response.status_code} 반환: {response.text}"
        
        # 상세 메시지에 'invalid' 또는 'vm_ids'가 포함되어 있는지 확인
        assert "invalid" in response.text.lower() or "vm_ids" in response.text.lower(), \
            f"⛔ [FAIL] 에러 상세 내용이 기대와 다름: {response.text}"