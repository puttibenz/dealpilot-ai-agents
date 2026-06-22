"""
Security Module — Google Cloud Secret Manager Wrapper
Implementation: Day 5
"""

import os
from dotenv import load_dotenv

# Load env for local fallback during Development
load_dotenv()


def get_secret(secret_id: str) -> str:
    """
    Retrieve Secret from Google Cloud Secret Manager.
    If USE_SECRET_MANAGER=false or the library is not installed, it falls back to Environment Variables.
    
    Args:
        secret_id: The ID of the secret (e.g., google-api-key).
        
    Returns:
        The configuration value or secret key as a string.
    """
    use_sm = os.getenv("USE_SECRET_MANAGER", "false").lower() == "true"
    
    if not use_sm:
        # Development mode: retrieve from local Environment Variable
        env_key = secret_id.upper().replace("-", "_")
        value = os.getenv(env_key)
        if not value:
            # If not found, return empty string
            return ""
        return value
        
    # Production mode: Use GCP Secret Manager
    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT must be set in production mode")
            
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except ImportError:
        # Fallback if google-cloud-secret-manager is not installed locally
        env_key = secret_id.upper().replace("-", "_")
        return os.getenv(env_key, "")
    except Exception as e:
        print(f"⚠️ Error accessing Secret Manager: {str(e)}. Falling back to env vars.")
        env_key = secret_id.upper().replace("-", "_")
        return os.getenv(env_key, "")
