# web server in Python Flask that receives requests from user
# the requests are forwarded to a backend fetcher swarm that fetches weather information from an internet web portal
#!/usr/bin/env python

from flask import Flask, request
import pika, socket, traceback, time, json
from datetime import datetime


# global variables
channel=None
HOSTNAME=None
RMQ_EXCHANGE = 'app4_exchange'
RMQ_FETCH_WEATHER_ROUTE_KEY = 'FETCH_WEATHER'
RESPONSE_FORMAT_GOOD = "Request from client:{client_ip} for location: {location} sent to msging bus"
RESPONSE_FORMAT_BAD_MISS_PARAM = "Error processing request from client:{client_ip} for location: {location} <br> Reason:<error_code>"


def getJSON(hostname, location):
	s_header = {'webhost':hostname}
	s_body = {'location':location}
	s_pkt = {'header':s_header, 'body': s_body}
	s_body = json.dumps(s_pkt)
	return s_body

def gettime():
	return str(datetime.now())



def fnConnectToRabbit():
	global channel, HOSTNAME

	try:
		channel = None
		# Create a channel, ensure that the exchange is present. Create an exclusive queue within the channel,
		# and bind it using the hostname as routing_key

		# disable heartbeats (interval=0) for the Blocking Connection. 
		# Else, you need to implement a busy loop for sending heartbeats in the same thread
		connectionParameters = pika.ConnectionParameters(host='bus', port=5672, heartbeat=0)
		connection = pika.BlockingConnection(connectionParameters)
		channel = connection.channel()
		channel.exchange_declare(exchange=RMQ_EXCHANGE, exchange_type='topic')
		#print (gettime(), " WEB: Setting up queue for myself with name=", HOSTNAME, " type=", type(HOSTNAME))
		rmq_queue = channel.queue_declare(queue=HOSTNAME, exclusive=True)
		rmq_queue_name = rmq_queue.method.queue
		channel.queue_bind(exchange=RMQ_EXCHANGE, queue=rmq_queue_name, routing_key=HOSTNAME)

		print (gettime()," WEB: Connected to Rabbit server")
	except Exception as ex:
		print (gettime()," WEB: Connection setup to RabbitMQ failed due to ", str(traceback.format_exception_only(type(ex), ex)))
		channel=None
	return channel


app = Flask(__name__)

@app.route("/forecast")
def fnLoginURL():
	global channel

	# extract user data from web GET request
	try:
		src_ip = request.environ['REMOTE_ADDR']
		location = request.args.get('loc', default=None) or request.args.get('location', default=None)

	except Exception as ex:
		print (gettime(), " WEB: Unable to find required parameters in GET request")
		response = RESPONSE_FORMAT_BAD_MISS_PARAM.format(client_ip=src_ip, location=location,
			error_code=str(traceback.format_exception_only(type(ex), ex)))
		return response

	# send user data to fetcher component via the msging bus
	try:
		json_str = getJSON(HOSTNAME, location)
		if (channel.is_open==True):
			channel.basic_publish(exchange=RMQ_EXCHANGE, routing_key=RMQ_FETCH_WEATHER_ROUTE_KEY, body=json_str.encode('utf-8'))
		print (gettime(), " WEB: Sent user data to messaging bus. Dump=", json_str)
		
	except Exception as ex:
		print (gettime()," WEB: Exception processing user request. Stack=",str(traceback.format_exc()))
		response = RESPONSE_FORMAT_BAD_MISS_PARAM.format(client_ip=src_ip, location=location, 
			error_code=str(traceback.format_exception_only(type(ex), ex)))
		return response

	# wait to hear back from the backend weather fetcher. Pick up and ACK, only to the first response
	for method, properties, body in channel.consume(queue=HOSTNAME, inactivity_timeout=10):
		if body==None:
			print (gettime(), " WEB: timed out waiting for a response from the backend weather fetcher")
			response = "Timed out waiting for a response from weather fetcher"
		else:
			try:
				if isinstance(body, bytes):
					body=body.decode('utf-8')
				print (gettime(), " WEB: Response from backend weather fetcher is", body)
				resp_dict = json.loads(body)
				resp_header = resp_dict['header']
				resp_body = resp_dict['body']
				response = "<i>Processed by WEB node: " + resp_header['webhost'] + "</i><br>"
				response += "<i>Processed by FETCHER node: " + resp_header['fetcherhost'] + "</i><br>"
				response += "Weather forecast for <b>" + resp_body['location'] + "</b> : " + resp_body['weather']
			except:
				response = "Error processing response from backend component: Weather fetcher !!!"
			# acknowledge the packet to the messaging bus
			channel.basic_ack(method.delivery_tag)
			break
	return response



def main():

	global channel, HOSTNAME

	HOSTNAME = socket.gethostname()
	print (gettime(), " WEB: Connecting in from hostname=", HOSTNAME)
	# run a continuous loop to reconnect every 1sec until connected to RabbitMQ bus
	while (1):
		print (gettime()," WEB: Connecting to messaging bus")
		channel=fnConnectToRabbit()
		if isinstance(channel, pika.adapters.blocking_connection.BlockingChannel):
			break
		time.sleep(1)
	app.run('0.0.0.0', 80)

if __name__=="__main__":
	main()
		
