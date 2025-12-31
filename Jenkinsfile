pipeline {
    agent any

    environment {
        VENV_PATH = "${WORKSPACE}/venv"
        REPORTS_DIR = "${WORKSPACE}/reports"
        ALLURE_DIR = "${WORKSPACE}/reports/allure"
        ALLURE_HOME = "${WORKSPACE}/allure"
        // Python UTF-8 출력 강제 설정 (Windows 인코딩 문제 해결)
        PYTHONIOENCODING = 'utf-8'
        PYTHONUTF8 = '1'
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
                            setlocal enabledelayedexpansion
                            echo 🔍 Python 설치 확인 중...
                            
                            REM Python Launcher 사용 시도 (가장 안전)
                            where py >nul 2>&1
                            if %ERRORLEVEL% EQU 0 (
                                echo ✓ Python Launcher 발견
                                py -3 --version 2>nul
                                if %ERRORLEVEL% EQU 0 (
                                    py -3 -m venv venv
                                    if %ERRORLEVEL% EQU 0 (
                                        call venv\\Scripts\\activate.bat
                                        python -m pip install --upgrade pip
                                        pip install -r requirements.txt
                                        exit /b 0
                                    )
                                )
                            )
                            
                            REM python 명령어 사용 시도
                            where python >nul 2>&1
                            if %ERRORLEVEL% EQU 0 (
                                echo ✓ python 명령어 발견
                                python --version 2>nul
                                if %ERRORLEVEL% EQU 0 (
                                    python -m venv venv
                                    if %ERRORLEVEL% EQU 0 (
                                        call venv\\Scripts\\activate.bat
                                        python -m pip install --upgrade pip
                                        pip install -r requirements.txt
                                        exit /b 0
                                    )
                                )
                            )
                            
                            REM 일반적인 Python 설치 경로 확인 (안정 버전 우선)
                            echo 🔍 일반 설치 경로에서 Python 검색 중...
                            
                            for %%P in (
                                "C:\\Users\\JMH\\AppData\\Local\\Programs\\Python\\Python314\\python.exe"
                                "%LOCALAPPDATA%\\Programs\\Python\\Python314\\python.exe"
                                "%LOCALAPPDATA%\\Programs\\Python\\Python312\\python.exe"
                                "%LOCALAPPDATA%\\Programs\\Python\\Python311\\python.exe"
                                "C:\\Python312\\python.exe"
                                "C:\\Python311\\python.exe"
                                "C:\\Python310\\python.exe"
                                "C:\\Program Files\\Python312\\python.exe"
                                "C:\\Program Files\\Python311\\python.exe"
                                "C:\\Program Files\\Python310\\python.exe"
                            ) do (
                                if exist %%P (
                                    echo 테스트 중: %%P
                                    %%P --version >nul 2>&1
                                    if !ERRORLEVEL! EQU 0 (
                                        echo ✓ 정상 작동하는 Python 발견: %%P
                                        %%P -m venv venv
                                        if !ERRORLEVEL! EQU 0 (
                                            call venv\\Scripts\\activate.bat
                                            python -m pip install --upgrade pip
                                            pip install -r requirements.txt
                                            exit /b 0
                                        )
                                    ) else (
                                        echo ✗ 손상됨: %%P
                                    )
                                )
                            )
                            
                            echo.
                            echo ❌ 정상 작동하는 Python을 찾을 수 없습니다!
                            echo.
                            echo 📌 문제: C:\\Python314\\python.exe가 손상되어 있습니다.
                            echo.
                            echo 해결 방법:
                            echo 1. 안정적인 Python 3.12 설치:
                            echo    winget install Python.Python.3.12
                            echo.
                            echo 2. 또는 수동 설치:
                            echo    https://www.python.org/downloads/
                            echo    "Add Python to PATH" 옵션 선택!
                            echo.
                            echo 3. 손상된 Python 3.14 제거 (선택):
                            echo    C:\\Python314 폴더 삭제
                            echo.
                            exit /b 1
                        '''
                    }
                }
                
                echo '📦 Allure Commandline 설치 확인...'
                script {
                    if (isUnix()) {
                        sh '''
                            if [ ! -d "allure/bin" ]; then
                                echo "⬇️ Allure Commandline 다운로드 중..."
                                curl -L https://github.com/allure-framework/allure2/releases/download/2.24.1/allure-2.24.1.zip -o allure.zip
                                unzip -q allure.zip
                                mv allure-2.24.1 allure
                                rm allure.zip
                            fi
                            echo "✅ Allure 설치 완료: $(./allure/bin/allure --version)"
                        '''
                    } else {
                        bat '''
                            @echo off
                            if not exist allure\bin\allure.bat (
                                echo ⬇️ Allure Commandline 다운로드 중...
                                powershell -Command "Invoke-WebRequest -Uri 'https://github.com/allure-framework/allure2/releases/download/2.24.1/allure-2.24.1.zip' -OutFile 'allure.zip'"
                                powershell -Command "Expand-Archive -Path 'allure.zip' -DestinationPath '.' -Force"
                                rename allure-2.24.1 allure
                                del allure.zip
                            )
                            echo ✅ Allure 설치 완료
                            allure\bin\allure.bat --version
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
                    // 테스트 실패해도 계속 진행 (catchError 사용)
                    catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                        if (isUnix()) {
                            sh '''
                                . venv/bin/activate
                                mkdir -p reports
                                pytest tests/api/ -v --junit-xml=reports/api-results.xml
                            '''
                        } else {
                            bat '''
                                @echo off
                                chcp 65001 >nul
                                call venv\\Scripts\\activate.bat
                                if not exist reports mkdir reports
                                pytest tests/api/ -v --junit-xml=reports/api-results.xml --alluredir=reports/allure
                            '''
                        }
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
                            @echo off
                            chcp 65001 >nul
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
                echo '📋 Allure HTML 리포트 생성...'
                script {
                    if (isUnix()) {
                        sh '''
                            ./allure/bin/allure generate reports/allure -o reports/allure-report --clean
                        '''
                    } else {
                        bat '''
                            @echo off
                            allure\\bin\\allure.bat generate reports\\allure -o reports\\allure-report --clean
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
                        reportDir: 'reports/allure-report',
                        reportFiles: 'index.html',
                        reportName: 'Allure Report'
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