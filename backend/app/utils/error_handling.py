from fastapi import HTTPException


def exceptions(code, message = None):
    match code:
        case 404:
            HTTPException(status_code=404, details='Not found' or message)
        