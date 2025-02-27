from fastapi import FastAPI
from mangum import Mangum
from api.routers import items  
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
handler = Mangum(app=app)

# CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Items Routers
app.include_router(items.router, prefix="/items", tags=["Items"])

@app.get("/")
async def root():
    return {"message": "Hello Worlddfdfdf"}
