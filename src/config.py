from configparser import ConfigParser
from pathlib import Path
from typing import Dict, Any
from pydantic_settings import BaseSettings
import hvac
import os

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

def get_kafka_brokers(self):
    secret = self.get_vault_secret("kafka")
    return secret['data']['data']['bootstrap_servers']

def get_kafka_username(self):
    secret = self.get_vault_secret("kafka")
    return secret['data']['data']['username']

def get_kafka_password(self):
    secret = self.get_vault_secret("kafka")
    return secret['data']['data']['password']

class Settings(BaseSettings):
    vault_addr: str = "http://vault:8200"
    vault_token: str = "root"
    vault_secret_path: str = "secret/data/postgres"

    def get_db_url(self) -> str:
        client = hvac.Client(url=self.vault_addr, token=self.vault_token)
        secret = client.secrets.kv.v2.read_secret_version(
            path=self.vault_secret_path.replace("secret/data/", "postgres")
        )
        data = secret['data']['data']
        return f"postgresql://{data['user']}:{data['password']}@db:5432/{data['db']}"

settings = Settings()