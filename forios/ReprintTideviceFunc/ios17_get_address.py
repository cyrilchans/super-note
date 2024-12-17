import datetime
import json
import os
import plistlib
import socket
import ssl
import struct
from construct import Struct, Const, Prefixed, Int16ub, GreedyBytes

address = ('127.0.0.1', 27015)
message_type = 8


def dump_plist(payload, is_fist=True):
    plist_bytes = plistlib.dumps(payload)
    if is_fist:
        length = 16 + len(plist_bytes)
        header = struct.pack("IIII", length, 1, message_type, 1)
    else:
        length = len(plist_bytes)
        header = struct.pack(">I", length)
    return header+plist_bytes


def loads_plist(sock, data, is_fist=True):
    if is_fist:
        (length, version, resp, tag) = struct.unpack("IIII", data)
        length -= 16
    else:
        (length,) = struct.unpack(">I", data)
    body_data = recv_all(sock, length)
    payload = plistlib.loads(body_data)
    return payload


def recv_all(sock, size: int) -> bytearray:
    buf = bytearray()
    while len(buf) < size:
        chunk = sock.recv(size - len(buf))
        if not chunk:
            raise "recvall: socket connection broken"
        buf.extend(chunk)
    return buf


device_id = 0
uuid = None


def save_pem(pair_record):
    appdir = r'./ssl'
    fpath = os.path.join(appdir, uuid + "-" + "4" + ".pem")
    if os.path.exists(fpath):
        # 3 minutes not regenerate pemfile
        st_mtime = datetime.datetime.fromtimestamp(
            os.stat(fpath).st_mtime)
        if datetime.datetime.now() - st_mtime < datetime.timedelta(
                minutes=3):
            return fpath
    with open(fpath, "wb") as f:
        pdata = pair_record
        f.write(pdata['HostPrivateKey'])
        f.write(b"\n")
        f.write(pdata['HostCertificate'])
    return fpath


def get_pair():
    payload = {
        'MessageType': 'ReadPairRecord',  # Required
        'PairRecordID': uuid,  # Required
        'ClientVersionString': 'libusbmuxd 1.1.0',
        'ProgName': "cyril",
        'kLibUSBMuxVersion': 3
    }
    sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock1.settimeout(10)
    sock1.connect(('127.0.0.1', 27015))

    data = dump_plist(payload)
    sock1.sendall(data)
    b = sock1.recv(16)
    payload = loads_plist(sock1, b)
    record_data = payload['PairRecordData']
    return plistlib.loads(record_data)


def create_inner_connection(LOCKDOWN_PORT = 62078, _ssl: bool = False,  sl_dial_only: bool = False):
    # print(f'通知usbmuxd连接设备, 并对应端口转换网络字节序：{LOCKDOWN_PORT}')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect(('127.0.0.1', 27015))
    _port = socket.htons(LOCKDOWN_PORT)
    payload = {
        'DeviceID': device_id,  # Required
        'MessageType': 'Connect',  # Required
        'PortNumber': _port,  # Required
        'ProgName': "cyril",
    }

    data = dump_plist(payload)
    sock.sendall(data)
    b = sock.recv(16)
    payload = loads_plist(sock, b)
    pair_record = get_pair()
    pem_path = save_pem(pair_record)
    if _ssl:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers("ALL:@SECLEVEL=0")
        context.load_cert_chain(pem_path, keyfile=pem_path)
        context.check_hostname = False
        ssock = context.wrap_socket(sock, server_hostname="iphone.localhost")
        sock = ssock

    return sock


def create_session():
    sock = create_inner_connection()
    # ----------------------------------------------------------------------
    payload = {"Request": "QueryType"}
    data = dump_plist(payload, is_fist=False)
    sock.sendall(data)
    b = sock.recv(4)
    payload = loads_plist(sock, b, is_fist=False)
    print(f"----->访问lockdown服务回包信息：{payload}")
    pair_record = get_pair()
    pem_path = save_pem(pair_record)
    payload = {
        "Request": "StartSession",
        "HostID": pair_record['HostID'],
        "SystemBUID": pair_record['SystemBUID'],
        "ProgName": "cyril",
    }
    data = dump_plist(payload, is_fist=False)
    sock.sendall(data)
    b = sock.recv(4)
    payload = loads_plist(sock, b, is_fist=False)
    print(f'----->请求访问lockdown回包信息：{payload}')
    if payload['EnableSessionSSL']:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers("ALL:@SECLEVEL=0")
        context.load_cert_chain(pem_path, keyfile=pem_path)
        context.check_hostname = False
        ssock = context.wrap_socket(sock, server_hostname="iphone.localhost")
        sock = ssock
    payload = {
            "Request": "GetValue",
            "Label": "cyril",
        }
    data = dump_plist(payload, is_fist=False)
    sock.sendall(data)
    b = sock.recv(4)
    payload = loads_plist(sock, b, is_fist=False)
    print(f'----->创建session成功后的回包: {payload}')
    print(f"----->创建session成功后的回包ProductVersion输出: {payload['Value']['ProductVersion']}")
    return sock

def get_device_list():
    global device_id, uuid
    sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock1.settimeout(10)
    sock1.connect(('127.0.0.1', 27015))
    payload = {
                "MessageType": "ListDevices",  # 必选
                "ClientVersionString": "libusbmuxd 1.1.0",
                "ProgName": 'cyril',
                "kLibUSBMuxVersion": 3,
                # "ProcessID": 0, # Xcode send it processID
            }
    data = dump_plist(payload)
    sock1.sendall(data)
    b = sock1.recv(16)
    payload = loads_plist(sock1, b)
    device_id = payload['DeviceList'][0]['DeviceID']
    uuid = payload['DeviceList'][0]['Properties']['SerialNumber']


if __name__ == '__main__':
    SERVICE_NAME = 'com.apple.internal.devicecompute.CoreDeviceProxy'
    get_device_list()
    sock = create_session()
    service_payload = {
            "Request": "StartService",
            "Service": SERVICE_NAME,
            "Label": 'cyril',
        }
    plist_bytes = plistlib.dumps(service_payload)
    length = len(plist_bytes)
    header = struct.pack(">I", length)
    sock.sendall(header + plist_bytes)
    b = sock.recv(4)
    (length,) = struct.unpack(">I", b)
    body_data = sock.recv(length)
    payload = plistlib.loads(body_data)
    print(payload)
    sock = create_inner_connection(payload.get("Port"), _ssl=True)
    print(sock)

    CDTunnelPacket = Struct(
        'magic' / Const(b'CDTunnel'),
        'body' / Prefixed(Int16ub, GreedyBytes),
    )

    # payload = {"type": "clientHandshakeRequest", "mtu": 16000}
    payload = b'CDTunnel\x000{"type": "clientHandshakeRequest", "mtu": 16000}'
    sock.sendall(payload)

    data = sock.recv(16000)
    print(data)
    handshake_response = json.loads(CDTunnelPacket.parse(data).body)
    # 这里是发回需要创建网段的回包

    mtu = handshake_response['serverRSDPort']
    print(handshake_response['serverAddress'], handshake_response['serverRSDPort'])
