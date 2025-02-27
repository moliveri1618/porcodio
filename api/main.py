# from mangum import Mangum
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello Wddddorld"}

# handler = Mangum(app=app)