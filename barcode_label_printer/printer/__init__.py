"""Printer modules for barcode-label-printer."""

from .svg_printer import SvgPrinter

try:
    from .niimbot.printer import NiimbotPrinter
    __all__ = ["SvgPrinter", "NiimbotPrinter"]
except ImportError:
    __all__ = ["SvgPrinter"]
