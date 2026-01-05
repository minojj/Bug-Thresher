import allure
from datetime import datetime

def attach_screenshot(driver, name="screenshot"):
    """Allure 리포트에 스크린샷 첨부"""
    timestamp = datetime.now().strftime('%H-%M-%S')
    allure.attach(
        driver.get_screenshot_as_png(),
        name=f"{name}{timestamp}",
        attachment_type=allure.attachment_type.PNG
    )