from fastapi import FastAPI
from mysite.post_api import router as post_router
from mysite2.post_api import router as pydantic_router
from mysite3.post_api import router as response_router
from mysite4.routers.post_router import router as layered_router

app = FastAPI()
app.include_router(post_router)
app.include_router(pydantic_router)
app.include_router(response_router)
app.include_router(layered_router)


@app.get("/")
def get_root():
    return {"Hello": "World"}
