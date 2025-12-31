"""
Niimbot printer usage example
"""
from barcode_label_printer import LabelRenderer, NiimbotPrinter

# Generate label
config = {
    "canvas": {
        "width_mm": 50,
        "height_mm": 30
    },
    "elements": [
        {
            "type": "barcode",
            "barcode_type": "code128",
            "value": "123456789012",
            "x_mm": 5,
            "y_mm": 5,
            "width_mm": 40,
            "height_mm": 15
        }
    ]
}

renderer = LabelRenderer()
renderer.render(config, "label.svg")

# Convert SVG to image (you'll need to do this separately or use svg_printer)
# For now, assuming you have a PNG/BMP file

# Print with Niimbot printer
printer = NiimbotPrinter(model="b21", connection_type="usb")
if printer.connect():
    printer.print_image_file("label.png", density=3)
    printer.disconnect()
