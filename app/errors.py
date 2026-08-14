from fastapi import HTTPException


class AppError(Exception): ...


class APIError(HTTPException, AppError): ...
