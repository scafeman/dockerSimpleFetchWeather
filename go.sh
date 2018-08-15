# shell scrip to build the container images for the 2 services and then deploy the stack on the swarm
docker build -t weather-web:v1 ./web/
docker build -t weather-fetcher:v1 ./fetchweather/
docker stack deploy -c docker-compose.yml weather
