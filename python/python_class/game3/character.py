from job import Job
from weapon import Weapon

class Character:
    def __init__(self, name, job : Job):
        self.name = name
        self.job = job
        self.weapon = None

    def attack(self):
        self.job.attack()

    def equip_weapon(self, weapon : Weapon):
        if self.job.equip_weapon(weapon):
            self.weapon = weapon
            print("무기 장착 완료")
        else:
            print("직업이 맞지 않음")

    def use_skill(self):
        if self.weapon is None :
            print("무기 장착 안했음!")
        else :
            self.weapon.use_skill()