from functools import wraps
from flask import request, jsonify
from db import check_api_key, get_user_from_api_key
import logging


def require_api_key(f):
    """Decorator to require and validate API key in Authorization header."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Retrieve Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            logging.warning("Authorization header is missing.")
            return jsonify({"error": "Unauthorized. Missing API key."}), 401

        if not auth_header.startswith('Bearer '):
            logging.warning(f"Malformed Authorization header: {auth_header}")
            return jsonify({"error": "Unauthorized. Invalid header format."}), 401

        # Extract API Key from the header
        api_key = auth_header.split(' ')[1].strip()
        if not api_key:
            logging.warning("Empty API key extracted from Authorization header.")
            return jsonify({"error": "Unauthorized. Empty API key."}), 401

        try:
            # Validate the API key
            validation_result = check_api_key(api_key)
            if not validation_result['valid']:
                logging.error(f"Invalid API Key: {api_key}. Reason: {validation_result['error']}")
                return jsonify({"error": f"Unauthorized. {validation_result['error']}"}), 401

            # Retrieve associated user from API key
            user = get_user_from_api_key(api_key)
            if not user:
                logging.error(f"Valid API key but no user found: {api_key}")
                return jsonify({"error": "Unauthorized. User not found."}), 401

            # Add user to kwargs for use in the endpoint
            kwargs['user'] = user
            return f(*args, **kwargs)

        except Exception as e:
            logging.critical(f"Unexpected error during API key validation: {str(e)}")
            return jsonify({"error": "Internal Server Error. Please try again later."}), 500

    return decorated_function
