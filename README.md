# Bug-Thresher

## 📋 프로젝트 개요
Bug-Thresher는 Elice Cloud Infrastructure(ECI) 플랫폼의 API 및 E2E 테스트 자동화 프레임워크입니다.  
블록 스토리지, 네트워크, 오브젝트 스토리지 등의 API 테스트와 UI 자동화 테스트를 지원합니다.

## 🎯 테스트 제품
- **Elice Cloud Infrastructure (ECI)**
  - 블록 스토리지 API (Block Storage)
  - 네트워크 API (Network)
  - 오브젝트 스토리지 API (Object Storage)
  - 웹 UI (로그인, 대시보드)

## 🛠️ 기술 스택

### Python 버전
- **Python 3.8 이상** (권장: Python 3.10+)

### 브라우저
- **Chrome** (권장 - Selenium 자동화용)
- Chrome WebDriver는 `webdriver-manager`를 통해 자동 설치됩니다

### 주요 라이브러리
- `pytest` - 테스트 프레임워크
- `requests` - API 테스트
- `selenium` - UI 자동화
- `python-dotenv` - 환경 변수 관리
- `allure-pytest` - 테스트 리포팅

## 📦 설치 및 설정

### 1. 저장소 클론
```bash
git clone https://github.com/minojj/Bug-Thresher
cd Bug-Thresher
```

### 2. 가상환경 설정
**가상환경을 사용해야 하는 이유:**
- 프로젝트별 의존성 격리
- 시스템 Python 환경과의 충돌 방지
- 버전 관리 용이
- 팀원 간 동일한 개발 환경 보장

#### Windows (PowerShell)
```powershell
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
.\venv\Scripts\Activate.ps1

# PowerShell 실행 정책 오류 발생 시
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### macOS / Linux
```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 환경 변수 설정 (.env 파일)
프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 입력합니다:

```dotenv
# 로그인 정보
LOGIN_ID=your_email@example.com
PASSWORD=your_password

# API Base URLs
BASE_URL_BLOCK_STORAGE=https://portal.gov.elice.cloud/api/user/resource/storage/block_storage
BASE_URL_NETWORK=https://portal.gov.elice.cloud/api/user/resource/network
BASE_URL_OBJECT_STORAGE=https://portal.gov.elice.cloud/api/user/resource/storage/object_storage
```

**⚠️ 주의:** `.env` 파일은 민감한 정보를 포함하므로 Git에 커밋하지 마세요!

## 🧪 테스트 실행

### 전체 테스트 실행
```bash
pytest
```

### 특정 테스트 파일 실행
```bash
# 블록 스토리지 테스트
pytest tests/api/test_block_storage.py

# 네트워크 테스트
pytest tests/api/test_network.py

# 오브젝트 스토리지 테스트
pytest tests/api/test_object_storage.py

### 특정 테스트 클래스 실행
```bash
pytest tests/api/test_block_storage.py::TestBlockStorageCRUD
```

### 특정 테스트 케이스 실행
```bash
pytest tests/api/test_block_storage.py::TestBlockStorageCRUD::test_BS003_create_success
```

### 병렬 실행 (속도 향상)
```bash
pytest -n auto
```

### 상세한 출력 보기
```bash
pytest -v
pytest -vv  # 더 상세한 출력
```

## 📊 리포트 생성

### HTML 리포트 생성
```bash
pytest --html=reports/report.html --self-contained-html
```

### Allure 리포트 생성
```bash
# 테스트 실행 및 결과 저장
pytest --alluredir=reports/allure-results

# 리포트 생성 및 실행 (Allure 설치 필요)
allure serve reports/allure-results
```

### 커버리지 리포트
```bash
pytest --cov=src --cov-report=html
```

리포트는 `reports/` 디렉토리에 저장됩니다.

## 📁 프로젝트 구조

```
Bug-Thresher/
├── .env                          # 환경 변수 (Git 제외)
├── requirements.txt              # Python 의존성
├── pytest.ini                    # pytest 설정
├── README.md                     # 프로젝트 문서
├── Jenkinsfile                   # CI/CD 파이프라인
│
├── src/                          # 소스 코드
│   ├── api/                      # API 클라이언트
│   │   ├── auth_api.py           # 인증 API
│   │   └── instance_api.py       # 인스턴스 API
│   ├── config/                   # 설정 파일
│   │   └── config.ini            # 애플리케이션 설정
│   ├── pages/                    # Page Object Model (POM)
│   │   └── login_page.py         # 로그인 페이지 객체
│   └── utils/                    # 유틸리티
│       └── file_reader.py        # 파일 읽기 유틸
│
├── tests/                        # 테스트 코드
│   ├── conftest.py               # pytest fixtures (토큰, URL 등)
│   ├── api/                      # API 테스트
│   │   ├── test_block_storage.py # 블록 스토리지 CRUD 테스트
│   │   ├── test_network.py       # 네트워크 테스트
│   │   └── test_object_storage.py# 오브젝트 스토리지 테스트
│   └── e2e/                      # End-to-End 테스트
│       └── test_smoke_login.py   # 로그인 스모크 테스트
│
├── reports/                      # 테스트 리포트 (자동 생성)
│   ├── logs/                     # 로그 파일
│   └── screenshots/              # 스크린샷 (테스트 실패 시)
│
├── performance/                  # 성능 테스트
│   ├── eci_load_test.jmx         # JMeter 성능 테스트
│   └── data/                     # 테스트 데이터
│
└── scripts/                      # 유틸리티 스크립트
    └── get_token.py              # 토큰 발급 스크립트
```

## 🔑 주요 기능

### 1. 자동 토큰 관리
`conftest.py`의 `generate_fresh_token()` 함수가 자동으로 로그인하여 인증 토큰을 생성합니다.

### 2. Fixture 기반 테스트
- `auth_token`: 인증 토큰 자동 생성
- `api_headers`: API 요청 헤더 자동 구성
- `base_url_*`: 환경별 Base URL 관리

### 3. Page Object Model (POM)
UI 테스트는 POM 패턴을 사용하여 유지보수성을 높였습니다.

## 🚀 CI/CD
Jenkins를 통한 자동화된 테스트 실행을 지원합니다.  
자세한 내용은 `Jenkinsfile`을 참조하세요.

## 📝 테스트 작성 가이드

### API 테스트 예시
```python
def test_BS001_list_exists_look_up(self, api_headers, base_url_block_storage):
    """블록 스토리지 목록 조회 테스트"""
    url = f"{base_url_block_storage}?skip=0&count=20"
    response = requests.get(url, headers=api_headers)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

### E2E 테스트 예시
```python
def test_login_success(self):
    """로그인 성공 테스트"""
    driver.get("https://qatrack.elice.io/eci")
    # 테스트 로직...
```

## 🤝 기여 방법
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이센스
This project is licensed under the MIT License.

## 👥 팀
QA Team 02 - Elice Cloud Infrastructure Testing

## 📞 문의
문제가 발생하거나 질문이 있으시면 Issue를 등록해주세요.