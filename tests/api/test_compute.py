import requests
import pytest
import uuid
import time


class TestComputeCRUD:
    created_vm_id = None

    # VM-001 VM 생성
# VM-001 VM 생성
    def test_VM001_create_vm(self, api_headers, base_url_compute):
        url = f"{base_url_compute}/virtual_machine"

        body = {
            "name": f"vm-auto-{uuid.uuid4().hex[:6]}",
            "zone_id": "0a89d6fa-8588-4994-a6d6-a7c3dc5d5ad0",
            "instance_type_id": "320909e3-44ce-4018-8b55-7e837cd84a15",
            "username": "test",
            "password": "1qaz2wsx@@",
            "on_init_script": "",
            "always_on": False,
            "dr": False
        }

        r = requests.post(url, headers=api_headers, json=body)
        assert r.status_code in (200, 201)

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
