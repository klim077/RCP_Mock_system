from celery import Celery


celeryApp = Celery(
    "sendWorkout",
    broker='amqp://user:bitnami@rabbitmq',
    backend='rpc://',
)


def sendGetRequest(url):
    print(f'gwWorker sendGetRequest({url})')
    task = celeryApp.send_task('getRequest', (url,))
    print(f'gwWorker sendGetRequest waiting for reply')
    result = task.get()
    print(f'gwWorker sendGetRequest {result}')
    return result


def sendPostRequest(url, body):
    print(f'gwWorker sendPostRequest({url})')
    task = celeryApp.send_task('sendWorkout', (url, body))
    print(f'gwWorker sendPostRequest waiting for reply')
    result = task.get()
    print(f'gwWorker sendPostRequest {result}')
    return result
