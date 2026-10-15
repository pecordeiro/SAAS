"""Etapa G — arquivos de teste para o upload de fotos (válidos e maliciosos)."""

from __future__ import annotations

import io
import struct
import zlib

GPS_MARK = b"SEGREDO-EXIF"


def jpeg(width: int = 64, height: int = 48, *, with_gps: bool = True, color=(200, 10, 10)) -> bytes:
    """JPEG válido; com EXIF (descrição, marca da câmera e GPS) por padrão."""
    from PIL import Image

    img = Image.new("RGB", (width, height), color)
    out = io.BytesIO()
    if with_gps:
        exif = Image.Exif()
        exif[0x010E] = GPS_MARK.decode()
        exif[0x010F] = "CameraMarca"
        exif[0x8825] = {1: "S", 2: (23.0, 33.0, 1.0), 3: "W", 4: (46.0, 38.0, 2.0)}
        img.save(out, "JPEG", exif=exif.tobytes())
    else:
        img.save(out, "JPEG")
    return out.getvalue()


def png(width: int = 40, height: int = 30, mode: str = "RGBA") -> bytes:
    from PIL import Image

    out = io.BytesIO()
    Image.new(mode, (width, height), (10, 120, 200, 128) if mode == "RGBA" else (10, 120, 200)).save(out, "PNG")
    return out.getvalue()


def webp(width: int = 40, height: int = 30) -> bytes:
    from PIL import Image

    out = io.BytesIO()
    Image.new("RGB", (width, height), (10, 200, 20)).save(out, "WEBP")
    return out.getvalue()


def gif() -> bytes:
    from PIL import Image

    out = io.BytesIO()
    Image.new("P", (10, 10)).save(out, "GIF")
    return out.getvalue()


def _chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def png_huge_dimensions(width: int = 60000, height: int = 60000) -> bytes:
    """PNG pequeno em bytes que DECLARA dimensões enormes (bomba de descompressão)."""
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    idat = zlib.compress(b"\x00" * 64)
    return b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", b"")


SVG = b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
HTML_AS_JPG = b"<html><script>alert(document.cookie)</script></html>"
# Começa com os magic bytes do JPEG mas não é imagem: o resto é HTML.
FAKE_JPEG_HEADER = b"\xff\xd8\xff\xe0" + b"<html><script>alert(1)</script></html>" * 20
POLYGLOT_PAYLOAD = b"<script>alert('polyglot')</script>PK\x03\x04zip-escondido"


def polyglot_jpeg() -> bytes:
    """JPEG válido + HTML/ZIP colados depois do fim da imagem (decodifica, mas carrega lixo)."""
    return jpeg(with_gps=False) + POLYGLOT_PAYLOAD
