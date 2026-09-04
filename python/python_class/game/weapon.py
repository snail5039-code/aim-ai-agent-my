from abc import ABC, abstractmethod
class Weapon(ABC):

    @abstractmethod
    def skill(self):
        pass



class Sword(Weapon):

    def skill(self):
        print('강력한 베기')


class Staff(Weapon):
    
    def skill(self):
        print('강력한 마법)')