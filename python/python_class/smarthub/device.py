from abc import ABC, abstractmethod
from protocol import Protocol

class Device(ABC):

    def __init__(self, name :str, compnay :str, protocol :Protocol):
        self.name :str = name
        self.company :str = compnay
        self.protocol :Protocol = protocol

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def check_status(self):
        pass

    @abstractmethod
    def stop(self):
        pass


    def __repr__(self):
        return self.name


class SmartLight(Device):

    def __init__(self, name, compnay, protocol):
        super().__init__(name, compnay, protocol)
        self.status = False # 전원이 켜져있는지 여부
        self.brightness = 0

    def run(self):
        if self.status:
            print('이미 켜져있습니다!')

        else:
            self.status = True
            print('전등 실행!')

    def check_status(self):
        if self.status:
            print('전등 켜져있음')
        else:
            print('전등 꺼져있음')

    def stop(self):
        if not self.status:
            print('이미 꺼져있습니다!')
        else:
            self.status = False
            print('전등 꺼짐!')


class AirConditioner(Device):

    def __init__(self, name, compnay, protocol):
        super().__init__(name, compnay, protocol)
        self.status = False # 전원이 켜져있는지 여부
        self.temperature = 25

    def run(self):
        if self.status:
            print('이미 켜져있습니다!')

        else:
            self.status = True
            print('에어컨 실행!')

    def check_status(self):
        if self.status:
            print('에어컨 켜져있음')
        else:
            print('에어컨 꺼져있음')

    def stop(self):
        if not self.status:
            print('이미 꺼져있습니다!')
        else:
            self.status = False
            print('에어컨 꺼짐!')
