# ===========================================================
# Arquivo: app/core/auth.py
# Implementa autenticação básica.
# ATENÇÃO: NÃO USE USUÁRIO/SENHA FIXOS EM PRODUÇÃO!
# Adicionado logging para depuração do erro 401.
# CORRIGIDO: Indentação do bloco try/except e definição final de classe.
# ===========================================================
import os
import logging # Adicionado para logs
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

# Importa dos schemas (garanta que o caminho está correto)
try:
    from app.schemas.dashboard import User, UserInDB, Token
# CORREÇÃO: Indentação do except e das classes fallback
except ImportError:
    # Fallback ou log de erro se o import falhar
    logging.critical("AUTH: Falha ao importar schemas de app.schemas.dashboard")
    # Definições básicas para evitar erros, mas idealmente corrigir o import
    # Indentação correta para as classes dentro do except
    class User:
        username: str
        disabled: Optional[bool] = None
    class UserInDB(User):
        hashed_password: str
    class Token:
        access_token: str
        token_type: str


logger = logging.getLogger("famdomes.auth") # Logger específico

# --- Configuração ---
SECRET_KEY = os.getenv("DASHBOARD_SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7") # Mantenha esta chave segura!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("DASHBOARD_TOKEN_EXPIRE_MINUTES", 60 * 24)) # 1 dia

# --- Banco de Dados Falso de Usuários ---
# ATENÇÃO: Substitua o valor de "hashed_password" pelo HASH GERADO NO TERMINAL!
FAKE_USERS_DB = {
    "admin": {
        "username": "admin",
        # COLE O HASH GERADO AQUI DENTRO DAS ASPAS:
        "hashed_password": "$2b$12$EixZaYVK1fsbwAp2rqm.y.eMAx2z1.PNgQOfnS2z5.l3N4fZtQmGO", # <--- SUBSTITUA ESTE VALOR!!!
        "disabled": False,
    }
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/dashboard/token") # Rota de login no backend

# --- Funções de Autenticação ---

def verify_password(plain_password, hashed_password):
    logger.debug("Verificando senha...")
    try:
        result = pwd_context.verify(plain_password, hashed_password)
        logger.debug(f"Resultado da verificação da senha: {result}")
        return result
    except Exception as e:
        logger.error(f"Erro durante verify_password: {e}")
        return False

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(username: str) -> Optional[UserInDB]:
    logger.debug(f"Buscando usuário: {username}")
    if username in FAKE_USERS_DB:
        user_dict = FAKE_USERS_DB[username]
        logger.debug(f"Usuário '{username}' encontrado no DB falso.")
        # Retorna um objeto UserInDB (assumindo que foi importado ou definido no fallback)
        return UserInDB(username=user_dict["username"], hashed_password=user_dict["hashed_password"], disabled=user_dict["disabled"])
    logger.debug(f"Usuário '{username}' NÃO encontrado no DB falso.")
    return None

def authenticate_user(username: str, password: str) -> Optional[User]:
    logger.info(f"Tentando autenticar usuário: {username}")
    user = get_user(username)
    if not user:
        logger.warning(f"Autenticação falhou: Usuário '{username}' não encontrado.")
        return None
    # Acessa o atributo 'disabled' do objeto user
    if user.disabled:
         logger.warning(f"Autenticação falhou: Usuário '{username}' está desabilitado.")
         return None

    # Acessa o atributo 'hashed_password' do objeto user
    if not verify_password(password, user.hashed_password):
        logger.warning(f"Autenticação falhou: Senha incorreta para usuário '{username}'.")
        return None

    logger.info(f"Usuário '{username}' autenticado com sucesso.")
    # Retorna um objeto User (sem o hash)
    return User(username=user.username, disabled=user.disabled)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_active_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            logger.warning("Token JWT inválido: sem 'sub' (username).")
            raise credentials_exception
    except JWTError as e:
        logger.warning(f"Erro ao decodificar token JWT: {e}")
        raise credentials_exception from e

    user = get_user(username=username)
    if user is None:
        logger.warning(f"Token válido, mas usuário '{username}' não encontrado no sistema.")
        raise credentials_exception
    if user.disabled:
         logger.warning(f"Token válido, mas usuário '{username}' está desabilitado.")
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    # Retorna um objeto User
    return User(username=user.username, disabled=user.disabled)

# CORREÇÃO: Bloco final para definir UserInDB se a importação falhou
# Garante que a verificação e a definição da classe estejam no nível superior do módulo (sem indentação extra)
try:
    # Verifica se UserInDB foi importado corretamente e é uma classe
    if not isinstance(UserInDB, type) or not issubclass(UserInDB, User):
        # Se não foi importado corretamente ou não é subclasse, define o fallback
        logger.warning("AUTH: UserInDB não importado corretamente ou inválido. Definindo fallback.")
        class UserInDB(User):
             hashed_password: str
except NameError:
     # Se UserInDB nem sequer está definido (ImportError grave)
     logger.error("AUTH: UserInDB não está definido. Definindo fallback.")
     class UserInDB(User):
          hashed_password: str

