"""
Secret Manager — Google Cloud Secret Manager wrapper

Implementation: วันที่ 5
ดู Project Plan Section 8.1
"""

import os


def get_secret(secret_id: str) -> str:
    """
    ดึง secret จาก Google Cloud Secret Manager
    ถ้า USE_SECRET_MANAGER=false จะใช้ environment variable แทน
    """
    # TODO วันที่ 5: Implement full Secret Manager integration
    # Development mode: ใช้ env var
    env_key = secret_id.upper().replace("-", "_")
    value = os.getenv(env_key)
    if not value:
        raise ValueError(f"Environment variable {env_key} not set")
    return value
