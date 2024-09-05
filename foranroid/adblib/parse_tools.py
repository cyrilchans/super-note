import array
import binascii
import struct


class Para:
    A_SYNC = 0x434e5953
    A_CNXN = 0x4e584e43
    A_OPEN = 0x4e45504f
    A_OKAY = 0x59414b4f
    A_CLSE = 0x45534c43
    A_WRTE = 0x45545257
    A_AUTH = 0x48545541


# 打印解析结果
command_map = {
    Para.A_AUTH: 'AUTH',
    Para.A_CNXN: 'CNXN',
    Para.A_SYNC: 'SYNC',
    Para.A_OPEN: 'OPEN',
    Para.A_OKAY: 'OKAY',
    Para.A_CLSE: 'CLSE',
    Para.A_WRTE: 'WRTE',
}


def adb_protocol(byte_array):
    command, arg0, arg1, data_length, data_check, magic = struct.unpack('6I', byte_array[:24])
    command_name = command_map.get(command, 'UNKNOWN')
    return {
        'command': command_name,
        'arg0': arg0,
        'arg1': arg1,
        'data_length': data_length,
        'data_check': data_check,
        'magic': magic,
    }


def parse_ws_data(hex_string):
    # 直接发wireshark的值过来解析
    byte_array = binascii.unhexlify(hex_string)
    if not len(byte_array):
        print("不是24字节， 不属于adb协议")
        return byte_array
    data = adb_protocol(byte_array)
    return data


def parse_recv_usb_data(array_data):
    # 解析adb请求头和数据
    if len(array_data) == 20:
        return array_data.tobytes()
    elif len(array_data) == 24:
        adb_message_bytes = array_data.tobytes()
        data = adb_protocol(adb_message_bytes)
        return data
    else:
        return array_data.tobytes()


def parse_data(data):
    if type(data) is str and int(data, 16):
        return parse_ws_data(data)
    elif type(data) is array.array:
        return parse_recv_usb_data(data)


if __name__ == '__main__':
    array1 = '5752544520000000030000008e02000000000000a8adabba'
    array2 = array.array('B', [79, 75, 65, 89, 61, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 176, 180, 190, 166])
    d = parse_data(array2)
    print(d)