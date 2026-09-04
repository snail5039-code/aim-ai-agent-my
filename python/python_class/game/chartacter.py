from python.python_class.game.job import Job
from python.python_class.game.weapon import Weapon
class Character:

    def __init__(self, name, job: Job):
        self.name = name
        self.job: Job = job
        self.weapon: Weapon | None = None

    def attack(self):
        self.job.attack()


    def equip_weapon(self, weapon: Weapon):
        # 허가 리스트에 있어?
        if type(weapon) in self.job.allow_weapon_list:
            self.weapon = weapon
            print('장비 착용 완료!')
        # 없으면
        else:
            print("장비할 수 없습니다.")
    # def use_skill(self):

    def use_skill(self):
        if self.weapon is not None:
            print('스킬 사용')
            self.weapon.skill()
        else:
            print('스킬 사용 불가.')