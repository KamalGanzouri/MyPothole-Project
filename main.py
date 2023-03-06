from fastapi import FastAPI

app = FastAPI()


@app.get("/how")
async def root():
    return {"message": "Hello World"}
