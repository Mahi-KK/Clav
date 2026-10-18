pipeline {
    agent any

    triggers {
        pollSCM('H/2 * * * *')
    }

    options {
        timestamps()
        timeout(time: 15, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
    }

    environment {
        IMAGE = 'clav'
        APP_CONTAINER = 'clav'
        SMOKE_CONTAINER = "clav-smoke-${env.BUILD_NUMBER}"
        NETWORK = 'clav-net'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --quiet --upgrade pip
                    pip install --quiet -r requirements-dev.txt
                '''
            }
        }

        stage('Lint') {
            steps {
                sh '. .venv/bin/activate && flake8 app tests'
            }
        }

        stage('Test') {
            steps {
                sh '''
                    . .venv/bin/activate
                    mkdir -p reports
                    pytest --junitxml=reports/junit.xml \
                           --cov=app --cov-report=xml:reports/coverage.xml --cov-report=term \
                           --cov-fail-under=80
                '''
            }
            post {
                always {
                    junit testResults: 'reports/junit.xml', allowEmptyResults: true
                    recordCoverage(tools: [[parser: 'COBERTURA', pattern: 'reports/coverage.xml']])
                }
            }
        }

        stage('Build image') {
            steps {
                sh 'docker build --build-arg APP_VERSION=$BUILD_NUMBER -t $IMAGE:$BUILD_NUMBER -t $IMAGE:latest .'
            }
        }

        stage('Smoke test') {
            steps {
                sh '''
                    docker run -d --name $SMOKE_CONTAINER --network $NETWORK $IMAGE:$BUILD_NUMBER
                    for i in $(seq 1 20); do
                        curl -fs http://$SMOKE_CONTAINER:5000/health && break
                        sleep 1
                    done
                    curl -fs http://$SMOKE_CONTAINER:5000/health \
                        | python3 -c "import sys, json; assert json.load(sys.stdin)['status'] == 'ok'"
                    curl -fs -X POST -H 'Content-Type: application/json' -d '{"text": "Hello"}' \
                        http://$SMOKE_CONTAINER:5000/api/analyze \
                        | python3 -c "import sys, json; assert json.load(sys.stdin)['keystrokes'] == 6"
                    echo 'Smoke test passed'
                '''
            }
            post {
                always {
                    sh 'docker rm -f $SMOKE_CONTAINER || true'
                }
            }
        }

        stage('Deploy') {
            when {
                expression { (env.GIT_BRANCH ?: '') ==~ /(origin\/)?main/ }
            }
            steps {
                sh '''
                    PREVIOUS=$(docker inspect -f '{{.Config.Image}}' $APP_CONTAINER 2>/dev/null || true)
                    docker rm -f $APP_CONTAINER || true
                    docker run -d --name $APP_CONTAINER --network $NETWORK -p 5000:5000 \
                        --restart unless-stopped $IMAGE:$BUILD_NUMBER

                    for i in $(seq 1 30); do
                        STATUS=$(docker inspect -f '{{.State.Health.Status}}' $APP_CONTAINER)
                        if [ "$STATUS" = healthy ]; then
                            echo "clav:$BUILD_NUMBER is live on http://localhost:5000"
                            exit 0
                        fi
                        sleep 2
                    done

                    echo 'New container never became healthy'
                    docker logs $APP_CONTAINER || true
                    docker rm -f $APP_CONTAINER || true
                    if [ -n "$PREVIOUS" ]; then
                        echo "Rolling back to $PREVIOUS"
                        docker run -d --name $APP_CONTAINER --network $NETWORK -p 5000:5000 \
                            --restart unless-stopped $PREVIOUS
                    fi
                    exit 1
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
        }
        success {
            echo "Build #${env.BUILD_NUMBER} passed every stage."
        }
        failure {
            echo "Build #${env.BUILD_NUMBER} failed. The previous version is still the one deployed."
        }
    }
}
