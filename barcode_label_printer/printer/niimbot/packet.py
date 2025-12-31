# -*- coding: utf-8 -*-
"""
Niimbot Packet: Niimbot printer communication packet handling
Based on https://github.com/AndBondStyle/niimprint
"""


class NiimbotPacket:
    """Niimbot printer communication packet class."""

    def __init__(self, type_: int, data: bytes):
        """
        Initialize packet.

        Args:
            type_: Packet type
            data: Packet data
        """
        self.type = type_
        self.data = data

    @classmethod
    def from_bytes(cls, pkt: bytes):
        """
        Create packet from byte data.

        Args:
            pkt: Byte data

        Returns:
            NiimbotPacket instance
        """
        assert pkt[:2] == b"\x55\x55"
        assert pkt[-2:] == b"\xaa\xaa"
        type_ = pkt[2]
        len_ = pkt[3]
        data = pkt[4 : 4 + len_]
        checksum = type_ ^ len_
        for i in data:
            checksum ^= i
        assert checksum == pkt[-3]
        return cls(type_, data)

    def to_bytes(self) -> bytes:
        """
        Convert packet to byte data.

        Returns:
            Byte data
        """
        checksum = self.type ^ len(self.data)
        for i in self.data:
            checksum ^= i
        return bytes(
            (0x55, 0x55, self.type, len(self.data), *self.data, checksum, 0xAA, 0xAA)
        )

    def __repr__(self):
        return f"<NiimbotPacket type={self.type:#04x} data={self.data.hex()}>"
