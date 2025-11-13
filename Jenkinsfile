pipeline {
    agent any

    environment {
        SONAR_PROJECT_KEY = 'gen-ai-chatbot'
        SONAR_SCANNER = 'Sonar'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Code Analysis') {
            steps {
                script {
                    // Trigger SonarQube analysis
                    withSonarQubeEnv('Sonar') {
                        sh "${SONAR_SCANNER} -Dsonar.projectKey=${SONAR_PROJECT_KEY}"
                    }
                }
            }
        }

        stage('Run Tests') {
            steps {
                script {
                    sh '''
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install -r requirements.txt
                        python -m pytest test_app.py -v --junitxml=test-results.xml
                    '''
                }
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
