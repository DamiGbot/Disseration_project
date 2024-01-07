from sklearn.metrics.pairwise import cosine_similarity

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
