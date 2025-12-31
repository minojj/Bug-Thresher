pipeline {
    agent any
    
    environment {
        // Python 가상환경 경로
        VENV_PATH = "${WORKSPACE}/venv"
        // 테스트 결과 경로
        TEST_RESULTS = "${WORKSPACE}/reports"
        // Python 실행 파일 경로 (Windows 시스템에 설치된 Python 경로로 수정 필요)
        // 예: PYTHON_HOME = 'C:\\Python311' 또는 'C:\\Users\\JMH\\AppData\\Local\\Programs\\Python\\Python311'
        PYTHON_CMD = 'py -3'  // Windows Python Launcher 사용
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '🔄 소스 코드 체크아웃...'
                checkout scm
            }
        }
        
        stage('Setup Environment') {
            steps {
                echo '🛠️ Python 가상환경 설정...'
                script {
                    if (isUnix()) {
                        sh '''
                            python3 -m venv venv
                            . venv/bin/activate
                            pip install --upgrade pip
                            pip install -r requirements.txt
                        '''
                    } else {
                        // Windows에서 Python 찾기 및 가상환경 생성
                        bat '''
                            @echo off
                            echo 🔍 Python 설치 확인 중...
                            
                            REM Python Launcher 사용 시도
                            where py >nul 2>&1
                            if %ERRORLEVEL% EQU 0 (
                                echo ✓ Python Launcher 발견
                                py -3 --version
                                py -3 -m venv venv
                                call venv\\Scripts\\activate.bat
                                python -m pip install --upgrade pip
                                pip install -r requirements.txt
                                exit /b 0
                            )
                            
                            REM python 명령어 사용 시도
                            where python >nul 2>&1
                            if %ERRORLEVEL% EQU 0 (
                                echo ✓ python 명령어 발견
                                python --version
                                python -m venv venv
                                call venv\\Scripts\\activate.bat
                                python -m pip install --upgrade pip
                                pip install -r requirements.txt
                                exit /b 0
                            )
                            
                            REM python3 명령어 사용 시도
                            where python3 >nul 2>&1
                            if %ERRORLEVEL% EQU 0 (
                                echo ✓ python3 명령어 발견
                                python3 --version
                                python3 -m venv venv
                                call venv\\Scripts\\activate.bat
                                python -m pip install --upgrade pip
                                pip install -r requirements.txt
                                exit /b 0
                            )
                            
                            REM 일반적인 Python 설치 경로 확인
                            echo 🔍 일반 설치 경로에서 Python 검색 중...
                            
                            for %%P in (
                                "C:\\Python312\\python.exe"
                                "C:\\Python311\\python.exe"
                                "C:\\Python310\\python.exe"
                                "C:\\Program Files\\Python312\\python.exe"
                                "C:\\Program Files\\Python311\\python.exe"
                                "C:\\Program Files\\Python310\\python.exe"
                                "%LOCALAPPDATA%\\Programs\\Python\\Python312\\python.exe"
                                "%LOCALAPPDATA%\\Programs\\Python\\Python311\\python.exe"
                                "C:\\Users\\JMH\\AppData\\Local\\Programs\\Python\\Python314\\python.exe"
                            ) do (
                                if exist %%P (
                                    echo ✓ Python 발견: %%P
                                    %%P --version
                                    %%P -m venv venv
                                    call venv\\Scripts\\activate.bat
                                    python -m pip install --upgrade pip
                                    pip install -r requirements.txt
                                    exit /b 0
                                )
                            )
                            
                            echo.
                            echo ❌ Python을 찾을 수 없습니다!
                            echo.
                            echo 📌 Jenkins 서버에서 다음 작업을 수행하세요:
                            echo.
                            echo 1. Python 다운로드 및 설치:
                            echo    https://www.python.org/downloads/
                            echo    설치 시 "Add Python to PATH" 옵션 선택!
                            echo.
                            echo 2. 또는 winget으로 설치:
                            echo    winget install Python.Python.3.12
                            echo.
                            echo 3. 설치 확인:
                            echo    python --version
                            echo.
                            exit /b 1
                        '''
                    }
                }
            }
        }
        
        stage('Validate Environment') {
            steps {
                echo '✅ 환경 변수 및 의존성 검증...'
                script {
                    if (isUnix()) {
                        sh '''
                            . venv/bin/activate
                            python --version
                            pip list
                        '''
                    } else {
                        bat '''
                            call venv\\Scripts\\activate.bat
                            python --version
                            pip list
                        '''
                    }
                }
            }
        }
        
        stage('Run API Tests') {
            steps {
                echo '🧪 API 테스트 실행...'
                script {
                    if (isUnix()) {
                        sh '''
                            . venv/bin/activate
                            pytest tests/api/ -v --junit-xml=reports/api-results.xml --html=reports/api-report.html --self-contained-html
                        '''
                    } else {
                        bat '''
                            call venv\\Scripts\\activate.bat
                            pytest tests/api/ -v --junit-xml=reports/api-results.xml --html=reports/api-report.html --self-contained-html
                        '''
                    }
                }
            }
            post {
                always {
                    junit 'reports/api-results.xml'
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'reports',
                        reportFiles: 'api-report.html',
                        reportName: 'API Test Report'
                    ])
                }
            }
        }
        
        stage('Run E2E Tests') {
            steps {
                echo '🌐 E2E 테스트 실행...'
                script {
                    if (isUnix()) {
                        sh '''
                            . venv/bin/activate
                            pytest tests/e2e/ -v --junit-xml=reports/e2e-results.xml --html=reports/e2e-report.html --self-contained-html
                        '''
                    } else {
                        bat '''
                            call venv\\Scripts\\activate.bat
                            pytest tests/e2e/ -v --junit-xml=reports/e2e-results.xml --html=reports/e2e-report.html --self-contained-html
                        '''
                    }
                }
            }
            post {
                always {
                    junit 'reports/e2e-results.xml'
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'reports',
                        reportFiles: 'e2e-report.html',
                        reportName: 'E2E Test Report'
                    ])
                }
            }
        }
        
        stage('Generate Coverage Report') {
            steps {
                echo '📊 코드 커버리지 리포트 생성...'
                script {
                    if (isUnix()) {
                        sh '''
                            . venv/bin/activate
                            pytest --cov=src --cov-report=html:reports/coverage --cov-report=xml:reports/coverage.xml
                        '''
                    } else {
                        bat '''
                            call venv\\Scripts\\activate.bat
                            pytest --cov=src --cov-report=html:reports/coverage --cov-report=xml:reports/coverage.xml
                        '''
                    }
                }
            }
            post {
                always {
                    publishHTML([
                        allowMissing: true,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'reports/coverage',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }
        
        stage('Archive Artifacts') {
            steps {
                echo '📦 아티팩트 보관...'
                archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true
            }
        }
    }
    
    post {
        always {
            echo '🧹 워크스페이스 정리...'
            cleanWs(
                deleteDirs: true,
                patterns: [
                    [pattern: 'venv/**', type: 'INCLUDE'],
                    [pattern: '**/__pycache__/**', type: 'INCLUDE'],
                    [pattern: '**/*.pyc', type: 'INCLUDE']
                ]
            )
        }
        success {
            echo '✅ 파이프라인 성공!'
            // 성공 시 알림 (Slack, Email 등)
            // slackSend(color: 'good', message: "Build Successful: ${env.JOB_NAME} #${env.BUILD_NUMBER}")
        }
        failure {
            echo '❌ 파이프라인 실패!'
            // 실패 시 알림
            // slackSend(color: 'danger', message: "Build Failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}")
        }
        unstable {
            echo '⚠️ 파이프라인 불안정!'
        }
    }
}
