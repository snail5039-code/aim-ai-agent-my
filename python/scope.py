# 파이썬 파일 실행시키기
# ctrl + j 터미널창 열기
# python 파일이름.py
# 또는 우측상단의 세모 (화살표)

# scope
# 변수가 살아있는 범위

value = 10

print(value)

print('\n함수 내부')

def func_1() :
    value_1 = 10

    print(value_1)

func_1()


print('\n함수 내부의 변수를 외부에서 접근')

def func_2() :
    value_2 = 20

# value_2라는 것이 정의되어있지 않아서 접근이 불가능하다.
# print(value_2) 접근 불가!

# 이것이 scope.
# 함수 내부의 변수는 외부에서 접근이 불가능하다.
# 함수 내부의 변수는 함수 내에서만 사용이 가능하다.

# 우리가 loop.py에 있는 변수에 접근이 가능하냐?
# -> 불가능


# LEGB rule
# local
# encloed
# gloval
# built-in


#############################
print('\n함수 외부의 변수를 함수 내에서 사용')

value_3 = 30

def func_3() :
    print(value_3)

func_3()

print('\nencloed 상황')

def func_4() :
    # enclosed
    value_3 = 40

    def inner() :
        # local
        print(value_3)
    inner()

func_4()

print('\n함수 내부에서는 외부의 값이 영향을 미칠 수 없다.')

value_5 = 50

def func_5() :

    value_5 = 500000

    print(value_5)

func_5()
print(value_5)


print('\n함수 내부에서 외부에 영향을 미칠 수 있는 경우도 있다.')

value_6 = 60
value_7 = 70
def func_6() :
    # value_6은 func_6의 공간이 아닌 global에 있는 value_6을 가르킨다
    global value_6
    value_6 = 6000000
    value_7 = 7000000

func_6()
print(value_6)
print(value_7)

# 단, global은 알고리즘 문제 풀때는 사용하지만
# 개발할때는 "절대" 사용하지 않는다.

# 다른 언어 하시다가 오신 분들을 위해서
# python은 if, for문에 block scope를 가지지 않습니다.
# 사용 가능.
if True :
    value_8 = 30
print(value_8)

print("\n 함수 내부에서 외부의 리스트 변경")
# global과 마찬가지로 개발에서는 사용하면 안됨.
# 알고리즘 문제를 풀때는 유용하게 사용이 됨.

lst = [1, 2, 3, 4]
lst2 = [1, 2, 3, 4]

def func_1() :
    lst[0] = 10000
    lst2 = [10000, 2, 3, 4]

func_1()
print(lst)
print(lst2)