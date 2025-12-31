"""
Tests for SvgPrinter
"""
import pytest

from barcode_label_printer import SvgPrinter


def test_printer_initialization():
    """Test SvgPrinter initialization."""
    printer = SvgPrinter()
    assert printer is not None
    assert printer.current_printer is None


def test_get_available_printers():
    """Test getting available printers."""
    printer = SvgPrinter()
    printers = printer.get_available_printers()
    assert isinstance(printers, list)
    # In CI environments, there may be no printers, which is OK


def test_set_printer():
    """Test setting printer."""
    printer = SvgPrinter()
    printers = printer.get_available_printers()
    
    if printers:
        result = printer.set_printer(printers[0])
        # May fail if printer is not actually available, so we just check it doesn't crash
        assert isinstance(result, bool)
    else:
        # No printers available (common in CI), test with invalid name
        result = printer.set_printer("NonExistentPrinter")
        assert result is False
        # In CI, this is expected behavior


def test_get_current_printer():
    """Test getting current printer."""
    printer = SvgPrinter()
    current = printer.get_current_printer()
    assert current is None or isinstance(current, str)
