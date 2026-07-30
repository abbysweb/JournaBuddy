from app.services.symbolic_checker import SymbolicChecker

def test_check_acronyms_undefined():
    checker = SymbolicChecker()
    text = "The quick brown fox jumps over the LAZY dog."
    result = checker.check(text)
    assert "LAZY" in result.undefined_acronyms

def test_check_acronyms_defined():
    checker = SymbolicChecker()
    text = "The quick brown fox jumps over the Lazy Dog (LAZY)."
    result = checker.check(text)
    assert "LAZY" not in result.undefined_acronyms
    assert "LAZY" in result.defined_acronyms
    assert result.defined_acronyms["LAZY"] == "Lazy Dog"

def test_check_missing_sections():
    checker = SymbolicChecker()
    text = "Abstract\n\nThis is an abstract.\n\nIntroduction\n\nWe start here."
    result = checker.check(text)
    assert "abstract" in result.found_sections
    assert "introduction" in result.found_sections
    assert "methodology" in result.missing_sections
    assert "results" in result.missing_sections

def test_check_readability():
    checker = SymbolicChecker()
    # A simple sentence with no passive voice
    text = "The cat sat on the mat."
    result = checker.check(text)
    assert result.passive_voice_percent == 0.0
    
    # A sentence with passive voice
    text_passive = "The ball was thrown by the boy."
    result_passive = checker.check(text_passive)
    assert result_passive.passive_voice_percent > 0.0
