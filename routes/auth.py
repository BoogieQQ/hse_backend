from fastapi import APIRouter, HTTPException, Response, Request
from loguru import logger

from schemas.account import AccountLogin, AccountResponse, TokenResponse
from services.auth_service import AuthService
from errors import AuthorizedError, UnauthorizedError


auth_router = APIRouter(prefix="/auth", tags=["authentication"])
auth_service = AuthService()


@auth_router.post("/login", response_model=TokenResponse)
async def login(login_data: AccountLogin, response: Response):
    try:
        logger.info(f"Запрос на авторизацию пользователя: {login_data.login}")

        access_token, refresh_token = await auth_service.login(
            login_data.login, 
            login_data.password
        )

        response.set_cookie(
            key="x-user-token",
            value=access_token,
            secure=True
        )

        logger.info(f"Пользователь {login_data.login} успешно авторизован")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    except AuthorizedError as e:
        logger.error(f"Ошибка авторизации для пользователя {login_data.login}: {e}")
        raise HTTPException(
            status_code=401,
            detail=str(e) or "Неверный логин или пароль"
        )
    except ValueError as e:
        logger.error(f"Ошибка валидации входных данных: {e}")
        raise HTTPException(
            status_code=422,
            detail=f"Ошибка валидации входных данных: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Внутренняя ошибка сервера при авторизации: {e}")
        raise HTTPException(
            status_code=500,
            detail="Внутренняя ошибка сервера при авторизации"
        )