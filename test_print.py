"""
Test script for barcode-label-printer package
"""
import json
import sys
from pathlib import Path

# Import the package
try:
    from barcode_label_printer import LabelRenderer, SvgPrinter
    print("✓ Package imported successfully")
except ImportError as e:
    print(f"✗ Failed to import package: {e}")
    print("Please install the package first: pip install barcode-label-printer")
    sys.exit(1)

# Load test JSON configuration
json_path = Path("test_label.json")
if not json_path.exists():
    print(f"✗ JSON file not found: {json_path}")
    print("Please ensure test_label.json exists in the current directory")
    sys.exit(1)

# Load configuration
print(f"\nLoading configuration from: {json_path}")
with open(json_path, "r", encoding="utf-8") as f:
    config = json.load(f)

print(f"Canvas size: {config['canvas']['width_mm']}mm x {config['canvas']['height_mm']}mm")
print(f"Elements: {len(config['elements'])}")

# Render label to SVG
output_svg = "test_output.svg"
print(f"\nRendering label to: {output_svg}")
renderer = LabelRenderer()
try:
    renderer.render(config, output_svg, config_path=str(json_path))
    print("✓ Label rendered successfully")
except Exception as e:
    print(f"✗ Failed to render label: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Setup printer
print("\nSetting up printer...")
printer = SvgPrinter()

# List available printers
print("Available printers:")
available_printers = printer.get_available_printers()
for p in available_printers:
    print(f"  - {p}")

# Set printer to "Rongta RP5xx Series"
target_printer = "Rongta RP5xx Series"
if target_printer in available_printers:
    print(f"\nSetting printer to: {target_printer}")
    if printer.set_printer(target_printer):
        print("✓ Printer set successfully")
    else:
        print("✗ Failed to set printer")
        sys.exit(1)
else:
    print(f"\n⚠ Warning: '{target_printer}' not found in available printers")
    if available_printers:
        print(f"Using first available printer: {available_printers[0]}")
        printer.set_printer(available_printers[0])
    else:
        print("✗ No printers available")
        sys.exit(1)

# Print the label
print(f"\nPrinting {output_svg}...")
try:
    success = printer.print_svg(output_svg)
    if success:
        print("✓ Print job sent successfully!")
        print(f"\nLabel file: {Path(output_svg).absolute()}")
    else:
        print("✗ Print job failed")
        sys.exit(1)
except Exception as e:
    print(f"✗ Error during printing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*50)
print("Test completed successfully!")
print("="*50)
