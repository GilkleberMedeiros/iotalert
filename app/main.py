from fastapi import FastAPI
import uvicorn


app = FastAPI(
    title="IoTAlert", summary="API de Telemetria industrial. (Projeto Pessoal)"
)


@app.get("/ping")
def ping():
    return {"message": "pong"}


def main():
    print("Hello from iotalert!")

    uvicorn.run(app, host="localhost", port=8000)


if __name__ == "__main__":
    main()
