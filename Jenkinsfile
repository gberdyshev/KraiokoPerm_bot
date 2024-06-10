properties([disableConcurrentBuilds()])

pipeline {
    agent any

    environment {
        SHORTHASH = "${sh(script:'git rev-parse --short HEAD', returnStdout: true).trim()}"
        CONTAINERNAME = "kraioko_cont"
        IMAGENAME = "kraioko_bot/bot"
        STORELEN = 10
    }

    stages {
        stage('Build') {
            steps {
                echo "========== Building image =========="
                sh 'docker build -t $IMAGENAME:$SHORTHASH .'
                echo "Build success"
            }
        }

        stage('Clear for old images') {
            steps {
                echo "========== Clearing old images =========="
                sh 'docker images --format "{{.Repository}}\t{{.ID}}" | grep $IMAGENAME | cut -f2 | tail -n+$STORELEN | xargs -r docker rmi'
                echo "Old images cleared"
            }
        }

        stage('Run') {
            steps {
                echo "========== Running container =========="

                sh 'docker rm -f $CONTAINERNAME &> /dev/null'

                waitUntil {
                    script {
                        sh 'docker wait $CONTAINERNAME &> /dev/null'
                        return true
                    }
                }

                sh 'docker run -d --name $CONTAINERNAME -v /opt/kraioko_bot/bot/db/:/usr/src/kraioko/db $IMAGENAME:$SHORTHASH'

                echo "Container created!"
            }
        }
    }
}
