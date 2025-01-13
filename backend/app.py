import os
import tempfile
import logging
import atexit
import shutil
import json
from datetime import datetime
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_session import Session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from auth import require_api_key
from db import (
    initialize_database, register_user_in_db, authenticate_user_in_db,
    save_sentiment_to_db, fetch_sentiment_from_db, update_database_schema,
    fetch_last_sentiment_from_db, save_sentiment_results_to_db, generate_api_key, 
    fetch_all_sentiments_from_db, check_session_validity, check_user_exists_in_db, 
    migrate_database
)
from sentiment_analysis import process_video_sentiment
from dropbox_storage import upload_to_dropbox, get_dropbox_client

# Constants and Configuration
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}
load_dotenv()

# Initialize Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize Flask Application
app = Flask(__name__)

# Main Configuration
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24).hex())
app.config.update(
    # Environment and Debug Settings
    ENV=os.getenv("FLASK_ENV", "production"),
    DEBUG=os.getenv("FLASK_DEBUG", "False").lower() == "true",
    
    # File Upload Settings
    UPLOAD_FOLDER=os.getenv("UPLOAD_FOLDER", '/home/Bastian/development/uploads'),
    
    # Session Settings
    SESSION_TYPE='filesystem',
    SESSION_PERMANENT=False,
    PERMANENT_SESSION_LIFETIME=3600,
    SESSION_FILE_DIR=tempfile.gettempdir(),
    SESSION_FILE_THRESHOLD=500,
    SESSION_FILE_MODE=384,
    SESSION_COOKIE_NAME='flask_session_cookie',
    SESSION_COOKIE_SECURE=True,  # Set to True in production
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Strict',
    
    # JSON Configuration
    JSON_SORT_KEYS=False  # Preserve JSON response order
)

# Initialize Extensions
Session(app)

# CORS Configuration
CORS(app, resources={
    r"/*": {
        "origins": ["https://sensiwithme.my.id"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-API-Key"],
        "supports_credentials": True,
        "expose_headers": ["Content-Type", "X-API-Key"]
    }
})

# Create Upload Directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Request Handlers
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    """Handle OPTIONS requests for CORS preflight."""
    return app.make_default_options_response()

@app.after_request
def after_request(response):
    """Add CORS headers to responses."""
    origin = request.headers.get('Origin')
    allowed_origins = ["https://sensiwithme.my.id"]
    
    if origin in allowed_origins:
        response.headers.update({
            'Access-Control-Allow-Origin': origin,
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-API-Key',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Expose-Headers': 'Content-Type, X-API-Key'
        })
    
    if response.mimetype == 'application/json':
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
    
    return response

@app.route('/test', methods=['GET'])
def test_cors():
    """Test endpoint for CORS configuration."""
    logging.info("Test CORS endpoint hit successfully.")
    return jsonify({"message": "CORS settings are working properly"}), 200

# Cleanup Function
def cleanup_uploads():
    """Clean up temporary upload directory on application exit."""
    try:
        shutil.rmtree(app.config['UPLOAD_FOLDER'])
        logging.info("Temporary uploads cleaned up successfully.")
    except Exception as e:
        logging.warning(f"Failed to clean up temporary uploads: {str(e)}")

# Cleanup on exit
def cleanup_uploads():
    try:
        shutil.rmtree(app.config['UPLOAD_FOLDER'])
        logging.info("Temporary uploads cleaned up successfully.")
    except Exception as e:
        logging.warning(f"Failed to clean up temporary uploads: {str(e)}")
atexit.register(cleanup_uploads)

# Helper Functions
def allowed_file(filename):
    """Check if file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/dropbox/authorize', methods=['GET'])
def authorize_dropbox():
    """Generate Dropbox authorization URL."""
    try:
        app_key = os.getenv('DROPBOX_APP_KEY')
        app_secret = os.getenv('DROPBOX_APP_SECRET')
        redirect_uri = os.getenv('DROPBOX_REDIRECT_URI')

        if not all([app_key, app_secret, redirect_uri]):
            return jsonify({"error": "Missing Dropbox credentials or redirect URI"}), 500

        flow = dropbox.oauth.DropboxOAuth2Flow(
            consumer_key=app_key,
            consumer_secret=app_secret,
            redirect_uri=redirect_uri,
            session=session,
            csrf_token_session_key='dropbox-auth-csrf-token',
            token_access_type='offline'
        )
        
        authorize_url = flow.start()
        return jsonify({"authorize_url": authorize_url}), 200
    except Exception as e:
        logging.error(f"Error generating Dropbox authorization URL: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/dropbox/callback', methods=['GET'])
def dropbox_callback():
    """Handle OAuth2 callback from Dropbox."""
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "Authorization code missing"}), 400

    try:
        app_key = os.getenv('DROPBOX_APP_KEY')
        app_secret = os.getenv('DROPBOX_APP_SECRET')
        redirect_uri = os.getenv('DROPBOX_REDIRECT_URI')

        logging.info(f"Processing callback with code: {code[:10]}...")
        
        token_url = "https://api.dropbox.com/oauth2/token"
        data = {
            "code": code,
            "grant_type": "authorization_code",
            "client_id": app_key,
            "client_secret": app_secret,
            "redirect_uri": redirect_uri
        }

        response = requests.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()

        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')

        if not all([access_token, refresh_token]):
            logging.error("Failed to retrieve tokens from Dropbox response")
            return jsonify({"error": "Failed to retrieve tokens"}), 400

        # Store tokens in environment variables
        os.environ['DROPBOX_ACCESS_TOKEN'] = access_token
        os.environ['DROPBOX_REFRESH_TOKEN'] = refresh_token
        
        logging.info("Dropbox authorization completed successfully")
        
        return jsonify({
            "message": "Authorization successful!",
            "access_token": access_token,
            "refresh_token": refresh_token
        }), 200
    except Exception as e:
        logging.error(f"Error during callback processing: {str(e)}")
        return jsonify({"error": str(e)}), 500

    
# Public endpoint
@app.route('/welcome', methods=['GET'])
def welcome():
    logging.info("Accessed the welcome endpoint.")
    return jsonify({"message": "Welcome to the Video Sentiment Analysis API!"})

@app.route('/callback', methods=['GET'])
def callback():
    """Handle OAuth2 callback from Dropbox."""
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "Authorization code missing"}), 400

    try:
        app_key = os.getenv('DROPBOX_APP_KEY')
        app_secret = os.getenv('DROPBOX_APP_SECRET')
        redirect_uri = os.getenv('DROPBOX_REDIRECT_URI')

        # Debugging logs
        logging.info(f"Code: {code}")
        logging.info(f"App Key: {app_key}, App Secret: {app_secret}, Redirect URI: {redirect_uri}")

        token_url = "https://api.dropbox.com/oauth2/token"
        data = {
            "code": code,
            "grant_type": "authorization_code",
            "client_id": app_key,
            "client_secret": app_secret,
            "redirect_uri": redirect_uri
        }

        import requests
        response = requests.post(token_url, data=data)
        logging.info(f"Dropbox Response: {response.text}")
        response.raise_for_status()
        token_data = response.json()

        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')

        if not refresh_token:
            return jsonify({"error": "Failed to retrieve refresh token"}), 400

        # Save refresh token securely
        with open(".env", "a") as env_file:
            env_file.write(f"\nDROPBOX_REFRESH_TOKEN={refresh_token}\n")

        return jsonify({
            "message": "Authorization successful!",
            "access_token": access_token,
            "refresh_token": refresh_token
        }), 200
    except Exception as e:
        logging.error(f"Error during callback processing: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/rotate_api_key', methods=['POST'])
@require_api_key
def rotate_api_key(user):
    """
    Rotate API key for the authenticated user.
    """
    try:
        new_key = generate_api_key(user['name'])
        logging.info(f"API key rotated successfully for user: {user['name']}")
        return jsonify({
            "status": "success",
            "message": "API key rotated successfully.",
            "api_key": new_key
        }), 200
    except Exception as e:
        logging.error(f"Failed to rotate API key for user '{user['name']}': {str(e)}")
        return jsonify({"status": "error", "message": f"Failed to rotate API key: {str(e)}"}), 500

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()

        # Check for missing data
        if not data:
            logging.warning("Request payload is missing.")
            return jsonify({"error": "No data provided"}), 400

        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        # Validate email
        import re
        email_regex = r'^[^@]+@[^@]+\.[^@]+$'
        if not re.match(email_regex, email):
            logging.warning(f"Invalid email format: {email}")
            return jsonify({"error": "Invalid email format"}), 400

        # Validate password strength
        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters long"}), 400
        
        if not any(char.isupper() for char in password):
            return jsonify({"error": "Password must contain at least one uppercase letter"}), 400
            
        if not any(char.islower() for char in password):
            return jsonify({"error": "Password must contain at least one lowercase letter"}), 400
            
        if not any(char.isdigit() for char in password):
            return jsonify({"error": "Password must contain at least one number"}), 400

        if not any(char in "!@#$%^&*(),.?\":{}|<>" for char in password):
            return jsonify({"error": "Password must contain at least one special character"}), 400

        # Check if user already exists
        if check_user_exists_in_db(username, email):
            logging.warning(f"User already exists with username or email: {username}, {email}")
            return jsonify({"error": "Username or email already exists"}), 400

        # Register user
        api_key = register_user_in_db(username, email, password)

        return jsonify({
            "message": "User registered successfully",
            "api_key": api_key
        }), 201

    except ValueError as ve:
        logging.warning(f"Validation error in registration: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logging.error(f"Error in registration: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()

        # Validate input
        if not data or not data.get('username') or not data.get('password'):
            logging.warning("Missing username or password")
            return jsonify({"error": "Username and password are required"}), 400

        # Authenticate user
        user_data = authenticate_user_in_db(data['username'], data['password'])
        if not user_data:
            logging.warning("Invalid login attempt")
            return jsonify({"error": "Invalid username or password"}), 401

        logging.info(f"User {data['username']} logged in successfully.")
        return jsonify({"message": "Login successful", "api_key": user_data['api_key']}), 200

    except Exception as e:
        logging.error(f"Error in login: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/last_analysis', methods=['GET'])
@require_api_key
def get_last_analysis(user):
    """Retrieve the latest sentiment analysis for a user with proper error handling and response formatting."""
    try:
        result = fetch_last_sentiment_from_db(user['name'])
        
        if not result:
            response = jsonify({
                "status": "error",
                "message": "No analysis results found"
            })
            response.headers['Content-Type'] = 'application/json'
            return response, 404

        # Ensure all fields are properly serializable
        formatted_result = {
            "video_name": result["video_name"],
            "sentiment": result["sentiment"],
            "overall_polarity": float(result["overall_polarity"]) if result["overall_polarity"] else 0.0,
            "profanity_level": result["profanity_level"],
            "profanity_count": int(result["profanity_count"]) if result["profanity_count"] else 0,
            "created_at": result["created_at"],
            "full_analysis": result["full_analysis"] if isinstance(result["full_analysis"], dict) else {}
        }

        # Create response with explicit content type
        response = jsonify(formatted_result)
        response.headers['Content-Type'] = 'application/json'
        return response, 200

    except Exception as e:
        logging.error(f"Error retrieving last analysis: {str(e)}")
        response = jsonify({
            "status": "error",
            "message": "Failed to retrieve analysis results",
            "details": str(e)
        })
        response.headers['Content-Type'] = 'application/json'
        return response, 500
    
@app.route('/upload_video', methods=['POST'])
@require_api_key
def upload_video(user):
    """Upload a video to Dropbox, analyze its sentiment, and return detailed insights."""
    temp_dir = None
    try:
        # Add detailed logging
        logging.info(f"Starting upload process for user: {user['name']}")
        
        if 'file' not in request.files:
            logging.warning(f"File part missing in request. Request files: {request.files}")
            return jsonify({"status": "error", "message": "No file part in the request."}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No file selected."}), 400

        logging.info(f"File received: {file.filename}")
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({
                "status": "error", 
                "message": f"Invalid file format. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400

        # Create temp directory with more explicit error handling
        try:
            temp_dir = tempfile.mkdtemp(dir=app.config['UPLOAD_FOLDER'])
            os.chmod(temp_dir, 0o755)  # Set appropriate permissions
        except Exception as e:
            logging.error(f"Failed to create temp directory: {str(e)}")
            return jsonify({"status": "error", "message": "Server storage error"}), 500

        temp_path = os.path.join(temp_dir, secure_filename(file.filename))
        
        # Save file with explicit error handling
        try:
            file.save(temp_path)
            logging.info(f"File saved at: {temp_path}")
        except Exception as e:
            logging.error(f"Failed to save file: {str(e)}")
            return jsonify({"status": "error", "message": "Failed to save uploaded file"}), 500

        # Upload to Dropbox
        try:
            dropbox_path = f"/{file.filename}"
            shared_url = upload_to_dropbox(temp_path, dropbox_path)
        except Exception as e:
            logging.error(f"Failed to upload file to Dropbox: {str(e)}")
            return jsonify({"status": "error", "message": f"Failed to upload file to Dropbox: {str(e)}"}), 500

        # Perform sentiment analysis
        try:
            success, sentiment_results = process_video_sentiment(temp_path)
            if not success:
                raise RuntimeError(sentiment_results.get('error', 'Analysis failed.'))

            # Ensure sentiment_results has the required structure
            sentiment_results = {
                'sentiment': sentiment_results.get('sentiment', 'neutral'),
                'overall_polarity': sentiment_results.get('overall_polarity', 0.0),
                'profanity_analysis': {
                    'profanity_level': sentiment_results.get('profanity_analysis', {}).get('profanity_level', 'none'),
                    'profanity_count': sentiment_results.get('profanity_analysis', {}).get('profanity_count', 0)
                },
                'detailed_results': sentiment_results.get('detailed_results', {}),
                'analysis_timestamp': datetime.now().isoformat()
            }

            logging.info("Sentiment analysis completed successfully.")
        except Exception as e:
            logging.error(f"Sentiment analysis failed: {str(e)}")
            return jsonify({"status": "error", "message": f"Sentiment analysis failed: {str(e)}"}), 500

        # Save analysis results to the database
        try:
            # Save to the 'sentiments' table
            save_sentiment_to_db(
                username=user['name'],
                video_name=file.filename,
                sentiment_results=sentiment_results
            )
            logging.info(f"Sentiment analysis results saved to database for user {user['name']}.")

            # Save to the 'sentiment_results' table
            save_sentiment_results_to_db(
                username=user['name'],
                video_name=file.filename,
                sentiment_results=sentiment_results
            )
            logging.info(f"Detailed sentiment results saved to database for user {user['name']}.")
        except Exception as e:
            logging.error(f"Failed to save sentiment analysis to database: {str(e)}")
            return jsonify({"status": "error", "message": f"Failed to save sentiment analysis to database: {str(e)}"}), 500

        return jsonify({
            "status": "success",
            "message": "File uploaded and sentiment analysis completed successfully.",
            "file_url": shared_url,
            "sentiment_results": sentiment_results
        }), 201

    except Exception as e:
        logging.error(f"Unexpected error during file upload or analysis: {str(e)}")
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {str(e)}"}), 500

    finally:
        # Cleanup temporary directory and file
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logging.info(f"Temporary directory removed: {temp_dir}")
            except Exception as cleanup_error:
                logging.error(f"Failed to remove temporary directory: {temp_dir}, Error: {cleanup_error}")
@app.route('/check-session', methods=['GET'])
@require_api_key
def check_session(user):
    """Check if the user session is still valid."""
    if check_session_validity(user['name']):
        return jsonify({"status": "valid", "username": user['name']}), 200
    return jsonify({"status": "invalid"}), 401

@app.route('/analysis_history', methods=['GET'])
@require_api_key
def get_analysis_history(user):
    """Retrieve all sentiment analysis results for a user."""
    try:
        results = fetch_all_sentiments_from_db(user['name'])
        
        formatted_results = []
        
        if results:
            for result in results:
                # Handle date formatting safely
                created_at = None
                if isinstance(result.get("created_at"), datetime):
                    created_at = result["created_at"].isoformat()
                elif isinstance(result.get("created_at"), str):
                    try:
                        # Try to parse string to datetime then back to isoformat
                        created_at = datetime.fromisoformat(result["created_at"]).isoformat()
                    except ValueError:
                        created_at = result["created_at"]

                formatted_result = {
                    "video_name": str(result.get("video_name", "")),
                    "sentiment": str(result.get("sentiment", "unknown")),
                    "overall_polarity": float(result.get("overall_polarity", 0.0) or 0.0),
                    "profanity_level": str(result.get("profanity_level", "none")),
                    "profanity_count": int(result.get("profanity_count", 0) or 0),
                    "created_at": created_at
                }
                formatted_results.append(formatted_result)

        return jsonify({
            "status": "success",
            "data": formatted_results
        }), 200

    except Exception as e:
        logging.error(f"Error in get_analysis_history: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Failed to fetch analysis history",
            "error": str(e)
        }), 500

@app.route('/results', methods=['GET'])
@require_api_key
def get_sentiment_results(user):
    """
    Return the last sentiment analysis result for the authenticated user.
    """
    try:
        video_name = request.args.get('video_name')
        if not video_name:
            return jsonify({"status": "error", "message": "Video name is required."}), 400

        # Fetch sentiment result from the database
        result = fetch_sentiment_from_db(user['name'], video_name)
        if not result:
            return jsonify({"status": "error", "message": f"No sentiment result found for video: {video_name}"}), 404

        return jsonify({
            "status": "success",
            "sentiment_result": result
        }), 200
    except Exception as e:
        logging.error(f"Error fetching sentiment results: {str(e)}")
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {str(e)}"}), 500

def ensure_upload_directory():
    upload_dir = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, mode=0o755)
    else:
        os.chmod(upload_dir, 0o755)
    logging.info(f"Upload directory ready: {upload_dir}")

if __name__ == "__main__":
    try:
        ensure_upload_directory()
        initialize_database()
        update_database_schema()
        migrate_database()
        app.run(
            host="0.0.0.0",
            port=5000,
            threaded=True  # Tambahkan ini
        )
    except Exception as e:
        logging.critical(f"Failed to start the application: {str(e)}")