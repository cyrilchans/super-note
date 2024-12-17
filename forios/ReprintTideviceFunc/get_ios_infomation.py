import plistlib
import socket
import struct

address = ('127.0.0.1', 27015)
message_type = 8


def get_device_list():
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
    plist_bytes = plistlib.dumps(payload)
    length = 16 + len(plist_bytes)
    header = struct.pack("IIII", length, 1, message_type, 1)
    sock1.sendall(header+plist_bytes)
    b = sock1.recv(16)
    (length, version, resp, tag) = struct.unpack("IIII", b)
    body_data = sock1.recv(length)
    payload = plistlib.loads(body_data)
    # print(payload)
    for i in payload['DeviceList']:
        print(i)


get_device_list()