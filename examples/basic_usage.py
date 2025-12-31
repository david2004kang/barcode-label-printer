"""
Basic usage example for barcode-label-printer
"""
import json
from barcode_label_printer import LabelRenderer, SvgPrinter

# Example 1: Generate a label from JSON configuration
config = {
    "canvas": {
        "width_mm": 100,
        "height_mm": 50
    },
    "elements": [
        {
            "type": "text",
            "value": "Product Name",
            "x_mm": 5,
            "y_mm": 5,
            "font_size_pt": 12,
            "bold": True
        },
        {
            "type": "barcode",
            "barcode_type": "code128",
            "value": "123456789012",
            "x_mm": 5,
            "y_mm": 15,
            "width_mm": 80,
            "height_mm": 20,
            "write_text": False
        }
    ]
}

# Render label to SVG
renderer = LabelRenderer()
renderer.render(config, "output_label.svg")

# Example 2: Print the label
printer = SvgPrinter()

# Option 1: Print to default printer
printer.print_svg_to_default("output_label.svg")

# Option 2: Print to specific printer
printers = printer.get_available_printers()
if printers:
    printer.set_printer(printers[0])
    printer.print_svg("output_label.svg")
