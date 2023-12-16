import time
from celery import Celery



class Config:
	CELERY_BROKER_URL =	'redis://127.0.0.1:6379/0'
	CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/"
	CELERY_IMPORTS = ("app.tasks")

	# CELERY_TASK_ROUTES = {
  #   'tasks.*': {
  #       'queue': 'high_priority',
  #   },
  #   'low_priority_tasks.*': {
  #       'queue': 'low_priority',
  #   },
	# }

settings = Config()

celery_app = Celery('app')
celery_app.config_from_object(settings, namespace="CELERY")


@celery_app.task(name="tasks")
def sleep_test():
    try:
      time.sleep(3)
      print("xxxxxxxx")
      print("xxxxxxxx")
      print("xxxxxxxx")
      print("xxxxxxxx")
      print("xxxxxxxx")
    except Exception as e:
      # call endpoint here
      # { e}
      raise e
    
@celery_app.task(name="tasks")
def embed():
    try:
      time.sleep(3)
      print("xxxxxxxx")
    except Exception as e:
      # call endpoint here
      # { e}
      raise e
