import requests
import pytest


class TestInfraCRUD:
    """인프라 API 테스트 클래스"""

    def test_INFRA001_get_region_list_success(self, api_headers, base_url_infra):
        """
        INFRA-001: Region 목록 조회
        """
        headers = api_headers
        url = f"{base_url_infra}/region"

        response = requests.get(url, headers=headers)
        res_data = response.json()

        # 상태 코드 검증
        assert response.status_code == 200

        # 응답 타입 및 데이터 존재 여부
        assert isinstance(res_data, list)
        assert len(res_data) > 0, "Region 데이터가 존재해야 하지만 빈 리스트가 반환되었습니다."

        # 필수 필드 검증
        assert "id" in res_data[0]
        assert "name" in res_data[0]
        
    def test_INFRA002_get_zone_list_success(self, api_headers, base_url_infra):
        """
        INFRA-002: Zone 목록 조회
        """
        headers = api_headers
        url = f"{base_url_infra}/infra/zone"
        
        response = requests.get(url, headers=headers)
        res_data = response.json()
        
        # 상태 코드 검증
        assert response.status_code == 200

        # 응답 타입 및 데이터 존재 여부
        assert isinstance(res_data, list)
        assert len(res_data) > 0, "Zone 데이터가 존재해야 하지만 빈 리스트가 반환되었습니다."

        # 필수 필드 검증
        assert "id" in res_data[0]
        assert "name" in res_data[0]
        assert "region_id" in res_data[0]
    
    def test_INFRA003_get_instance_type_list_success(self, api_headers, base_url_infra):
        """
        INFRA-003: Instance Type 목록 조회
        """
        headers = api_headers
        url = f"{base_url_infra}/infra/instance_type"

        response = requests.get(url, headers=headers)
        res_data = response.json()

        # 상태 코드 검증
        assert response.status_code == 200

        # 응답 타입 및 데이터 존재 여부
        assert isinstance(res_data, list)
        assert len(res_data) > 0, "Instance Type 데이터가 존재해야 하지만 빈 리스트가 반환되었습니다."

        # 필수 필드 검증
        assert "id" in res_data[0]
        assert "name" in res_data[0]
        assert "cpu_vcore" in res_data[0]
        assert "memory_gib" in res_data[0]
        
    def test_INFRA004_get_block_storage_image_list_success(self, api_headers, base_url_infra):
        """
        INFRA004: Block Storage Image 목록 조회
        - 데이터가 없는 경우에도 정상 응답(200)인지 확인
        """
        headers = api_headers
        url = f"{base_url_infra}/infra/block_storage_image"

        response = requests.get(url, headers=headers)
        res_data = response.json()

        # 상태 코드 검증
        assert response.status_code == 200

        # 응답 타입 검증
        assert isinstance(res_data, list)

        # 데이터가 존재하는 경우에만 최소 필드 검증
        if len(res_data) > 0:
            assert "id" in res_data[0]
            assert "zone_id" in res_data[0]
            assert "name" in res_data[0]
            assert "status" in res_data[0]

    def test_INFRA005_get_notice_list_success(self, api_headers, base_url_infra):
        """
        INFRA005: 공지사항 및 업데이트 조회
        - 공지가 없는 경우에도 정상 응답(200)인지 확인
        """
        headers = api_headers
        url = f"{base_url_infra}/notice"

        response = requests.get(url, headers=headers)
        res_data = response.json()

        # 상태 코드 검증
        assert response.status_code == 200

        # 응답 타입 검증
        assert isinstance(res_data, list)

        # 데이터가 존재하는 경우에만 필드 검증
        if len(res_data) > 0:
            assert "id" in res_data[0]
            # 공지 타입/필드는 환경에 따라 달라질 수 있어서, 흔히 있는 필드만 '있으면' 검증
            if "title" in res_data[0]:
                assert isinstance(res_data[0]["title"], str)
            if "message" in res_data[0]:
                assert isinstance(res_data[0]["message"], str)
            if "created" in res_data[0]:
                assert isinstance(res_data[0]["created"], str)

    def test_INFRA006_get_resource_usage_success(self, api_headers, base_url_infra):
        """
        INFRA006: 리소스 사용 현황 조회
        """
        headers = api_headers
        url = f"{base_url_infra}/organization/resource_usage"

        response = requests.get(url, headers=headers)
        res_data = response.json()

        # 상태 코드 검증
        assert response.status_code == 200

        # 응답 타입 검증 (dict)
        assert isinstance(res_data, dict)

        # 주요 리소스 카테고리 존재 여부 검증
        for key in ["compute", "storage", "network"]:
            assert key in res_data, f"resource_usage에 '{key}' 항목이 존재해야 합니다."

        # 각 카테고리 내부 구조는 환경마다 달라질 수 있으므로,
        # 값 비교는 하지 않고 dict 구조만 최소 검증
        assert isinstance(res_data["compute"], dict)
        assert isinstance(res_data["storage"], dict)
        assert isinstance(res_data["network"], dict)