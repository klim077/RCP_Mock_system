## backend-celery-saving-postman
Ingestion pipelines:
- stage-1 ingestion: `stream`
- stage-2 ingestion: `save`
- stage-3 ingestion: `process`


`backend-celery-saving-postman` listens to the `save` queue

- Forwards the celery task to the appropriate ingestion worker.