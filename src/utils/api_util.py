import time
import requests
from loguru import logger

def wait_for_status(url, headers, expected_status, timeout=60, initial_wait=1, max_wait=5, status_key="status"):
    """
    리소스의 상태가 목표 상태가 될 때까지 지수 백오프를 사용하여 반복 조회(Polling)
    
    :param expected_status: 목표 상태 (예: "active", "available", "deleted")
    :param status_key: JSON 응답에서 상태를 확인할 키 이름 (기본값 "status")
    """
    end_time = time.time() + timeout
    wait_time = initial_wait
    attempt = 0

    logger.info(f"⏳ 상태 대기 시작 [{expected_status}]: {url}")

    while time.time() < end_time:
        attempt += 1
        try:
            response = requests.get(url, headers=headers)
            
            # 1. 삭제 확인 케이스 (404/422 응답)
            if response.status_code in [404, 422]:
                if expected_status == "deleted":
                    logger.success(f"✅ 리소스 삭제 확인 완료")
                    return True
                else:
                    logger.warning(f"⚠️ 조회 중 리소스 사라짐 (Status: {response.status_code})")
                    return False

            # 2. 정상 응답(200) 시 상태 비교
            if response.ok:
                res_body = response.json()
                # dict.get()을 사용하여 키가 없을 경우 None 반환
                current_status = res_body.get(status_key)
                
                # 목표 상태 도달 확인
                if str(current_status).lower() == str(expected_status).lower():
                    logger.success(f"✅ 목표 상태 도달: {current_status}")
                    return True
                
                # 진행 상황 로그 (매 5회 시도마다)
                if attempt % 5 == 0:
                    logger.info(f"🔄 대기 중... (현재: {current_status} / 목표: {expected_status})")
            else:
                logger.debug(f"ℹ️ 서버 응답 대기 중... (HTTP {response.status_code})")

        except Exception as e:
            if attempt % 5 == 0:
                logger.debug(f"⚠️ 연결 재시도 중... ({str(e)[:30]})")
            
        # --- 지수 백오프 적용 ---
        time.sleep(wait_time)
        wait_time = min(wait_time * 1.5, max_wait)
        
    logger.error(f"⛔ {timeout}초 내에 목표 상태({expected_status})에 도달하지 못했습니다.")
    return False