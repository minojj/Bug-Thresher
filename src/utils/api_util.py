import time
import requests
from loguru import logger

def wait_for_status(url, headers, expected_status="deleted", timeout=60, initial_wait=0.5, max_wait=5):
    """
    특정 리소스의 상태가 목표 상태가 될 때까지 지수 백오프를 사용하여 반복 조회(Polling)
    - expected_status="deleted" 일 경우, 404 응답을 성공으로 간주함
    """
    end_time = time.time() + timeout
    wait_time = initial_wait
    attempt = 0

    logger.info(f"⏳ 상태 대기 시작 ({expected_status}): {url}")

    while time.time() < end_time:
        attempt += 1
        try:
            response = requests.get(url, headers=headers)
            
            # 1. 삭제 확인 케이스 (404/422 응답 시)
            if response.status_code in [404, 422]:
                if expected_status == "deleted":
                    logger.success(f"✅ 리소스 삭제 확인 완료 (404/422)")
                    return True
                else:
                    # 삭제를 기다리는 게 아닌데 404가 뜨면 중단
                    logger.warning(f"⚠️ 조회 중 리소스 사라짐 (404)")
                    return False

            # 2. 정상 응답 시 상태값 비교
            if response.status_code == 200:
                res_body = response.json()
                current_status = res_body.get("status")
                
                if current_status == expected_status:
                    logger.success(f"✅ 목표 상태 도달: {expected_status}")
                    return True
                
                # 삭제 대기 중인데 아직 데이터가 남아있는 경우 로그 (선택)
                if attempt % 5 == 0:
                    logger.info(f"🔄 아직 대기 중... (현재 상태: {current_status})")

        except Exception as e:
            # 통신 에러 등은 로그만 남기고 재시도
            if attempt % 5 == 0:
                logger.debug(f"⚠️ 연결 재시도 중... ({str(e)[:30]})")
            pass
            
        # --- 지수 백오프 적용 ---
        time.sleep(wait_time)
        # 대기 시간을 1.5배씩 늘리되, max_wait(5초)를 넘지 않음
        wait_time = min(wait_time * 1.5, max_wait)
        
    logger.error(f"⛔ {timeout}초 내에 목표 상태({expected_status})에 도달하지 못했습니다.")
    return False