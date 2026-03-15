from fastapi import Depends, Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated, Optional
from loguru import logger

from services.auth_service import AuthService
from schemas.account import Account
from errors import UnauthorizedError, AccountBlockedError
from repositories.account import AccountRepository

def auth_service() -> AuthService:
    return AuthService()

def account_repo() -> AccountRepository:
    return AccountRepository()

AuthServiceDepend = Annotated[AuthService, Depends(auth_service)]
AccountRepositoryDepend = Annotated[AccountRepository, Depends(account_repo)]

security = HTTPBearer(auto_error=False)

async def get_current_user_optional(
    request: Request,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    auth_service: AuthServiceDepend,
    account_repo: AccountRepositoryDepend
) -> Optional[Account]:
    
    token = request.cookies.get("x-user-token")
    
    if not token and credentials:
        token = credentials.credentials
        source = "header"
    
    if not token:
        return None
    
    try:
        user_id = await auth_service.verify(token)
        
        account = await account_repo.get_by_id(user_id)
        
        if account.is_blocked:
            logger.warning(f"Заблокированный аккаунт пытается получить доступ: {account.login}")
            return None
            
        return account
        
    except UnauthorizedError:
        logger.debug(f"Невалидный токен из cookie")
        return None
    except AccountBlockedError:
        logger.warning(f"Попытка доступа заблокированного аккаунта")
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении пользователя из cookie: {e}")
        return None


async def get_current_user_required(
    request: Request,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    auth_service: AuthServiceDepend,
    account_repo: AccountRepositoryDepend
) -> Account:

    user = await get_current_user_optional(request, credentials, auth_service, account_repo)
    
    if not user:
        logger.warning("Попытка доступа к защищенному ресурсу без авторизации")
        raise HTTPException(
            status_code=401,
            detail="Не авторизован",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


CurrentUserOptional = Annotated[Optional[Account], Depends(get_current_user_optional)]
CurrentUserRequired = Annotated[Account, Depends(get_current_user_required)]