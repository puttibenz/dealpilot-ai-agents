"""
Security Module — Google Cloud Secret Manager Wrapper
Implementation: วันที่ 5
"""

import os
from dotenv import load_dotenv

# โหลด env เพื่อใช้โลคัลก่อนในกรณี Development
load_dotenv()


def get_secret(secret_id: str) -> str:
    """
    ดึงค่า Secret จาก Google Cloud Secret Manager
    หาก USE_SECRET_MANAGER=false หรือไม่พบไลบรารี จะสลับมาใช้ Environment Variable ทั่วไปแทน (Local Fallback)
    
    Args:
        secret_id: รหัสของ Secret (เช่น google-api-key)
        
    Returns:
        ค่าคอนฟิกูเรชันหรือคีย์ลับในรูปแบบสตริง
    """
    use_sm = os.getenv("USE_SECRET_MANAGER", "false").lower() == "true"
    
    if not use_sm:
        # Development mode: ดึงจาก Environment Variable โลคัล
        env_key = secret_id.upper().replace("-", "_")
        value = os.getenv(env_key)
        if not value:
            # หากไม่มี ให้คืนค่าว่างเปล่า หรือกรณีพิเศษ
            return ""
        return value
        
    # Production mode: ใช้ GCP Secret Manager
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
        # Fallback กรณีไม่ได้ติดตั้ง google-cloud-secret-manager บนเครื่องโลคัล
        env_key = secret_id.upper().replace("-", "_")
        return os.getenv(env_key, "")
    except Exception as e:
        print(f"⚠️ Error accessing Secret Manager: {str(e)}. Falling back to env vars.")
        env_key = secret_id.upper().replace("-", "_")
        return os.getenv(env_key, "")
