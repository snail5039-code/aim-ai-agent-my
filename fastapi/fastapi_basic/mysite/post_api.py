from fastapi import APIRouter
from .post import Post

router = APIRouter(prefix="/posts", tags=["mysite"])

# 게시글 객체들을 저장하는 리스트
posts = []
post_id = 0


# 게시글 생성
@router.post("")
def create_post():
    global post_id
    post_id += 1

    post = Post(post_id, "제목", "내용")

    posts.append(post)

    return post


# 게시글 조회
# posts 보여주기
posts.append(Post(1, "기본 제목", "기본 내용"))
post_id = 1


@router.get("")
def get_posts():
    # 게시글 리스트 전체를 반환
    return posts


# mysite/post_api.py 내부에 추가


@router.get("/{id}")
def get_post(id: int):
    # 리스트 내 객체들을 하나씩 검사
    for post in posts:
        # 객체의 식별자와 입력받은 식별자가 일치하는지 확인
        if post.id == id:
            return post
    return None


# update

# mysite/post_api.py 내부에 추가


@router.put("/{id}")
def update_post(id: int):
    for post in posts:
        if post.id == id:
            # 객체의 속성 값 변경
            post.title = "수정된 제목"
            post.content = "수정된 내용"
            return post
    return None


# delete
# mysite/post_api.py 내부에 추가


@router.delete("/{id}")
def delete_post(id: int):
    # 리스트를 순회하며 인덱스(i)와 내용(post)을 함께 추출
    for i, post in enumerate(posts):
        if post.id == id:
            # 해당 인덱스의 데이터를 삭제하고 루프 종료

            return posts.pop(i)

    return "삭제 실패"
