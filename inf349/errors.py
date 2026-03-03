from flask import jsonify

class APIError(Exception):
    """Base API error class"""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

class ValidationError(APIError):
    """Validation error"""
    def __init__(self, errors, status_code=422):
        self.errors = errors
        super().__init__("Validation failed", status_code)

class NotFoundError(APIError):
    """Resource not found error"""
    def __init__(self, message="Resource not found"):
        super().__init__(message, 404)

class BusinessError(APIError):
    """Business logic error"""
    def __init__(self, message, code="business-error", status_code=422):
        super().__init__(message, status_code)
        self.code = code

def handle_validation_error(e):
    """Handle validation errors"""
    response = jsonify({'errors': format_validation_errors(e.errors)})
    response.status_code = e.status_code
    return response

def handle_api_error(e):
    """Handle general API errors"""
    response = jsonify(e.to_dict())
    response.status_code = e.status_code
    return response

def handle_not_found_error(e):
    """Handle not found errors"""
    response = jsonify({'message': e.message})
    response.status_code = e.status_code
    return response

def format_validation_errors(errors):
    """Format validation errors according to API specification"""
    formatted = {}
    
    for error in errors:
        field = error['field']
        if field not in formatted:
            formatted[field] = {
                'code': error['code'],
                'name': error['name']
            }
    
    return formatted
