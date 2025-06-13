from configparser import ConfigParser
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings
import hvac
import os
from time import sleep
import logging

logger = logging.getLogger(__name__)

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

def get_vault_secrets(vault_addr: str, vault_token: str, path: str) -> dict:
    max_retries = 5
    retry_delay = 3
        
    for attempt in range(max_retries):
        try:
            client = hvac.Client(url=vault_addr, token=vault_token)
            secret = client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point="secret"
            )
            return secret['data']['data']
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            sleep(retry_delay)

class Settings(BaseSettings):
    vault_addr: str = "http://vault:8200"
    vault_token: str = "root"
    vault_db_secret_path: str = "postgres"
    vault_kafka_secret_path: str = "kafka"
    
    # Параметры БД
    database_url: Optional[str] = None
    
    # Параметры Kafka
    kafka_bootstrap_servers: Optional[str] = None
    kafka_username: Optional[str] = None
    kafka_password: Optional[str] = None
    kafka_security_protocol: Optional[str] = None
    kafka_sasl_mechanism: str = "PLAIN"
    kafka_topic: str = "predictions"
    
    def __init__(self, **data):
        super().__init__(**data)
        
        # Загружаем секреты БД
        if not self.database_url:
            db_secrets = get_vault_secrets(
                self.vault_addr,
                self.vault_token,
                self.vault_db_secret_path
            )
            self.database_url = (
                f"postgresql://{db_secrets['user']}:{db_secrets['password']}"
                f"@{db_secrets['host']}:{db_secrets['port']}/{db_secrets['db']}"
            )
        
        # Загружаем секреты Kafka
        kafka_secrets = get_vault_secrets(
            self.vault_addr,
            self.vault_token,
            self.vault_kafka_secret_path
        )
        self.kafka_bootstrap_servers = kafka_secrets.get('bootstrap_servers')

settings = Settings()