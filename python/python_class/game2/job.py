from abc import ABC, abstractmethod
from weapon import Weapon, Sword, Staff

class Job(ABC):
    allowed_weapons = []

    @abstractmethod
    def attack(self):
        pass

    def can_use_weapon(self, weapon : Weapon):
        return type(weapon) in self.allowed_weapons
    
class Warrior(Job):
    allowed_weapons = [Sword]
    def attack(self):
        print("검을 휘두름")

class Mage(Job):
    allowed_weapons = [Staff]
    def attack(self):
        print("지팡이를 휘두름")
