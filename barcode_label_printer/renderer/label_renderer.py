# -*- coding: utf-8 -*-
"""
Label Renderer: Render labels from JSON configuration to SVG
"""
import logging
from pathlib import Path
from xml.etree import ElementTree as ET

import svgwrite

from .barcode_generator import BarcodeGenerator


class RawSvgContainer:
    """A container for raw SVG content that can be added to an svgwrite drawing."""

    def __init__(self, raw_svg: str):
        """
        Initialize raw SVG container.

        Args:
            raw_svg: SVG fragment string starting with <g>
        """
        if not isinstance(raw_svg, str) or not raw_svg.strip().startswith("<g"):
            raise TypeError("RawSvgContainer content must be an SVG fragment string.")
        self.raw_svg = raw_svg

    def get_xml(self):
        """Parse the raw SVG string and return it as an ElementTree element."""
        elem = ET.fromstring(self.raw_svg)
        # Remove white background rect if present
        for child in list(elem):
            if (
                child.tag == "rect"
                and child.attrib.get("width") == "100%"
                and child.attrib.get("height") == "100%"
                and child.attrib.get("style", "").replace(" ", "") in ["fill:white", "fill:#ffffff;"]
            ):
                elem.remove(child)
        return elem


class LabelRenderer:
    """Render labels from JSON configuration to SVG."""

    def __init__(self):
        """Initialize the label renderer."""
        self.barcode_generator = BarcodeGenerator()

    def render(
        self,
        config: dict,
        output_svg_path: str,
        config_path: str = None,
        debug: bool = False,
    ):
        """
        Render the complete label SVG based on the configuration.

        Args:
            config: Label configuration dictionary
            output_svg_path: Path to output SVG file
            config_path: Path to the config file (for resolving relative paths)
            debug: Enable debug mode (saves individual elements as separate SVG files)
        """
        if debug:
            debug_dir = Path("svg_debug")
            debug_dir.mkdir(exist_ok=True)
            logging.info(f"Debug mode enabled. Saving individual elements to '{debug_dir}/'")

        # Determine config directory for resolving relative paths
        if config_path:
            config_dir = Path(config_path).parent
        else:
            config_dir = Path(output_svg_path).parent

        canvas_w_mm = config["canvas"]["width_mm"]
        canvas_h_mm = config["canvas"]["height_mm"]

        dwg = svgwrite.Drawing(
            output_svg_path,
            size=(f"{canvas_w_mm}mm", f"{canvas_h_mm}mm"),
            viewBox=f"0 0 {canvas_w_mm} {canvas_h_mm}",
            profile="full",
            debug=False,  # Disable validation due to bug with 'mm' units in transforms
        )

        # Add white background
        dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="white"))

        # Render each element
        for elem in config["elements"]:
            self._render_element(elem, dwg, config_dir, debug, debug_dir if debug else None)

        dwg.save(pretty=True)
        logging.info(f"SVG saved to {output_svg_path}")

    def _render_element(self, elem: dict, dwg: svgwrite.Drawing, config_dir: Path, debug: bool, debug_dir: Path = None):
        """Render a single element."""
        x_mm = elem["x_mm"]
        y_mm = elem["y_mm"]
        elem_type = elem["type"]

        if elem_type == "barcode":
            self._render_barcode(elem, dwg, x_mm, y_mm)
        elif elem_type == "text":
            self._render_text(elem, dwg, x_mm, y_mm, debug, debug_dir)
        elif elem_type == "box":
            self._render_box(elem, dwg, x_mm, y_mm, debug, debug_dir)
        elif elem_type == "picture":
            self._render_picture(elem, dwg, x_mm, y_mm, config_dir, debug, debug_dir)
        else:
            logging.warning("Unknown element type: %s", elem_type)

    def _render_barcode(self, elem: dict, dwg: svgwrite.Drawing, x_mm: float, y_mm: float):
        """Render a barcode element."""
        barcode_options = {
            "module_height": elem.get("height_mm", 9),
            "module_width": elem.get("module_width", 0.2),
            "write_text": elem.get("write_text", False),
            "width_mm": elem.get("width_mm"),
            "height_mm": elem.get("height_mm"),
        }
        barcode_svg_str = self.barcode_generator.generate(
            elem["barcode_type"], elem["value"], **barcode_options
        )

        # Skip if barcode generation failed
        if 'id="barcode_error"' in barcode_svg_str:
            logging.warning(
                "Skipping barcode element %s due to generation error", elem.get("id", "unknown")
            )
            return

        # Parse group to get actual dimensions
        try:
            group_element = ET.fromstring(barcode_svg_str)
        except ET.ParseError as e:
            logging.error(
                "Failed to parse barcode SVG for element %s: %s",
                elem.get("id", "unknown"),
                str(e),
            )
            return

        rects = [
            child
            for child in group_element
            if child.tag == "rect" and not child.attrib.get("width", "").endswith("%")
        ]

        min_x = (
            min(float(rect.attrib.get("x", "0").replace("mm", "")) for rect in rects) if rects else 0
        )
        max_x = (
            max(
                float(rect.attrib.get("x", "0").replace("mm", ""))
                + float(rect.attrib.get("width", "0").replace("mm", ""))
                for rect in rects
            )
            if rects
            else 1
        )
        min_y = (
            min(float(rect.attrib.get("y", "0").replace("mm", "")) for rect in rects) if rects else 0
        )
        max_y = (
            max(
                float(rect.attrib.get("y", "0").replace("mm", ""))
                + float(rect.attrib.get("height", "0").replace("mm", ""))
                for rect in rects
            )
            if rects
            else 1
        )
        orig_w = max_x - min_x
        orig_h = max_y - min_y

        # Calculate scale & translate
        scale_x = elem.get("width_mm", orig_w) / orig_w if orig_w > 0 else 1
        scale_y = elem.get("height_mm", orig_h) / orig_h if orig_h > 0 else 1
        translate_x = elem.get("x_mm", 0) - min_x * scale_x
        translate_y = elem.get("y_mm", 0) - min_y * scale_y

        # Apply matrix transform
        transform = f"matrix({scale_x},0,0,{scale_y},{translate_x},{translate_y})"
        transform_group = dwg.g(transform=transform)
        transform_group.add(RawSvgContainer(barcode_svg_str))
        dwg.add(transform_group)

    def _render_text(self, elem: dict, dwg: svgwrite.Drawing, x_mm: float, y_mm: float, debug: bool, debug_dir: Path = None):
        """Render a text element."""
        font_weight = "bold" if elem.get("bold") else "normal"
        font_size_pt = elem.get("font_size_pt", 10)
        font_size_mm = font_size_pt * 0.352778  # Convert pt to mm

        letter_spacing_pt = elem.get("letter_spacing_pt", 0)
        letter_spacing_mm = letter_spacing_pt * 0.352778

        text_color = elem.get("text_color", "black")
        bg_color = elem.get("bg_color", None)

        # Create text element
        text_element = dwg.text(
            elem["value"],
            insert=(x_mm, y_mm),
            font_size=font_size_mm,
            font_family="Arial",
            font_weight=font_weight,
            fill=text_color,
            dominant_baseline="text-before-edge",
            letter_spacing=letter_spacing_mm,
        )

        # Add background if specified
        bg_rect = None
        if bg_color:
            est_text_width_mm = len(elem["value"]) * font_size_mm * 0.65
            if len(elem["value"]) > 1:
                est_text_width_mm += (len(elem["value"]) - 1) * letter_spacing_mm
            est_text_height_mm = font_size_mm * 1.1

            bg_rect = dwg.rect(
                insert=(x_mm, y_mm),
                size=(est_text_width_mm, est_text_height_mm),
                fill=bg_color,
                stroke="none",
            )
            dwg.add(bg_rect)

        dwg.add(text_element)

        if debug and debug_dir:
            sanitized_text_data = (
                elem["value"].replace(":", "_").replace("/", "_").replace("\\", "_")
            )
            debug_text_path = debug_dir / f"text_{sanitized_text_data}.svg"
            debug_dwg = svgwrite.Drawing(
                debug_text_path, size=("100px", "100px"), profile="full"
            )
            if bg_color and bg_rect:
                debug_dwg.add(bg_rect)
            debug_dwg.add(text_element)
            debug_dwg.save()

    def _render_box(self, elem: dict, dwg: svgwrite.Drawing, x_mm: float, y_mm: float, debug: bool, debug_dir: Path = None):
        """Render a box element."""
        width_mm = elem["width_mm"]
        height_mm = elem["height_mm"]
        fill_color = elem.get("fill_color", "black")

        box_element = dwg.rect(
            insert=(x_mm, y_mm), size=(width_mm, height_mm), fill=fill_color
        )
        dwg.add(box_element)

        if debug and debug_dir:
            debug_box_path = debug_dir / f"box_at_{x_mm}_{y_mm}.svg"
            debug_dwg = svgwrite.Drawing(
                debug_box_path, size=("100px", "100px"), profile="full"
            )
            debug_dwg.add(box_element)
            debug_dwg.save()

    def _render_picture(self, elem: dict, dwg: svgwrite.Drawing, x_mm: float, y_mm: float, config_dir: Path, debug: bool, debug_dir: Path = None):
        """Render a picture element."""
        svg_file = elem.get("svg_file")
        if not svg_file:
            logging.warning(
                "Picture element %s missing 'svg_file' attribute, skipping",
                elem.get("id", "unknown")
            )
            return

        # Resolve SVG file path
        svg_path = config_dir / svg_file
        if not svg_path.exists():
            logging.warning(
                "SVG file not found for picture element %s: %s, skipping",
                elem.get("id", "unknown"),
                svg_path
            )
            return

        try:
            # Load and parse SVG
            with open(svg_path, "r", encoding="utf-8") as f:
                svg_content = f.read()

            svg_tree = ET.parse(svg_path)
            svg_root = svg_tree.getroot()

            # Extract dimensions
            orig_w = None
            orig_h = None

            if "width" in svg_root.attrib and "height" in svg_root.attrib:
                orig_w = float(svg_root.attrib["width"].replace("mm", "").replace("px", ""))
                orig_h = float(svg_root.attrib["height"].replace("mm", "").replace("px", ""))
            elif "viewBox" in svg_root.attrib:
                viewbox = svg_root.attrib["viewBox"].split()
                if len(viewbox) >= 4:
                    orig_w = float(viewbox[2])
                    orig_h = float(viewbox[3])

            if orig_w is None or orig_h is None or orig_w <= 0 or orig_h <= 0:
                logging.warning(
                    "Could not determine dimensions for SVG file %s, using default 100x100",
                    svg_path
                )
                orig_w = 100.0
                orig_h = 100.0

            # Calculate scale
            target_w = elem.get("width_mm")
            target_h = elem.get("height_mm")

            if target_w is not None and target_h is not None:
                scale_x = target_w / orig_w if orig_w > 0 else 1
                scale_y = target_h / orig_h if orig_h > 0 else 1
            elif target_w is not None:
                scale_x = target_w / orig_w if orig_w > 0 else 1
                scale_y = scale_x
            elif target_h is not None:
                scale_y = target_h / orig_h if orig_h > 0 else 1
                scale_x = scale_y
            else:
                scale_x = 1.0
                scale_y = 1.0

            # Extract inner content
            svg_root_parsed = ET.fromstring(svg_content)
            inner_elements = list(svg_root_parsed)

            if not inner_elements:
                logging.warning(
                    "SVG file %s appears to be empty, skipping picture element %s",
                    svg_path,
                    elem.get("id", "unknown")
                )
                return

            # Create transform group
            transform = f"translate({x_mm},{y_mm}) scale({scale_x},{scale_y})"
            transform_group = dwg.g(transform=transform)

            # Add each child element
            for child in inner_elements:
                child_str = ET.tostring(child, encoding="unicode")
                wrapped_str = f"<g>{child_str}</g>"
                try:
                    transform_group.add(RawSvgContainer(wrapped_str))
                except (TypeError, ValueError) as e:
                    logging.warning(
                        "Could not add SVG element from %s: %s, skipping",
                        svg_path,
                        e
                    )
                    continue

            dwg.add(transform_group)

            if debug and debug_dir:
                debug_picture_path = debug_dir / f"picture_{elem.get('id', 'unknown')}.svg"
                debug_dwg = svgwrite.Drawing(
                    debug_picture_path, size=("100px", "100px"), profile="full"
                )
                debug_dwg.add(transform_group)
                debug_dwg.save()

        except Exception as e:
            logging.error(
                "Error processing picture element %s: %s",
                elem.get("id", "unknown"),
                e,
                exc_info=True
            )
