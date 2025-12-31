# -*- coding: utf-8 -*-
"""
SVG Printer: Print SVG files to various printers
"""
import io
import logging
import os
import shutil
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET

import PyPDF2

# Windows printing imports (optional)
WINDOWS_PRINT_AVAILABLE = False
try:
    import cairosvg
    import win32api
    import win32con
    import win32print
    import win32ui
    from PIL import Image, ImageDraw, ImageWin

    WINDOWS_PRINT_AVAILABLE = True
except ImportError:
    logging.debug(
        "Windows printing libraries not available. Install pywin32, pillow, and cairosvg for native Windows printing."
    )

# Niimbot printing imports (optional)
NIIMBOT_PRINT_AVAILABLE = False
try:
    from .niimbot.printer import NiimbotPrinter

    NIIMBOT_PRINT_AVAILABLE = True
except ImportError:
    logging.debug("Niimbot printing not available.")


class SvgPrinter:
    """SVG file printing class."""

    def __init__(self):
        """Initialize SVG printer."""
        self.current_printer = None
        self.current_printer_paper = None
        self.custom_paper_width = None  # Custom paper width (mm)
        self.custom_paper_height = None  # Custom paper height (mm)
        self.available_printers = []
        self.inkscape_path = self._find_inkscape()
        self._refresh_printer_list()

        # Niimbot printer settings
        self.niimbot_printer = None
        self.niimbot_model = "b21"
        self.niimbot_connection = "usb"
        self.niimbot_address = None
        self.niimbot_density = 3

    def _find_inkscape(self):
        """Auto-find Inkscape executable path."""
        inkscape_path = shutil.which("inkscape")
        if inkscape_path:
            return inkscape_path

        possible_paths = [
            r"C:\\Program Files\\Inkscape\\inkscape.exe",
            r"C:\\Program Files\\Inkscape\\bin\\inkscape.exe",
            r"C:\\Program Files (x86)\\Inkscape\\inkscape.exe",
            r"C:\\Program Files (x86)\\Inkscape\\bin\\inkscape.exe",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def _ensure_inkscape(self):
        """Ensure Inkscape is available."""
        if not self.inkscape_path:
            logging.error(
                "[Error] Inkscape executable not found. Please install Inkscape or add it to PATH.\n"
                "Or manually install it at C:/Program Files/Inkscape/\n"
                "https://inkscape.org/release/"
            )
            return False
        return True

    def _refresh_printer_list(self):
        """Refresh available printer list."""
        import platform
        
        self.available_printers = []
        
        try:
            system = platform.system()
            
            if system == "Windows":
                # Windows: Use PowerShell
                cmd = [
                    "powershell",
                    "-Command",
                    "Get-Printer | Select-Object Name | Format-Table -HideTableHeaders",
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True)

                if result.returncode == 0:
                    for line in result.stdout.strip().split("\n"):
                        if line.strip():
                            self.available_printers.append(line.strip())
                else:
                    logging.debug("Failed to get printer list: %s", result.stderr)
            elif system == "Linux":
                # Linux: Use lpstat or CUPS
                try:
                    cmd = ["lpstat", "-p"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        for line in result.stdout.strip().split("\n"):
                            if line.startswith("printer"):
                                # Extract printer name from "printer PRINTER_NAME is idle..."
                                parts = line.split()
                                if len(parts) > 1:
                                    self.available_printers.append(parts[1])
                except (subprocess.SubprocessError, FileNotFoundError):
                    # lpstat not available, try CUPS
                    try:
                        cmd = ["lpinfo", "-v"]
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            # Extract printer names from output
                            for line in result.stdout.strip().split("\n"):
                                if "direct" in line.lower() or "network" in line.lower():
                                    # Try to extract printer name
                                    parts = line.split()
                                    if parts:
                                        self.available_printers.append(parts[-1])
                    except (subprocess.SubprocessError, FileNotFoundError):
                        logging.debug("lpstat and lpinfo not available")
            elif system == "Darwin":  # macOS
                # macOS: Use lpstat
                try:
                    cmd = ["lpstat", "-p"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        for line in result.stdout.strip().split("\n"):
                            if line.startswith("printer"):
                                parts = line.split()
                                if len(parts) > 1:
                                    self.available_printers.append(parts[1])
                except (subprocess.SubprocessError, FileNotFoundError):
                    logging.debug("lpstat not available on macOS")
            else:
                logging.debug("Unsupported platform for printer listing: %s", system)
                
        except Exception as e:
            logging.debug("Error listing printers: %s", e)
            # Don't fail, just return empty list

    def get_available_printers(self):
        """
        Get currently available printer names.

        Returns:
            list: List of printer names
        """
        self._refresh_printer_list()
        return self.available_printers.copy()

    def set_printer(
        self, printer_name: str, paper_size: str = None, paper_width: float = None, paper_height: float = None
    ):
        """
        Set current printer.

        Args:
            printer_name: Printer name
            paper_size: Paper size name
            paper_width: Custom paper width (mm)
            paper_height: Custom paper height (mm)

        Returns:
            bool: True if successful
        """
        self._refresh_printer_list()

        if printer_name in self.available_printers:
            self.current_printer = printer_name
            self.current_printer_paper = paper_size
            if paper_width is not None and paper_height is not None:
                self.custom_paper_width = float(paper_width)
                self.custom_paper_height = float(paper_height)
                logging.info(
                    "Printer set to: %s (custom size: %.2f x %.2f mm)",
                    printer_name,
                    self.custom_paper_width,
                    self.custom_paper_height,
                )
            else:
                self.custom_paper_width = None
                self.custom_paper_height = None
                if paper_size:
                    logging.info("Printer set to: %s (paper: %s)", printer_name, paper_size)
                else:
                    logging.info("Printer set to: %s", printer_name)
            return True
        else:
            logging.error("Printer '%s' not found in available printers:", printer_name)
            for printer in self.available_printers:
                logging.info("  - %s", printer)
            return False

    def get_current_printer(self):
        """
        Get current printer.

        Returns:
            str: Current printer name or None
        """
        return self.current_printer

    def set_niimbot_printer(
        self, model: str = "b21", connection: str = "usb", address: str = None, density: int = 3
    ):
        """
        Set Niimbot printer.

        Args:
            model: Printer model (b1, b18, b21, b31, d11, d110)
            connection: Connection type (usb, bluetooth)
            address: Bluetooth MAC address or USB serial port path
            density: Print density (1-5)

        Returns:
            bool: True if successful
        """
        if not NIIMBOT_PRINT_AVAILABLE:
            logging.error(
                "Niimbot printing not available. Please install required dependencies."
            )
            return False

        try:
            self.niimbot_model = model
            self.niimbot_connection = connection
            self.niimbot_address = address
            self.niimbot_density = density

            if model.lower() not in NiimbotPrinter.SUPPORTED_MODELS:
                logging.error("Unsupported Niimbot model: %s", model)
                return False

            logging.info("Niimbot printer configured: %s via %s", model, connection)
            return True

        except (subprocess.SubprocessError, OSError, IOError, AttributeError, ValueError) as e:
            logging.error("Error setting up Niimbot printer: %s", e)
            return False

    def get_niimbot_serial_ports(self):
        """
        Get available serial ports.

        Returns:
            list: List of serial port information
        """
        if not NIIMBOT_PRINT_AVAILABLE:
            return []

        try:
            return NiimbotPrinter.list_serial_ports()
        except (ImportError, AttributeError, OSError, IOError) as e:
            logging.error("Error listing serial ports: %s", e)
            return []

    def _svg_to_pdf_inkscape(self, svg_path: str, pdf_path: str = None):
        """
        Convert SVG to PDF using Inkscape.

        Args:
            svg_path: Path to SVG file
            pdf_path: Path to output PDF file

        Returns:
            str: Path to PDF file or None
        """
        if pdf_path is None:
            pdf_path = str(Path(svg_path).with_suffix(".pdf"))

        try:
            cmd = [
                self.inkscape_path,
                svg_path,
                "--export-type=pdf",
                f"--export-filename={pdf_path}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logging.info("PDF saved to %s", pdf_path)
                return pdf_path
            else:
                logging.error("Inkscape PDF conversion failed: %s", result.stderr)
                return None
        except (subprocess.SubprocessError, OSError, IOError, FileNotFoundError) as e:
            logging.error("Error converting SVG to PDF with Inkscape: %s", e)
            return None

    def _find_sumatra_pdf(self):
        """Auto-find SumatraPDF executable."""
        sumatra_path = shutil.which("SumatraPDF")
        if sumatra_path:
            return sumatra_path

        possible_paths = [
            r"C:\\Program Files\\SumatraPDF\\SumatraPDF.exe",
            r"C:\\Program Files (x86)\\SumatraPDF\\SumatraPDF.exe",
            os.path.expanduser(r"~\AppData\Local\SumatraPDF\SumatraPDF.exe"),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def _is_pdf_landscape(self, pdf_path: str):
        """Check if PDF first page is landscape."""
        try:
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                page = reader.pages[0]
                mediabox = page.mediabox
                width = float(mediabox.width)
                height = float(mediabox.height)
                return width > height
        except (ValueError, TypeError, AttributeError, OSError, IOError) as e:
            logging.warning("Warning: Could not determine PDF orientation: %s", e)
            return False

    def _print_pdf(self, pdf_path: str, printer_name: str = None):
        """
        Print PDF file using SumatraPDF.

        Args:
            pdf_path: Path to PDF file
            printer_name: Printer name (None for default)

        Returns:
            bool: True if successful
        """
        sumatra_path = self._find_sumatra_pdf()
        if not sumatra_path:
            logging.error("SumatraPDF not found. Trying alternative methods...")
            return self._print_pdf_fallback(pdf_path, printer_name)

        landscape = self._is_pdf_landscape(pdf_path)
        settings_parts = ["landscape" if landscape else "portrait"]

        paper_name = self.current_printer_paper
        if paper_name:
            sanitized = paper_name.replace(",", " ")
            settings_parts.append(f"paper={sanitized}")

        print_settings = ",".join(settings_parts)

        try:
            if printer_name:
                cmd = [
                    sumatra_path,
                    "-print-to",
                    printer_name,
                    "-print-settings",
                    print_settings,
                    "-silent",
                    pdf_path,
                ]
            else:
                cmd = [
                    sumatra_path,
                    "-print-to-default",
                    "-print-settings",
                    print_settings,
                    "-silent",
                    pdf_path,
                ]

            logging.info("Using SumatraPDF: %s", " ".join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logging.info("SumatraPDF print job sent successfully")
                return True
            else:
                logging.error("SumatraPDF print failed: %s", result.stderr)
                return self._print_pdf_fallback(pdf_path, printer_name)

        except (subprocess.SubprocessError, OSError, IOError, FileNotFoundError) as e:
            logging.error("Error with SumatraPDF: %s", e)
            return self._print_pdf_fallback(pdf_path, printer_name)

    def _print_pdf_fallback(self, pdf_path: str, printer_name: str = None):
        """Fallback print method."""
        try:
            cmd = [
                "powershell",
                "-Command",
                f'Start-Process -FilePath "{pdf_path}" -Verb Print -WindowStyle Hidden',
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return True
            else:
                logging.error("PowerShell print failed: %s", result.stderr)
                return False

        except (subprocess.SubprocessError, OSError, IOError, FileNotFoundError) as e:
            logging.error("Error in fallback print method: %s", e)
            return False

    def print_svg(self, svg_path: str, force_direct: bool = False):
        """
        Print SVG file to selected printer.

        Args:
            svg_path: Path to SVG file
            force_direct: Force Windows native printing

        Returns:
            bool: True if successful
        """
        if not os.path.exists(svg_path):
            logging.error("Error: SVG file not found: %s", svg_path)
            return False
        if not self.current_printer:
            logging.error("Error: No printer selected. Use set_printer() first.")
            return False

        use_windows_native = force_direct or (
            WINDOWS_PRINT_AVAILABLE
            and (self.custom_paper_width and self.custom_paper_height)
        )

        if WINDOWS_PRINT_AVAILABLE and use_windows_native:
            logging.info("Attempting Windows native printing (SVG → BMP → Print)...")
            try:
                bmp_path = self._svg_to_bmp_native(svg_path)
                if bmp_path:
                    success = self._print_bmp_windows(bmp_path, self.current_printer)
                    if success:
                        logging.info("Windows native printing completed successfully")
                        # Clean up BMP file
                        try:
                            os.remove(bmp_path)
                        except (OSError, IOError, PermissionError):
                            pass
                        return True
            except Exception as e:
                logging.warning(f"Windows native printing error: {e}, trying fallback method...")

        # Fallback to PDF method
        logging.info("Using fallback method (SVG → PDF → Print)...")
        if not self._ensure_inkscape():
            logging.error("Inkscape not available for fallback method")
            return False

        try:
            pdf_path = self._svg_to_pdf_inkscape(svg_path)
            if not pdf_path:
                logging.error("Error: Failed to convert SVG to PDF")
                return False

            logging.info("Printing %s to %s...", svg_path, self.current_printer)
            success = self._print_pdf(pdf_path, self.current_printer)

            if success:
                logging.info("Print job sent successfully")
                import time
                time.sleep(0.5)
                try:
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                except (OSError, IOError, PermissionError) as e:
                    logging.warning("Failed to delete PDF file: %s", e)
                return True
            else:
                logging.error("Printing failed.")
                return False
        except Exception as e:
            logging.error("Error printing SVG: %s", e)
            return False

    def print_svg_to_default(self, svg_path: str, force_direct: bool = False):
        """
        Print SVG file to default printer.

        Args:
            svg_path: Path to SVG file
            force_direct: Force Windows native printing

        Returns:
            bool: True if successful
        """
        if not os.path.exists(svg_path):
            logging.error("Error: SVG file not found: %s", svg_path)
            return False

        use_windows_native = force_direct or (
            WINDOWS_PRINT_AVAILABLE
            and (self.custom_paper_width and self.custom_paper_height)
        )

        if WINDOWS_PRINT_AVAILABLE and use_windows_native:
            logging.info("Attempting Windows native printing (SVG → BMP → Print)...")
            try:
                bmp_path = self._svg_to_bmp_native(svg_path)
                if bmp_path:
                    success = self._print_bmp_windows(bmp_path)
                    if success:
                        logging.info("Windows native printing completed successfully")
                        try:
                            os.remove(bmp_path)
                        except (OSError, IOError, PermissionError):
                            pass
                        return True
            except Exception as e:
                logging.warning(f"Windows native printing error: {e}, trying fallback method...")

        # Fallback to PDF method
        logging.info("Using fallback method (SVG → PDF → Print)...")
        if not self._ensure_inkscape():
            logging.error("Inkscape not available for fallback method")
            return False

        try:
            pdf_path = self._svg_to_pdf_inkscape(svg_path)
            if not pdf_path:
                logging.error("Error: Failed to convert SVG to PDF")
                return False

            logging.info("Printing %s to default printer...", svg_path)
            success = self._print_pdf(pdf_path)

            if success:
                logging.info("Print job sent successfully")
                import time
                time.sleep(0.5)
                try:
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                except (OSError, IOError, PermissionError) as e:
                    logging.warning("Failed to delete PDF file: %s", e)
                return True
            else:
                logging.error("Printing failed.")
                return False
        except Exception as e:
            logging.error("Error printing SVG: %s", e)
            return False

    def _svg_to_bmp_native(self, svg_path: str, bmp_path: str = None, dpi: int = 300):
        """
        Convert SVG to BMP using cairosvg.

        Args:
            svg_path: Path to SVG file
            bmp_path: Path to output BMP file
            dpi: DPI for conversion

        Returns:
            str: Path to BMP file or None
        """
        if not WINDOWS_PRINT_AVAILABLE:
            logging.error("Windows printing libraries not available")
            return None

        if bmp_path is None:
            bmp_path = str(Path(svg_path).with_suffix(".bmp"))

        try:
            png_data = cairosvg.svg2png(url=svg_path, dpi=dpi)
            image = Image.open(io.BytesIO(png_data))

            if image.mode != "RGB":
                image = image.convert("RGB")

            image.save(bmp_path, "BMP")
            logging.info("BMP saved to %s", bmp_path)
            return bmp_path

        except Exception as e:
            logging.error("Error converting SVG to BMP: %s", e)
            return None

    def _print_bmp_windows(self, bmp_path: str, printer_name: str = None):
        """
        Print BMP file using Windows native API.

        Args:
            bmp_path: Path to BMP file
            printer_name: Printer name (None for default)

        Returns:
            bool: True if successful
        """
        if not WINDOWS_PRINT_AVAILABLE:
            logging.error("Windows printing libraries not available")
            return False

        hdc = None
        image = None
        dib = None

        try:
            logging.info("Starting Windows native printing...")
            image = Image.open(bmp_path)
            logging.debug("Image loaded: %dx%d", image.width, image.height)

            target_printer = printer_name or win32print.GetDefaultPrinter()
            logging.info("Target printer: %s", target_printer)

            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(target_printer)
            logging.debug("Printer DC created successfully")

            hdc.StartDoc("SVG Print Job")
            hdc.StartPage()
            logging.debug("Print document started")

            if (
                self.custom_paper_width is not None
                and self.custom_paper_height is not None
            ):
                dpi_x = hdc.GetDeviceCaps(win32con.LOGPIXELSX)
                dpi_y = hdc.GetDeviceCaps(win32con.LOGPIXELSY)
                printer_width = int(self.custom_paper_width / 25.4 * dpi_x)
                printer_height = int(self.custom_paper_height / 25.4 * dpi_y)
            else:
                printer_width = hdc.GetDeviceCaps(win32con.PHYSICALWIDTH)
                printer_height = hdc.GetDeviceCaps(win32con.PHYSICALHEIGHT)

            img_width, img_height = image.size
            scale_x = printer_width / img_width
            scale_y = printer_height / img_height
            scale = min(scale_x, scale_y) * 0.9

            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            x_offset = (printer_width - new_width) // 2
            y_offset = (printer_height - new_height) // 2

            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            dib = ImageWin.Dib(resized_image)
            dib.draw(
                hdc.GetHandleOutput(),
                (x_offset, y_offset, x_offset + new_width, y_offset + new_height),
            )

            hdc.EndPage()
            hdc.EndDoc()
            logging.debug("Print document completed")

            logging.info("Windows native print job sent successfully")
            return True

        except Exception as e:
            logging.error("Error with Windows native printing: %s", e)
            if hdc:
                try:
                    hdc.AbortDoc()
                except Exception:
                    pass
            return False

        finally:
            try:
                if dib:
                    del dib
                if image:
                    image.close()
                if hdc:
                    hdc.DeleteDC()
            except Exception as cleanup_error:
                logging.warning("Error during resource cleanup: %s", cleanup_error)

    def print_svg_niimbot(self, svg_path: str, rotate: int = 0):
        """
        Print SVG file using Niimbot printer.

        Args:
            svg_path: Path to SVG file
            rotate: Rotation angle (0, 90, 180, 270)

        Returns:
            bool: True if successful
        """
        if not NIIMBOT_PRINT_AVAILABLE:
            logging.error(
                "Niimbot printing not available. Please install required dependencies."
            )
            return False

        if not os.path.exists(svg_path):
            logging.error("Error: SVG file not found: %s", svg_path)
            return False

        try:
            # Convert SVG to BMP
            bmp_path = self._svg_to_bmp_native(svg_path)
            if not bmp_path:
                logging.error("Failed to convert SVG to BMP for Niimbot printing")
                return False

            # Connect to Niimbot printer
            printer = NiimbotPrinter(
                model=self.niimbot_model,
                connection_type=self.niimbot_connection,
                address=self.niimbot_address,
            )

            if not printer.connect():
                logging.error("Failed to connect to Niimbot printer")
                return False

            try:
                # Print image
                printer.print_image_file(
                    bmp_path, density=self.niimbot_density, rotate=rotate
                )
                logging.info("Niimbot print job completed successfully")

                # Clean up BMP file
                try:
                    os.remove(bmp_path)
                except (OSError, IOError, PermissionError):
                    pass

                return True

            finally:
                printer.disconnect()

        except Exception as e:
            logging.error("Error printing with Niimbot: %s", e)
            try:
                if "bmp_path" in locals() and os.path.exists(bmp_path):
                    os.remove(bmp_path)
            except (OSError, IOError, PermissionError):
                pass
            return False
