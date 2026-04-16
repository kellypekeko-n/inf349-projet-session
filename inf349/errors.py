from flask import jsonify


class APIError(Exception):
    def __init__(self, message, status_code=400, payload=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}

    def to_dict(self):
        return dict(self.payload)


class ValidationError(APIError):
    def __init__(self, errors, status_code=422):
        super().__init__("Validation failed", status_code)
        self.errors = errors


class NotFoundError(APIError):
    def __init__(self, field="order", code="not-found", message="La ressource demandée est introuvable."):
        super().__init__(message, 404)
        self.field = field
        self.code = code


class BusinessError(APIError):
    def __init__(self, message, code="business-error", status_code=422, field="order"):
        super().__init__(message, status_code)
        self.code = code
        self.field = field


def format_validation_errors(errors):
    formatted = {}

    for error in errors:
        field = error["field"]
        if field not in formatted:
            formatted[field] = {
                "code": error["code"],
                "name": error["name"],
            }

    return formatted


def handle_validation_error(error):
    response = jsonify({"errors": format_validation_errors(error.errors)})
    response.status_code = error.status_code
    return response


def handle_not_found_error(error):
    response = jsonify({
        "errors": {
            error.field: {
                "code": error.code,
                "name": error.message,
            }
        }
    })
    response.status_code = error.status_code
    return response


def handle_business_error(error):
    response = jsonify({
        "errors": {
            error.field: {
                "code": error.code,
                "name": error.message,
            }
        }
    })
    response.status_code = error.status_code
    return response


def handle_api_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response