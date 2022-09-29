from src import mongoapi2
from flask import Response


def post_feedback(body: dict):
    """Routes /feedback
    Args:
        body: request body
    Returns:
        nothing
    """

    result = mongoapi2.post_feedback(body)

    if result:
        status_code = 201
    else:
        status_code = 500

    return result, status_code

def post_feedbackv2(body: dict):
    """Routes /feedback
    Args:
        body: request body
    Returns:
        nothing
    """

    result = mongoapi2.post_feedbackv2(body)

    if result:
        status_code = 201
    else:
        status_code = 500

    return result, status_code

def post_feedback_question(body: dict):
    """Routes /feedback
    Args:
        body: request body
    Returns:
        nothing
    """

    result = mongoapi2.post_feedback_question(body)

    if result:
        status_code = 201
    else:
        status_code = 500

    return result, status_code

def get_feedback_question(type):
    """Routes /feedback
    Args:
        body: request body
    Returns:
        nothing
    """

    result = mongoapi2.get_feedback_question(type)

    if result:
        status_code = 201
    else:
        status_code = 500

    return result, status_code
    