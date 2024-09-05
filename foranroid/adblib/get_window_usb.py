import base64
from contextlib import contextmanager

import usb.core
from usb import util

ADB_CLASS = 0xff    # 255 bInterfaceClass
ADB_SUBCLASS = 0x42  # 66 bInterfaceSubClass
ADB_PROTOCOL = 0x1   # bInterfaceProtocol


class AdbUsb:
    idVendor: int
    idProduct: int
    serial_number: str
    bus: int
    address: int
    bInterfaceNumber: int
    bEndpointAddress_in: int
    bEndpointAddress_out: int


def is_adb_interface(usb_class, usb_subclass, usb_protocol):
    return usb_class == ADB_CLASS and usb_subclass == ADB_SUBCLASS and usb_protocol == ADB_PROTOCOL


@contextmanager
def judgment_adb_device():
    usb_devices = usb.core.find(find_all=True)
    try:
        adb_devices = []
        for usb_device in usb_devices:
            for cfg in usb_device:
                for intf in cfg:
                    if is_adb_interface(intf.bInterfaceClass, intf.bInterfaceSubClass, intf.bInterfaceProtocol):
                        point_in = None
                        point_out = None
                        interface_number = intf.bInterfaceNumber
                        for iInter in intf:
                            if util.endpoint_direction(iInter.bEndpointAddress) == util.ENDPOINT_IN:
                                point_in = iInter.bEndpointAddress
                            elif util.endpoint_direction(iInter.bEndpointAddress) == util.ENDPOINT_OUT:
                                point_out = iInter.bEndpointAddress
                        adb_usb = AdbUsb()
                        adb_usb.idVendor = usb_device.idVendor
                        adb_usb.idProduct = usb_device.idProduct
                        adb_usb.serial_number = usb_device.serial_number
                        adb_usb.bus = usb_device.bus
                        adb_usb.address = usb_device.address
                        adb_usb.bInterfaceNumber = interface_number
                        adb_usb.bEndpointAddress_in = point_in
                        adb_usb.bEndpointAddress_out = point_out
                        adb_devices.append(adb_usb)
        yield adb_devices
    finally:
        pass


if __name__ == '__main__':
    with judgment_adb_device() as devices:
        for device in devices:
            print(device)
            print([getattr(device, attr) for attr in vars(device)])
