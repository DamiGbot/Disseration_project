from flask import Flask, jsonify
from services.preprcessing import read_and_preprocess_student_data, read_and_preprocess_supervisor_data
from services.embeddings import get_embeddings
from celery_config import make_celery
from sklearn.metrics.pairwise import cosine_similarity

import json

app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379/0',
    CELERY_RESULT_BACKEND='redis://localhost:6379/0'
)

celery = make_celery(app)

@app.route('/') 
def hello_world():
    return 'Hello, World!'

@app.route('/process-data', methods=['GET', 'POST'])
def process_data():
    # Example file paths - adjust as needed
    student_file_path = '../../List_of_Topics.json'
    supervisor_file_path = '../../List_of_research_areas.json'

    # Preprocess the data
    students_df = read_and_preprocess_student_data(student_file_path)
    supervisors_df = read_and_preprocess_supervisor_data(supervisor_file_path)

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

    # Return clustering results along with student and supervisor data
    return jsonify({"suggestion": supervisor_suggestions })


def calculate_individual_compatibility(student, supervisor):
    # Calculate the compatibility between a student and a supervisor
    return cosine_similarity([student['embeddings']], [supervisor['embeddings']])[0][0]

def suggest_supervisors_for_students(students_df, supervisors_df):    
    student_supervisor_suggestions = {}
    supervisor_suggestion_count = {sup_id: 0 for sup_id in supervisors_df['id']}

    for _, student in students_df.iterrows():
        # Calculate compatibility with each supervisor
        compatibilities = {
            supervisor['id']: calculate_individual_compatibility(student, supervisor)
            for _, supervisor in supervisors_df.iterrows()
        }

        # Sort supervisors by compatibility and filter out over-suggested ones
        sorted_and_filtered_supervisors = [
            sup_id for sup_id in sorted(compatibilities, key=compatibilities.get, reverse=True)
            if supervisor_suggestion_count[sup_id] < 2 * int(supervisors_df[supervisors_df['id'] == sup_id]['availableSlot'].iloc[0])
        ][:5]

        # Add student details and top 5 supervisors to the student's suggestions
        student_supervisor_suggestions[student['id']] = {
            'studentTopic': student['studentTopic'],
            'numberOfSuggestions': len(sorted_and_filtered_supervisors),
            'supervisorSuggestions': []
        }
        for sup_id in sorted_and_filtered_supervisors:
            student_supervisor_suggestions[student['id']]['supervisorSuggestions'].append({
                'supervisorId': sup_id,
                'compatibilityScore': compatibilities[sup_id],
                'researchArea': supervisors_df[supervisors_df['id'] == sup_id]['researchArea'].iloc[0],
                'availableSlot': int(supervisors_df[supervisors_df['id'] == sup_id]['availableSlot'].iloc[0])  # Convert to Python int
            })
            supervisor_suggestion_count[sup_id] += 1

    return student_supervisor_suggestions


if __name__ == '__main__':
    app.run(debug=True)
