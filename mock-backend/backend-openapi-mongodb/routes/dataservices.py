from src import mongoapi2


def get_monthly_leaderboard(limit: int, location: str, metric: str, age_lower:str = "0", age_upper: str = "100", gender:str = "", desc:bool = True):
    """Route to /leaderboard.

    Args:
      limit: Number to limit response by.
      location: Location to retrieve leaderboard from.
      metric: Leaderboard metric.

    Returns:
      result: List of dictionaries containing [score], [name] and [phoneNo]
      status_code: int
    """

    # Route
    result = mongoapi2.get_monthly_leaderboard(limit, location, metric, int(age_lower), int(age_upper), gender, desc)

    # Status
    if result:
        status_code = 200
    else:
        result = None
        status_code = 404
    return result, status_code


def get_leaderboard_by_dates_gyms(
    limit: int,
    metric: str,
    start_date: str = None,
    end_date: str = None,
    gyms: list = None,
):
    """Route to /leaderboard/v2.

    Args:
      limit: Number to limit response by.
      metric: Leaderboard metric.
      body: Body containing startDate (str), endDate (str) and gyms (List[str]).

    Returns:
      result: List[dict] containing [score], [name] and [user_id].
      status_code: int
    """
    # Remove arguements with None values.
    kwargs = locals()
    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    # Route
    result = mongoapi2.get_leaderboard_by_dates_gyms(**kwargs)

    # Status
    if result:
        status_code = 200
    else:
        result = None
        status_code = 404

    return result, status_code


def get_user_metrics_by_dates_gyms(
    user_id: str,
    start_date: str = None,
    end_date: str = None,
    gyms: list = None,
):
    """Route to /leaderboard/user
    Args:
      limit: Number to limit response by.
      metric: Leaderboard metric.
      body: Body containing startDate (str), endDate (str) and gyms (List[str]).

    Returns:
      result: List[dict] containing [score], [name] and [user_id].
      status_code: int
    """
    # Remove arguements with None values.
    kwargs = locals()
    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    # Route
    result = mongoapi2.get_user_metrics_by_dates_gyms(**kwargs)

    # Status
    if result:
        status_code = 200
    else:
        result = None
        status_code = 404

    return result, status_code


def post_leaderboard_computation(user: str, body: dict):
    """Route to /leaderboard/dispatch.
    Args:
      body (dict): {
        "user_id": Valid user_id.
        "location": Valid location.
      }

    Returns:
      result: List[dict] containing [score], [name] and [user_id].
      status_code: int
    """

    # Dispatch
    result = mongoapi2.dispatch_leaderboard_computation(**body)

    # Status
    if result:
        status_code = 201
    else:
        result = None
        status_code = 500

    return result, status_code


def ban_leaderboard_user(body: dict):
    result = mongoapi2.ban_leaderboard_user(**body)
    # Status
    if result:
        status_code = 201
    else:
        result = None
        status_code = 500


def ban_leaderboard_user_mongo(body: dict):
    result = mongoapi2.ban_leaderboard_user_mongo(**body)

    if result:
        status_code = 201
    else:
        result = {'error': 'error banning user'}
        status_code = 500

    return result, status_code


def fetch_banned_leaderboard_users_mongo(location: str):
    result = mongoapi2.fetch_banned_leaderboard_users_mongo(location)

    if result:
        status_code = 201
    else:
        result = {'error', 'error getting banned users'}
        status_code = 400

    return result, status_code


def unban_leaderboard_user_mongo(body: dict):
    result = mongoapi2.unban_leaderboard_user_mongo(**body)

    if result:
        status_code = 201
    else:
        result = {'error': 'error unbanning user'}
        status_code = 400

    return result, status_code


def reset_leaderboard_username(body: dict):
    result = mongoapi2.reset_username(**body)
    # Status
    if result:
        status_code = 201
    else:
        result = None
        status_code = 500


def leaderboard_metrics(active: bool = True, location: str = "all", recurring: bool = False):
    """Routes /leaderboard_metrics

      Args:
        location: Requested gym location (default: all)
        active: True or False (default True)
      Returns:
        leaderboard_metrics base on filter in query parameter [active or location]
      """
    try:
        result = mongoapi2.leaderboard_metrics(
            location=location, active=active, recurring=recurring)
        return result, 200
    except:
        result = {}
        return result, 400


def post_leaderboard_metrics(body: dict):
    # TODO: Add in comments
    """
        Route: /leaderboard_metrics [POST]

        Args:
            body
    """
    try:
        result = mongoapi2.create_leaderboard_metrics(body)
        return result, 201
    except Exception as e:
        return str(e), 400


def put_leaderboard_metrics(body: dict):
    # TODO: Add in comments
    """
        Route: /leaderboard_metrics [POST]

        Args:
            body
    """
    try:
        result = mongoapi2.update_leaderboard_metrics(body)
        return result, 201
    except Exception as e:
        return str(e), 400

def delete_leaderboard_metrics(campaignId : str):
    """
    # TODO: Add in comments
        Route: /leaderboard_metrics [POST]

        Args:
            body
    """
    try: 
        result = mongoapi2.delete_leaderboard_metrics(campaignId)
        return result, 200
    except Exception as e:
        return str(e), 400

def recalculate_leaderboard_metrics(body: dict):
    """
    # TODO: Add in comments
        Route: /leaderboard/recalculate[POST]

        Args:
            body
    """
    try: 
        result = mongoapi2.dispatch_leaderboard_computation(recalculate_leaderboard=True)
        return result, 200
    except Exception as e:
        return str(e), 400