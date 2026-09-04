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
        if self.job.can_use_weapon(weapon):
            self.weapon = weapon
            print(f"{self.name}이 무기 장착 완료")
        else :
            print(f"{self.name} 직업과 다른 무기 장착 불가능!")

    def use_weapon_skill(self):
        if self.weapon is None:
            print(f"장착한 무기가 없습니다.")
        else:
            self.weapon.use_skill()