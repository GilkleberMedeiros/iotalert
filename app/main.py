from fastapi import FastAPI
import uvicorn

from app.db import init_db

app = FastAPI(
  title="IoTAlert", summary="API de Telemetria industrial. (Projeto Pessoal)"
)


@app.get("/ping")
async def ping():
  return {"message": "pong"}


async def main():
  print("Hello from iotalert!")
  await init_db()

  uvicorn.run(app, host="localhost", port=8000)


if __name__ == "__main__":
  main()
