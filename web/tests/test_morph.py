import pytest
from app.services.morph_service import detect_encoding, to_slp1

def test_detect_encoding():
    assert detect_encoding("arjuna") == "SLP1"
    assert detect_encoding("kṛṣṇa") == "IAST"
    assert detect_encoding("कृष्ण") == "Devanagari"
    assert detect_encoding("āpastamba") == "IAST"

def test_to_slp1():
    # IAST to SLP1
    assert to_slp1("arjuna", "SLP1") == "arjuna"
    assert to_slp1("kṛṣṇa", "IAST") == "kfzRa"
    assert to_slp1("कृष्ण", "Devanagari") == "kfzRa"
    
    # Mixed/Ambiguous cases
    # SLP1 'a' vs Devanagari 'अ'
    assert to_slp1("अ", "Devanagari") == "a"
