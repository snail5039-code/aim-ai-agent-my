from abc import ABC, abstractmethod
from python.python_class.game.weapon import Weapon, Staff, Sword
class Job(ABC):

    @abstractmethod
    def attack(self):
        pass


class Warrior(Job):
    allow_weapon_list: set[Weapon]= { Sword, }

    def attack(self):
        print('검을 휘두른다!')


class Magicion(Job):
    allow_weapon_list: set[Weapon]= { Staff, }

    def attack(self):
        print('마법 발사!')
