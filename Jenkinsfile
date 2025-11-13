pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = 'ai-chatbot'
        DOCKER_TAG = "${BUILD_NUMBER}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Install Dependencies') {
            steps {
                script {
                    sh '''
                        python -m pip install --upgrade pip
                        pip install -r requirements.txt
                        npm install
                    '''
                }
            }
        }
        
        stage('Run Tests') {
            steps {
                script {
                    sh '''
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
        
        stage('Build React App') {
            steps {
                script {
                    sh 'npm run build'
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    sh '''
                        docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                        docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest
                    '''
                }
            }
        }
        
        stage('Security Scan') {
            steps {
                script {
                    sh '''
                        # Install safety for Python security scan
                        pip install safety
                        safety check --json --output safety-report.json || true
                        
                        # Install npm audit for Node.js security scan
                        npm audit --json > npm-audit.json || true
                    '''
                }
            }
        }
        
        stage('Deploy to Staging') {
            when {
                branch 'develop'
            }
            steps {
                script {
                    sh '''
                        docker stop ai-chatbot-staging || true
                        docker rm ai-chatbot-staging || true
                        docker run -d --name ai-chatbot-staging -p 5001:5000 ${DOCKER_IMAGE}:${DOCKER_TAG}
                    '''
                }
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                script {
                    input message: 'Deploy to Production?', ok: 'Deploy'
                    sh '''
                        docker stop ai-chatbot-prod || true
                        docker rm ai-chatbot-prod || true
                        docker run -d --name ai-chatbot-prod -p 5000:5000 ${DOCKER_IMAGE}:${DOCKER_TAG}
                    '''
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline succeeded!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}