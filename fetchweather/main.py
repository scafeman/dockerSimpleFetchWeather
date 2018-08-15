# python script to pull messages from the messaging bus, parse out the user details from it, and fetch corresponding weather details from internet
#!/usr/bin/env python

import pika
import traceback, sys, time, json, socket
from datetime import datetime


# global variables
RMQ_EXCHANGE = 'app4_exchange'
RMQ_FETCH_WEATHER_ROUTE_KEY = 'FETCH_WEATHER'
RMQ_FETCH_WEATHER_QUEUE = 'FETCH_WEATHER_QUEUE'

def gettime():
	return str(datetime.now())

# callback function invoked everytime the RMQ queue has a message in it
def callback(ch, method, properties, body):
	print (gettime(), " FETCHER: Log message dump: ", body)

	# if unicode, then decode the body
	if isinstance(body, bytes):
		body=body.decode('utf-8')

	# parse out the contents of the JSON string
	try:
		pkt_dict = json.loads(body)
		pkt_header = pkt_dict['header']
		pkt_body = pkt_dict['body']
		webhost = pkt_header['webhost']
		loc = pkt_body['location']
		print (gettime(), " FETCHER: Received weather fetch request for location=", loc, " from web_node=", webhost)
	except:
		print (gettime(), " FETCHER: Exception parsing out JSON contents. Stack=", traceback.format_exc())

	# imitate backend processing by delay of 5sec
	time.sleep(2)

	# send a message back to the webhost
	try:
		pkt_body['weather'] = gettime() + " : The weather is nice and sunny today !"
		pkt_header['fetcherhost'] = socket.gethostname()
		pkt_dict = {'header': pkt_header, 'body':pkt_body}
		resp_pkt = json.dumps(pkt_dict)
		if ch.is_open:
			ch.basic_publish(exchange=RMQ_EXCHANGE, routing_key=webhost, body=resp_pkt.encode('utf-8'))
		print (gettime(), " FETCHER: Sent response packet back to host=", webhost)
	except:
		print (gettime(), " FETCHER: Exception sending response to webhost. Stack=", traceback.format_exc())



# connect to RabbitMQ messaging bus
def fnConnectToMsgingBus():
	try:
		channel, fetcher_queue_name = None,None

		# disable heartbeats (interval=0). Else implement a busy loop in the same thread.
		connectionParameters = pika.ConnectionParameters(host='bus', port=5672, heartbeat=0)
		connection = pika.BlockingConnection(connectionParameters)
		channel = connection.channel()
		channel.exchange_declare(exchange=RMQ_EXCHANGE, exchange_type='topic')
		fetcher_q = channel.queue_declare(queue=RMQ_FETCH_WEATHER_QUEUE, exclusive=False)
		fetcher_queue_name = fetcher_q.method.queue
		channel.queue_bind(exchange=RMQ_EXCHANGE, queue=fetcher_queue_name, routing_key=RMQ_FETCH_WEATHER_ROUTE_KEY)
		print(gettime()," FETCHER: Connected to messaging bus")

	except Exception as ex:
		channel=None
		fetcher_queue_name=None
		print (gettime(), " FETCHER: Failed to connect to messaging bus. Stack="+str(traceback.format_exception_only(type(ex), ex)))
	return channel, fetcher_queue_name

def main():

	# connect to messaging bus
	while (1):
		print (gettime(), " FETCHER: Attempting to connect to messaging bus")
		channel, fetcher_queue = fnConnectToMsgingBus()
		if isinstance(channel, pika.adapters.blocking_connection.BlockingChannel):
			break
		time.sleep(1)

	try:
		channel.basic_consume(callback, queue=fetcher_queue, no_ack=True)
		channel.start_consuming()
		#callback(None,None,None,"FETCHER:listening for messages from messaging bus")
	except Exception:
		#callback(None,None,None,"FETCHER: Exception raised when listening for logs. Stack="+traceback.format_exc())
		print (gettime(), " FETCHER: Exception raised when listening for logs. Stack=", traceback.format_exc())
	finally:
		channel.close()

	print (gettime(), " FETCHER: Closing down")
	# end of logger process

if __name__=="__main__":
	main()
