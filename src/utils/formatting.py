from typing import Union

def create_response_message(status: str, response: Union[dict[str, str], str]) -> str:
    """
    Purpose: Create a response message.
    Args:
        status: str - The status of the message.
        response: dict[str, str] | str - The response to be returned.
    """
    message = {
        "status": status,
        "response": response
    }
    return message