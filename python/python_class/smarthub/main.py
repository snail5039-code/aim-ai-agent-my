from smarthub import SmartHub
from device import Device, AirConditioner, SmartLight
from protocol import Protocol, ZigbeeProtocol, WiFiProtocol


zigbee = ZigbeeProtocol()
wifi = WiFiProtocol()

light = SmartLight('전등', '애플', zigbee)
aircon = AirConditioner('에어컨', '삼성', wifi)


sh = SmartHub("스마트허브", zigbee)

# 스마트허브에 전등 추가
sh.register_device(light)

print(sh.devices)

# 스마트허브에 에어컨 추가
sh.register_device(aircon)

print(sh.devices)

# 사마트허브에 다른 에어컨 추가
aircon_zigbee = AirConditioner('에어컨', '캐리어', zigbee)
sh.register_device(aircon_zigbee)

print(sh.devices)

# 전등 하나 켜두고
sh.devices[0].run()
print()

# 전체 실행

sh.run_all()