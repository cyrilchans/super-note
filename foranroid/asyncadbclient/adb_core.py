import datetime
import pathlib
import shlex
import socket
import struct
from contextlib import asynccontextmanager, contextmanager
from typing import Union
from mixed_file import EnumStatusType, AdbConnectionError, AdbSyncError, \
    AdbError, AdbDeviceInfo, FileInfo, AdbTimeout


SEND = "SEND"
STAT = "STAT"
LIST = "LIST"
RECV = "RECV"
S_IFDIR = 0x4000
S_IFREG = 0x8000


class CoreCode:
    def __init__(self, host: str = None, port: int = None, timeout: float = None):
        self.__host = host
        self.__port = port
        self.__timeout = timeout
        self.__conn = self._create_socket()

    def _create_socket(self) -> socket.socket:
        s = socket.socket()
        try:
            s.settimeout(3)
            s.connect((self.__host, self.__port))
            s.settimeout(None)
            return s
        except:
            raise AdbConnectionError(f'adb connect {self.__host} { self.__port} fail')

    @property
    def conn(self) -> socket.socket:
        return self.__conn

    def _send(self, data: bytes) -> int:
        return self.__conn.send(data)

    def close(self):
        self.__conn.close()

    def send_command(self, cmd: Union[str, bytes], do_encode=True):
        self._send("{:04x}".format(len(cmd.encode("utf-8"))).encode("utf-8") + cmd.encode("utf-8")
                   if do_encode else cmd)

    def _recv_fully(self, n: int) -> bytes:
        t = n
        buffer = b''
        while t > 0:
            chunk = self.__conn.recv(t)
            if not chunk:
                break
            buffer += chunk
            t = n - len(buffer)
        return buffer

    def recv(self, byte: int) -> bytes:
        return self._recv_fully(byte)

    def recv_command(self, byte: int, encoding=None, do_decode=True):
        recv_data = self.recv(byte)
        return (recv_data.decode(encoding, errors="replace") if encoding else
                recv_data.decode("utf-8", errors="replace")) if do_decode else recv_data

    def is_okay(self) -> bool:
        data = self.recv_command(4)
        if data == EnumStatusType.FAIL:
            raise AdbConnectionError('adb connection fail')
        elif data == EnumStatusType.OKAY:
            return True

    def recv_string_block(self) -> str:
        length = self.recv_command(4)
        if length is None:
            raise
        size = int(length, 16)
        return self.recv_command(size)

    def read_until_close(self, encoding=None):
        content = ""
        while True:
            chunk = self.recv_command(4096, encoding)
            if not chunk:
                break
            content += chunk
        return content


class AdbClient:
    def __init__(self, host: str, port: int, timeout=None):
        self._host = host
        self._port = port
        self._timeout = timeout

    @asynccontextmanager
    async def _make_socket_connection(self) -> socket.socket:
        try:
            _conn = CoreCode(self._host, self._port)
            if self._timeout:
                _conn.conn.settimeout(self._timeout)
            yield _conn
        except TimeoutError:
            raise AdbTimeout("connect to adb server timeout")

    @asynccontextmanager
    async def _sync(self, serial: str) -> socket.socket:
        async with self._make_socket_connection() as c:
            c.send_command(f"host:transport:{serial}")
            c.is_okay()
            c.send_command(f'sync:')
            c.is_okay()
            yield c

    async def _async_device(self) -> AdbDeviceInfo:
        device_list = await self.async_devices()
        if len(device_list) == 0:
            raise AdbError("no devices/emulators found")
        if len(device_list) > 1:
            raise AdbError("more than one device/emulator")
        if device_list[0].state != "device":
            raise AdbError("No device available")
        return device_list[0]

    @contextmanager
    def _list(self, path: str, serial: str):
        with self._sync(serial) as c:
            d_bytes = LIST.encode("utf-8") + struct.pack("<I", len(path)) + path.encode("utf-8")
            c.send_command(d_bytes, do_encode=False)
            while 1:
                status = c.recv_command(4)
                if status == EnumStatusType.DONE:
                    break
                mode, size, ctime, namelen = struct.unpack("<IIII", c.recv_command(16, do_decode=False))
                name = c.recv_command(namelen)
                try:
                    ctime = datetime.datetime.fromtimestamp(ctime)
                except OSError:
                    ctime = datetime.datetime.now()
                yield FileInfo(mode, size, ctime, name)

    @asynccontextmanager
    async def _push_file(self, src, dst, serial):
        path = dst + "," + str(S_IFREG | 0o755)  # 给文件加权
        total_size = 0
        async with self._sync(serial) as c:
            d_bytes = SEND.encode("utf-8") + struct.pack("<I", len(path)) + path.encode("utf-8")
            c.send_command(d_bytes, do_encode=False)
            print("正在准备推文件")
            while 1:
                chunk = src.read(4096)
                if not chunk:
                    ctime = int(datetime.datetime.now().timestamp())
                    c.send_command(b"DONE" + struct.pack("<I", ctime), do_encode=False)
                    break
                c.send_command(b"DATA" + struct.pack("<I", len(chunk)), do_encode=False)
                c.send_command(chunk, do_encode=False)
                total_size += len(chunk)
            if c.is_okay():
                print('推送文件成功')
        yield total_size

    @asynccontextmanager
    async def _pull_file(self, src, dst, serial):
        print('正在pull文件')
        with dst.open("wb") as f:
            size = 0
            try:
                async with self._sync(serial) as c:
                    d_bytes = RECV.encode("utf-8") + struct.pack("<I", len(src)) + src.encode("utf-8")
                    c.send_command(d_bytes, do_encode=False)
                    while True:
                        cmd = c.recv_command(4)
                        if cmd == EnumStatusType.FAIL:
                            str_size = struct.unpack("<I", c.recv_command(4, do_decode=False))[0]
                            error_message = c.recv_command(str_size)
                            raise AdbError(error_message, src)
                        elif cmd == EnumStatusType.DONE:
                            break
                        elif cmd == EnumStatusType.DATA:
                            chunk_size = struct.unpack("<I", c.recv(4))[0]
                            chunk = c.recv(chunk_size)
                            if len(chunk) != chunk_size:
                                raise AdbError("read chunk missing")
                            f.write(chunk)
                            size += len(chunk)
            finally:
                if hasattr(dst, "close"):
                    dst.close()
            yield size

    async def async_server_version(self) -> int:
        """
        adb version
        """
        async with self._make_socket_connection() as c:
            c.send_command("host:version")
            c.is_okay()
            data = c.recv_string_block()
            return int(data, 16)

    async def async_server_kill(self) -> bool:
        """
        adb kill-server
        """
        async with self._make_socket_connection() as c:
            c.send_command("host:kill")
            return c.is_okay()

    async def async_devices(self) -> list:
        """
        adb devices
        """
        async with self._make_socket_connection() as c:
            c.send_command("host:devices")
            c.is_okay()
            output = c.recv_string_block()
            device_info = list()
            for line in output.splitlines():
                parts = line.strip().split("\t")
                if len(parts) != 2:
                    continue
                device_info.append(AdbDeviceInfo(serial=parts[0], state=parts[1]))
            return device_info

    async def async_shell(self, cmd: str, serial=None, encoding: str = "utf-8") -> str:
        """
        adb -s shell or adb shell
        """
        if isinstance(cmd, list):
            cmd = ' '.join(map(shlex.quote, cmd))
        device_info = await self._async_device()
        serial = device_info.serial if serial is None else serial
        async with self._make_socket_connection() as c:
            c.send_command(f"host:tport:serial:{serial}")
            c.is_okay()
            c.recv_command(8)
            c.send_command(f'shell:{cmd}')
            c.is_okay()
            output = c.read_until_close()
            if encoding:
                return output.rstrip()
            return output

    def ls(self, path: str, serial: str) -> list:
        """
        adb -s xxx shell ls xxx/xxx
        """
        return list(self._list(path, serial))

    @asynccontextmanager
    async def async_stat(self, path: str, serial: str):
        async with self._sync(serial) as c:
            d_bytes = STAT.encode("utf-8") + struct.pack("<I", len(path)) + path.encode("utf-8")
            c.send_command(d_bytes, do_encode=False)
            status = c.recv_command(4)
            if status == STAT:
                mode, size, ctime = struct.unpack("<III", c.recv_command(12, do_decode=False))
                try:
                    ctime = datetime.datetime.fromtimestamp(ctime)
                except OSError:
                    ctime = datetime.datetime.now()
                yield FileInfo(mode, size, ctime, path)
            return

    async def async_push(self, src, dst, serial, check=True):  # 只实现了push文件功能
        """
        adb -s xxx push xxx xxx
        """
        async with self.async_stat(dst, serial) as src_file_info:
            src_size = pathlib.Path(src).stat().st_size
            dst_act_size = None
            total_size = 0
            if src_file_info.mode & S_IFDIR != 0:
                if not isinstance(dst, (pathlib.Path, str)):
                    raise AdbSyncError(f"target path {dst} is not a directory")
                dst = (pathlib.Path(dst) / pathlib.Path(src).name).as_posix()
                src = pathlib.Path(src).open("rb")
                async with self._push_file(src, dst, serial) as s:
                    total_size = s

            if check:  # 检查文件大小
                async with self.async_stat(dst, serial) as file_info:
                    dst_act_size = file_info
                    if total_size != dst_act_size.size:
                        raise AdbError(
                            f"missing file size, expect pushed {total_size}, actually pushed {src_file_info.size}")
            return src_size, dst_act_size, dst

    async def async_pull(self, src, dst, serial):  # 只实现了pull文件功能
        """
        adb -s xxx pull xxx xxx
        """
        async with self.async_stat(src, serial) as src_file_info:
            if src_file_info.mode & S_IFREG != 0:
                if isinstance(dst, str):
                    dst = pathlib.Path(dst)
                async with self._pull_file(src, dst, serial) as s:
                    return s
