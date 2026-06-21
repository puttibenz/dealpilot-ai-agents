"""
Tests for Research Agent
Implementation: วันที่ 2
"""

import pytest
from models.data_models import CompanyResearch
from tools.search_tools import (
    search_company_news,
    extract_pain_points,
    generate_talking_points,
)


def test_search_company_news():
    """ทดสอบว่าการค้นหาข่าวสารของบริษัทคืนค่าหัวข้อข่าวจำลองที่สมจริง"""
    # ทดสอบกรณีมีบริษัทในฐานข้อมูลจำลอง (case-insensitive & substring matching)
    shield_news = search_company_news("Shield Tech")
    assert len(shield_news) == 3
    assert any("series c funding" in news.lower() for news in shield_news)

    # ทดสอบกรณีไม่มีในฐานข้อมูลจำลอง (สร้างข่าวจำลองแบบ Dynamic)
    unknown_news = search_company_news("Unknown Inc")
    assert len(unknown_news) == 3
    assert any("Unknown Inc" in news for news in unknown_news)


def test_extract_pain_points():
    """ทดสอบความสามารถในการสกัดปัญหา (pain points) ของบริษัท"""
    # ทดสอบดึงปัญหาของบริษัทในฐานข้อมูลจำลอง
    shield_news = [
        "Shield Tech announces new series C funding of $50M for AI defense systems"
    ]
    pain_points = extract_pain_points(shield_news)
    assert len(pain_points) > 0
    assert any("ความปลอดภัย" in point for point in pain_points)

    # ทดสอบวิเคราะห์ข่าวนอกเหนือจากฐานข้อมูล
    dynamic_news = ["SomeCorp Inc announces major expansion of workflow automation"]
    dynamic_pain = extract_pain_points(dynamic_news)
    assert len(dynamic_pain) > 0
    assert any("scaling" in point or "ความยากลำบาก" in point for point in dynamic_pain)


def test_generate_talking_points():
    """ทดสอบการสร้างจุดเปิดการขายภาษาไทยจากผลการค้นคว้าข้อมูลบริษัท"""
    research = CompanyResearch(
        company="Apex Finance",
        recent_news=["Apex Finance reports 40% growth in transactions"],
        pain_points=["ระบบรายงานธุรกรรมล่าช้าและปรับปรุงตามกฎเกณฑ์การเงินไม่ทัน"],
        sources=["Bloomberg"]
    )
    
    talking_points = generate_talking_points(research)
    assert len(talking_points) > 0
    # ยืนยันว่ามีการอ้างอิงข้อมูล หรือมีประโยคเปิดใจที่เป็นประโยชน์
    assert any("ยินดีด้วย" in pt or "Apex Finance" in pt for pt in talking_points)
