"""
Self-test for barcode-label-printer package
This test verifies that the package can be installed and basic functionality works.
"""
import json
import sys
import tempfile
from pathlib import Path

# Test imports
try:
    from barcode_label_printer import LabelRenderer, SvgPrinter, BarcodeGenerator
    print("✓ Core modules imported successfully")
except ImportError as e:
    print(f"✗ Failed to import core modules: {e}")
    sys.exit(1)

# Test optional imports
try:
    from barcode_label_printer import NiimbotPrinter
    NIIMBOT_AVAILABLE = True
    print("✓ NiimbotPrinter imported successfully")
except ImportError:
    NIIMBOT_AVAILABLE = False
    print("⚠ NiimbotPrinter not available (optional dependency)")

# Test version
try:
    import barcode_label_printer
    version = barcode_label_printer.__version__
    print(f"✓ Package version: {version}")
    if not version or version == "0.0.0":
        print("⚠ Warning: Version is 0.0.0 or empty")
except AttributeError:
    print("⚠ Warning: __version__ not found")

# Test BarcodeGenerator
print("\nTesting BarcodeGenerator...")
try:
    generator = BarcodeGenerator()
    
    # Test Code128
    result = generator.generate("code128", "123456789012")
    assert result.startswith("<g"), "Barcode should return SVG group"
    assert 'id="barcode_error"' not in result, "Barcode generation should succeed"
    print("✓ Code128 barcode generation works")
    
    # Test EAN13
    result = generator.generate("ean13", "1234567890128")
    assert result.startswith("<g"), "Barcode should return SVG group"
    assert 'id="barcode_error"' not in result, "Barcode generation should succeed"
    print("✓ EAN13 barcode generation works")
    
    # Test invalid barcode type
    result = generator.generate("invalid", "123456789012")
    assert 'id="barcode_error"' in result, "Invalid barcode type should return error"
    print("✓ Error handling for invalid barcode type works")
    
except Exception as e:
    print(f"✗ BarcodeGenerator test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test LabelRenderer
print("\nTesting LabelRenderer...")
try:
    renderer = LabelRenderer()
    
    # Create a test configuration
    test_config = {
        "canvas": {
            "width_mm": 100,
            "height_mm": 50
        },
        "elements": [
            {
                "type": "text",
                "value": "Test Label",
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
            },
            {
                "type": "box",
                "x_mm": 5,
                "y_mm": 40,
                "width_mm": 90,
                "height_mm": 5,
                "fill_color": "black"
            }
        ]
    }
    
    # Render to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        output_path = f.name
    
    try:
        renderer.render(test_config, output_path)
        
        # Verify file was created
        assert Path(output_path).exists(), "SVG file should be created"
        assert Path(output_path).stat().st_size > 0, "SVG file should not be empty"
        
        # Verify SVG content
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '<svg' in content.lower(), "SVG file should contain <svg> tag"
            assert 'Test Label' in content, "SVG should contain text element"
        
        print("✓ Label rendering works")
        print(f"✓ Generated SVG file: {output_path}")
        
    finally:
        # Clean up
        if Path(output_path).exists():
            Path(output_path).unlink()
    
except Exception as e:
    print(f"✗ LabelRenderer test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test SvgPrinter (basic initialization)
print("\nTesting SvgPrinter...")
try:
    printer = SvgPrinter()
    
    # Test printer list (may be empty in CI environment, which is OK)
    printers = printer.get_available_printers()
    assert isinstance(printers, list), "get_available_printers() should return a list"
    print(f"✓ SvgPrinter initialized (found {len(printers)} printers)")
    
    # Test Niimbot serial ports (if available)
    if NIIMBOT_AVAILABLE:
        ports = printer.get_niimbot_serial_ports()
        assert isinstance(ports, list), "get_niimbot_serial_ports() should return a list"
        print(f"✓ Niimbot serial ports check works (found {len(ports)} ports)")
    
except Exception as e:
    print(f"✗ SvgPrinter test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test NiimbotPrinter (if available)
if NIIMBOT_AVAILABLE:
    print("\nTesting NiimbotPrinter...")
    try:
        # Test initialization
        printer = NiimbotPrinter(model="b21", connection_type="usb")
        assert printer.model == "b21", "Model should be set correctly"
        assert printer.connection_type == "usb", "Connection type should be set correctly"
        print("✓ NiimbotPrinter initialization works")
        
        # Test serial port listing
        ports = NiimbotPrinter.list_serial_ports()
        print(f"✓ Serial port listing works (found {len(ports)} ports)")
        
        # Test unsupported model
        try:
            NiimbotPrinter(model="invalid", connection_type="usb")
            print("✗ Should raise ValueError for invalid model")
            sys.exit(1)
        except ValueError:
            print("✓ Error handling for invalid model works")
        
    except Exception as e:
        print(f"✗ NiimbotPrinter test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Test with real JSON file if available
print("\nTesting with JSON configuration file...")
json_files = list(Path(".").glob("*.json")) + list(Path("tests").glob("*.json"))
if json_files:
    test_json = json_files[0]
    print(f"Using JSON file: {test_json}")
    try:
        with open(test_json, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Validate configuration structure
        assert "canvas" in config, "Config should have 'canvas' key"
        assert "elements" in config, "Config should have 'elements' key"
        assert "width_mm" in config["canvas"], "Canvas should have 'width_mm'"
        assert "height_mm" in config["canvas"], "Canvas should have 'height_mm'"
        
        # Render test
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            output_path = f.name
        
        try:
            renderer.render(config, output_path, config_path=str(test_json))
            assert Path(output_path).exists(), "SVG file should be created"
            print(f"✓ JSON configuration rendering works")
        finally:
            if Path(output_path).exists():
                Path(output_path).unlink()
    except Exception as e:
        print(f"⚠ JSON file test skipped: {e}")
else:
    print("⚠ No JSON configuration files found for testing")

print("\n" + "="*50)
print("All self-tests passed! ✓")
print("="*50)
print("\nPackage is ready for distribution.")
