import time

import rsa

from get_window_usb import judgment_adb_device
from protocol_port import adb_connect, adb_auth_signature, adb_auth_rsa_publickey, shell_command
from usb_socket import DeviceMonitor


def device_authorization(info):
    # TODO：定义一个token和设备认证， 默认第一次认证
    pubkey, privkey = rsa.newkeys(2048)
    id_vendor, id_product, interface, address_in, address_out = info
    dev = DeviceMonitor(id_vendor, id_product, interface, address_in, address_out)
    ms = adb_connect()
    dev.send_packet(ms)
    time.sleep(0.1)
    token = dev.handle_packet()[1]
    msg, signature = adb_auth_signature(token, privkey)
    dev.send_packet(msg)
    dev.send_packet(signature, is_adb=False)
    time.sleep(0.1)
    signature_info = dev.handle_packet()
    token1 = signature_info[1]
    msg2, pub2 = adb_auth_rsa_publickey(pubkey)
    dev.send_packet(msg2)
    dev.send_packet(pub2, is_adb=False)
    time.sleep(5)
    print(dev.handle_packet()[1])
    dev.stop_monitoring()


def adb_shell_command(command, info):
    id_vendor, id_product, interface, address_in, address_out = info
    dev = DeviceMonitor(id_vendor, id_product, interface, address_in, address_out)
    mes, b_mes = shell_command(command)
    dev.send_packet(mes)
    dev.send_packet(b_mes, is_adb=False)
    time.sleep(0.1)
    for i in dev.handle_packet():
        print(i)


if __name__ == '__main__':
    '''
    使用说明查看readme.txt文档
    '''
    # TODO: 代码很粗造， 仅演示adb-server是如果和Android设备通信。
    #  实现设备授权和shell命令
    dev = tuple()
    with judgment_adb_device() as devices:
        for device in devices:
            print(device)
            a = [getattr(device, attr) for attr in vars(device)]
            print(a)
            # 默认找到第一台设备退出
            # 返回的格式 [idVendor, idProduct, serial_number, bus, address,
            # bInterfaceNumber, bEndpointAddress_in, bEndpointAddress_out]
            dev = a[0], a[1], a[-3], a[-2], a[-1]
            break
    device_authorization(dev)
    adb_shell_command('am start -n com.tencent.mobileqq/com.tencent.mobileqq.activity.SplashActivity', dev)
    # adb_shell_command('ls -l /data/local/tmp/'， dev)
    # adb_shell_command('ls -l'， dev)
    # adb_shell_command('getprop ro.product.cpu.abi'，dev)
