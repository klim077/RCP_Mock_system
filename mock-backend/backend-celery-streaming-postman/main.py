from config import *
from helpers import *

time.sleep(30)

streaming_consumer_pipelines = {
    "bodyweight":{ 
        "queue": "bodyweight_queue",
        "task":"bodyweightComputation"
    },
    "bike":{
        "queue": "spinning_bike_queue",
        "task":"spinningBikeComputation"
    },
    "treadmill":{
        "queue": "treadmill_streaming_queue",
        "task":"stream_treadmill_exercise"
    },
    "weighingscale":{
        "queue": "compute_queue",
        "task":"computeWeighingScaleMetrics"
    },
    "weightstack":{
        "queue": "weightstack_queue",
        "task":"weightstackComputation"
    },
    "rower":{
        "queue": "rower_queue",
        "task":"rowerComputation"
    },
}

##### Callbacks #####

# e.g.
#  ch:<BlockingChannel impl=<Channel number=1 OPEN conn=<SelectConnection OPEN transport=<pika.adapters.utils.io_services_utils._AsyncPlaintextTransport object at 0x7f888039f0d0> params=<ConnectionParameters host=rabbitmq port=5672 virtual_host=/ ssl=False>>>>
#  method:<Basic.Deliver(['consumer_tag=ctag1.4f0bb462dc15451d8c0f90b0812c077e', 'delivery_tag=3', 'exchange=', 'redelivered=False', 'routing_key=update'])>
#  properties:<BasicProperties(['delivery_mode=2'])>
def stream_callback(ch, method, properties, body): # Stage 1
    try:
        payload_data = body.decode('utf-8')
        logger.info(payload_data)
        payloadData = json.loads(payload_data)
        logger.info(payloadData)
        logger.info(f"payloadData:{payloadData}")
        machineId = payloadData["machineId"]

        logger.info(f" [x] Received streaming task for machine: {machineId}")
        machine_type = getMachineType(machineId)

        celeryApp.send_task(
            streaming_consumer_pipelines[machine_type]["task"], 
            queue=streaming_consumer_pipelines[machine_type]["queue"], 
            args=(payload_data,)
        )
        ch.basic_ack(delivery_tag = method.delivery_tag)
        logger.info(f'dispatching {streaming_consumer_pipelines[machine_type]["task"]} task')
    
    except Exception as e:
        ## removes bad message from queue so queue does not jam upon error
        ch.basic_ack(delivery_tag = method.delivery_tag)
        logger.error(e)


    
def save_callback(ch, method, properties, body): # Stage 2
    logger.info(" [x] Received %r" % body)
    logger.debug(f" ch:{ch}")
    logger.debug(f" method:{method}")
    logger.debug(f" properties:{properties}")
    ch.basic_ack(delivery_tag = method.delivery_tag)

def process_callback(ch, method, properties, body): # Stage 3
    logger.info(" [x] Received %r" % body)
    logger.debug(f" ch:{ch}")
    logger.debug(f" method:{method}")
    logger.debug(f" properties:{properties}")
    ch.basic_ack(delivery_tag = method.delivery_tag)

producer_queues_to_callbacks = {
    "stream":stream_callback, # Stage 1
    # "save":save_callback, # Stage 2
    # "prcoess":process_callback # Stage 3
}


def main():
    with RMQ(rabbitmq_ip, rabbitmq_port, rabbitmq_user, rabbitmq_pw) as conn:
        channel = conn.channel()
        for queue,callback in producer_queues_to_callbacks.items():
            channel.queue_declare(queue=queue,durable=True)
            channel.basic_consume(queue=queue, on_message_callback=callback)

        print(' [*] Waiting for messages. To exit press CTRL+C')
        channel.start_consuming()


if __name__ == '__main__':
    main()