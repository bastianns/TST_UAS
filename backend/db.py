import psycopg2
from psycopg2 import sql, DatabaseError, IntegrityError
from dotenv import load_dotenv
import os
import hashlib
import logging
import json
from datetime import datetime

# Load environment variables
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# PostgreSQL configuration
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "sentiment_db"),
    "user": os.getenv("DB_USER", "sentiment_user"),
    "password": os.getenv("DB_PASSWORD", "StrongPassword123!"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
}

def get_db_connection():
    """Establish a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logging.info("Database connection established successfully.")
        return conn
    except DatabaseError as e:
        logging.error(f"Database connection error: {str(e)}")
        raise RuntimeError(f"Database connection error: {str(e)}")

def update_database_schema():
    """Update the database schema to include missing columns and add indexes."""
    schema_updates = [
        {
            "table": "sentiments",
            "columns": [
                "ALTER TABLE sentiments ADD COLUMN IF NOT EXISTS overall_polarity REAL",
                "ALTER TABLE sentiments ADD COLUMN IF NOT EXISTS profanity_level TEXT",
                "ALTER TABLE sentiments ADD COLUMN IF NOT EXISTS profanity_count INTEGER",
                "ALTER TABLE sentiments ADD COLUMN IF NOT EXISTS full_analysis JSONB",
                "ALTER TABLE sentiments ADD COLUMN IF NOT EXISTS reasoning TEXT",
                "ALTER TABLE sentiments ADD COLUMN IF NOT EXISTS detailed_results JSONB"
            ]
        },
        {
            "table": "sentiment_results",
            "columns": [
                "ALTER TABLE sentiment_results ADD COLUMN IF NOT EXISTS detailed_analysis JSONB"
            ]
        },
        {
            "table": "api_keys",
            "columns": [
                "CREATE INDEX IF NOT EXISTS idx_api_keys_api_key ON api_keys(api_key)",
                "CREATE INDEX IF NOT EXISTS idx_api_keys_created_at ON api_keys(created_at)"
            ]
        }
    ]

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            for update in schema_updates:
                for query in update["columns"]:
                    cur.execute(query)
                    logging.info(f"Schema updated: {query}")
        conn.commit()
        conn.close()
        logging.info("Database schema updated successfully.")
    except Exception as e:
        logging.error(f"Failed to update database schema: {str(e)}")
        raise RuntimeError(f"Database schema update error: {str(e)}")

def initialize_database():
    """Initialize the database with required tables."""
    table_definitions = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS api_keys (
            api_key TEXT PRIMARY KEY,
            username TEXT NOT NULL REFERENCES users(username),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS sentiments (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL REFERENCES users(username),
            video_name TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            overall_polarity REAL,
            profanity_level TEXT,
            profanity_count INTEGER,
            full_analysis JSONB,
            reasoning TEXT,
            detailed_results JSONB,
            UNIQUE (username, video_name)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS sentiment_results (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            video_name TEXT NOT NULL,
            sentiment_results JSONB NOT NULL,
            detailed_analysis JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (username, video_name)
        );
        """
    ]

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            for table in table_definitions:
                cur.execute(table)
                logging.info("Table initialized or already exists.")
        conn.commit()
        conn.close()
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize database: {str(e)}")
        raise RuntimeError(f"Database initialization error: {str(e)}")

def check_user_exists_in_db(username: str, email: str) -> bool:
    """Check if a user exists in the database by username or email."""
    query = """
    SELECT EXISTS (
        SELECT 1 FROM users 
        WHERE username = %s
    ) AS username_exists,
    EXISTS (
        SELECT 1 FROM users 
        WHERE email = %s
    ) AS email_exists;
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(query, (username, email))
            username_exists, email_exists = cur.fetchone()
            
            if username_exists:
                logging.warning(f"Username '{username}' already exists")
            if email_exists:
                logging.warning(f"Email '{email}' already exists")
                
            return username_exists or email_exists
    except Exception as e:
        logging.error(f"Error checking user existence: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

def generate_api_key(username: str) -> str:
    """Generate a unique API key for a user."""
    raw_key = os.urandom(32).hex()
    
    insert_api_key_query = """
        INSERT INTO api_keys (api_key, username)
        VALUES (%s, %s);
    """

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(insert_api_key_query, (raw_key, username))
        conn.commit()
        conn.close()
        logging.info(f"API key generated for user '{username}'.")
        return raw_key
    except IntegrityError:
        logging.error(f"API key generation failed. User '{username}' may already have an API key.")
        raise ValueError("User already has an API key.")
    except Exception as e:
        logging.error(f"Failed to generate API key: {str(e)}")
        raise RuntimeError(f"API key generation error: {str(e)}")

    
def bootstrap_database():
    """Bootstrap database initialization and schema updates."""
    try:
        initialize_database()
        update_database_schema()
        logging.info("Database bootstrap completed successfully.")
    except Exception as e:
        logging.critical(f"Database bootstrap failed: {str(e)}")
        raise
def check_session_validity(username: str) -> bool:
    """Check if user session is valid."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM users WHERE username = %s",
                (username,)
            )
            return bool(cur.fetchone())
    except Exception as e:
        logging.error(f"Session check error: {str(e)}")
        return False

def check_api_key(api_key: str) -> dict:
    """Validate the API key and provide detailed results."""
    if not api_key:
        return {"valid": False, "error": "API key is missing", "username": None}

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT username, created_at 
                FROM api_keys 
                WHERE api_key = %s 
                ORDER BY created_at DESC 
                LIMIT 1;
                """,
                (api_key,)
            )
            result = cur.fetchone()
        conn.close()

        if not result:
            return {"valid": False, "error": "Invalid API key", "username": None}

        username, created_at = result
        if (datetime.now() - created_at).total_seconds() > 86400:  # 24 hours
            return {"valid": False, "error": "API key expired", "username": None}

        return {"valid": True, "error": None, "username": username}

    except Exception as e:
        logging.error(f"API key validation error: {str(e)}")
        return {"valid": False, "error": "Validation error", "username": None}

    
def get_user_from_api_key(api_key: str):
    """Retrieve the username associated with a given API key."""
    query = "SELECT username FROM api_keys WHERE api_key = %s"
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(query, (api_key,))
            result = cur.fetchone()
        conn.close()
        return {"name": result[0]} if result else None
    except Exception as e:
        logging.error(f"Failed to retrieve user for API key: {str(e)}")
        return None

def register_user_in_db(username: str, email: str, password: str) -> str:
    """Register a new user and return their API key."""
    if not username or not email or not password:
        raise ValueError("Username, email, and password are required.")
    
    # Hash the password for security
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    # SQL queries for inserting user and generating API key
    insert_user_query = """
        INSERT INTO users (username, email, password) 
        VALUES (%s, %s, %s)
        RETURNING username;
    """
    
    insert_api_key_query = """
        INSERT INTO api_keys (api_key, username)
        VALUES (%s, %s);
    """
    
    # Generate a unique API key
    raw_key = os.urandom(32).hex()
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Insert user into the users table
            cur.execute(insert_user_query, (username, email, hashed_password))
            cur.execute(insert_api_key_query, (raw_key, username))
        
        conn.commit()
        conn.close()
        logging.info(f"User '{username}' registered successfully.")
        return raw_key  # Return the raw API key for the user to use
    except IntegrityError as e:
        if "email" in str(e):
            logging.error(f"Email '{email}' is already registered.")
            raise ValueError("Email already registered.")
        else:
            logging.error(f"Username '{username}' is already taken.")
            raise ValueError("Username already exists.")
    except Exception as e:
        logging.error(f"Failed to register user: {str(e)}")
        raise RuntimeError(f"User registration error: {str(e)}")
    
def authenticate_user_in_db(username: str, password: str) -> dict:
    """Authenticate user credentials and manage API key."""
    if not username or not password:
        raise ValueError("Username and password are required.")
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # First verify the user credentials
            cur.execute(
                "SELECT 1 FROM users WHERE username = %s AND password = %s",
                (username, hashed_password)
            )
            if not cur.fetchone():
                conn.close()
                return None

            # Generate new API key
            raw_key = os.urandom(32).hex()
            
            # Revoke old API key and insert new one
            cur.execute(
                """
                WITH old_key AS (
                    DELETE FROM api_keys 
                    WHERE username = %s
                    RETURNING username
                )
                INSERT INTO api_keys (api_key, username)
                SELECT %s, username FROM old_key
                RETURNING username;
                """,
                (username, raw_key)
            )
            
            if not cur.fetchone():
                # If no old key was found, insert new one directly
                cur.execute(
                    "INSERT INTO api_keys (api_key, username) VALUES (%s, %s)",
                    (raw_key, username)
                )
        
        conn.commit()
        conn.close()
        
        logging.info(f"User '{username}' authenticated and API key rotated successfully.")
        return {"api_key": raw_key}
        
    except Exception as e:
        logging.error(f"Authentication error: {str(e)}")
        raise RuntimeError(f"Authentication error: {str(e)}")
    
def save_sentiment_to_db(username: str, video_name: str, sentiment_results: dict) -> None:
    """Save sentiment analysis results to the database."""
    insert_into_sentiments = """
    INSERT INTO sentiments (
        username, video_name, sentiment, overall_polarity, profanity_level,
        profanity_count, full_analysis
    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (username, video_name) DO UPDATE
    SET sentiment = EXCLUDED.sentiment, 
        overall_polarity = EXCLUDED.overall_polarity,
        profanity_level = EXCLUDED.profanity_level,
        profanity_count = EXCLUDED.profanity_count,
        full_analysis = EXCLUDED.full_analysis,
        created_at = CURRENT_TIMESTAMP;
    """
    insert_into_sentiment_results = """
    INSERT INTO sentiment_results (
        username, video_name, sentiment_results
    ) VALUES (%s, %s, %s)
    ON CONFLICT (username, video_name) DO UPDATE
    SET sentiment_results = EXCLUDED.sentiment_results,
        created_at = CURRENT_TIMESTAMP;
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(insert_into_sentiments, (
                username, video_name, 
                sentiment_results.get('sentiment', 'unknown'),
                sentiment_results.get('overall_polarity', 0.0),
                sentiment_results.get('profanity_analysis', {}).get('profanity_level', 'none'),
                sentiment_results.get('profanity_analysis', {}).get('profanity_count', 0),
                json.dumps(sentiment_results)
            ))
            cur.execute(insert_into_sentiment_results, (
                username, video_name, json.dumps(sentiment_results)
            ))
        conn.commit()
        conn.close()
        logging.info(f"Sentiment saved for user '{username}', video '{video_name}'")
    except Exception as e:
        logging.error(f"Error saving sentiment to database: {str(e)}")
        raise RuntimeError(f"Error saving sentiment: {str(e)}")

def fetch_sentiment_from_db(username: str, video_name: str) -> dict:
    """Retrieve sentiment analysis result from the database."""
    query = """
        SELECT sentiment, overall_polarity, profanity_level, profanity_count, full_analysis
        FROM sentiments WHERE username = %s AND video_name = %s;
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(query, (username, video_name))
            result = cur.fetchone()
        conn.close()

        if result:
            return {
                "sentiment": result[0],
                "overall_polarity": result[1],
                "profanity_level": result[2],
                "profanity_count": result[3],
                "full_analysis": json.loads(result[4])  # Convert JSONB to Python dict
            }
        else:
            logging.warning(f"No sentiment found for user '{username}' and video '{video_name}'.")
            return None
    except Exception as e:
        logging.error(f"Error fetching sentiment from database: {str(e)}")
        raise RuntimeError(f"Error fetching sentiment: {str(e)}")

def fetch_last_sentiment_from_db(username: str) -> dict:
    """Fetch the most recent sentiment analysis result for a given user."""
    query = """
        SELECT video_name, sentiment, overall_polarity, profanity_level, profanity_count, full_analysis, created_at
        FROM sentiments
        WHERE username = %s
        ORDER BY created_at DESC
        LIMIT 1;
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(query, (username,))
            result = cur.fetchone()
        conn.close()

        if result:
            # The full_analysis field is already a Python dict when retrieved from JSONB
            return {
                "video_name": result[0],
                "sentiment": result[1],
                "overall_polarity": result[2],
                "profanity_level": result[3],
                "profanity_count": result[4],
                "full_analysis": result[5],  # Remove json.loads() call
                "created_at": result[6].isoformat()  # Format timestamp to ISO string
            }
        else:
            logging.warning(f"No recent sentiment analysis found for user '{username}'.")
            return None
    except Exception as e:
        logging.error(f"Error fetching last sentiment analysis from database: {str(e)}")
        raise RuntimeError(f"Error fetching last sentiment analysis: {str(e)}")

def save_sentiment_results_to_db(username: str, video_name: str, sentiment_results: dict) -> None:
    """Save detailed sentiment results to sentiment_results table."""
    query = """
        INSERT INTO sentiment_results (
            username, video_name, sentiment_results, created_at
        ) VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (username, video_name) DO UPDATE
        SET sentiment_results = EXCLUDED.sentiment_results,
            created_at = CURRENT_TIMESTAMP;
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(query, (
                username,
                video_name,
                json.dumps(sentiment_results)  # Serialize results as JSON
            ))
        conn.commit()
        conn.close()
        logging.info(f"Detailed sentiment results saved for user '{username}', video '{video_name}'.")
    except Exception as e:
        logging.error(f"Error saving sentiment results to database: {str(e)}")
        raise RuntimeError(f"Error saving sentiment results: {str(e)}")

def fetch_all_sentiments_from_db(username: str) -> list:
    """Fetch all sentiment analysis results for a given user."""
    query = """
        SELECT video_name, sentiment, overall_polarity, profanity_level, 
               profanity_count, full_analysis, created_at
        FROM sentiments
        WHERE username = %s
        ORDER BY created_at DESC;
    """
    try:
        logging.info(f"Preparing to fetch sentiment analysis for user: {username}")
        conn = get_db_connection()
        with conn.cursor() as cur:
            logging.info(f"Executing query: {query} with username: {username}")
            cur.execute(query, (username,))
            results = cur.fetchall()
            logging.info(f"Raw results fetched from database: {results}")
        conn.close()

        if results:
            formatted_results = [{
                "video_name": result[0],
                "sentiment": result[1],
                "overall_polarity": result[2],
                "profanity_level": result[3],
                "profanity_count": result[4],
                "full_analysis": result[5],
                "created_at": result[6].isoformat()
            } for result in results]
            logging.info(f"Formatted results: {formatted_results}")
            return formatted_results
        else:
            logging.warning(f"No sentiment analysis found for user '{username}'.")
            return []
    except Exception as e:
        logging.error(f"Error fetching sentiment analysis from database for user '{username}': {str(e)}")
        raise RuntimeError(f"Error fetching sentiment analysis: {str(e)}")

def migrate_database():
    """Add email column to users table if it doesn't exist."""
    migration_queries = [
        """
        DO $$ 
        BEGIN 
            IF NOT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='email'
            ) THEN 
                ALTER TABLE users ADD COLUMN email TEXT UNIQUE;
            END IF;
        END $$;
        """
    ]
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            for query in migration_queries:
                cur.execute(query)
                logging.info("Migration query executed successfully.")
        conn.commit()
        conn.close()
        logging.info("Database migration completed successfully.")
    except Exception as e:
        logging.error(f"Failed to migrate database: {str(e)}")
        raise RuntimeError(f"Database migration error: {str(e)}")

if __name__ == "__main__":
    # Run the bootstrap process when executed directly
    bootstrap_database()
    migrate_database()
