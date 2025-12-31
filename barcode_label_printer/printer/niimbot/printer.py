# -*- coding: utf-8 -*-
"""
Niimbot Printer: High-level interface for Niimbot thermal printers
Based on https://github.com/AndBondStyle/niimprint
"""
import enum
import logging
import math
import os
import struct
import time

try:
    from PIL import Image, ImageOps

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL not available. Image processing will not work.")

from .packet import NiimbotPacket
from .transport import BluetoothTransport, SerialTransport


class InfoEnum(enum.IntEnum):
    """Printer info type enumeration."""

    DENSITY = 1
    PRINTSPEED = 2
    LABELTYPE = 3
    LANGUAGETYPE = 6
    AUTOSHUTDOWNTIME = 7
    DEVICETYPE = 8
    SOFTVERSION = 9
    BATTERY = 10
    DEVICESERIAL = 11
    HARDVERSION = 12


class RequestCodeEnum(enum.IntEnum):
    """Request code enumeration."""

    GET_INFO = 64  # 0x40
    GET_RFID = 26  # 0x1A
    HEARTBEAT = 220  # 0xDC
    SET_LABEL_TYPE = 35  # 0x23
    SET_LABEL_DENSITY = 33  # 0x21
    START_PRINT = 1  # 0x01
    END_PRINT = 243  # 0xF3
    START_PAGE_PRINT = 3  # 0x03
    END_PAGE_PRINT = 227  # 0xE3
    ALLOW_PRINT_CLEAR = 32  # 0x20
    SET_DIMENSION = 19  # 0x13
    SET_QUANTITY = 21  # 0x15
    GET_PRINT_STATUS = 163  # 0xA3


def _packet_to_int(x):
    """Convert packet data to integer."""
    return int.from_bytes(x.data, "big")


class PrinterClient:
    """Niimbot printer client."""

    def __init__(self, transport, debug_mode=False):
        """
        Initialize printer client.

        Args:
            transport: Transport layer instance
            debug_mode: Enable debug mode
        """
        self._transport = transport
        self._packetbuf = bytearray()
        self._debug_mode = debug_mode

    def _debug_log(self, message, *args):
        """Debug log output."""
        if self._debug_mode:
            logging.info(f"[NIIMBOT DEBUG] {message}", *args)

    def print_image(self, image: Image, density: int = 3):
        """
        Print image.

        Args:
            image: PIL Image instance
            density: Print density (1-5)
        """
        if not PIL_AVAILABLE:
            raise RuntimeError(
                "PIL not available. Please install Pillow for image processing."
            )

        self._debug_log(
            "Starting image print - size: %sx%s, density: %s",
            image.width,
            image.height,
            density,
        )

        self._debug_log("Setting print density: %s", density)
        self.set_label_density(density)

        self._debug_log("Using normal label mode")
        self.set_label_type(1)

        self._debug_log("Starting print sequence")
        self.start_print()
        self._debug_log("Starting page print")
        self.start_page_print()
        self._debug_log("Setting print dimensions: %sx%s", image.height, image.width)
        self.set_dimension(image.height, image.width)

        self._debug_log("Sending image data")
        for pkt in self._encode_image(image):
            self._send(pkt)

        self._debug_log("Ending page print")
        self.end_page_print()
        time.sleep(0.3)

        self._debug_log("Waiting for print completion")
        while not self.end_print():
            time.sleep(0.1)

        self._debug_log("Image print completed")

    def _encode_image(self, image: Image):
        """Encode image to printer format."""
        img = ImageOps.invert(image.convert("L")).convert("1")

        logging.info("Processing image for printing: size=%s, mode=%s", img.size, img.mode)

        for y in range(img.height):
            line_data = [img.getpixel((x, y)) for x in range(img.width)]
            line_data = "".join("0" if pix == 0 else "1" for pix in line_data)
            line_data = int(line_data, 2).to_bytes(math.ceil(img.width / 8), "big")
            counts = (0, 0, 0)
            header = struct.pack(">H3BB", y, *counts, 1)
            pkt = NiimbotPacket(0x85, header + line_data)
            yield pkt

    def _recv(self):
        """Receive packets."""
        packets = []
        self._packetbuf.extend(self._transport.read(1024))
        while len(self._packetbuf) > 4:
            pkt_len = self._packetbuf[3] + 7
            if len(self._packetbuf) >= pkt_len:
                packet = NiimbotPacket.from_bytes(self._packetbuf[:pkt_len])
                self._log_buffer("recv", packet.to_bytes())
                packets.append(packet)
                del self._packetbuf[:pkt_len]
        return packets

    def _send(self, packet):
        """Send packet."""
        self._transport.write(packet.to_bytes())

    def _log_buffer(self, prefix: str, buff: bytes):
        """Log buffer content (only when NIIMBOT_DEBUG=1)."""
        if os.environ.get("NIIMBOT_DEBUG") == "1":
            msg = ":".join(f"{i:#04x}"[-2:] for i in buff)
            logging.debug("%s: %s", prefix, msg)

    def _transceive(self, reqcode, data, respoffset=1):
        """Send request and receive response."""
        respcode = respoffset + reqcode
        packet = NiimbotPacket(reqcode, data)
        self._log_buffer("send", packet.to_bytes())
        self._send(packet)

        resp = None
        for _ in range(6):
            for packet in self._recv():
                if packet.type == 219:
                    raise ValueError("Printer error")
                if packet.type == 0:
                    raise NotImplementedError("Unsupported operation")
                if packet.type == respcode:
                    resp = packet
            if resp:
                return resp
            time.sleep(0.1)
        return resp

    def get_info(self, key):
        """Get printer info."""
        if packet := self._transceive(RequestCodeEnum.GET_INFO, bytes((key,)), key):
            match key:
                case InfoEnum.DEVICESERIAL:
                    return packet.data.hex()
                case InfoEnum.SOFTVERSION:
                    return _packet_to_int(packet) / 100
                case InfoEnum.HARDVERSION:
                    return _packet_to_int(packet) / 100
                case _:
                    return _packet_to_int(packet)
        else:
            return None

    def set_label_type(self, n):
        """Set label type."""
        assert 1 <= n <= 3
        self._debug_log("Setting label type: %s", n)
        packet = self._transceive(RequestCodeEnum.SET_LABEL_TYPE, bytes((n,)), 16)
        result = bool(packet.data[0])
        self._debug_log("Label type setting result: %s", result)
        return result

    def set_label_density(self, n):
        """Set print density."""
        assert 1 <= n <= 5
        self._debug_log("Setting print density: %s", n)
        packet = self._transceive(RequestCodeEnum.SET_LABEL_DENSITY, bytes((n,)), 16)
        result = bool(packet.data[0])
        self._debug_log("Print density setting result: %s", result)
        return result

    def start_print(self):
        """Start print."""
        self._debug_log("Sending start print command")
        packet = self._transceive(RequestCodeEnum.START_PRINT, b"\x01")
        result = bool(packet.data[0])
        self._debug_log("Start print command result: %s", result)
        return result

    def end_print(self):
        """End print."""
        self._debug_log("Sending end print command")
        packet = self._transceive(RequestCodeEnum.END_PRINT, b"\x01")
        result = bool(packet.data[0])
        self._debug_log("End print command result: %s", result)
        return result

    def start_page_print(self):
        """Start page print."""
        self._debug_log("Sending start page print command")
        packet = self._transceive(RequestCodeEnum.START_PAGE_PRINT, b"\x01")
        result = bool(packet.data[0])
        self._debug_log("Start page print command result: %s", result)
        return result

    def end_page_print(self):
        """End page print."""
        self._debug_log("Sending end page print command")
        packet = self._transceive(RequestCodeEnum.END_PAGE_PRINT, b"\x01")
        result = bool(packet.data[0])
        self._debug_log("End page print command result: %s", result)
        return result

    def set_dimension(self, w, h):
        """Set dimensions."""
        self._debug_log("Setting print dimensions: %sx%s", w, h)
        packet = self._transceive(RequestCodeEnum.SET_DIMENSION, struct.pack(">HH", w, h))
        result = bool(packet.data[0])
        self._debug_log("Dimension setting result: %s", result)
        return result

    def close(self):
        """Close connection."""
        if hasattr(self, "_transport"):
            self._transport.close()


class NiimbotPrinter:
    """High-level interface for Niimbot printers."""

    # Supported printer models and their maximum widths
    SUPPORTED_MODELS = {
        "b1": 384,
        "b18": 384,
        "b21": 384,
        "b31": 384,
        "d11": 96,
        "d110": 96,
    }

    def __init__(
        self, model="b21", connection_type="usb", address=None, debug_mode=False
    ):
        """
        Initialize Niimbot printer.

        Args:
            model: Printer model (b1, b18, b21, b31, d11, d110)
            connection_type: Connection type (usb, bluetooth)
            address: Bluetooth MAC address or USB serial port path
            debug_mode: Enable debug mode (default: False)
        """
        self.model = model.lower()
        self.connection_type = connection_type.lower()
        self.address = address
        self.debug_mode = debug_mode
        self.client = None
        self.transport = None

        if self.model not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported model: {model}. Supported: {list(self.SUPPORTED_MODELS.keys())}"
            )

    def connect(self):
        """
        Connect to printer.

        Returns:
            bool: True if connection successful
        """
        try:
            if self.connection_type == "bluetooth":
                if not self.address:
                    raise ValueError(
                        "Bluetooth address required for bluetooth connection"
                    )
                self.transport = BluetoothTransport(self.address)
            elif self.connection_type == "usb":
                port = self.address if self.address else "auto"
                self.transport = SerialTransport(port=port)
            else:
                raise ValueError(f"Unsupported connection type: {self.connection_type}")

            self.client = PrinterClient(self.transport, debug_mode=self.debug_mode)
            logging.info(
                "Connected to %s via %s", self.model.upper(), self.connection_type
            )
            if self.debug_mode:
                logging.info("[NIIMBOT DEBUG] Debug mode enabled")
            return True

        except (OSError, ValueError, RuntimeError) as e:
            logging.error("Failed to connect to printer: %s", e)
            return False

    def disconnect(self):
        """Disconnect from printer."""
        if self.client:
            self.client.close()
            self.client = None
        if self.transport:
            self.transport.close()
            self.transport = None

    def print_image_file(self, image_path: str, density: int = 3, rotate: int = 0):
        """
        Print image file.

        Args:
            image_path: Path to image file
            density: Print density (1-5)
            rotate: Rotation angle (0, 90, 180, 270)
        """
        if not PIL_AVAILABLE:
            raise RuntimeError(
                "PIL not available. Please install Pillow for image processing."
            )

        if not self.client:
            raise RuntimeError("Not connected to printer. Call connect() first.")

        # Load image
        image = Image.open(image_path)

        # Rotate image
        if rotate != 0:
            image = image.rotate(-int(rotate), expand=True)

        # Check image width and auto-scale if needed
        max_width = self.SUPPORTED_MODELS[self.model]
        if image.width > max_width:
            scale_ratio = max_width / image.width
            new_width = max_width
            new_height = int(image.height * scale_ratio)

            logging.info(
                "Image width %spx exceeds %s limit (%spx)",
                image.width,
                self.model.upper(),
                max_width,
            )
            logging.info(
                "Auto-scaling image: %sx%s px → %sx%s px (ratio: %.3f)",
                image.width,
                image.height,
                new_width,
                new_height,
                scale_ratio,
            )

            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logging.info("Image scaled successfully")

        # Adjust density limit
        if self.model in ("b18", "d11", "d110") and density > 3:
            logging.warning("%s only supports density up to 3", self.model.upper())
            density = 3

        # Print image
        logging.info(
            "Printing image %s (%sx%s px) with density %s",
            image_path,
            image.width,
            image.height,
            density,
        )

        self.client.print_image(image, density=density)
        logging.info("Print job completed")

    def get_printer_info(self):
        """
        Get printer information.

        Returns:
            dict: Printer information
        """
        if not self.client:
            raise RuntimeError("Not connected to printer. Call connect() first.")

        info = {}
        try:
            info["device_serial"] = self.client.get_info(InfoEnum.DEVICESERIAL)
            info["software_version"] = self.client.get_info(InfoEnum.SOFTVERSION)
            info["hardware_version"] = self.client.get_info(InfoEnum.HARDVERSION)
            info["battery"] = self.client.get_info(InfoEnum.BATTERY)
        except (OSError, ValueError, RuntimeError) as e:
            logging.warning("Failed to get some printer info: %s", e)

        return info

    @classmethod
    def list_serial_ports(cls):
        """
        List available serial ports.

        Returns:
            list: List of serial port information dictionaries
        """
        try:
            from serial.tools.list_ports import comports as list_comports

            ports = []
            for port, desc, hwid in list_comports():
                ports.append({"port": port, "description": desc, "hardware_id": hwid})
            return ports
        except ImportError:
            return []
