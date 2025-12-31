# -*- coding: utf-8 -*-
"""
Barcode Generator: Generate barcode SVG fragments
"""
import logging
import re
from io import BytesIO
from xml.etree import ElementTree as ET

from barcode import EAN13, Code128
from barcode.writer import SVGWriter

# Barcode generator mapping
BARCODE_MAP = {
    "ean13": EAN13,
    "code128": Code128,
}


class BarcodeGenerator:
    """Generate barcode SVG fragments."""

    def __init__(self):
        """Initialize the barcode generator."""
        self.barcode_map = BARCODE_MAP.copy()

    def generate(
        self,
        barcode_type: str,
        value: str,
        module_height: float = 15.0,
        module_width: float = 0.2,
        write_text: bool = False,
        width_mm: float = None,
        height_mm: float = None,
    ) -> str:
        """
        Generate barcode SVG fragment (without <svg> tag).

        Args:
            barcode_type: Barcode type ("ean13" or "code128")
            value: Barcode value
            module_height: Module height in mm
            module_width: Module width in mm
            write_text: Whether to show text below barcode
            width_mm: Target width in mm (optional, for scaling)
            height_mm: Target height in mm (optional, for scaling)

        Returns:
            SVG fragment string (group element)
        """
        # Validate value
        if not value or not isinstance(value, (str, bytes)):
            logging.warning(
                "Barcode value is empty or invalid for type %s: %s", barcode_type, value
            )
            return '<g id="barcode_error" />'

        # Convert value to string
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="ignore")
        else:
            value = str(value).strip()

        # Check again after conversion
        if not value:
            logging.warning("Barcode value is empty after conversion for type %s", barcode_type)
            return '<g id="barcode_error" />'

        # Map barcode type
        barcode_type_key = barcode_type.lower()
        if barcode_type_key not in self.barcode_map:
            logging.error("Unknown barcode type: %s", barcode_type)
            return '<g id="barcode_error" />'

        barcode_cls = self.barcode_map[barcode_type_key]

        writer_options = {
            "module_height": module_height,
            "module_width": module_width,
            "quiet_zone": 0,
            "unit": "mm",
            "write_text": write_text,
        }

        if write_text:
            writer_options["font_size"] = 10  # pt
        else:
            writer_options["font_size"] = 0
            writer_options["text_distance"] = 0

        try:
            writer = SVGWriter()
            writer.set_options(writer_options)
            barcode = barcode_cls(value, writer=writer)
            output = BytesIO()
            barcode.write(output, options=writer_options)
            svg_data = output.getvalue().decode("utf-8")

            # Find SVG group element
            g_start = svg_data.find("<g")
            g_end = svg_data.rfind("</g>")

            if g_start == -1 or g_end == -1:
                logging.warning(
                    "Could not find SVG group element in barcode output for value: %s", value
                )
                return '<g id="barcode_error" />'

            svg_fragment = svg_data[g_start : g_end + 4]
        except (IndexError, ValueError, AttributeError) as e:
            logging.error(
                "Failed to generate barcode for type %s with value '%s': %s",
                barcode_type,
                value,
                str(e),
            )
            return '<g id="barcode_error" />'
        except Exception as e:
            logging.error(
                "Unexpected error generating barcode for type %s with value '%s': %s",
                barcode_type,
                value,
                str(e),
            )
            return '<g id="barcode_error" />'

        # Parse group content and scale if needed
        try:
            group_element = ET.fromstring(svg_fragment)
            rects = [
                child
                for child in group_element
                if child.tag == "rect" and not child.attrib.get("width", "").endswith("%")
            ]

            if rects and (module_width or module_height) and (width_mm or height_mm):
                # Calculate original dimensions
                min_x = min(
                    float(rect.attrib.get("x", "0").replace("mm", "")) for rect in rects
                )
                max_x = max(
                    float(rect.attrib.get("x", "0").replace("mm", ""))
                    + float(rect.attrib.get("width", "0").replace("mm", ""))
                    for rect in rects
                )
                min_y = min(
                    float(rect.attrib.get("y", "0").replace("mm", "")) for rect in rects
                )
                max_y = max(
                    float(rect.attrib.get("y", "0").replace("mm", ""))
                    + float(rect.attrib.get("height", "0").replace("mm", ""))
                    for rect in rects
                )
                orig_w = max_x - min_x
                orig_h = max_y - min_y

                scale_x = 1.0
                scale_y = 1.0
                if module_width and width_mm:
                    scale_x = width_mm / orig_w
                elif width_mm:
                    scale_x = width_mm / orig_w
                if module_height and height_mm:
                    scale_y = height_mm / orig_h
                elif height_mm:
                    scale_y = height_mm / orig_h

                # Scale all rects
                for rect in rects:
                    rect.attrib["x"] = str(
                        (float(rect.attrib.get("x", "0").replace("mm", "")) - min_x) * scale_x
                    )
                    rect.attrib["width"] = str(
                        float(rect.attrib.get("width", "0").replace("mm", "")) * scale_x
                    )
                    rect.attrib["y"] = str(
                        (float(rect.attrib.get("y", "0").replace("mm", "")) - min_y) * scale_y
                    )
                    rect.attrib["height"] = str(
                        float(rect.attrib.get("height", "0").replace("mm", "")) * scale_y
                    )
                svg_fragment = ET.tostring(group_element, encoding="unicode")
            else:
                svg_fragment = ET.tostring(group_element, encoding="unicode")
        except ET.ParseError as e:
            logging.warning("Could not parse and clean barcode SVG fragment. Error: %s", e)

        # Remove white background rect if present
        svg_fragment = re.sub(
            r'<rect width="100%" height="100%" style="fill:white"\s*/?>', "", svg_fragment
        )
        return svg_fragment
