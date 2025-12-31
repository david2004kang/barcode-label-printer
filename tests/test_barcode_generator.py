"""
Tests for barcode generator
"""
import pytest
from barcode_label_printer import BarcodeGenerator


def test_generate_code128():
    """Test Code128 barcode generation."""
    generator = BarcodeGenerator()
    result = generator.generate("code128", "123456789012")
    assert result.startswith("<g")
    assert 'id="barcode_error"' not in result


def test_generate_ean13():
    """Test EAN13 barcode generation."""
    generator = BarcodeGenerator()
    result = generator.generate("ean13", "1234567890128")
    assert result.startswith("<g")
    assert 'id="barcode_error"' not in result


def test_invalid_barcode_type():
    """Test invalid barcode type."""
    generator = BarcodeGenerator()
    result = generator.generate("invalid", "123456789012")
    assert 'id="barcode_error"' in result


def test_empty_value():
    """Test empty barcode value."""
    generator = BarcodeGenerator()
    result = generator.generate("code128", "")
    assert 'id="barcode_error"' in result
