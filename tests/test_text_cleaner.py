# tests/test_text_cleaner.py
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.text_cleaner import clean_text

print("Testing clean_text...\n")

# Test 1: Windows line endings (\r\n)
def test_windows_line_endings():
    text = "Line1\r\nLine2\r\nLine3"
    result = clean_text(text)
    expected = "Line1\nLine2\nLine3"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print("[OK] Windows line endings normalized correctly")

# Test 2: Mac line endings (\r)
def test_mac_line_endings():
    text = "Line1\rLine2\rLine3"
    result = clean_text(text)
    expected = "Line1\nLine2\nLine3"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print("[OK] Mac line endings normalized correctly")

# Test 3: Multiple spaces
def test_multiple_spaces():
    text = "Hello    world    here"
    result = clean_text(text)
    expected = "Hello world here"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print("[OK] Multiple spaces normalized to single space")

# Test 4: Tabs
def test_tabs():
    text = "Hello\t\tworld\there"
    result = clean_text(text)
    expected = "Hello world here"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print("[OK] Tabs normalized to single space")

# Test 5: Mixed spaces and tabs
def test_mixed_spaces_tabs():
    text = "Hello  \t  world  \t\t  here"
    result = clean_text(text)
    expected = "Hello world here"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print("[OK] Mixed spaces and tabs normalized correctly")

# Test 6: Trailing whitespace on lines
def test_trailing_whitespace():
    text = "Line1   \nLine2\t\t\nLine3  "
    result = clean_text(text)
    expected = "Line1\nLine2\nLine3"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print("[OK] Trailing whitespace removed from lines")

# Test 7: Leading and trailing whitespace
def test_leading_trailing_whitespace():
    text = "   \n  Line1\nLine2  \n  "
    result = clean_text(text)
    expected = "Line1\nLine2"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print("[OK] Leading and trailing whitespace removed")

# Test 8: Empty string
def test_empty_string():
    text = ""
    result = clean_text(text)
    expected = ""
    assert result == expected, f"Expected empty string, got '{result}'"
    print("[OK] Empty string handled correctly")

# Test 9: Whitespace only
def test_whitespace_only():
    text = "   \t  \n  \r\n  \r  "
    result = clean_text(text)
    expected = ""
    assert result == expected, f"Expected empty string, got '{result}'"
    print("[OK] Whitespace-only string returns empty string")

# Test 10: Preserve intentional newlines
def test_preserve_newlines():
    text = "Line1\n\nLine2\n\n\nLine3"
    result = clean_text(text)
    expected = "Line1\n\nLine2\n\n\nLine3"
    assert result == expected, f"Expected newlines preserved, got '{result}'"
    print("[OK] Intentional newlines preserved")

# Test 11: Complex mixed scenario
def test_complex_mixed():
    text = "  Hello    world\r\n\n  \t  Test   \r  End  "
    result = clean_text(text)
    expected = "Hello world\n\n Test\n End"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print("[OK] Complex mixed scenario handled correctly")

# Test 12: Markdown-like content
def test_markdown_content():
    text = "# Title  \r\n\n## Section  \t  \n\nContent   here  "
    result = clean_text(text)
    expected = "# Title\n\n## Section\n\nContent here"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print("[OK] Markdown content cleaned correctly")

# Test 13: Single line with spaces
def test_single_line():
    text = "  Hello    world  "
    result = clean_text(text)
    expected = "Hello world"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print("[OK] Single line cleaned correctly")

# Test 14: Already clean text
def test_already_clean():
    text = "Hello world\nThis is clean"
    result = clean_text(text)
    expected = "Hello world\nThis is clean"
    assert result == expected, f"Expected unchanged, got '{result}'"
    print("[OK] Already clean text unchanged")

# Test 15: Mixed line endings
def test_mixed_line_endings():
    text = "Line1\r\nLine2\rLine3\nLine4"
    result = clean_text(text)
    expected = "Line1\nLine2\nLine3\nLine4"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print("[OK] Mixed line endings normalized correctly")

# Run all tests
def run_all_tests():
    test_windows_line_endings()
    test_mac_line_endings()
    test_multiple_spaces()
    test_tabs()
    test_mixed_spaces_tabs()
    test_trailing_whitespace()
    test_leading_trailing_whitespace()
    test_empty_string()
    test_whitespace_only()
    test_preserve_newlines()
    test_complex_mixed()
    test_markdown_content()
    test_single_line()
    test_already_clean()
    test_mixed_line_endings()
    print("\nAll tests passed! [OK]")

# Execute tests
if __name__ == "__main__":
    run_all_tests()