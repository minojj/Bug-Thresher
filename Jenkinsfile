pipeline {
    agent any

    environment {
        VENV_PATH = "${WORKSPACE}/venv"
        REPORTS_DIR = "${WORKSPACE}/reports"
        ALLURE_DIR = "${WORKSPACE}/reports/allure"
    }

    stages {
        /* --- 1. 프로젝트 체크아웃 --- */
        stage('체크아웃') {
            steps {
                echo '🔄 소스 코드 체크아웃...'
                checkout scm
            }
        }

        /* --- 2. Python 가상환경 생성 + 의존성 설치 --- */
        stage('환경 설정') {
            steps {
                echo '🛠️ Python 가상환경 설정...'
                script {
                    if (isUnix()) {
                        sh '''
                            python3 -m venv venv
                            . venv/bin/activate
                            python -m pip install --upgrade pip
                            pip install -r requirements.txt
                        '''
                    } else {
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
                            
                            REM 일반적인 Python 설치 경로 확인
                            echo 🔍 일반 설치 경로에서 Python 검색 중...
                            
                            for %%P in (
                                "C:\\Python314\\python.exe"
                                "C:\\Python312\\python.exe"
                                "C:\\Python311\\python.exe"
                                "C:\\Python310\\python.exe"
                                "C:\\Program Files\\Python314\\python.exe"
                                "C:\\Program Files\\Python312\\python.exe"
                                "C:\\Program Files\\Python311\\python.exe"
                                "%LOCALAPPDATA%\\Programs\\Python\\Python314\\python.exe"
                                "%LOCALAPPDATA%\\Programs\\Python\\Python312\\python.exe"
                                "%LOCALAPPDATA%\\Programs\\Python\\Python311\\python.exe"
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
                            
                            echo ❌ Python을 찾을 수 없습니다!
                            echo Jenkins 서버에 Python을 설치하세요: https://www.python.org/downloads/
                            exit /b 1
                        '''
                    }
                }
            }
        }

        /* --- 3. 환경 검증 --- */
        stage('환경 검증') {
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

        /* --- 4. API 테스트 실행 --- */
        stage('API 테스트') {
            steps {
                echo '🧪 API 테스트 실행...'
                script {
                    if (isUnix()) {
                        sh '''
                            . venv/bin/activate
                            mkdir -p reports
                            pytest tests/api/ -v --junit-xml=reports/api-results.xml
                        '''
                    } else {
                        bat '''
                            call venv\\Scripts\\activate.bat
                            if not exist reports mkdir reports
                            pytest tests/api/ -v --junit-xml=reports/api-results.xml
                        '''
                    }
                }
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/api-results.xml'
                }
            }
        }

        /* --- 5. 코드 커버리지 리포트 --- */
        stage('커버리지 리포트') {
            steps {
                echo '📊 코드 커버리지 리포트 생성...'
                script {
                    if (isUnix()) {
                        sh '''
                            . venv/bin/activate
                            pytest tests/api/ --cov=src --cov-report=html:reports/coverage --cov-report=xml:reports/coverage.xml
                        '''
                    } else {
                        bat '''
                            call venv\\Scripts\\activate.bat
                            pytest tests/api/ --cov=src --cov-report=html:reports/coverage --cov-report=xml:reports/coverage.xml
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

        /* --- 6. Allure 리포트 생성 --- */
        stage('Allure 리포트') {
            steps {
                echo '📋 Allure 리포트 생성...'
                script {
                    if (isUnix()) {
                        sh '''
                            . venv/bin/activate
                            pytest tests/api/ --alluredir=reports/allure
                        '''
                    } else {
                        bat '''
                            call venv\\Scripts\\activate.bat
                            pytest tests/api/ --alluredir=reports/allure
                        '''
                    }
                }
            }
            post {
                always {
                    allure([
                        includeProperties: false,
                        results: [[path: 'reports/allure']],
                        commandline: 'Allure'
                    ])
                }
            }
        }

        /* --- 7. 아티팩트 보관 --- */
        stage('아티팩트 보관') {
            steps {
                echo '📦 테스트 결과 및 리포트 보관...'
                archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true
            }
        }

        /* --- 8. 브랜치별 배포 (선택) --- */
        stage('배포') {
            when { 
                anyOf { 
                    branch 'develop'
                    branch 'main' 
                } 
            }
            steps {
                echo '🚀 배포 단계 (현재는 메시지만 출력)'
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
        }
        
        failure {
            echo '❌ 파이프라인 실패!'
        }
    }
}
