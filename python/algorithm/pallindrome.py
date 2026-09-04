# 회문
# 거꾸로 했을 때 나 자신과 같은 단어
# 수박이박수
# abcdcba
# 회문이라고 부릅니다.

# 단어를 입력받아서 회문인지 아닌지 찾아보는 함수를 만들어보세요.


def is_pallindrome(str) :
    return str == str[::-1]

    # 슬라이싱
    # [start : end : step]


# 반복을 통해 뒤집어보기
def is_pallindrome(str) :
    word = '다시합창합시다'

    reversd_word = ''
    # 맨 뒤부터 하나씩 꺼내와서 앞에 붙인다.
    for index in range(len(word)) :
        reversed_index = len(word) - index - 1
        print(index, reversed_index)    
        reversd_word = reversd_word + word[reversed_index]
    return word == reversd_word

def is_pallindrome(word) :

    reversd_word = ''
    # 맨 뒤부터 하나씩 꺼내와서 앞에 붙인다.
    for index in range(len(word) -1, -1, -1) :
        reversd_word = reversd_word + word[index]
    return word == reversd_word

def is_pallindrome(word) :

    reversd_word = ''
    for char in word :
        # print(char)
        reversd_word = char + reversd_word

    return word == reversd_word

# 뒤집지 않고 글자 하나하나를 확인한다
def is_pallindrome(word) :

    # for start in range(len(word)) :
    for start in range(len(word) // 2) : # 앞과 뒤를 비교하기때문에 절반만 봐도 괜찮다
        end= len(word) - start - 1
        # print(start, end)

        if word[start] != word[end] :
            return False
    return True

# 뒤집지 않고 글자 하나하나를 확인한다
def is_pallindrome(word) :

    # 왼쪽 / 오른쪽의 index
    # two pointer
    left = 0
    right = len(word) - 1

    while left < right :
        if word[left] != word[right] :
            return False    
        left += 1
        right -= 1
    return True

print(is_pallindrome('수박이박수') )# => True
print(is_pallindrome('abcde')) # => False
