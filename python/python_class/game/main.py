from python.python_class.game.chartacter import Character
from python.python_class.game.job import Warrior, Magicion
from python.python_class.game.weapon import Sword, Staff
# 캐릭터 만들기(이름, job)

warrior = Warrior()
magician = Magicion()

arther = Character('아서', warrior)
# 무기 쥐어주기

arther.attack()

arther.job = magician

arther.attack()

# 공격하기

# 장비 착용하기

staff = Staff()

arther.equip_weapon(staff)
# 스킬사용하기

arther.use_skill()

# 무기를 착용한 상태에서 직업을 바꿔버려요.
# 그럼 staff를 착용한 상태에서 warrior로 직업이 바뀝니다.
# job에 대한 setter에다가 다시 weapon이 해당 job에 맞는지를 체크하는 로직이
# 들어가야 할겁니다.