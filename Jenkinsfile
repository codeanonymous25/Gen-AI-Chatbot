pipeline {
    agent any

    environment {
        SONAR_TOKEN = credentials(sonar_token)
        SONAR_PROJECT_KEY = 'gen-ai-chatbot'      
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Code Analysis') {
            steps {
                withSonarQubeEnv('Sonar') {
                    sh '''
                        sonar-scanner \
                        -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                        -Dsonar.projectName=Chatbot \
                        -Dsonar.sources=.
                        -Dsonar.token=${SONAR_TOKEN}
                    '''
                }
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    # Install python3-venv if missing
                    # apt-get update && apt-get install -y python3-venv

                    # Create virtual environment and run tests
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                    python -m pytest test_app.py -v --junitxml=test-results.xml
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                }
            }
        }

        stage('Approval') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                input message: 'Tests passed. Approve to merge?', ok: 'Merge'
            }
        }

        stage('Done') {
            steps {
                echo 'Validation pipeline completed!'
            }
        }
    }

    post {
        success {
            echo 'Pipeline succeeded!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}
