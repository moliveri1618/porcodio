from fastapi import FastAPI
from mangum import Mangum
from dependecies import setup_imports
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

# Import routers dynamically based on environment
routers = setup_imports()
items = routers.get("items")

@app.get("/")
async def root():
    return {"message": "Hello asdasd"}
