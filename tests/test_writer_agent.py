"""
Tests for Writer Agent
Implementation: วันที่ 3
"""

import pytest
from agents.writer_agent import load_sdr_style


def test_load_sdr_style():
    """ทดสอบว่าสามารถโหลดข้อมูลโปรไฟล์ของ SDR จากไฟล์ JSON ได้อย่างถูกต้อง"""
    # โหลดโปรไฟล์ sdr_001 (สมชาย)
    somchai = load_sdr_style("sdr_001")
    assert somchai["sdr_id"] == "sdr_001"
    assert "สมชาย" in somchai["sdr_name"]
    assert "สุภาพ" in somchai["style_description"]
    assert len(somchai["past_emails"]) == 3
    assert somchai["past_emails"][0]["subject"] is not None
    assert somchai["past_emails"][0]["body"] is not None

    # โหลดโปรไฟล์ sdr_002 (เควิน)
    kevin = load_sdr_style("sdr_002")
    assert kevin["sdr_id"] == "sdr_002"
    assert "เควิน" in kevin["sdr_name"]
    assert "เป็นกันเอง" in kevin["style_description"]
    assert len(kevin["past_emails"]) == 3

    # ตรวจสอบตัวเลือก fallback กรณีใส่รหัสไม่ถูกต้อง
    fallback = load_sdr_style("invalid_id")
    assert fallback["sdr_id"] == "sdr_001"  # คืนสัญญาสมชายเป็นค่าดีฟอลต์
