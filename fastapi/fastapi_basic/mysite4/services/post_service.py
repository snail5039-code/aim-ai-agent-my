from fastapi import HTTPException, status

from mysite4.repositories.post_repository import post_repository
from mysite4.schemas.post import Post, PostCreate


class PostService:
    def create_post(self, data: PostCreate):
        if data.title == "":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="title을 입력하세요",
            )

        if data.content == "":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="content를 입력하세요",
            )

        new_post = Post(title=data.title, content=data.content)

        return post_repository.save(new_post)

    def get_posts(self):
        return post_repository.find_all()

    def get_post(self, id: int):
        post = post_repository.find_by_id(id)
        if post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다.",
            )
        return post

    def update_post(self, id: int, data: PostCreate):
        if data.title == "":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="title을 입력하세요",
            )

        if data.content == "":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="content를 입력하세요",
            )

        self.get_post(id)
        return post_repository.update(id, data)

    def delete_post(self, id: int):
        self.get_post(id)
        post_repository.delete(id)


post_service = PostService()
