pipeline {
    agent any
    
    // tools {
    //     // Jenkins Global Tool Configuration에 Python 등록 시 사용
    //     // python 'Python3'
    // }
    
    environment {
        // Python 가상환경 경로
        VENV_PATH = "${WORKSPACE}/venv"
        // 테스트 결과 경로
        TEST_RESULTS = "${WORKSPACE}/reports"
        // Python 경로 (필요시 수정)
        // PATH = "C:\\Python312;C:\\Python312\\Scripts;${env.PATH}"
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
                        bat '''
                            @echo off
                            echo [INFO] Python 경로 확인 중...
                            where python >nul 2>&1
                            if errorlevel 1 (
                                echo [ERROR] Python이 설치되지 않았거나 PATH에 없습니다.
                                echo [INFO] 다음 경로들을 확인합니다:
                                if exist "C:\\Python312\\python.exe" (
                                    set PYTHON_CMD=C:\\Python312\\python.exe
                                ) else if exist "C:\\Python311\\python.exe" (
                                    set PYTHON_CMD=C:\\Python311\\python.exe
                                ) else if exist "C:\\Python310\\python.exe" (
                                    set PYTHON_CMD=C:\\Python310\\python.exe
                                ) else if exist "%LOCALAPPDATA%\\Programs\\Python\\Python312\\python.exe" (
                                    set PYTHON_CMD=%LOCALAPPDATA%\\Programs\\Python\\Python312\\python.exe
                                ) else if exist "%LOCALAPPDATA%\\Programs\\Python\\Python311\\python.exe" (
                                    set PYTHON_CMD=%LOCALAPPDATA%\\Programs\\Python\\Python311\\python.exe
                                ) else (
                                    echo [ERROR] Python을 찾을 수 없습니다. Jenkins 서버에 Python을 설치해주세요.
                                    echo [INFO] https://www.python.org/downloads/ 에서 다운로드
                                    echo [INFO] 설치 시 'Add Python to PATH' 옵션 체크 필수
                                    exit /b 1
                                )
                            ) else (
                                set PYTHON_CMD=python
                            )
                            
                            echo [INFO] Python 명령어: %PYTHON_CMD%
                            %PYTHON_CMD% --version
                            
                            echo [INFO] 가상환경 생성 중...
                            %PYTHON_CMD% -m venv venv
                            
                            echo [INFO] 가상환경 활성화 중...
                            call venv\\Scripts\\activate.bat
                            
                            echo [INFO] pip 업그레이드 중...
                            python -m pip install --upgrade pip
                            
                            echo [INFO] 의존성 설치 중...
                            pip install -r requirements.txt
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
