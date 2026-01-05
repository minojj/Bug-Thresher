pipeline {
    agent any

    environment {
       VENV_PATH = "${WORKSPACE}/venv"
        REPORTS_DIR = "${WORKSPACE}/reports"
        ALLURE_DIR = "${WORKSPACE}/reports/allure"
        ALLURE_HOME = "${WORKSPACE}/allure"
        
        // 🔑 Credentials 불러오기
        LOGIN_INFO = credentials('portal_login_credentials') 
        
        // 🚨 중요: conftest.py의 os.getenv("PASSWORD")와 이름을 일치시켜야 합니다.
        LOGIN_ID = "${env.LOGIN_INFO_USR}"
        LOGIN_PW = "${env.LOGIN_INFO_PSW}"
        PASSWORD = "${env.LOGIN_INFO_PSW}"  // <--- 이 줄이 반드시 있어야 에러가 해결됩니다.
        
        // Python UTF-8 설정
        PYTHONIOENCODING = 'utf-8'
        PYTHONUTF8 = '1'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '🔄 소스 코드 체크아웃...'
                checkout scm
            }
        }

        // 🟢 추가된 단계: 젠킨스 금고에서 토큰 파일을 가져옵니다.
        stage('Prepare Token') {
            steps {
                echo '🔑 Credentials에서 토큰 파일 가져오는 중...'
                script {
                    try {
                        // ID는 젠킨스에 등록한 'auth_token_file'이어야 합니다.
                        withCredentials([file(credentialsId: 'auth_token_file', variable: 'SECRET_PATH')]) {
                            if (isUnix()) {
                                sh "cp -f ${SECRET_PATH} token.txt"
                                sh "chmod 644 token.txt"
                            } else {
                                bat "copy /y ${SECRET_PATH} token.txt"
                            }
                        }
                        echo "✅ token.txt 파일 복사 완료"
                    } catch (e) {
                        echo "⚠️ 토큰 파일을 가져오지 못했습니다 (ID 확인 필요): ${e.message}"
                        // 파일이 없어도 빌드를 멈추지 않고 진행하려면 error 대신 echo 사용
                    }
                }
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
                            python -m venv venv
                            call venv\\Scripts\\activate.bat
                            pip install --upgrade pip
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
                            ls -l token.txt || echo "token.txt 없음"
                        '''
                    } else {
                        bat '''
                            call venv\\Scripts\\activate.bat
                            python --version
                            pip list
                            dir token.txt
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
        }

        // ... 이후 Archive Artifacts 등의 단계는 동일 ...
    }

    post {
        always {
            echo '🧹 워크스페이스 정리...'
            cleanWs(
                deleteDirs: true,
                patterns: [
                    [pattern: 'venv/**', type: 'INCLUDE'],
                    [pattern: '**/__pycache__/**', type: 'INCLUDE']
                ]
            )
        }
    }
}
