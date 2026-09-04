from abc import ABC, abstractmethod

class Weapon(ABC):
    @abstractmethod
    def use_skill(self):
        pass

class Sword(Weapon):
    def use_skill(self):
        print("강력한 베기")

class Staff(Weapon):
    def use_skill(self):
        print("강력하게 지팡이 휘두르기")