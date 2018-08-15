# shell script to remove the stack, remove the built images, remove any stale container (if any) from the stack
docker stack rm weather
sleep 30

# remove all built images from the stack
docker rmi $(docker images -q "weather*")

# clean up any stale containers from the stack
docker rm $(docker  ps -q -af name='weather')
