"""
Logging Utility — PII Masking
Implementation: วันที่ 5
ดู Project Plan Section 8.3
"""

import re
import logging

# กำหนดรูปแบบการ Logging มาตรฐาน
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("dealpilot")


def mask_pii(text: str) -> str:
    """
    ปิดบังข้อมูลระบุตัวตนบุคคล (PII) เช่น อีเมล และเบอร์โทรศัพท์ ในสายข้อความ Logs
    
    Args:
        text: ข้อความ Log ดิบ
        
    Returns:
        ข้อความ Log ที่ทำการ Mask เรียบร้อยแล้ว
    """
    if not text:
        return ""
        
    # Mask อีเมล (เช่น steve@shieldtech.gov -> s***e@s***h.gov)
    def replace_email(match):
        email = match.group(0)
        if "@" not in email:
            return "***@***.***"
        local, domain = email.split("@", 1)
        
        # จัดการส่วน Local
        if len(local) > 2:
            masked_local = local[0] + "***" + local[-1]
        else:
            masked_local = "***"
            
        # จัดการส่วน Domain
        if "." in domain:
            parts = domain.split(".")
            masked_domain_parts = []
            for p in parts:
                if len(p) > 2:
                    masked_domain_parts.append(p[0] + "***" + p[-1])
                else:
                    masked_domain_parts.append("***")
            masked_domain = ".".join(masked_domain_parts)
        else:
            masked_domain = "***"
            
        return f"{masked_local}@{masked_domain}"

    # ตรวจจับอีเมล
    email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    text = re.sub(email_pattern, replace_email, text)
    
    # ตรวจจับเบอร์โทรศัพท์ (เช่น 081-234-5678, +66 2 123 4567, 123-456-7890)
    phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}\b'
    text = re.sub(phone_pattern, '***-***-****', text)
    
    return text


def log_info(msg: str, *args, **kwargs):
    """ส่งข้อความ Log ระดับ INFO ที่ทำการ Mask PII เรียบร้อยแล้ว"""
    masked_msg = mask_pii(str(msg))
    logger.info(masked_msg, *args, **kwargs)


def log_warning(msg: str, *args, **kwargs):
    """ส่งข้อความ Log ระดับ WARNING ที่ทำการ Mask PII เรียบร้อยแล้ว"""
    masked_msg = mask_pii(str(msg))
    logger.warning(masked_msg, *args, **kwargs)


def log_error(msg: str, *args, **kwargs):
    """ส่งข้อความ Log ระดับ ERROR ที่ทำการ Mask PII เรียบร้อยแล้ว"""
    masked_msg = mask_pii(str(msg))
    logger.error(masked_msg, *args, **kwargs)
