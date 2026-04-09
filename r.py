import itertools as it
import math
import struct
import shutil
import os
import sys
import uuid
import hashlib
import platform
import subprocess
import requests
import base64
import zlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import PurePath, Path
from typing import List, Dict, Tuple, Optional, Any
import time
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich import print as rprint
from rich.markup import escape
import gmalg
from Crypto.Cipher import AES
from Crypto.Cipher.AES import MODE_CBC
from Crypto.Hash import SHA1
from Crypto.Util.Padding import unpad
from zstandard import ZstdDecompressor, ZstdCompressionDict, DICT_TYPE_AUTO, ZstdCompressor
console = Console()

class CyberpunkTheme:
    NEON_PINK = '#FF00FF'
    NEON_BLUE = '#00FFFF'
    NEON_PURPLE = '#9D00FF'
    NEON_GREEN = '#00FF00'
    NEON_YELLOW = '#FFFF00'
    NEON_RED = '#FF0033'
    DARK_BG = '#0A0A14'
    DARK_PANEL = '#121220'
    DARK_ACCENT = '#1A1A2E'
    TEXT_PRIMARY = '#E0E0FF'
    TEXT_SECONDARY = '#A0A0CC'
    TEXT_DIM = '#666699'
    SUCCESS = '#00FF88'
    WARNING = '#FFAA00'
    ERROR = '#FF0055'
    INFO = '#00CCFF'
    HIGHLIGHT = '#FF00FF'

def tprint(msg: str, style: str='cyan'):
    """Print with Cyberpunk theme"""
    color_map = {'SUCCESS': 'bold #00FF88', 'ERROR': 'bold #FF0055', 'WARNING': '#FFAA00', 'INFO': '#00CCFF', 'TITLE': 'bold #E0E0FF', 'BLUE': '#00FFFF', 'NEON': '#FF00FF', 'RED': '#FF0033'}
    if style in color_map:
        console.print(msg, style=color_map[style])
    else:
        console.print(msg, style=style)

ZUC_KEY = bytes.fromhex('01010101010101010101010101010101')
ZUC_IV = bytes.fromhex('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')
RSA_MOD_1 = bytes.fromhex('CBE8B9F2504050EF9831B719E9A6249A6D238505ADE909BDE78C180DED6072A0C3347B8AF4780E1F212D952D82D4BF7F233C1ECA499E1F9D9A85B4FAD759F54BABC1666C5DE411EA9E4B2374425DD6C6F54333BBC8F2610FE6063E4D0D6C21A671A8F7C3740555E5DC06D4E1691C456DB4116C0C012BF7B206E8311AAAEC689952BF804EF638F09D5822B4117B114208F14DEB459E80CB770E5B0D7978E21F5E6CED4999D3583108221A7AB28B960277ADB5690A332784019D9C195BE4EA9EA0A09459010F236465DE0D59C3EF7324E954E1118D93EE19F299760C2CDB963CE87973EA5ECC9BBE81C27D4C7C8572AC07E9BCEAC9BD72AB7A56A3C0AD736ABCE4')
RSA_MOD_2 = bytes.fromhex('7F58E8A39A4DA4E87357DDD650EAA16D3B5CE95B213D1030A662566444796A78A84AE9AC3DBFFDE7F41094896696835DAF13B89E6EC2B84963B1B1BAF7151DA245C3FBFAE2A6AE18B2684D03F9229DE2C91440F2A3A3BCDE1E5680C16722A88039C73560D5D43F4B6562C2EEA5B1D926D86B51108A2643C70FB74D6442CE3A08339B8FD8F660AE88129B7AB8C46F2FA58124485CCCB1E987B05A6DA65A01858ED3F89905449AE42BB07290FCB9994BF22E26610BCABB9804783A3B9587917F3D97316EDDA15C5E13F79066407B55A93B291B68A4AC42A98D6E35FED84B14A792D154E62028DDAD20FC301951E5924BE9AD62FB719DD94CC30CAB871BEC4377A8')
SIMPLE1_DECRYPT_KEY = 121
SIMPLE2_DECRYPT_KEY = bytes.fromhex('E55B4ED1')
SIMPLE2_BLOCK_SIZE = 16
SM4_SECRET_4 = 'eb691efea914241317a8'
SM4_SECRET_2 = 'Q0hVTKey$as*1ZFlQCiA'
SM4_SECRET_NEW = [
        'xG2qW5lP7lV2iN5fN5pG',
        'xT1cJ6dL5wC0kK1rB4dK',
        'qC4jS5bZ6fL5xE6nD4zA',
        'gD4jQ2aL3bS3lC3xT0iW',
        'xU1yQ8wE9zY3gZ3bT5aE',
        'uQ3cO2dX7xY4xU7gH7iS',
        'gW1fR0jK6wQ4oN0oK1kZ',
        'aJ4pV7iZ7pU4wP2aC2cZ',
        'cX6jT3cM2oT3vK0kJ1qN',
        'iT2vS0cS6yT6cZ1sE1lO',
        'hM1pH9iY8wM9hT4lN5uJ',
        'kG6bC8jK0fL0dE4sH4mL',
        'dB6lB3vE0eZ8wM8rI0aC'
    ]
EM_SIMPLE1 = 1
EM_SIMPLE2 = 16
EM_SM4_2 = 2
EM_SM4_4 = 4
EM_SM4_NEW_BASE = 31
EM_SM4_NEW_MASK = ~EM_SM4_NEW_BASE
EM_UNKNOWN_17 = 17
CM_NONE = 0
CM_ZLIB = 1
CM_ZSTD = 6
CM_ZSTD_DICT = 8
CM_MASK = 15

class SM4:
    """SM4 Algorithm Implementation."""
    _S_BOX = bytes([
        52, 102, 37, 116, 137, 120, 228, 169, 90, 65, 188, 122, 214, 22, 33, 35,
        77, 97, 218, 148, 155, 223, 19, 60, 105, 58, 49, 10, 95, 215, 153, 149,
        241, 174, 114, 61, 7, 96, 36, 182, 152, 238, 196, 162, 45, 136, 221, 141,
        4, 234, 187, 17, 202, 62, 93, 161, 246, 63, 176, 151, 128, 71, 43, 166,
        230, 247, 217, 177, 89, 192, 124, 190, 84, 40, 183, 126, 79, 248, 67, 110,
        160, 80, 14, 245, 144, 184, 251, 163, 123, 98, 25, 70, 3, 42, 185, 143,
        159, 119, 180, 91, 131, 135, 8, 235, 226, 30, 66, 240, 15, 232, 113, 106,
        117, 173, 85, 31, 181, 171, 51, 250, 127, 21, 189, 133, 216, 6, 104, 179,
        82, 48, 72, 11, 0, 237, 239, 178, 87, 142, 231, 108, 213, 229, 46, 83,
        130, 5, 249, 129, 244, 86, 191, 140, 75, 227, 219, 74, 145, 76, 44, 211,
        64, 41, 78, 32, 20, 54, 121, 9, 111, 209, 55, 224, 57, 12, 138, 146,
        56, 18, 53, 109, 225, 253, 147, 154, 23, 212, 201, 156, 107, 132, 38, 157,
        175, 118, 193, 158, 208, 150, 197, 203, 233, 115, 73, 210, 205, 100, 195, 199,
        1, 125, 243, 172, 252, 222, 164, 68, 50, 27, 194, 186, 28, 2, 198, 39,
        69, 139, 242, 24, 167, 16, 81, 29, 200, 207, 99, 255, 47, 13, 88, 206,
        101, 165, 220, 26, 59, 134, 254, 34, 92, 168, 94, 103, 170, 236, 112, 204
    ])
    _FK = [1184304796, 1270900830, 1493524870, 3164752158]
    _CK = [964907, 973793155, 2654690407, 2916866751, 2071233739, 1226140771, 3348805095, 2045549823, 388349611, 800627875, 612403927, 3721562911, 1195432523, 3150178931, 612053223, 2445162591, 67183755, 1174197155, 1393249511, 3331183455, 3822152747, 1332317203, 1804781383, 1990130463, 1282653851, 3376591251, 2910902311, 925872959, 332098219, 735840931, 396665415, 3588844719]

    @staticmethod
    def ROL32(x, n):
        return x << n & 4294967295 | x >> 32 - n

    @staticmethod
    def _BS(X):
        return SM4._S_BOX[X >> 24 & 255] << 24 | SM4._S_BOX[X >> 16 & 255] << 16 | SM4._S_BOX[X >> 8 & 255] << 8 | SM4._S_BOX[X & 255]

    @staticmethod
    def _T0(X):
        X = SM4._BS(X)
        return X ^ SM4.ROL32(X, 2) ^ SM4.ROL32(X, 10) ^ SM4.ROL32(X, 18) ^ SM4.ROL32(X, 24)

    @staticmethod
    def _T1(X):
        X = SM4._BS(X)
        return X ^ SM4.ROL32(X, 13) ^ SM4.ROL32(X, 23)

    @staticmethod
    def _key_expand(key: bytes, rkey: list):
        K0 = int.from_bytes(key[0:4], 'big') ^ SM4._FK[0]
        K1 = int.from_bytes(key[4:8], 'big') ^ SM4._FK[1]
        K2 = int.from_bytes(key[8:12], 'big') ^ SM4._FK[2]
        K3 = int.from_bytes(key[12:16], 'big') ^ SM4._FK[3]
        for i in range(0, 32, 4):
            K0 = K0 ^ SM4._T1(K1 ^ K2 ^ K3 ^ SM4._CK[i])
            rkey[i] = K0
            K1 = K1 ^ SM4._T1(K2 ^ K3 ^ K0 ^ SM4._CK[i + 1])
            rkey[i + 1] = K1
            K2 = K2 ^ SM4._T1(K3 ^ K0 ^ K1 ^ SM4._CK[i + 2])
            rkey[i + 2] = K2
            K3 = K3 ^ SM4._T1(K0 ^ K1 ^ K2 ^ SM4._CK[i + 3])
            rkey[i + 3] = K3

    @classmethod
    def key_length(cls):
        return 16

    @classmethod
    def block_length(cls):
        return 16

    def __init__(self, key: bytes):
        if len(key)!= self.key_length():
            raise ValueError(f'Key must be {self.key_length()} bytes')
        else:
            self._key = key
            self._rkey = [0] * 32
            SM4._key_expand(self._key, self._rkey)
            self._block_buffer = bytearray()

    def encrypt(self, block: bytes) -> bytes:
        if len(block)!= self.block_length():
            raise ValueError(f'Block must be {self.block_length()} bytes')
        else:
            RK = self._rkey
            X0 = int.from_bytes(block[0:4], 'big')
            X1 = int.from_bytes(block[4:8], 'big')
            X2 = int.from_bytes(block[8:12], 'big')
            X3 = int.from_bytes(block[12:16], 'big')
            for i in range(0, 32, 4):
                X0 = X0 ^ SM4._T0(X1 ^ X2 ^ X3 ^ RK[i])
                X1 = X1 ^ SM4._T0(X2 ^ X3 ^ X0 ^ RK[i + 1])
                X2 = X2 ^ SM4._T0(X3 ^ X0 ^ X1 ^ RK[i + 2])
                X3 = X3 ^ SM4._T0(X0 ^ X1 ^ X2 ^ RK[i + 3])
            BUFFER = self._block_buffer
            BUFFER.clear()
            BUFFER.extend(X3.to_bytes(4, 'big'))
            BUFFER.extend(X2.to_bytes(4, 'big'))
            BUFFER.extend(X1.to_bytes(4, 'big'))
            BUFFER.extend(X0.to_bytes(4, 'big'))
            return bytes(BUFFER)

    def decrypt(self, block: bytes) -> bytes:
        if len(block)!= self.block_length():
            raise ValueError(f'Block must be {self.block_length()} bytes')
        else:
            RK = self._rkey
            X0 = int.from_bytes(block[0:4], 'big')
            X1 = int.from_bytes(block[4:8], 'big')
            X2 = int.from_bytes(block[8:12], 'big')
            X3 = int.from_bytes(block[12:16], 'big')
            for i in range(0, 32, 4):
                X0 = X0 ^ SM4._T0(X1 ^ X2 ^ X3 ^ RK[31 - i])
                X1 = X1 ^ SM4._T0(X2 ^ X3 ^ X0 ^ RK[30 - i])
                X2 = X2 ^ SM4._T0(X3 ^ X0 ^ X1 ^ RK[29 - i])
                X3 = X3 ^ SM4._T0(X0 ^ X1 ^ X2 ^ RK[28 - i])
            BUFFER = self._block_buffer
            BUFFER.clear()
            BUFFER.extend(X3.to_bytes(4, 'big'))
            BUFFER.extend(X2.to_bytes(4, 'big'))
            BUFFER.extend(X1.to_bytes(4, 'big'))
            BUFFER.extend(X0.to_bytes(4, 'big'))
            return bytes(BUFFER)

class Misc:
    @staticmethod
    def pad_to_n(data: bytes, n: int) -> bytes:
        assert n > 0
        padding = n - len(data) % n
        if padding == n:
            return data
        else:
            return data + b'\x00' * padding

    @staticmethod
    def align_up(x: int, n: int) -> int:
        return (x + n - 1) // n * n

class Reader:
    def __init__(self, buffer, cursor=0):
        self._buffer = buffer
        self._cursor = cursor

    def u1(self, move_cursor=True) -> int:
        return self.unpack('B', move_cursor=move_cursor)[0]

    def u4(self, move_cursor=True) -> int:
        return self.unpack('<I', move_cursor=move_cursor)[0]

    def u8(self, move_cursor=True) -> int:
        return self.unpack('<Q', move_cursor=move_cursor)[0]

    def i1(self, move_cursor=True) -> int:
        return self.unpack('b', move_cursor=move_cursor)[0]

    def i4(self, move_cursor=True) -> int:
        return self.unpack('<i', move_cursor=move_cursor)[0]

    def i8(self, move_cursor=True) -> int:
        return self.unpack('<q', move_cursor=move_cursor)[0]

    def s(self, n: int, move_cursor=True) -> bytes:
        return self.unpack(f'{n}s', move_cursor=move_cursor)[0]

    def unpack(self, f: str | bytes, offset=0, move_cursor=True):
        x = struct.unpack_from(f, self._buffer, self._cursor + offset)
        if move_cursor:
            self._cursor += struct.calcsize(f)
        return x

    def string(self, move_cursor=True) -> str:
        length = self.i4(move_cursor=move_cursor)
        if length == 0:
            return str()
        else:
            assert length > 0
            offset = 0 if move_cursor else 4
            return self.unpack(f'{length}s', offset=offset, move_cursor=move_cursor)[0].rstrip(b'\x00').decode()

class PakInfo:
    def __init__(self, buffer, keystream: List[int]):
        def decrypt_index_encrypted(x: int) -> int:
            MASK_8 = 255
            return (x ^ keystream[3]) & MASK_8
        def decrypt_magic(x: int) -> int:
            return x ^ keystream[2]
        def decrypt_index_hash(x: bytes) -> bytes:
            key = struct.pack('<5I', *keystream[4:][:5])
            assert len(x) == len(key)
            return bytes((a ^ b for a, b in zip(x, key)))
        def decrypt_index_size(x: int) -> int:
            return x ^ (keystream[10] << 32 | keystream[11])
        def decrypt_index_offset(x: int) -> int:
            return x ^ (keystream[0] << 32 | keystream[1])
        reader = Reader(buffer[-PakInfo._mem_size((-1)):])
        self.index_encrypted = decrypt_index_encrypted(reader.u1()) == 1
        self.magic = decrypt_magic(reader.u4())
        self.version = reader.u4()
        self.index_hash = decrypt_index_hash(reader.s(20)) if self.version >= 6 else bytes()
        self.index_size = decrypt_index_size(reader.u8())
        self.index_offset = decrypt_index_offset(reader.u8())
        if self.version <= 3:
            self.index_encrypted = False

    @staticmethod
    def _mem_size(_: int) -> int:
        return 45

class TencentPakInfo(PakInfo):
    def __init__(self, buffer, keystream: List[int]):
        def decrypt_unk(x: bytes) -> bytes:
            key = struct.pack('<8I', *keystream[7:][:8])
            assert len(x) == len(key)
            return bytes((a ^ b for a, b in zip(x, key)))
        def decrypt_stem_hash(x: int) -> int:
            return x ^ keystream[8]
        def decrypt_unk_hash(x: int) -> int:
            return x ^ keystream[9]
        super().__init__(buffer, keystream)
        reader = Reader(buffer[-TencentPakInfo._mem_size(self.version):])
        self.unk1 = decrypt_unk(reader.s(32)) if self.version >= 7 else bytes()
        self.packed_key = reader.s(256) if self.version >= 8 else bytes()
        self.packed_iv = reader.s(256) if self.version >= 8 else bytes()
        self.packed_index_hash = reader.s(256) if self.version >= 8 else bytes()
        self.stem_hash = decrypt_stem_hash(reader.u4()) if self.version >= 9 else 0
        self.unk2 = decrypt_unk_hash(reader.u4()) if self.version >= 9 else 0
        self.content_org_hash = reader.s(20) if self.version >= 12 else bytes()

    @staticmethod
    def _mem_size(version: int) -> int:
        size_for_7 = 32 if version >= 7 else 0
        size_for_8 = 768 if version >= 8 else 0
        size_for_9 = 8 if version >= 9 else 0
        size_for_12 = 20 if version >= 12 else 0
        return PakInfo._mem_size(version) + size_for_7 + size_for_8 + size_for_9 + size_for_12

class PakCompressedBlock:
    def __init__(self, reader: Reader):
        self.start = reader.u8()
        self.end = reader.u8()

@dataclass
class TencentPakEntry:
    def __init__(self, reader: Reader, version: int):
        self.content_hash = reader.s(20)
        if version <= 1:
            _ = reader.u8()
        self.offset = reader.u8()
        self.uncompressed_size = reader.u8()
        self.compression_method = reader.u4() & CM_MASK
        self.size = reader.u8()
        self.unk1 = reader.u1() if version >= 5 else 0
        self.unk2 = reader.s(20) if version >= 5 else bytes()
        if self.compression_method != 0 and version >= 3:
            self.compressed_blocks = [PakCompressedBlock(reader) for _ in range(reader.u4())]
        else:
            self.compressed_blocks = []
        self.compression_block_size = reader.u4() if version >= 4 else 0
        self.encrypted = reader.u1() == 1 if version >= 4 else False
        self.encryption_method = reader.u4() if version >= 12 else 0
        self.index_new_sep = reader.u4() if version >= 12 else 0

    def _mem_size(self, version: int) -> int:
        size_for_123 = 48 + (8 if version == 1 else 0)
        size_for_4 = 5 if version >= 4 else 0
        size_for_compressed_blocks = 4 + len(self.compressed_blocks) * 16 if self.compressed_blocks else 0
        size_for_5 = 21 if version >= 5 else 0
        size_for_12 = 4 if version >= 12 else 0
        return size_for_123 + size_for_4 + size_for_5 + size_for_12 + size_for_compressed_blocks

class PakCrypto:
    class _LCG:
        def __init__(self, seed: int):
            self.state = seed
        def next(self) -> int:
            MASK_32 = 4294967295
            MSB_1 = 2147483648
            def wrap(x: int) -> int:
                x &= MASK_32
                if not x & MSB_1:
                    return x
                else:
                    return (x + MSB_1 & MASK_32) - MSB_1
            x1 = wrap(1103515245 * self.state)
            self.state = wrap(x1 + 12345)
            x2 = wrap(x1 + 77880) if self.state < 0 else self.state
            return (x2 >> 16 & MASK_32) % 32767

    @staticmethod
    def zuc_keystream() -> List[int]:
        zuc = gmalg.ZUC(ZUC_KEY, ZUC_IV)
        return [struct.unpack('>I', zuc.generate())[0] for _ in range(16)]

    @staticmethod
    def _xorxor(buffer, x) -> bytes:
        return bytes((buffer[i] ^ x[i % len(x)] for i in range(len(buffer))))

    @staticmethod
    def _hashhash(buffer, n: int) -> bytes:
        result = bytes()
        for i in range(math.ceil(n / SHA1.digest_size)):
            result += SHA1.new(buffer).digest()
        if len(result) >= n:
            result = result[:n]
            return result
        else:
            result += b'\x00' * (n - len(result))
            return result

    @staticmethod
    def _meowmeow(buffer) -> bytes:
        def unpad(x):
            skip = 1 + next((i for i in range(len(x)) if x[i]!= 0))
            return x[skip:]
        if len(buffer) < 43:
            return bytes()
        else:
            x1 = buffer[1:][:SHA1.digest_size]
            x2 = buffer[SHA1.digest_size + 1:]
            x1 = PakCrypto._xorxor(x1, PakCrypto._hashhash(x2, len(x1)))
            x2 = PakCrypto._xorxor(x2, PakCrypto._hashhash(x1, len(x2)))
            part1, m = (x2[:SHA1.digest_size], x2[SHA1.digest_size:])
            if part1!= SHA1.new(b'\x00' * SHA1.digest_size).digest():
                return bytes()
            else:
                return unpad(m)

    @staticmethod
    def rsa_extract(signature: bytes, modulus: bytes) -> bytes:
        c = int.from_bytes(signature, 'little')
        n = int.from_bytes(modulus, 'little')
        e = 65537
        m = pow(c, e, n).to_bytes(256, 'little').rstrip(b'\x00')
        return PakCrypto._meowmeow(Misc.pad_to_n(m, 4))

    @staticmethod
    def _decrypt_simple1(ciphertext) -> bytes:
        return bytes((x ^ SIMPLE1_DECRYPT_KEY for x in ciphertext))

    @staticmethod
    def _decrypt_simple2(ciphertext) -> bytes:
        class RollingKey:
            def __init__(self, initial_value: int):
                self._value = initial_value
            def update(self, x: int) -> int:
                self._value ^= x
                return self._value
        assert len(ciphertext) % SIMPLE2_BLOCK_SIZE == 0
        initial_key, = struct.unpack('<I', SIMPLE2_DECRYPT_KEY)
        rolling_key = RollingKey(initial_key)
        plaintext = (struct.pack('<I', rolling_key.update(x)) for x in struct.unpack(f'<{len(ciphertext) // 4}I', ciphertext))
        return bytes(it.chain.from_iterable(plaintext))

    @staticmethod
    @lru_cache(maxsize=1)
    def _derive_sm4_key(file_path: PurePath, encryption_method: int) -> bytes:
        part1 = file_path.stem.lower()
        if encryption_method == EM_SM4_2:
            secret = SM4_SECRET_2
        else:
            if encryption_method == EM_SM4_4:
                secret = SM4_SECRET_4
            else:
                index = (encryption_method - EM_SM4_NEW_BASE) % len(SM4_SECRET_NEW)
                secret = f'{SM4_SECRET_NEW[index]}{encryption_method}'
        return SHA1.new(str(part1 + secret).encode()).digest()[:SM4.key_length()]

    @staticmethod
    @lru_cache(maxsize=1)
    def _sm4_context_for_key(key: bytes) -> SM4:
        return SM4(key)

    @staticmethod
    def _decrypt_sm4(ciphertext, file_path: PurePath, encryption_method: int) -> bytes:
        assert len(ciphertext) % SM4.block_length() == 0
        key = PakCrypto._derive_sm4_key(file_path, encryption_method)
        sm4 = PakCrypto._sm4_context_for_key(key)
        return bytes(it.chain.from_iterable((sm4.decrypt(x) for x in it.batched(ciphertext, SM4.block_length()))))

    @staticmethod
    def decrypt_index(ciphertext, pak_info: TencentPakInfo) -> bytes:
        if pak_info.version > 7:
            key = PakCrypto.rsa_extract(pak_info.packed_key, RSA_MOD_1)
            iv = PakCrypto.rsa_extract(pak_info.packed_iv, RSA_MOD_1)
            assert len(key) == 32 and len(iv) == 32
            aes = AES.new(key, MODE_CBC, iv[:16])
            return unpad(aes.decrypt(ciphertext), AES.block_size)
        else:
            return bytes(PakCrypto._decrypt_simple1(ciphertext))

    @staticmethod
    def _is_simple1_method(encryption_method: int) -> bool:
        return encryption_method == EM_SIMPLE1

    @staticmethod
    def _is_simple2_method(encryption_method: int) -> bool:
        return encryption_method == EM_SIMPLE2 or encryption_method == 17

    @staticmethod
    def _is_sm4_method(encryption_method: int) -> bool:
        return encryption_method == EM_SM4_2 or encryption_method == EM_SM4_4 or encryption_method & EM_SM4_NEW_MASK!= 0

    @staticmethod
    def align_encrypted_content_size(n: int, encryption_method: int) -> int:
        if PakCrypto._is_simple2_method(encryption_method):
            return Misc.align_up(n, SIMPLE2_BLOCK_SIZE)
        else:
            if PakCrypto._is_sm4_method(encryption_method):
                return Misc.align_up(n, SM4.block_length())
            else:
                return n

    @staticmethod
    def decrypt_block(ciphertext, file: PurePath, encryption_method: int) -> bytes:
        if PakCrypto._is_simple1_method(encryption_method):
            return PakCrypto._decrypt_simple1(ciphertext)
        else:
            if PakCrypto._is_simple2_method(encryption_method):
                return PakCrypto._decrypt_simple2(ciphertext)
            else:
                if PakCrypto._is_sm4_method(encryption_method):
                    return PakCrypto._decrypt_sm4(ciphertext, file, encryption_method)
                else:
                    raise ValueError(f'Unknown encryption method: {encryption_method}')

    @staticmethod
    @lru_cache(maxsize=33)
    def generate_block_indices(n: int, encryption_method: int) -> List[int]:
        if not PakCrypto._is_sm4_method(encryption_method):
            return list(range(n))
        else:
            permutation = []
            lcg = PakCrypto._LCG(n)
            while len(permutation)!= n:
                x = lcg.next() % n
                if x not in permutation:
                    permutation.append(x)
            inverse = [0] * len(permutation)
            for i, x in enumerate(permutation):
                inverse[x] = i
            return inverse

class PakCompression:
    @staticmethod
    @lru_cache(maxsize=33)
    def _zstd_decompressor(dict: ZstdCompressionDict) -> ZstdDecompressor:
        return ZstdDecompressor(dict)

    @staticmethod
    def zstd_dictionary(dict_data) -> ZstdCompressionDict:
        return ZstdCompressionDict(dict_data, DICT_TYPE_AUTO)

    @staticmethod
    def decompress_block(block, dict: Optional[ZstdCompressionDict], compression_method: int) -> bytes:
        if compression_method == CM_ZLIB:
            try:
                return zlib.decompress(block)
            except zlib.error:
                return block
        else:
            if compression_method == CM_ZSTD or compression_method == CM_ZSTD_DICT:
                if compression_method!= CM_ZSTD_DICT:
                    dict = None
                return PakCompression._zstd_decompressor(dict).decompress(block)
            else:
                raise ValueError(f'Unknown compression method: {compression_method}')

class TencentPakFile:
    def __init__(self, file_path: PurePath, is_od=False):
        self._file_path = file_path
        with open(file_path, 'rb') as file:
            self._file_content = memoryview(file.read())
        self._is_od = is_od
        self._mount_point = PurePath()
        self._is_zstd_with_dict = 'zsdic' in str(self._file_path)
        self._zstd_dict = None
        self._files = []
        self._index = {}
        self._pak_info = TencentPakInfo(self._file_content, PakCrypto.zuc_keystream())
        self._verify_stem_hash()
        self._tencent_load_index()

    def _verify_stem_hash(self) -> None:
        if not self._is_od and self._pak_info.version >= 9:
                assert self._pak_info.stem_hash == zlib.crc32(self._file_path.stem.encode('utf-32le'))

    def _tencent_load_index(self) -> None:
        index_data = self._file_content[self._pak_info.index_offset:][:self._pak_info.index_size]
        if self._pak_info.index_encrypted:
            index_data = PakCrypto.decrypt_index(index_data, self._pak_info)
        else:
            index_data = index_data
        self._verify_index_hash(index_data)
        self._load_index(index_data)

    def _verify_index_hash(self, index_data) -> None:
        expected_hash = self._pak_info.index_hash
        if not self._is_od and self._pak_info.version >= 8:
                assert expected_hash == PakCrypto.rsa_extract(self._pak_info.packed_index_hash, RSA_MOD_2)
        assert expected_hash == SHA1.new(index_data).digest()

    @staticmethod
    def _construct_mount_point(mount_point: str) -> PurePath:
        result = PurePath()
        for part in PurePath(mount_point).parts:
            if part!= '..':
                result /= part
        return result

    def _peek_content(self, offset: int, size: int, encryption_method: int) -> memoryview:
        size = PakCrypto.align_encrypted_content_size(size, encryption_method)
        return self._file_content[offset:][:size]

    def _peek_block_content(self, block: PakCompressedBlock, encryption_method: int) -> memoryview:
        size = PakCrypto.align_encrypted_content_size(block.end - block.start, encryption_method)
        return self._file_content[block.start:][:size]

    def _construct_zstd_dict(self, dict_entry: TencentPakEntry) -> None:
        assert not self._zstd_dict
        assert not dict_entry.encrypted
        assert dict_entry.compression_method == CM_NONE
        reader = Reader(self._peek_content(dict_entry.offset, dict_entry.size, 0))
        dict_size = reader.u8()
        _ = reader.u4()
        assert dict_size == reader.u4()
        dict_data = reader.s(dict_size)
        self._zstd_dict = PakCompression.zstd_dictionary(dict_data)

    def _load_index(self, index_data) -> None:
        if self._pak_info.version <= 10:
            raise ValueError(f'Unsupported version: {self._pak_info.version}')
        else:
            reader = Reader(index_data)
            self._mount_point = self._construct_mount_point(reader.string())
            self._files = [TencentPakEntry(reader, self._pak_info.version) for _ in range(reader.u4())]
            for _ in range(reader.u8()):
                dir_path = PurePath(reader.string())
                e = {reader.string(): self._files[~reader.i4()] for _ in range(reader.u8())}
                if self._is_zstd_with_dict and dir_path.name == 'zstddic':
                    assert len(e) == 1
                    self._construct_zstd_dict(e[[*e.keys()][0]])
                else:
                    self._index.update({PurePath(dir_path): e})

    def _write_to_disk(self, file_path: PurePath, entry: TencentPakEntry) -> None:
        encryption_method = entry.encryption_method
        compression_method = entry.compression_method
        console.print(f'[#00CCFF]{file_path.name}[/#00CCFF] - Encryption: {encryption_method}, Compression: {compression_method}, Blocks: {len(entry.compressed_blocks)}')
        with open(file_path, 'wb') as file:
            if compression_method == CM_NONE:
                data = self._peek_content(entry.offset, entry.size, encryption_method)
                if entry.encrypted:
                    data = PakCrypto.decrypt_block(data, file_path, encryption_method)
                file.write(data)
                return
            else:
                for x in PakCrypto.generate_block_indices(len(entry.compressed_blocks), encryption_method):
                    data = self._peek_block_content(entry.compressed_blocks[x], encryption_method)
                    if entry.encrypted:
                        data = PakCrypto.decrypt_block(data, file_path, encryption_method)
                    data = PakCompression.decompress_block(data, self._zstd_dict, compression_method)
                    file.write(data)

    def dump(self, out_path: PurePath) -> None:
        out_path /= self._mount_point
        for dir_path, dir in self._index.items():
            current_out_path = Path(out_path / dir_path)
            if not current_out_path.exists():
                current_out_path.mkdir(parents=True, exist_ok=True)
            for file_name, entry in dir.items():
                self._write_to_disk(current_out_path / file_name, entry)

def debug_entry_info(entry):
    """Debug function to print entry details"""
    console.print('[bold #FFFF00]ENTRY DEBUG INFO:[/bold #FFFF00]')
    console.print(f'  • Uncompressed size: {entry.uncompressed_size}')
    console.print(f'  • Compressed size: {entry.size}')
    console.print(f'  • Compression method: {entry.compression_method}')
    console.print(f'  • Encryption method: {entry.encryption_method}')
    console.print(f'  • Encrypted: {entry.encrypted}')
    console.print(f'  • Blocks: {len(entry.compressed_blocks)}')
    console.print(f'  • Block size: {entry.compression_block_size}')
    if entry.compressed_blocks:
        console.print('  • Block ranges:')
        for i, blk in enumerate(entry.compressed_blocks[:5]):
            console.print(f'    Block {i}: {blk.start} - {blk.end} (size: {blk.end - blk.start})')
        if len(entry.compressed_blocks) > 5:
            console.print(f'    ... and {len(entry.compressed_blocks) - 5} more blocks')

def _zstd_add_skippable_padding(data: bytes, pad_len: int) -> bytes:
    if pad_len <= 0:
        return data
    else:
        out = bytearray(data)
        while pad_len > 0:
            frame_len = min(max(pad_len - 8, 0), 1048576)
            out += b'P*M\x18'
            out += struct.pack('<I', frame_len)
            out += b'\x00' * frame_len
            pad_len -= 8 + frame_len
        return bytes(out)

def _compress_to_target(plaintext: bytes, method: int, zstd_dict, target_size: int, encryption_method: int) -> bytes:
    align = PakCrypto.align_encrypted_content_size
    if method in (CM_ZSTD, CM_ZSTD_DICT):
        for lvl in [22, 19, 16, 13, 10, 7, 4, 1]:
            try:
                c = ZstdCompressor(level=lvl, dict_data=zstd_dict if method == CM_ZSTD_DICT else None, threads=1)
                comp = c.compress(plaintext)
                a = align(len(comp), encryption_method)
                if a <= target_size:
                    if a < target_size:
                        comp = _zstd_add_skippable_padding(comp, target_size - a)
                    return comp
            except Exception:
                pass
        c = ZstdCompressor(dict_data=zstd_dict if method == CM_ZSTD_DICT else None, threads=1)
        return c.compress(plaintext)[:target_size]

def _encrypt_plaintext(plaintext: bytes, pak_relative_path: PurePath, encryption_method: int) -> bytes:
    if PakCrypto._is_simple1_method(encryption_method):
        return bytes((b ^ SIMPLE1_DECRYPT_KEY for b in plaintext))
    else:
        if PakCrypto._is_simple2_method(encryption_method):
            pad = -len(plaintext) % SIMPLE2_BLOCK_SIZE
            plaintext += b'\x00' * pad
            key, = struct.unpack('<I', SIMPLE2_DECRYPT_KEY)
            rolling = key
            out = []
            for x, in struct.iter_unpack('<I', plaintext):
                c = rolling ^ x
                out.append(c)
                rolling ^= c
            return struct.pack(f'<{len(out)}I', *out)
        else:
            if PakCrypto._is_sm4_method(encryption_method):
                key = PakCrypto._derive_sm4_key(pak_relative_path, encryption_method)
                sm4 = PakCrypto._sm4_context_for_key(key)
                pad_len = -len(plaintext) % 16
                if pad_len > 0:
                    plaintext = plaintext + b'\x00' * pad_len
                out = bytearray()
                for i in range(0, len(plaintext), 16):
                    block = plaintext[i:i + 16]
                    if len(block) < 16:
                        block = block.ljust(16, b'\x00')
                    out.extend(sm4.encrypt(block))
                return bytes(out)
            else:
                return plaintext

def _repack_uncompressed(outfh, pak_file, entry, pak_relative_path: PurePath, new_data: bytes):
    enc_method = entry.encryption_method
    target_size = entry.size
    enc_region = PakCrypto.align_encrypted_content_size(target_size, enc_method) if entry.encrypted else target_size
    plaintext = new_data[:enc_region]
    if entry.encrypted:
        a = PakCrypto.align_encrypted_content_size(len(plaintext), enc_method)
        plaintext += b'\x00' * (a - len(plaintext))
        cipher = _encrypt_plaintext(plaintext, pak_relative_path, enc_method)
        outfh.seek(entry.offset)
        outfh.write(cipher)
        with open(pak_file._file_path, 'rb') as src:
            src.seek(entry.offset + len(cipher))
            outfh.write(src.read(enc_region - len(cipher)))
    else:
        outfh.seek(entry.offset)
        outfh.write(plaintext)
        with open(pak_file._file_path, 'rb') as src:
            src.seek(entry.offset + len(plaintext))
            outfh.write(src.read(target_size - len(plaintext)))

def _repack_compressed(outfh, pak_file, entry, pak_relative_path, new_data, repack_dir):
    blocks = entry.compressed_blocks
    enc_method = entry.encryption_method
    comp_method = entry.compression_method
    order = PakCrypto.generate_block_indices(len(blocks), enc_method)
    console.print('[#FFFF00]REPACK DEBUG:[/#FFFF00]')
    console.print(f'  Original uncompressed: {entry.uncompressed_size:,} bytes')
    console.print(f'  New data size: {len(new_data):,} bytes')
    console.print(f'  Blocks: {len(blocks)}')
    console.print(f'  Total compressed space: {sum((b.end - b.start for b in blocks)):,} bytes')
    
    if len(new_data) != entry.uncompressed_size:
        console.print('[#FF0055]❌ CRITICAL: New data size mismatch![/#FF0055]')
        if len(new_data) < entry.uncompressed_size:
            new_data = new_data.ljust(entry.uncompressed_size, b'\x00')
        else:
            new_data = new_data[:entry.uncompressed_size]

    if len(blocks) > 1:
        if entry.compression_block_size > 0:
            chunk_size = entry.compression_block_size
        else:
            block_sizes = [blk.end - blk.start for blk in blocks]
            total_block_size = sum(block_sizes)
            avg_block_size = total_block_size / len(blocks)
            avg_compression_ratio = total_block_size / entry.uncompressed_size
            chunk_size = int(avg_block_size / avg_compression_ratio) if avg_compression_ratio > 0 else 65536
        
        ptr = 0
        processed_blocks = 0
        skipped_blocks = 0
        for logical_i, phys_i in enumerate(order):
            blk = blocks[phys_i]
            target_size = blk.end - blk.start
            chunk_len = min(chunk_size, len(new_data) - ptr)
            if chunk_len <= 0: break
            chunk = new_data[ptr:ptr + chunk_len]
            ptr += chunk_len
            
            with open(pak_file._file_path, 'rb') as src:
                src.seek(blk.start)
                original_compressed = src.read(target_size)
            
            compressed_ok = False
            new_compressed = None
            zstd_dict = pak_file._zstd_dict if comp_method == CM_ZSTD_DICT else None
            
            if comp_method in (CM_ZSTD, CM_ZSTD_DICT):
                for level in [22, 19, 16, 13, 10, 7, 4, 1]:
                    c = ZstdCompressor(level=level, dict_data=zstd_dict, threads=1)
                    new_compressed = c.compress(chunk)
                    if len(new_compressed) <= target_size:
                        compressed_ok = True
                        break
            elif comp_method == CM_ZLIB:
                new_compressed = zlib.compress(chunk, zlib.Z_BEST_COMPRESSION)
                if len(new_compressed) <= target_size:
                    compressed_ok = True
            
            if not compressed_ok:
                outfh.seek(blk.start)
                outfh.write(original_compressed)
                skipped_blocks += 1
                continue
            
            if entry.encrypted:
                if PakCrypto._is_sm4_method(enc_method):
                    pad_len = -len(new_compressed) % 16
                    if pad_len > 0: new_compressed += b'\x00' * pad_len
                new_compressed = _encrypt_plaintext(new_compressed, pak_relative_path, enc_method)
            
            if len(new_compressed) > target_size:
                outfh.seek(blk.start)
                outfh.write(original_compressed)
                skipped_blocks += 1
            else:
                outfh.seek(blk.start)
                outfh.write(new_compressed)
                if len(new_compressed) < target_size:
                    outfh.write(b'\x00' * (target_size - len(new_compressed)))
                processed_blocks += 1
        return True
    else:
        # Single block case
        if not blocks: return True
        blk = blocks[0]
        target_size = blk.end - blk.start
        with open(pak_file._file_path, 'rb') as src:
            src.seek(blk.start)
            original_compressed = src.read(target_size)
        
        compressed_ok = False
        new_compressed = None
        zstd_dict = pak_file._zstd_dict if comp_method == CM_ZSTD_DICT else None
        
        if comp_method in (CM_ZSTD, CM_ZSTD_DICT):
            for level in [22, 19, 16, 13, 10, 7, 4, 1]:
                c = ZstdCompressor(level=level, dict_data=zstd_dict, threads=1)
                new_compressed = c.compress(new_data)
                if len(new_compressed) <= target_size:
                    compressed_ok = True
                    break
        elif comp_method == CM_ZLIB:
            new_compressed = zlib.compress(new_data, zlib.Z_BEST_COMPRESSION)
            if len(new_compressed) <= target_size:
                compressed_ok = True
        
        if not compressed_ok:
            outfh.seek(blk.start)
            outfh.write(original_compressed)
            return True
        
        if entry.encrypted:
            if PakCrypto._is_sm4_method(enc_method):
                pad_len = -len(new_compressed) % 16
                if pad_len > 0: new_compressed += b'\x00' * pad_len
            new_compressed = _encrypt_plaintext(new_compressed, pak_relative_path, enc_method)
        
        if len(new_compressed) > target_size:
            outfh.seek(blk.start)
            outfh.write(original_compressed)
        else:
            outfh.seek(blk.start)
            outfh.write(new_compressed)
            if len(new_compressed) < target_size:
                outfh.write(b'\x00' * (target_size - len(new_compressed)))
        return True

def smart_resolve_by_fingerprint(filename: str, repack_file: Path, candidates: list):
    """
    Resolve ambiguous pak entries using structural fingerprint matching.
    Returns (full_path, entry) or None.
    """
    repack_size = repack_file.stat().st_size
    size_matches = [(path, entry) for path, entry in candidates if entry.uncompressed_size == repack_size]
    if len(size_matches) == 1:
        return size_matches[0]
    if not size_matches:
        return None

    def fingerprint(e):
        return (e.uncompressed_size, e.size, e.compression_method, len(e.compressed_blocks), e.compression_block_size)

    base_fp = fingerprint(size_matches[0][1])
    final_matches = [(path, entry) for path, entry in size_matches if fingerprint(entry) == base_fp]

    if len(final_matches) == 1:
        return final_matches[0]
    return None

def _build_pak_filename_map(pak_file):
    """Build safe filename -> full pak path map"""
    name_map = {}
    for dir_path, files in pak_file._index.items():
        for name in files.keys():
            full = str(PurePath(dir_path) / name).replace('\\', '/')
            stem = Path(name).stem.lower()
            ext = Path(name).suffix.lower()
            key1 = name.lower()
            key2 = f"{stem}{ext}"
            key3 = stem
            for k in [key1, key2, key3]:
                name_map.setdefault(k, []).append(full)
    return name_map

def detect_repack_mode(pak_path: Path) -> str:
    name = pak_path.name.lower()
    if name == 'mini_obb.pak':
        return 'MINI_OBB'
    if 'zsdic' in name:
        return 'OBBZSDIC'
    if 'game' in name or 'patch' in name:
        return 'GAMEPATCH'
    return 'OBBZSDIC'

def repack_pak_file_fileA_style(pak_file, edited_root: Path, output_path: Path):
    """\n    SAFE FILE-A REPACK (FIXED VERSION)\n    • NO FORCE matching\n    • Exact extension matching for .uasset/.uexp\n    • Strict validation\n    """
    shutil.copy2(pak_file._file_path, output_path)
    pak_name_map = {}
    for dir_path, files in pak_file._index.items():
        for name, entry in files.items():
            full_path = str(PurePath(dir_path) / name).replace('\\', '/')
            key = name.lower()
            pak_name_map.setdefault(key, []).append((full_path, entry))
    edited = {}
    skipped_files = []
    console.print(f'[#00CCFF]🔍 Matching files from {edited_root}...[/#00CCFF]')
    for p in edited_root.rglob('*'):
        if not p.is_file():
            continue
        else:
            fname_lower = p.name.lower()
            if fname_lower in pak_name_map:
                candidates = pak_name_map[fname_lower]
                if len(candidates) == 1:
                    full_path, entry = candidates[0]
                    edited[full_path] = (p, entry)
                    console.print(f'[#00FF88]✓ Match: {p.name} → {full_path}[/#00FF88]')
                    continue
                else:
                    resolved = smart_resolve_by_fingerprint(filename=p.name, repack_file=p, candidates=candidates)
                    if resolved:
                        full_path, entry = resolved
                        edited[full_path] = (p, entry)
                        console.print(f'[#00FF88]✓ Smart-matched: {p.name} → {full_path}[/#00FF88]')
                    else:
                        console.print(f'[#FFAA00]⚠ Multiple matches for {p.name}:[/#FFAA00]')
                        for cand_path, _ in candidates:
                            console.print(f'    - {cand_path}')
                        skipped_files.append(p.name)
            else:
                stem = p.stem.lower()
                ext = p.suffix.lower()
                potential_matches = []
                for dir_path, files in pak_file._index.items():
                    for name, entry in files.items():
                        if Path(name).stem.lower() == stem and Path(name).suffix.lower() == ext:
                                full_path = str(PurePath(dir_path) / name).replace('\\', '/')
                                potential_matches.append((full_path, entry))
                if len(potential_matches) == 1:
                    full_path, entry = potential_matches[0]
                    edited[full_path] = (p, entry)
                    console.print(f'[#00FF88]✓ Stem+Ext Match: {p.name} → {full_path}[/#00FF88]')
                else:
                    if len(potential_matches) > 1:
                        console.print(f'[#FF0055]✗ Multiple stem matches for {p.name}:[/#FF0055]')
                        for cand_path, _ in potential_matches:
                            console.print(f'    - {cand_path}')
                        skipped_files.append(p.name)
                    else:
                        console.print(f'[#FF0055]✗ No match found for {p.name}[/#FF0055]')
                        skipped_files.append(p.name)
    console.print('\n[bold #00FFFF]📊 Matching Summary:[/bold #00FFFF]')
    console.print(f'[#00FF88]✓ Files matched: {len(edited)}[/#00FF88]')
    if skipped_files:
        console.print(f'[#FFAA00]⚠ Files skipped: {len(skipped_files)}[/#FFAA00]')
        for fname in skipped_files[:10]:
            console.print(f'    - {fname}')
        if len(skipped_files) > 10:
            console.print(f'    ... and {len(skipped_files) - 10} more')
    if not edited:
        console.print('[bold #FF0055]❌ No files to repack![/bold #FF0055]')
        return
    else:
        confirm = 'y'
        if confirm!= 'y':
            console.print('[#FFAA00]Repack cancelled by user.[/#FFAA00]')
            return
        else:
            with open(output_path, 'r+b') as outfh:
                for full_path, (p, entry) in edited.items():
                    console.print(f'[#FFFF00][REPACK][/#FFFF00] {full_path} | Compression: {entry.compression_method} | Encryption: {entry.encryption_method} | Blocks: {len(entry.compressed_blocks)}')
                    debug_entry_info(entry)
                    new_data = p.read_bytes()
                    pak_rel = PurePath(full_path)
                    if entry.compression_method == CM_NONE:
                        _repack_uncompressed(outfh, pak_file, entry, pak_rel, new_data)
                    else:
                        success = _repack_compressed(outfh, pak_file, entry, pak_rel, new_data, edited_root)
                        if not success:
                            console.print(f'[#FF0055]❌ FAILED to repack {full_path}. File may be corrupted![/#FF0055]')
            console.print(f'[bold #00FF88]✅ Repack completed! {len(edited)} file(s) replaced.[/bold #00FF88]')

def repack_mini_obb(pak, repack_dir, output_pak):
    console.print('[bold #00FFFF]🧩 Repack Mode: MINI_OBB[/bold #00FFFF]')
    pak._is_zstd_with_dict = False
    pak._zstd_dict = None
    repack_pak_file_fileA_style(pak_file=pak, edited_root=repack_dir, output_path=output_pak)

def repack_obbzsdic(pak, repack_dir, output_pak):
    console.print('[bold #00FFFF]🧩 Repack Mode: OBBZSDIC[/bold #00FFFF]')
    repack_pak_file_fileA_style(pak_file=pak, edited_root=repack_dir, output_path=output_pak)

def repack_gamepatch(pak, repack_dir, output_pak):
    console.print('[bold #00FFFF]🧩 Repack Mode: GAMEPATCH[/bold #00FFFF]')
    pak._is_zstd_with_dict = False
    pak._zstd_dict = None
    repack_pak_file_fileA_style(pak_file=pak, edited_root=repack_dir, output_path=output_pak)

def print_banner():
    """Print Cyberpunk styled banner"""
    os.system('cls' if os.name == 'nt' else 'clear')
    banner = '\n[bold #FD0363]██████╗░░██████╗██╗░░██╗███╗░░░███╗░█████╗░██████╗░[/bold #FD0363]\n[bold #CC095D]██╔══██╗██╔════╝╚██╗██╔╝████╗░████║██╔══██╗██╔══██╗[/bold #CC095D]\n[bold #9C1057]██║░░██║╚█████╗░░╚███╔╝░██╔████╔██║██║░░██║██║░░██║[/bold #9C1057]\n[bold #6B1650]██║░░██║░╚═══██╗░██╔██╗░██║╚██╔╝██║██║░░██║██║░░██║[/bold #6B1650]\n[bold #3B1D4A]██████╔╝██████╔╝██╔╝╚██╗██║░╚═╝░██║╚█████╔╝██████╔╝[/bold #3B1D4A]\n[bold #0A2344]╚═════╝░╚═════╝░╚═╝░░╚═╝╚═╝░░░░░╚═╝░╚════╝░╚═════╝░[/bold #0A2344]\n[bold #FD0363]\n  ✦ ────────────────────────────────────────── ✦\n  • Update-By     : [bold #d3f6db]DSxDEMON (@DSXDEMON_OWNER)[/bold #d3f6db] │\n  • Channel       : [bold #d3f6db]@DSXDEMON[/bold #d3f6db]                  │\n  • Credits       : [bold #d3f6db]@AMANYT2 | TWOAM[/bold #d3f6db]           │\n  • Platform      : [bold #d3f6db]BGMI|PUBG|KR|TW|JP|VNG[/bold #d3f6db]     │\n  • Game Version  : [bold #01befe]4.2[/bold #01befe]                        │\n  • Tool Version  : [bold #adff02]2[/bold #adff02]                          │\n  ✦ ────────────────────────────────────────── ✦\n[/bold #FD0363]\n    '
    console.print(banner)
    print()

def detect_pak_files(data_path: Path) -> List[Path]:
    """Detect all .pak files in the current directory"""
    pak_files = list(data_path.glob('*.pak'))
    pak_files.extend(data_path.glob('*.obb'))
    return sorted(pak_files, key=lambda x: x.name)

def safe_input(prompt: str='') -> str:
    """Safe input function that works with redirected stdin"""
    try:
        return input(prompt)
    except (EOFError, RuntimeError):
        try:
            if sys.platform != 'win32':
                with open('/dev/tty', 'r') as tty:
                    sys.stderr.write(prompt)
                    sys.stderr.flush()
                    return tty.readline().rstrip('\n')
            else:
                with open('CON', 'r') as con:
                    sys.stderr.write(prompt)
                    sys.stderr.flush()
                    return con.readline().rstrip('\r\n')
        except Exception:
            return ''
    except Exception:
        return ''

def clear_folders(data_path: Path) -> None:
    """Clear all repack folders"""
    with Progress() as progress:
        task = progress.add_task('[#00CCFF]Cleaning folders...', total=1)
        count = 0
        for item in data_path.iterdir():
            if item.is_dir() and item.name.startswith('DSxRepack_'):
                    try:
                        shutil.rmtree(item)
                        console.print(f'[#00FF88]✓ Cleared: {item.name}[/#00FF88]')
                        count += 1
                    except Exception as e:
                        console.print(f'[#FF0055]✗ Error clearing {item.name}: {escape(str(e))}[/#FF0055]')
                    else:
                        pass
        progress.update(task, completed=1)
        if count > 0:
            console.print(f'[#00FF88]✓ Successfully cleared {count} folder(s)[/#00FF88]')
        else:
            console.print('[#FFAA00]⚠ No folders to clear[/#FFAA00]')

def main_menu():
    """Main menu interface with Cyberpunk theme - REPACK ONLY"""
    if getattr(sys, 'frozen', False):
        data_path = Path(sys.executable).parent
    else:
        data_path = Path(__file__).parent

    while True:
        print_banner()
        pak_files = detect_pak_files(data_path)
        if not pak_files:
            console.print('[bold #FF0055]⚠  No .pak/.obb files found in the current directory![/bold #FF0055]')
            console.print('[#FFAA00]Please place .pak/.obb files in the same directory as this tool.[/#FFAA00]')
            safe_input('\nPress Enter to continue...')
            continue

        console.print(f'[bold #00FFFF]📁 Found {len(pak_files)} .pak/.obb file(s):[/bold #00FFFF]')
        console.print('────────────────────────────────────────────────────────────', style='#666699')
        for i, pak_file in enumerate(pak_files, 1):
            file_size = pak_file.stat().st_size
            size_mb = file_size / 1048576
            console.print(f'[#00CCFF]{i:2}. {pak_file.name}[/#00CCFF] [#FFFF00]({size_mb:.2f} MB)[/#FFFF00]')
        console.print('────────────────────────────────────────────────────────────', style='#666699')
        console.print('\n[bold #00FF88]OPTIONS:[/bold #00FF88]')
        console.print('[#00FFFF]1. 🔧 REPAK - Rebuild .pak file[/#00FFFF]')
        console.print('[#FF0055]2. 🗑️  CLEAR - Remove all Repack folders[/#FF0055]')
        console.print('[#FFFF00]0. 🚪 EXIT - Close the tool[/#FFFF00]')
        console.print('────────────────────────────────────────────────────────────', style='#666699')

        choice = safe_input('Enter your choice (0-2):').strip()

        if choice == '1':
            if len(pak_files) == 1:
                selected_pak = pak_files[0]
            else:
                file_choice = safe_input(f'Select .pak file (1-{len(pak_files)}): ').strip()
                try:
                    index = int(file_choice) - 1
                    if 0 <= index < len(pak_files):
                        selected_pak = pak_files[index]
                    else:
                        console.print('[bold #FF0055]❌ Invalid selection![/bold #FF0055]')
                        time.sleep(2)
                        continue
                except ValueError:
                    console.print('[bold #FF0055]❌ Invalid input! Please enter a number.[/bold #FF0055]')
                    time.sleep(2)
                    continue

            pak_name = selected_pak.stem
            repack_dir = data_path / f'DSxRepack_{pak_name}'
            if not repack_dir.exists():
                console.print(f'[bold #FF0055]❌ ERROR: {repack_dir} not found.[/bold #FF0055]')
                console.print('[#FFAA00]⚠  Please ensure DSxRepack folder exists with modified files.[/#FFAA00]')
                safe_input('\nPress Enter to continue...')
                continue

            try:
                console.print(f'[bold #00FFFF]🚀 Repacking {selected_pak.name}...[/bold #00FFFF]')
                with Progress(SpinnerColumn(), TextColumn('[progress.description]{task.description}'), BarColumn(), TextColumn('[progress.percentage]{task.percentage:>3.0f}%'), console=console) as progress:
                    task = progress.add_task(f'Repacking {selected_pak.name}', total=100)
                    pak = TencentPakFile(selected_pak)
                    progress.update(task, advance=20)
                    output_pak = selected_pak.with_suffix('.repacked')
                    mode = detect_repack_mode(selected_pak)
                    if mode == 'MINI_OBB':
                        repack_mini_obb(pak, repack_dir, output_pak)
                    elif mode == 'GAMEPATCH':
                        repack_gamepatch(pak, repack_dir, output_pak)
                    else:
                        repack_obbzsdic(pak, repack_dir, output_pak)
                    progress.update(task, advance=50)
                    if output_pak.stat().st_size != selected_pak.stat().st_size:
                        raise ValueError('Repack size mismatch! Aborting to prevent corruption.')
                    selected_pak.unlink()
                    output_pak.rename(selected_pak)
                    progress.update(task, completed=100)
                console.print('[bold #00FF88]✅ REPACK COMPLETED SUCCESSFULLY![/bold #00FF88]')
                console.print('[#00CCFF]📦 Original file replaced with repacked version[/#00CCFF]')
            except Exception as e:
                console.print(f'[bold #FF0055]❌ Repack failed:[/bold #FF0055] {e}')
                import traceback
                traceback.print_exc()
            safe_input('\nPress Enter to continue...')

        elif choice == '2':
            console.print('[bold #FFFF00]⚠  WARNING: This will delete all DSxRepack_* folders[/bold #FFFF00]')
            confirm = safe_input('Are you sure? (y/N): ').strip().lower()
            if confirm == 'y':
                clear_folders(data_path)
            else:
                console.print('[#FFAA00]Operation cancelled.[/#FFAA00]')
            safe_input('\nPress Enter to continue...')

        elif choice == '0':
            console.print('[bold #FFFF00]\n👋 Allah Hafiz... Thanks for Using This Tool![/bold #FFFF00]')
            time.sleep(2)
            break
        else:
            console.print('[bold #FF0055]❌ Invalid choice! Please enter 0, 1, or 2.[/bold #FF0055]')
            time.sleep(2)

if __name__ == '__main__':
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print('\n[bold #FFFF00]⚠  Interrupted by user. Exiting...[/bold #FFFF00]')
        sys.exit(0)
    except Exception as e:
        console.print(f'[bold #FF0055]💥 UNEXPECTED ERROR:[/bold #FF0055] {escape(str(e))}')
        import traceback
        traceback.print_exc()
        safe_input('\nPress Enter to exit...')
        sys.exit(1)