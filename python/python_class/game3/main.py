from job import Job, Warrior, Mage
from character import Character
from weapon import Weapon, Sword, Staff

warrior = Warrior()
mage = Mage()


arthur = Character("전사", warrior)
magi = Character("법사", mage)

arthur.attack()
magi.attack()


arthur.use_skill()
arthur.equip_weapon(Staff())
arthur.equip_weapon(Sword())
arthur.use_skill()

magi.use_skill()
magi.equip_weapon(Sword())
magi.equip_weapon(Staff())
magi.use_skill()