from configparser import ConfigParser
from pathlib import Path
from typing import Dict, Any
from pydantic_settings import BaseSettings
import hvac
import os
from time import sleep

def load_config(config_path: str = 'config.ini') -> ConfigParser:
    config = ConfigParser()
    if not Path(config_path).exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    config.read(config_path)
    return config

def save_config(config: ConfigParser, config_path: str = 'config.ini'):
    with open(config_path, 'w') as f:
        config.write(f)

def load_config_to_dict(config_path: str) -> Dict[str, Any]:
    """Загружает .ini файл и возвращает как словарь"""
    config = ConfigParser()
    config.read(config_path)
    
    result = {}
    for section in config.sections():
        result[section.lower()] = dict(config[section])
    
    return result

def get_db_url(vault_addr, vault_token, vault_secret_path) -> str:
    max_retries = 5
    retry_delay = 3
        
    for attempt in range(max_retries):
        try:
            client = hvac.Client(url=vault_addr, token=vault_token)
            secret = client.secrets.kv.v2.read_secret_version(
                path=vault_secret_path,
                mount_point="secret"
            )
            data = secret['data']['data']
            return f"postgresql://{data['user']}:{data['password']}@{data['host']}:{data['port']}/{data['db']}"
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            sleep(retry_delay)

class Settings(BaseSettings):
    vault_addr: str = "http://vault:8200"
    vault_token: str = "root"
    vault_secret_path: str = "postgres"  # Без префикса secret/data/
    database_url: str = get_db_url(vault_addr, vault_token, vault_secret_path)
    

settings = Settings()