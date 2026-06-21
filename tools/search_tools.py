"""
Search Tools — MCP Web Search wrapper และฐานข้อมูลจำลองข้อมูลข่าวสารธุรกิจ

Implementation: วันที่ 2
ดู Project Plan Section 2.2 (Agent 2)
"""

import re
from typing import List
from models.data_models import CompanyResearch


# ฐานข้อมูลข่าวจำลองสำหรับ 20 บริษัทใน mock_crm.csv เพื่อการรันที่เสถียรและรวดเร็ว
MOCK_COMPANY_DATABASE = {
    "shield tech": {
        "news": [
            "Shield Tech announces new series C funding of $50M for AI defense systems",
            "Shield Tech secures contract with US government for secure network communications",
            "Security breach attempt repelled successfully by Shield Tech's advanced firewall systems"
        ],
        "pain_points": [
            "ระบบความปลอดภัยต้องการการตรวจสอบอย่างสม่ำเสมอเนื่องจากทำงานกับหน่วยงานรัฐ",
            "การขยายระบบ Cloud ภายใต้ข้อกำหนดความปลอดภัยที่เข้มงวดทำได้ยาก",
            "ความต้องการในช่องทางการเชื่อมต่อที่ปลอดภัยและเข้ารหัสในทุกอุปกรณ์"
        ],
        "talking_points": [
            "ยินดีด้วยกับทุนรอบ Series C มูลค่า 50 ล้านเหรียญสำหรับระบบป้องกันภัย AI ครับ!",
            "เราทราบว่าระบบของคุณต้องรองรับการสื่อสารข้อมูลของรัฐบาลที่ปลอดภัยสูงสุด",
            "เราขอเสนอโซลูชันที่ช่วยตรวจสอบและจัดการสิทธิ์การเข้าถึงข้อมูลตามมาตรฐานความปลอดภัย"
        ],
        "sources": ["TechCrunch", "Government Technology", "Defense News"]
    },
    "apex finance": {
        "news": [
            "Apex Finance reports 40% growth in digital asset management transactions",
            "Apex Finance to launch automated portfolio balancing tools next month",
            "Regulatory compliance changes force Apex Finance to upgrade reporting systems"
        ],
        "pain_points": [
            "ความยุ่งยากในการปรับปรุงระบบรายงานให้สอดคล้องกับกฎระเบียบการเงินใหม่",
            "ปริมาณธุรกรรมสินทรัพย์ดิจิทัลที่เติบโตอย่างรวดเร็วจนระบบรับโหลดไม่ไหวในบางช่วง",
            "การจัดการพอร์ตการลงทุนแบบอัตโนมัติยังต้องการโมเดลการคำนวณที่แม่นยำขึ้น"
        ],
        "talking_points": [
            "ยินดีด้วยกับอัตราการเติบโตของธุรกรรมสินทรัพย์ดิจิทัลถึง 40% ครับ!",
            "เราสามารถช่วยแบ่งเบาภาระการปรับปรุงระบบตรวจสอบการปฏิบัติตามกฎเกณฑ์การเงินล่าสุดได้",
            "ระบบจัดสรรและปรับสมดุลพอร์ตอัตโนมัติของคุณสามารถทำงานร่วมกับ AI Agent ของเราได้เป็นอย่างดี"
        ],
        "sources": ["Bloomberg", "FinTech Futures", "Wall Street Journal"]
    },
    "stark industries": {
        "news": [
            "Stark Industries reveals new arc-reactor data monitoring technology",
            "Tony Stark announces transition of software infrastructure to clean energy monitoring",
            "Stark Industries experiences increased demand for real-time sensor analytics in energy grids"
        ],
        "pain_points": [
            "ระบบการรวบรวมข้อมูลเซ็นเซอร์แบบเรียลไทม์ในโครงข่ายพลังงานมีขนาดใหญ่เกินกว่าจะประมวลผลด้วยมือ",
            "การย้ายฐานข้อมูลระบบเดิม (legacy infrastructure) ไปยังระบบสะอาดตัวใหม่",
            "ต้องการระบบวิเคราะห์ความปลอดภัยและการทำงานที่ต้องทำงานอย่างต่อเนื่องตลอด 24 ชั่วโมง"
        ],
        "talking_points": [
            "ประทับใจกับนวัตกรรมการติดตามข้อมูลเครื่องปฏิกรณ์อาร์กตัวใหม่มากครับ",
            "เรามีแพลตฟอร์มวิเคราะห์ข้อมูลเซ็นเซอร์แบบเรียลไทม์ที่สอดคล้องกับระบบ Clean Energy Monitoring ของคุณ",
            "AI Agent ของเราสามารถช่วยเฝ้าระวังความปลอดภัยและวิเคราะห์ความเสี่ยงโครงข่ายพลังงานได้อัตโนมัติ"
        ],
        "sources": ["Stark Energy Portal", "Wired", "Scientific American"]
    },
    "tomb exploration ltd": {
        "news": [
            "Tomb Exploration Ltd expands operations to remote archaeological sites in South America",
            "Tomb Exploration Ltd partners with mapping agencies for offline GPS synchronization",
            "Connectivity issues plague Tomb Exploration's field research teams in remote jungle areas"
        ],
        "pain_points": [
            "การเชื่อมต่ออินเทอร์เน็ตที่ติดขัดในพื้นที่ห่างไกลทำให้ส่งข้อมูลกลับศูนย์ใหญ่ไม่ได้",
            "ความยากลำบากในการปรับประสานข้อมูลแผนที่และ GPS แบบออฟไลน์",
            "นักวิจัยภาคสนามเสียเวลากับการคีย์ข้อมูลการสำรวจด้วยมือ"
        ],
        "talking_points": [
            "ยินดีด้วยกับการขยายพื้นที่สำรวจไปยังโซนอเมริกาใต้ครับ!",
            "เรามีระบบสนับสนุนการทำงานแบบออฟไลน์ (Offline-first sync) ที่ช่วยเก็บข้อมูลโดยไม่ต้องมีอินเทอร์เน็ต",
            "AI ของเราสามารถช่วยจัดการแปลงข้อมูลเอกสารบันทึกการสำรวจด้วยภาพถ่ายเพื่อความรวดเร็วได้"
        ],
        "sources": ["Archaeology Today", "National Geographic", "Global Mapping News"]
    },
    "techcorp inc": {
        "news": [
            "TechCorp Inc launches new enterprise software division for workflow automation",
            "TechCorp Inc experiences customer service backlog due to rapid user expansion",
            "Industry analysts praise TechCorp's new security features in the cloud"
        ],
        "pain_points": [
            "มีงานบริการลูกค้าค้างสะสม (backlog) จำนวนมากเนื่องจากจำนวนผู้ใช้โตเร็วเกินไป",
            "การเชื่อมโยงระบบ workflow automation ตัวใหม่เข้ากับแอปพลิเคชันเดิมของลูกค้า",
            "การฝึกอบรมทีมงานสนับสนุนให้เข้าใจความปลอดภัยระบบคลาวด์แบบใหม่"
        ],
        "talking_points": [
            "ยินดีด้วยกับแผนกซอฟต์แวร์ระดับองค์กรสำหรับการทำ Workflow Automation ตัวใหม่ครับ!",
            "เราสามารถช่วยจัดการกับ Backlog งานบริการลูกค้าของคุณด้วย AI Customer Service Agents",
            "เราช่วยลดความยุ่งยากในการเชื่อมโยงระบบออโตเมชันตัวใหม่เข้ากับฐานข้อมูลเดิมของคุณได้"
        ],
        "sources": ["TechInAsia", "Enterprise Software Review", "SaaS Insider"]
    }
}


def search_company_news(company: str) -> List[str]:
    """
    ค้นหาข้อมูลข่าวสารล่าสุดของบริษัทในรอบ 30 วันที่ผ่านมา
    
    Args:
        company: ชื่อบริษัทที่ต้องการค้นหาข่าว
        
    Returns:
        รายการข่าวล่าสุด (สูงสุด 3 รายการ)
    """
    company_lower = company.lower().strip()
    
    # พยายามหาแบบตรงเป้าหมายในฐานข้อมูลจำลองก่อน
    for name, data in MOCK_COMPANY_DATABASE.items():
        if name in company_lower or company_lower in name:
            return data["news"]
            
    # กรณีไม่พบข้อมูลบริษัทใน Mock DB ให้สร้างข่าวจำลองแบบ Dynamic
    return [
        f"{company} announces major expansion of its digital services and cloud solutions division.",
        f"{company} focuses on automating manual workflows to increase operational efficiency in 2026.",
        f"{company} partners with technology leaders to enhance security and regulatory compliance."
    ]


def extract_pain_points(news: List[str]) -> List[str]:
    """
    วิเคราะห์ข้อมูลข่าวสารและดึงความท้าทายหรือจุดติดขัด (Pain Points) ของบริษัทออกมา
    
    Args:
        news: รายการของข่าวสารล่าสุดที่ดึงมาจากขั้นตอนก่อนหน้า
        
    Returns:
        รายการความท้าทาย/ปัญหาของบริษัท
    """
    # ตรวจสอบหาความสอดคล้องในฐานข้อมูลจำลอง
    for data in MOCK_COMPANY_DATABASE.values():
        # ถ้ามีข่าวสารข่าวใดข่าวหนึ่งตรงกัน
        if any(n in data["news"] for n in news):
            return data["pain_points"]
            
    # กรณีข่าวสารแบบ Dynamic ทั่วไป สกัด pain points จำลอง
    pain_points = []
    for item in news:
        item_lower = item.lower()
        if "expansion" in item_lower or "rapid" in item_lower:
            pain_points.append("ความยากลำบากในการปรับขนาดการทำงาน (scaling) ให้ทันการเติบโต")
        if "workflow" in item_lower or "manual" in item_lower:
            pain_points.append("การพึ่งพากระบวนการแบบแมนนวลทำให้พนักงานเสียเวลาและเกิดข้อผิดพลาด")
        if "security" in item_lower or "compliance" in item_lower or "regulation" in item_lower:
            pain_points.append("แรงกดดันด้านการตรวจสอบและการปฏิบัติตามมาตรฐานความปลอดภัยที่เข้มงวด")
            
    # Fallback หากไม่มีคีย์เวิร์ดตรงเลย
    if not pain_points:
        pain_points = [
            "กระบวนการทำงานภายในล่าช้า ขาดระบบอัตโนมัติในการช่วยประมวลผลข้อมูล",
            "การขาดข้อมูลเชิงลึกแบบเรียลไทม์เพื่อสนับสนุนการตัดสินใจของฝ่ายบริหาร",
            "การบริการลูกค้าปลายทางติดขัดเนื่องจากการเติบโตแบบก้าวกระโดด"
        ]
        
    return pain_points[:3]


def generate_talking_points(research: CompanyResearch) -> List[str]:
    """
    สร้างจุดเปิดใจ/ประโยคเปิดการขาย (Talking Points) ที่ SDR สามารถหยิบไปใช้ทักทายลูกค้าในอีเมลได้เลย
    
    Args:
        research: วัตถุข้อมูล CompanyResearch ที่มีข่าวสารและ Pain Points ครบถ้วน
        
    Returns:
        รายการ Talking Points ภาษาไทยที่กระชับและดึงดูดใจ
    """
    company_lower = research.company.lower().strip()
    
    # ดึงจากฐานข้อมูลจำลองโดยตรงถ้ามี
    for name, data in MOCK_COMPANY_DATABASE.items():
        if name in company_lower or company_lower in name:
            return data["talking_points"]
            
    # เจนเนอเรตแบบ Heuristic
    talking_points = []
    talking_points.append(f"เห็นข่าวล่าสุดเรื่องแผนการพัฒนาระบบคลาวด์และดิจิทัลของทาง {research.company} แล้วน่าสนใจมากครับ")
    
    if research.pain_points:
        primary_pain = research.pain_points[0]
        talking_points.append(f"เราทราบว่าหลายบริษัทที่กำลังเผชิญปัญหาเรื่อง '{primary_pain}' สามารถใช้ระบบ Multi-Agent ของเราช่วยแก้ปัญหานี้ได้โดยตรง")
        
    talking_points.append(f"ยินดีด้วยกับการขยายพันธมิตรทางเทคโนโลยีล่าสุดของ {research.company} หวังว่าเราจะได้ร่วมงานกันในระบบตรวจสอบอัตโนมัติครับ")
    
    return talking_points[:3]
