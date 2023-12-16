from app.celery_config import celery
from app.services.embeddings import get_embeddings

@celery.task
def async_get_embeddings(text_series):
    return get_embeddings(text_series)
