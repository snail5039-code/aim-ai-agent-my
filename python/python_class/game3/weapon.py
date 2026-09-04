from abc import ABC, abstractmethod

class Weapon(ABC):

    @abstractmethod
    def use_skill(self):
        pass

class Sword(Weapon):

    def use_skill(self):
        print("강력한 검 내려치기")

class Staff(Weapon):
    def use_skill(self):
        print("강력한 지팡이 내려치기")