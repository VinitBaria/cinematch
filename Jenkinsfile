pipeline {
    agent any

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

        stage('Docker Build (Optional)') {
            steps {
                script {
                    try {
                        echo 'Building backend Docker image...'
                        bat 'docker build -t cinematch-backend:latest ./backend'
                    } catch (Exception e) {
                        echo 'Docker build skipped or failed (Docker might not be running on host).'
                    }
                }
            }
        }
    }

    post {
        always {
            echo 'Cleaning up and completing pipeline execution.'
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Please inspect the stage logs above.'
        }
    }
}
