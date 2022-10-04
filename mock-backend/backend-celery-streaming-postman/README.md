## backend-celery-streaming-postman
Ingestion pipelines:
- stage-1 ingestion: `stream`
- stage-2 ingestion: `save`
- stage-3 ingestion: `process`


`backend-celery-streaming-postman` listens to the `stream` queue

- Forwards the celery task to the appropriate ingestion worker.