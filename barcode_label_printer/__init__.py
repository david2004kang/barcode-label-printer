"""
Barcode Label Printer: A Python package for generating barcode labels and printing.

This package provides functionality for:
- Generating SVG labels from JSON configuration
- Printing labels to various printers (Windows native, PDF, Niimbot thermal printers)
- Generating barcodes (EAN13, Code128)
"""

from .renderer import BarcodeGenerator, LabelRenderer
from .printer import SvgPrinter

try:
    from .printer.niimbot import NiimbotPrinter
    __all__ = ["BarcodeGenerator", "LabelRenderer", "SvgPrinter", "NiimbotPrinter"]
except ImportError:
    __all__ = ["BarcodeGenerator", "LabelRenderer", "SvgPrinter"]

__version__ = "0.1.0"
