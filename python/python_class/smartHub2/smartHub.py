from abc import ABC, abstractmethod
from device import Device
from protocol import Protocol


class SmartHub:
    def __init__(self, name, protocol : Protocol, devices : list[Device] =[]):
        self.name : str = name
        self.protocol : Protocol = protocol
        self.devices : list[Device] = devices

    def register_device(self, device):
        if isinstance(device.protocol, type(self.protocol)):
            self.devices.append(device)
            print("연결 성공")
        else :
            print("연결실패")

    def run_all(self):
        for device in self.devices:
            self.protocol.start_connection()
            device.run()

    def stop_all(self):
         for device in self.devices:
            self.protocol.start_connection()
            device.stop()