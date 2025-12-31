# -*- coding: utf-8 -*-
"""
Niimbot Transport: Transport layer for Niimbot printer communication
"""
import abc
import logging
import platform
import socket

from serial.tools import list_ports

try:
    import serial
    from serial.tools.list_ports import comports as list_comports

    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    logging.warning("pyserial not available. USB connection will not work.")


class BaseTransport(metaclass=abc.ABCMeta):
    """Base transport layer class."""

    @abc.abstractmethod
    def read(self, length: int) -> bytes:
        """Read specified length of data."""
        raise NotImplementedError

    @abc.abstractmethod
    def write(self, data: bytes):
        """Write data."""
        raise NotImplementedError

    @abc.abstractmethod
    def close(self):
        """Close connection."""
        raise NotImplementedError


class BluetoothTransport(BaseTransport):
    """Bluetooth transport layer."""

    def __init__(self, address: str):
        """
        Initialize Bluetooth transport.

        Args:
            address: Bluetooth MAC address
        """
        if platform.system() == "Windows":
            try:
                import bluetooth  # pylint: disable=import-outside-toplevel

                self._sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                self._sock.connect((address, 1))
            except ImportError:
                try:
                    com_port = self._find_bluetooth_com_port(address)
                    if com_port:
                        self._serial = serial.Serial(
                            port=com_port, baudrate=115200, timeout=0.5
                        )
                        self._use_serial = True
                    else:
                        raise RuntimeError(
                            f"Unable to find COM port for Bluetooth device {address}"
                        ) from None
                except ImportError as exc:
                    raise RuntimeError(
                        "Windows Bluetooth connection requires pybluez or ensure device is paired and mapped as COM port"
                    ) from exc
        else:
            self._sock = socket.socket(
                socket.AF_BLUETOOTH,
                socket.SOCK_STREAM,
                socket.BTPROTO_RFCOMM,
            )
            self._sock.connect((address, 1))

        self._use_serial = getattr(self, "_use_serial", False)

    def _find_bluetooth_com_port(self, mac_address: str):
        """Find COM port for Bluetooth device on Windows."""
        try:
            mac_clean = mac_address.replace(":", "").upper()
            ports = list_ports.comports()

            for port in ports:
                if hasattr(port, "hwid") and mac_clean in port.hwid.upper():
                    logging.info(
                        "Found matching Bluetooth COM port: %s - %s", port.device, port.description
                    )
                    return port.device

                if (
                    hasattr(port, "description")
                    and "bluetooth" in port.description.lower()
                    and hasattr(port, "hwid")
                    and mac_clean in port.hwid.upper()
                ):
                    logging.info(
                        "Found Bluetooth COM port: %s - %s", port.device, port.description
                    )
                    return port.device

            for port in ports:
                if (
                    hasattr(port, "description")
                    and "bluetooth" in port.description.lower()
                ):
                    mac_suffix = mac_clean[-6:]
                    if hasattr(port, "hwid") and mac_suffix in port.hwid.upper():
                        logging.info(
                            "Found possible Bluetooth COM port: %s - %s",
                            port.device,
                            port.description,
                        )
                        return port.device

            logging.warning("No COM port found for MAC address %s", mac_address)
            return None

        except (OSError, ValueError) as e:
            logging.warning("Failed to query Bluetooth COM port: %s", e)
            return None

    def read(self, length: int) -> bytes:
        """Read data."""
        if self._use_serial:
            return self._serial.read(length)
        return self._sock.recv(length)

    def write(self, data: bytes):
        """Write data."""
        if self._use_serial:
            return self._serial.write(data)
        return self._sock.send(data)

    def close(self):
        """Close connection."""
        if hasattr(self, "_serial") and self._serial:
            self._serial.close()
        if hasattr(self, "_sock") and self._sock:
            self._sock.close()


class SerialTransport(BaseTransport):
    """USB serial port transport layer."""

    def __init__(self, port: str = "auto"):
        """
        Initialize serial transport.

        Args:
            port: Serial port name or "auto" for auto-detection
        """
        if not SERIAL_AVAILABLE:
            raise RuntimeError(
                "pyserial not available. Please install pyserial for USB connection."
            )

        port = port if port != "auto" else self._detect_port()
        self._serial = serial.Serial(port=port, baudrate=115200, timeout=0.5)

    def _detect_port(self):
        """Auto-detect serial port."""
        all_ports = list(list_comports())
        if len(all_ports) == 0:
            raise RuntimeError("No serial ports detected")
        if len(all_ports) > 1:
            msg = "Too many serial ports, please select specific one:"
            for port, desc, hwid in all_ports:
                msg += f"\n- {port} : {desc} [{hwid}]"
            raise RuntimeError(msg)
        return all_ports[0][0]

    def read(self, length: int) -> bytes:
        """Read data."""
        return self._serial.read(length)

    def write(self, data: bytes):
        """Write data."""
        return self._serial.write(data)

    def close(self):
        """Close connection."""
        if hasattr(self, "_serial"):
            self._serial.close()
