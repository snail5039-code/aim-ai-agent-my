from fastapi import APIRouter, HTTPException, status
from mysite3.post import PostCreate, Post, PostDetailResponse, PostListResponse

router = APIRouter(prefix="/posts-response", tags=["mysite3"])

posts = []
post_id = 0


@router.post(
    "",
    response_model=PostDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_post(post_data: PostCreate):
    global post_id
    post_id += 1

    new_post = Post(post_id, post_data.title, post_data.content)
    posts.append(new_post)

    return new_post


@router.get("", response_model=list[PostListResponse])
def get_posts():
    return posts


@router.get("/search", response_model=list[PostListResponse])
def search_posts(keyword: str | None = None):
    if keyword:
        return [post for post in posts if keyword in post.title]
    return posts


@router.get("/{id}", response_model=PostDetailResponse)
def get_post(id: int):
    for post in posts:
        if post.id == id:
            return post
    raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")


@router.put("/{id}", response_model=PostDetailResponse)
def update_post(id: int, updated_post: PostCreate):
    for post in posts:
        if post.id == id:
            post.title = updated_post.title
            post.content = updated_post.content
            return post
    raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int):
    for index, post in enumerate(posts):
        if post.id == id:
            posts.pop(index)
            return
    raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
