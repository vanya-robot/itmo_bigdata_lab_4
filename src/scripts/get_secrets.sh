#!/bin/bash

# Ждем, пока Vault станет доступен
until curl -s http://vault:8200/v1/sys/health | grep -q '"initialized":true'; do
  echo "Waiting for Vault..."
  sleep 1
done

# Получаем секреты из Vault
export POSTGRES_USER=$(curl -s -H "X-Vault-Token: $VAULT_TOKEN" $VAULT_ADDR/v1/secret/data/postgres | jq -r '.data.data.user')
export POSTGRES_PASSWORD=$(curl -s -H "X-Vault-Token: $VAULT_TOKEN" $VAULT_ADDR/v1/secret/data/postgres | jq -r '.data.data.password')
export POSTGRES_DB=$(curl -s -H "X-Vault-Token: $VAULT_TOKEN" $VAULT_ADDR/v1/secret/data/postgres | jq -r '.data.data.db')
export POSTGRES_HOST=$(curl -s -H "X-Vault-Token: $VAULT_TOKEN" $VAULT_ADDR/v1/secret/data/postgres | jq -r '.data.data.host')
export POSTGRES_PORT=$(curl -s -H "X-Vault-Token: $VAULT_TOKEN" $VAULT_ADDR/v1/secret/data/postgres | jq -r '.data.data.port')

# Экспортируем переменные в текущую сессию
echo "Using secrets from Vault:"
echo "POSTGRES_USER=$POSTGRES_USER"