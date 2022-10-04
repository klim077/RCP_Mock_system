from config import *
from helpers import *

time.sleep(30)

saving_consumer_pipelines = {
    "bodyweight":{ 
        "queue": "bodyweight_saving_queue",
        "task":"save_bodyweight_exercise"
    },
    "bike":{
        "queue": "spinningbike_saving_queue",
        "task":"save_spinningbike_exercise"
    },
    "treadmill":{
        "queue": "treadmill_saving_queue",
        "task":"save_treadmill_exercise"
    },
    "weighingscale":{
        "queue": "weighingscale_saving_queue",
        "task":"save_weighingscale_bodymetrics"
    },
    "weightstack":{
        "queue": "weightstack_saving_queue",
        "task":"save_weightstack_exercise"
    },
    "bpm":{
        "queue": "bpm_saving_queue",
        "task":"save_bpm_bodymetrics"
    },
    "rower":{
        "queue": "rower_saving_queue",
        "task":"save_rower_exercise"
    },
}

##### Callbacks #####

# e.g.
#  ch:<BlockingChannel impl=<Channel number=1 OPEN conn=<SelectConnection OPEN transport=<pika.adapters.utils.io_services_utils._AsyncPlaintextTransport object at 0x7f888039f0d0> params=<ConnectionParameters host=rabbitmq port=5672 virtual_host=/ ssl=False>>>>
#  method:<Basic.Deliver(['consumer_tag=ctag1.4f0bb462dc15451d8c0f90b0812c077e', 'delivery_tag=3', 'exchange=', 'redelivered=False', 'routing_key=update'])>
#  properties:<BasicProperties(['delivery_mode=2'])>
def stream_callback(ch, method, properties, body): # Stage 1
        logger.info(" [x] Received %r" % body)
        logger.debug(f" ch:{ch}")
        logger.debug(f" method:{method}")
        logger.debug(f" properties:{properties}")
        ch.basic_ack(delivery_tag = method.delivery_tag)

def save_callback(ch, method, properties, body): # Stage 2
    try:
        machineId = body.decode('utf-8')
        logger.info(f" [x] Received saving task for machine: {machineId}")
        data = getRedisChannelDict(machineId)
        payload_data = dumps(data)

        type = data["type"]
        celeryApp.send_task(
            saving_consumer_pipelines[type]["task"], 
            queue=saving_consumer_pipelines[type]["queue"], 
            args=(payload_data,)
        )
        ch.basic_ack(delivery_tag = method.delivery_tag)
        logger.info(f'dispatching {saving_consumer_pipelines[type]["task"]} task')
    
    except Exception as e:
        ## removes bad message from queue so queue does not jam upon error
        ch.basic_ack(delivery_tag = method.delivery_tag)
        logger.error(e)

def process_callback(ch, method, properties, body): # Stage 3
        logger.info(" [x] Received %r" % body)
        logger.debug(f" ch:{ch}")
        logger.debug(f" method:{method}")
        logger.debug(f" properties:{properties}")
        ch.basic_ack(delivery_tag = method.delivery_tag)


producer_queues_to_callbacks = {
    # "stream":stream_callback, # Stage 1
    "save":save_callback, # Stage 2
    # "process":process_callback # Stage 3
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