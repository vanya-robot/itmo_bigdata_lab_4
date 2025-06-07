#!/bin/sh

# Запуск Vault в фоновом режиме
vault server -dev -dev-root-token-id root > /vault/logs/vault.log 2>&1 &

export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN=root

vault secrets enable -path=secret kv-v2
vault kv put secret/postgres \
  user=${POSTGRES_USER:-penguin_user} \
  password=${POSTGRES_PASSWORD:-123321} \
  db=${POSTGRES_DB:-penguin_db} \
  port=${POSTGRES_PORT:-5432} \
  host=${POSTGRES_HOST:-db}

echo "Vault initialization complete!"
tail -f /vault/logs/vault.log  # Чтобы контейнер не завершался