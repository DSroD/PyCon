from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from dependencies import dependencies
from routes import login, index, servers

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(login.router)
app.include_router(index.router)
app.include_router(servers.router)


@app.on_event("startup")
async def startup():
    await dependencies.on_start()


@app.on_event("shutdown")
async def shutdown():
    dependencies.on_stop()
