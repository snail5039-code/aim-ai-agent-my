from pydantic import BaseModel


class PostCreate(BaseModel):
    title: str
    content: str


class Post:
    def __init__(self, id, title, content):
        self.id = id
        self.title = title
        self.content = content
