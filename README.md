# Barcode Label Printer

A Python package for generating barcode labels from JSON configuration and printing to various printers including Niimbot thermal printers.

## Features

- **Label Rendering**: Generate SVG labels from JSON configuration
- **Barcode Generation**: Support for EAN13, Code128 barcode formats
- **Multiple Element Types**: Text, barcode, box, and picture elements
- **Printer Support**: 
  - Windows native printing
  - PDF printing via SumatraPDF
  - Niimbot thermal printers (USB/Bluetooth)
- **Flexible Configuration**: JSON-based label configuration

## Installation

```bash
pip install barcode-label-printer
```

### Optional Dependencies

For Windows native printing:
```bash
pip install barcode-label-printer[windows]
```

For Bluetooth support (Niimbot):
```bash
pip install barcode-label-printer[bluetooth]
```

## Quick Start

### Generate a Label

```python
from barcode_label_printer import LabelRenderer
import json

# Load configuration
with open("label_config.json", "r") as f:
    config = json.load(f)

# Render label to SVG
renderer = LabelRenderer()
renderer.render(config, "output_label.svg")
```

### Print a Label

```python
from barcode_label_printer import SvgPrinter

# Print to default printer
printer = SvgPrinter()
printer.print_svg_to_default("output_label.svg")

# Print to specific printer
printer.set_printer("HP LaserJet")
printer.print_svg("output_label.svg")
```

### Print with Niimbot Printer

```python
from barcode_label_printer import NiimbotPrinter

# Connect and print
printer = NiimbotPrinter(model="b21", connection_type="usb")
if printer.connect():
    printer.print_image_file("label.png", density=3)
    printer.disconnect()
```

## Label Configuration Format

```json
{
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
            "bold": true
        },
        {
            "type": "barcode",
            "barcode_type": "code128",
            "value": "123456789012",
            "x_mm": 5,
            "y_mm": 15,
            "width_mm": 80,
            "height_mm": 20,
            "write_text": false
        }
    ]
}
```

## Supported Element Types

### Text Element
- `type`: "text"
- `value`: Text content
- `x_mm`, `y_mm`: Position
- `font_size_pt`: Font size in points
- `bold`: Boolean
- `text_color`: Color (default: "black")
- `bg_color`: Background color (optional)

### Barcode Element
- `type`: "barcode"
- `barcode_type`: "ean13" or "code128"
- `value`: Barcode value
- `x_mm`, `y_mm`: Position
- `width_mm`, `height_mm`: Size
- `write_text`: Show text below barcode

### Box Element
- `type`: "box"
- `x_mm`, `y_mm`: Position
- `width_mm`, `height_mm`: Size
- `fill_color`: Fill color

### Picture Element
- `type`: "picture"
- `svg_file`: Path to SVG file (relative to config)
- `x_mm`, `y_mm`: Position
- `width_mm`, `height_mm`: Size (optional, maintains aspect ratio)

## Supported Niimbot Models

- B1, B18, B21, B31 (384px width)
- D11, D110 (96px width)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
