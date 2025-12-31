"""
Tests for LabelRenderer
"""
import json
import pytest
import tempfile
from pathlib import Path

from barcode_label_printer import LabelRenderer


def test_renderer_initialization():
    """Test LabelRenderer initialization."""
    renderer = LabelRenderer()
    assert renderer is not None
    assert renderer.barcode_generator is not None


def test_render_simple_label():
    """Test rendering a simple label."""
    renderer = LabelRenderer()
    
    config = {
        "canvas": {
            "width_mm": 100,
            "height_mm": 50
        },
        "elements": [
            {
                "type": "text",
                "value": "Test",
                "x_mm": 5,
                "y_mm": 5,
                "font_size_pt": 12
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        output_path = f.name
    
    try:
        renderer.render(config, output_path)
        assert Path(output_path).exists()
        assert Path(output_path).stat().st_size > 0
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '<svg' in content.lower()
            assert 'Test' in content
    finally:
        if Path(output_path).exists():
            Path(output_path).unlink()


def test_render_with_barcode():
    """Test rendering label with barcode."""
    renderer = LabelRenderer()
    
    config = {
        "canvas": {
            "width_mm": 100,
            "height_mm": 50
        },
        "elements": [
            {
                "type": "barcode",
                "barcode_type": "code128",
                "value": "123456789012",
                "x_mm": 5,
                "y_mm": 5,
                "width_mm": 80,
                "height_mm": 20
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        output_path = f.name
    
    try:
        renderer.render(config, output_path)
        assert Path(output_path).exists()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '<svg' in content.lower()
    finally:
        if Path(output_path).exists():
            Path(output_path).unlink()


def test_render_with_box():
    """Test rendering label with box element."""
    renderer = LabelRenderer()
    
    config = {
        "canvas": {
            "width_mm": 100,
            "height_mm": 50
        },
        "elements": [
            {
                "type": "box",
                "x_mm": 5,
                "y_mm": 5,
                "width_mm": 90,
                "height_mm": 40,
                "fill_color": "black"
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        output_path = f.name
    
    try:
        renderer.render(config, output_path)
        assert Path(output_path).exists()
    finally:
        if Path(output_path).exists():
            Path(output_path).unlink()
