# 다음 2차원 배열을 만들어보세요.

#  1  2  3  4  5
# 16 17 18 19  6
# 15 24 25 20  7        24는 2, 1   25 2, 2
# 14 23 22 21  8        23   3, 1   15 2 , 0    17  1, 1
# 13 12 11 10  9

n = 5

mat = []

for i in range(n) :
    li = []
    for j in range(n) :
        li.append(0)
    mat.append(li) 

# 우측 부터 아래 왼쪽 위 이런 순으로 진행한다
di = [0, 1, 0, -1]
dj = [1, 0, -1, 0]

i = 0
j = 0
dr = 0 # 시작 방향

for num in range(1, 26) :
    mat[i][j] = num

    ni = i + di[dr]
    nj = j + dj[dr]

    if ni < 0 or ni >= n or nj < 0 or nj >= n or mat[ni][nj] != 0 :
        dr = (dr + 1) % 4
        ni = i + di[dr]
        nj = j + dj[dr]

    i = ni
    j = nj

# 출력
for i in mat :
    print(i)

