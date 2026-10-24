pipeline {
    agent any

    environment {
        NOTIFY_EMAIL = 'vinitbaria2006@gmail.com'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out source code...'
                checkout scm
            }
        }

        stage('Environment Check') {
            steps {
                echo 'Verifying environment...'
                bat 'python --version'
                bat 'git --version'
            }
        }

        stage('Install Dependencies') {
            steps {
                echo 'Installing Python dependencies...'
                bat 'python -m pip install --upgrade pip'
                bat 'pip install email-validator pytest'
                bat 'pip install -r backend/requirements.txt'
                bat 'pip install -r ml/requirements.txt'
            }
        }

        stage('Run Tests') {
            steps {
                echo 'Running unit and integration tests...'
                bat 'pytest tests/ -v'
            }
        }

        // ── Deployment Stages ──
        stage('Build Docker') {
            steps {
                echo 'Building production Docker images via docker-compose...'
                bat 'docker compose -p cinematch-ai build backend frontend'
            }
        }

        stage('Deploy') {
            steps {
                echo 'Starting and updating container stack...'
                bat 'docker compose -p cinematch-ai up -d mongodb'
                bat 'docker compose -p cinematch-ai up -d --no-deps backend frontend nginx'
            }
        }

        stage('Smoke Test') {
            steps {
                echo 'Verifying live application health...'
                sleep 5
                bat 'curl.exe -f http://127.0.0.1/api/health'
            }
        }
    }

    post {
        always {
            echo 'Cleaning up and completing pipeline execution.'
        }
        success {
            echo 'Pipeline completed and deployed successfully!'
            script {
                try {
                    mail to: "${NOTIFY_EMAIL}",
                         subject: "SUCCESS: Jenkins Build #${env.BUILD_NUMBER} - ${env.JOB_NAME}",
                         body: """Great news!

Jenkins Build #${env.BUILD_NUMBER} has successfully passed all tests and deployed the updated containers.
Application URL: http://localhost
Build Details: ${env.BUILD_URL}
"""
                } catch (Exception e) {
                    echo "Notice: Could not send email (check Jenkins SMTP settings): ${e.message}"
                }
            }
        }
        failure {
            echo 'Pipeline failed. Please inspect the stage logs above.'
            script {
                try {
                    mail to: "${NOTIFY_EMAIL}",
                         subject: "FAILURE: Jenkins Build #${env.BUILD_NUMBER} - ${env.JOB_NAME}",
                         body: """Attention!

Jenkins Build #${env.BUILD_NUMBER} failed during execution.
Please check the console logs to inspect the failure:
Build Console: ${env.BUILD_URL}console
"""
                } catch (Exception e) {
                    echo "Notice: Could not send email (check Jenkins SMTP settings): ${e.message}"
                }
            }
        }
    }
}
