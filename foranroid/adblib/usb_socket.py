import queue
import struct
import threading
import usb

from parse_tools import parse_data


class DeviceMonitor:
    def __init__(self, id_vendor, id_product, interface, address_in, address_out):
        self.running = None
        self.read_thread = None
        self.dev = None
        self.stop_event = threading.Event()
        self.data_queue = queue.Queue()
        self.id_vendor = id_vendor
        self.id_product = id_product
        self.usb_interface = interface
        self.address_in = address_in
        self.address_out = address_out
        self.device_usb_found = self.find_usb_device()
        if self.device_usb_found:
            self.start_monitoring()

    def _recv_msg_for_in_port(self):
        while self.running and not self.stop_event.isSet():
            try:
                data = self.dev.read(self.address_in, 1024 * 1024, timeout=1000)
                response_data = parse_data(data)
                self.data_queue.put(response_data)
            except usb.core.USBError as e:
                if e.errno == 110 or e.errno == 10060:  # 超时错误
                    continue
                else:
                    print(f"USB Error: {e}")
                    break
            except Exception as e:
                self.stop_monitoring()

    def _write_msg_to_out_port(self, cm):
        self.dev.write(self.address_out, cm)

    def start_monitoring(self):
        self.running = True
        self.read_thread = threading.Thread(target=self._recv_msg_for_in_port)
        # self.read_thread.daemon = True
        self.read_thread.start()

    def send_packet(self, command, is_adb=True):
        message = command
        if is_adb:
            message = b''.join([struct.pack('<I', getattr(command, attr)) for attr in vars(command)])
        self._write_msg_to_out_port(message)

    def handle_packet(self):
        items = []
        while not self.data_queue.empty():
            try:
                info = self.data_queue.get_nowait()
                items.append(info)
            except queue.Empty:
                break
        return items

    def find_usb_device(self):
        self.dev = usb.core.find(idVendor=self.id_vendor, idProduct=self.id_product)
        if self.dev is None:
            return False
        self.dev.set_configuration()
        self.dev.reset()
        self.dev.set_interface_altsetting(self.usb_interface, 0)
        return True

    def stop_monitoring(self):
        self.running = False
        self.stop_event.set()
        usb.util.dispose_resources(self.dev)
