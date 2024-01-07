import time
from celery import Celery
import os
import openai
from openai.embeddings_utils import get_embedding
from openai.error import OpenAIError, RateLimitError
import tiktoken
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


class Config:
	CELERY_BROKER_URL =	'redis://redis:6379/0'
	CELERY_RESULT_BACKEND = "redis://redis:6379/0"
	CELERY_IMPORTS = ("app.tasks")

settings = Config()

celery_app = Celery('app')
celery_app.config_from_object(settings, namespace="CELERY")


@celery_app.task(name="tasks.sleep")
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
    
@celery_app.task(name="tasks.emded")
def embed(data):
    try:
      # Convert the JSON data to pandas DataFrame
      students_df = pd.DataFrame(data['student'])
      supervisors_df = pd.DataFrame(data['supervisor'])

      # Preprocess the data
      students_df['studentTopic'] = students_df['studentTopic'].str.replace('\n', ', ', regex=False)
      supervisors_df['researchArea'] = supervisors_df['researchArea'].str.replace('\n', ', ', regex=False)
      # Define the number of examples you want to process
      number_of_student_examples = students_df.shape[0]
      number_of_supervisor_examples = supervisors_df.shape[0]

      # Check if we have enough data to sample, if not take the maximum possible
      number_of_student_examples = min(number_of_student_examples, len(students_df))
      number_of_supervisor_examples = min(number_of_supervisor_examples, len(supervisors_df))

      # Sample a subset of your dataframes
      students_sampled = students_df.sample(n=number_of_student_examples, random_state=1)
      supervisors_sampled = supervisors_df.sample(n=number_of_supervisor_examples, random_state=1)

      # Apply the get_embeddings function to your sampled text series.
      students_sampled['embeddings'] = get_embeddings(students_sampled['studentTopic'])
      supervisors_sampled['embeddings'] = get_embeddings(supervisors_sampled['researchArea'])
      
      # Call the function to suggest supervisors for students
      supervisor_suggestions = suggest_supervisors_for_students(students_sampled, supervisors_sampled)
      # print(supervisor_suggestions)
      return supervisor_suggestions
    except Exception as e:
      logger.error(f"Error in task: {e}")
      return {'error': str(e)}


# Configuration
openai.api_key = os.getenv('OPENAI_API_KEY')  # Set your API key here
encoding = tiktoken.get_encoding("cl100k_base")
embedding_model = "text-embedding-ada-002"
max_tokens = 8000  # Set to your chosen maximum token count

def get_embeddings(text_series):
    embeddings = []
    backoff_time = 1  # Start with a 1 second wait, will increase on each retry

    for text in text_series:
        while True:
            try:
                # Ensure the text is within the token limit using tiktoken
                encoded_text = encoding.encode(text)
                if len(encoded_text) > max_tokens:
                    print(f"Text is too long ({len(encoded_text)} tokens), truncating.")
                    text = encoding.decode(encoded_text[:max_tokens])
                
                # Get the embedding using OpenAI API
                embedding = get_embedding(text, engine=embedding_model, max_tokens=max_tokens)
                embeddings.append(embedding)
                # Reset backoff time if successful
                backoff_time = 1
                break  # Break out of the retry loop if successful
            except RateLimitError as e:
                print("Hit rate limit, backing off...")
                time.sleep(backoff_time)
                backoff_time *= 2  # Exponential back-off
            except OpenAIError as e:
                # Handle other possible exceptions from the OpenAI API
                print(f"An error occurred: {e}")
                break  # Break out of the loop if there's an unknown error
    return embeddings

def calculate_individual_compatibility(student, supervisor):
    # Calculate the compatibility between a student and a supervisor
    return cosine_similarity([student['embeddings']], [supervisor['embeddings']])[0][0]

# def suggest_supervisors_for_students(students_df, supervisors_df):    
#     student_supervisor_suggestions = {}
#     supervisor_suggestion_count = {sup_id: 0 for sup_id in supervisors_df['id']}

#     for _, student in students_df.iterrows():
#         # Calculate compatibility with each supervisor
#         compatibilities = {
#             supervisor['id']: calculate_individual_compatibility(student, supervisor)
#             for _, supervisor in supervisors_df.iterrows()
#         }

#         # Sort supervisors by compatibility and filter out over-suggested ones
#         sorted_and_filtered_supervisors = [
#             sup_id for sup_id in sorted(compatibilities, key=compatibilities.get, reverse=True)
#             if supervisor_suggestion_count[sup_id] < 10 * int(supervisors_df[supervisors_df['id'] == sup_id]['availableSlot'].iloc[0])
#         ][:5]

#         # Add student details and top 5 supervisors to the student's suggestions
#         student_supervisor_suggestions[student['id']] = {
#             'studentTopic': student['studentTopic'],
#             'numberOfSuggestions': len(sorted_and_filtered_supervisors),
#             'supervisorSuggestions': []
#         }
#         for sup_id in sorted_and_filtered_supervisors:
#             student_supervisor_suggestions[student['id']]['supervisorSuggestions'].append({
#                 'supervisorId': sup_id,
#                 'compatibilityScore': compatibilities[sup_id],
#                 'researchArea': supervisors_df[supervisors_df['id'] == sup_id]['researchArea'].iloc[0],
#                 'availableSlot': int(supervisors_df[supervisors_df['id'] == sup_id]['availableSlot'].iloc[0])  # Convert to Python int
#             })
#             supervisor_suggestion_count[sup_id] += 1

#     return student_supervisor_suggestions



def suggest_supervisors_for_students(students_df, supervisors_df):
    student_supervisor_suggestions = {}
    supervisor_suggestion_count = {sup_id: 0 for sup_id in supervisors_df['id']}

    for _, student in students_df.iterrows():
        # Calculate compatibility with each supervisor
        compatibilities = {
            supervisor['id']: calculate_individual_compatibility(student, supervisor)
            for _, supervisor in supervisors_df.iterrows()
        }

        # Sort supervisors by compatibility
        sorted_supervisors = sorted(compatibilities, key=compatibilities.get, reverse=True)

        student_supervisor_suggestions[student['id']] = {
            'studentTopic': student['studentTopic'],
            'supervisorSuggestions': []
        }

        for sup_id in sorted_supervisors:
            if supervisor_suggestion_count[sup_id] < 10 * int(supervisors_df[supervisors_df['id'] == sup_id]['availableSlot'].iloc[0]):
                # Add supervisor suggestion
                student_supervisor_suggestions[student['id']]['supervisorSuggestions'].append({
                    'supervisorId': sup_id,
                    'compatibilityScore': compatibilities[sup_id],
                    'researchArea': supervisors_df[supervisors_df['id'] == sup_id]['researchArea'].iloc[0],
                    'availableSlot': int(supervisors_df[supervisors_df['id'] == sup_id]['availableSlot'].iloc[0])
                })
                supervisor_suggestion_count[sup_id] += 1

                # Break if five supervisors have been suggested
                if len(student_supervisor_suggestions[student['id']]['supervisorSuggestions']) == 5:
                    break

        # If less than 5 supervisors suggested, fill in with available supervisors
        if len(student_supervisor_suggestions[student['id']]['supervisorSuggestions']) < 5:
            for sup_id in supervisor_suggestion_count.keys():
                if supervisor_suggestion_count[sup_id] < 10 * int(supervisors_df[supervisors_df['id'] == sup_id]['availableSlot'].iloc[0]):
                    student_supervisor_suggestions[student['id']]['supervisorSuggestions'].append({
                        'supervisorId': sup_id,
                        'compatibilityScore': compatibilities.get(sup_id, 0),
                        'researchArea': supervisors_df[supervisors_df['id'] == sup_id]['researchArea'].iloc[0],
                        'availableSlot': int(supervisors_df[supervisors_df['id'] == sup_id]['availableSlot'].iloc[0])
                    })
                    supervisor_suggestion_count[sup_id] += 1

                    if len(student_supervisor_suggestions[student['id']]['supervisorSuggestions']) == 5:
                        break

    return student_supervisor_suggestions


    