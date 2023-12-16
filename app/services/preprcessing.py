import pandas as pd
import numpy as np

def read_and_preprocess_student_data(filepath):
    """
    Reads and preprocesses supervisor data from a JSON file.

    :param filepath: Path to the supervisor data JSON file.
    :return: Preprocessed DataFrame.
    """
    # Read JSON file into DataFrame
    students_df = pd.read_json(filepath)

    # Replace newline characters with spaces in 'supervisorInterest'
    if 'studentTopic' in students_df.columns:
        students_df['studentTopic'] = students_df['studentTopic'].str.replace('\n', ', ', regex=False)

    return students_df

def read_and_preprocess_supervisor_data(filepath):
    """
    Reads and preprocesses supervisor data from an Excel file.

    :param filepath: Path to the supervisor data Excel file.
    :return: Preprocessed DataFrame.
    """
    supervisors_df = pd.read_json(filepath)

    # Replace newline characters with spaces in 'supervisorInterest'
    if 'researchArea' in supervisors_df.columns:
        supervisors_df['researchArea'] = supervisors_df['researchArea'].str.replace('\n', ', ', regex=False)

    return supervisors_df
