from abc import ABC, abstractmethod
from weapon import Weapon, Staff, Sword

class Job(ABC):
    allowed_weapon = []

    @abstractmethod
    def attack(self):
        pass

    def equip_weapon(self, weapon : Weapon):
        return type(weapon) in self.allowed_weapon

class Warrior(Job):
    allowed_weapon = [Sword]

    def attack(self):
        print("검을 내려친다")

class Mage(Job):
    allowed_weapon = [Staff]

    def attack(self):
        print("지팡이를 내려친다")