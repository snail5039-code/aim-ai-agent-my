from character import Character
from job import Warrior, Mage
from weapon import Weapon, Sword, Staff

warrior = Warrior()
mage = Mage()

arthur = Character("아더", warrior)
merlin = Character("멀린", mage)

arthur.attack()
merlin.attack()

sword = Sword()
staff = Staff()

sword.use_skill()
staff.use_skill()

print(warrior.can_use_weapon(sword))
print(mage.can_use_weapon(staff))

arthur.equip_weapon(staff)
print(arthur.weapon)

arthur.use_weapon_skill()

arthur.equip_weapon(sword)
# print(arthur.weapon)

arthur.use_weapon_skill()

