from fastapi import APIRouter, status
from mysite4.services.post_service import post_service
from mysite4.schemas.post import PostCreate, PostDetailResponse, PostListResponse

router = APIRouter(prefix="/posts-layered", tags=["mysite4"])


@router.post("", response_model=PostDetailResponse, status_code=status.HTTP_201_CREATED)
def create_post(data: PostCreate):
    return post_service.create_post(data)


@router.get("", response_model=list[PostListResponse])
def get_posts():
    return post_service.get_posts()


@router.get("/{id}", response_model=PostDetailResponse)
def get_post(id: int):
    return post_service.get_post(id)


@router.put("/{id}", response_model=PostDetailResponse)
def update_post(id: int, data: PostCreate):
    return post_service.update_post(id, data)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int):
    post_service.delete_post(id)
