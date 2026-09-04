from abc import ABC, abstractmethod

class Protocol(ABC):

    @abstractmethod
    def start_connection(self):
        pass



class WiFiProtocol(Protocol):

    def start_connection(self):
        print('와이파이 연결 시도')

    def __str__(self):
        return '와이파이'

class ZigbeeProtocol(Protocol):

    def start_connection(self):
        print('Zigbee 연결 시도')

    def __str__(self):
            return '직비'
    

