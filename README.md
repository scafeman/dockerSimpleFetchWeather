# dockerSimpleFetchWeather
A simple application consisting of 3 components that demonstrates containerization of application modules, 
and how to deploy distributed applications as a Docker stack. 
Please go through my Medium post here to understand the concept: <>

To run the application:
1. create a docker swarm using 
  $ docker swarm init
2. To deploy the application: run the ./go.sh script 
  - It will build the container images for the services, and deploy the stack. 
3. To delete / remove the application stack: run the ./destroy.sh script
  - It will delete the stack, any built images, and any stale containers that may have been left around from the stack.
  
  
Happy containerization !
