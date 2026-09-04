from abc import ABC, abstractmethod
from device import Device
from protocol import Protocol

class SmartHub:

    def __init__(self, name :str, protocol :Protocol, devices :list[Device] = []):
        self.name :str = name
        self.protocol :Protocol = protocol
        self.devices :list[Device]= devices


    def register_device(self, device : Device):
        # 디바이스의 프로토콜과 내가 지원하는 프로토콜이 같은지를 알고 싶다.
        # if type(device.protocol) is type(self.protocol):
        # print(type(device.protocol), type(self.protocol))
        if isinstance(device.protocol, type(self.protocol)):

            self.devices.append(device)
            print('연결 완료')
        else:
            print(f'디바이스의 프로토콜 : {device.protocol}')
            print(f'허브의 프로토콜 : {self.protocol}')
            print('연결 실패')
            # raise Exception
        

    def run_all(self):

        for device in self.devices:
            device.protocol.start_connection()

            device.run()

    def stop_all(self):
        for device in self.devices:
            device.protocol.start_connection()

            device.stop()