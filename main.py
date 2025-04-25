import uvicorn
from fastapi import FastAPI


app = FastAPI()

app.include_router(..., prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run(app="main:app", reload=True)
