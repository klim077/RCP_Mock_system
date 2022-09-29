import random
from flask import Response
from bson.json_util import dumps
from better_profanity import profanity



def makeResponse(response, status, headers=None):
    """Helper function to make Response object

    Args:
      response: str response is sent as is, list or dict is sent as json
      status: status code
      headers: custom header
    Return:
      Response object
    """

    # Guard
    if (
        not isinstance(response, str)
        and not isinstance(response, list)
        and not isinstance(response, dict)
    ):
        raise ValueError("response is not str, list or dict")

    if isinstance(response, str):
        return Response(response=response, status=status, headers=headers)

    if isinstance(response, list) or isinstance(response, dict):
        return Response(
            response=dumps(response),
            status=status,
            headers=headers,
            content_type="application/json",
        )

    return


###
# Random Username Helpers.
###

# Load nouns.
with open("src/utils/assets/nouns.txt") as file:
    noun_list = file.read().splitlines()


# Load adjectives.
with open("src/utils/assets/adjectives.txt") as file:
    adj_list = file.read().splitlines()


def gen_random_user_display_name():
    """Generates random user_display_name from a set of nouns/adj.

    Credits:
        Thanks LiYang and Chin Hiong!
        https://github.com/moby/moby/blob/master/pkg/namesgenerator/names-generator.go

    Returns:
        Random user_display_name.
    """
    return (
        random.choice(adj_list).capitalize()
        + random.choice(noun_list).capitalize()
        + str(random.randint(0, 999))
    )

def is_profane(string: str) -> bool:
    """Checks if a word is profane.

    Args:
        string(str): Input String.
    Returns:
        (bool): True/False if the input string is profane.
    """

    return profanity.contains_profanity(string)
