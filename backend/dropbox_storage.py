import dropbox
import os
import logging
from dropbox.exceptions import ApiError, AuthError
from dropbox.files import WriteMode
from dropbox.sharing import CreateSharedLinkWithSettingsError
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def refresh_dropbox_token():
    """Refresh Dropbox token using refresh token and app credentials."""
    refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")
    client_id = os.getenv("DROPBOX_APP_KEY")
    client_secret = os.getenv("DROPBOX_APP_SECRET")

    if not (refresh_token and client_id and client_secret):
        raise RuntimeError("Missing Dropbox credentials for token refresh.")

    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        new_token = response.json().get("access_token")
        if not new_token:
            raise RuntimeError("Failed to retrieve new Dropbox access token.")

        # Update environment variable in memory only
        os.environ["DROPBOX_ACCESS_TOKEN"] = new_token
        logging.info("Dropbox access token refreshed successfully.")
        return new_token
    except Exception as e:
        logging.error(f"Error refreshing Dropbox token: {e}")
        raise RuntimeError(f"Error refreshing Dropbox token: {e}")

def get_dropbox_client():
    """Get a Dropbox client, refreshing the token if necessary."""
    access_token = os.getenv("DROPBOX_ACCESS_TOKEN")
    if not access_token:
        logging.error("Dropbox access token is missing.")
        raise RuntimeError("Dropbox access token is missing.")
    
    try:
        dbx = dropbox.Dropbox(access_token)
        # Test the connection
        dbx.users_get_current_account()
        return dbx
    except AuthError:
        # Token is invalid or expired, try refreshing
        new_token = refresh_dropbox_token()
        return dropbox.Dropbox(new_token)

def upload_to_dropbox(local_path, dropbox_path):
    """Upload a file to Dropbox and return its shared link."""
    max_retries = 2
    retry_count = 0

    while retry_count < max_retries:
        try:
            dbx = get_dropbox_client()
            
            # Upload file to Dropbox
            with open(local_path, "rb") as f:
                dbx.files_upload(f.read(), dropbox_path, mode=WriteMode("overwrite"))
            logging.info(f"File uploaded to Dropbox at path: {dropbox_path}")

            # Check if shared link already exists
            try:
                links = dbx.sharing_list_shared_links(path=dropbox_path)
                if links.links:
                    shared_url = links.links[0].url
                    logging.info(f"Using existing shared link: {shared_url}")
                else:
                    # Create a new shared link
                    shared_link = dbx.sharing_create_shared_link_with_settings(dropbox_path)
                    shared_url = shared_link.url
                    logging.info(f"New shared link created: {shared_url}")
                return shared_url

            except CreateSharedLinkWithSettingsError as e:
                if e.is_shared_link_already_exists():
                    existing_link = e.get_shared_link_already_exists_metadata()
                    shared_url = existing_link.url
                    logging.info(f"Using existing shared link: {shared_url}")
                    return shared_url
                raise

        except AuthError:
            if retry_count < max_retries - 1:
                retry_count += 1
                logging.warning(f"Authentication failed, attempting retry {retry_count}")
                continue
            raise
        except Exception as e:
            logging.error(f"Error during Dropbox upload: {e}")
            raise RuntimeError(f"Failed to upload to Dropbox: {e}")

        retry_count += 1
    
    raise RuntimeError("Max retries exceeded for Dropbox upload")