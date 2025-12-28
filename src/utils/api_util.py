import time
import requests

def wait_for_status(url, headers, expected_status="deleted", timeout=10, interval=0.5):
    """
    특정 리소스의 상태가 목표 상태가 될 때까지 반복 조회(Polling)
    """
    end = time.time() + timeout
    
    while time.time() < end:
        try:
            response = requests.get(url, headers=headers)
            
            # 1. 404/422 응답 시 (Hard Delete 되었을 경우)
            if response.status_code in [404, 422]:
                return expected_status == "deleted"
            
            # 2. 상태값 비교 (Soft Delete 혹은 Active 확인)
            res_body = response.json()
            if res_body.get("status") == expected_status:
                return True
                
        except Exception:
            pass # 통신 에러 등은 무시하고 재시도
            
        time.sleep(interval)
        
    return False