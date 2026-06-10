
import secrets
import base64

def generate_secret_encoded(length=32):
    return base64.b64encode(secrets.token_hex(length).encode()).decode()

def encode_value(value):
    return base64.b64encode(value.encode()).decode()

secret_key = generate_secret_encoded()
postgres_password = encode_value("postgres") # Use 'postgres' to match existing connection string
redis_password = encode_value("redis_secure_password") 
jwt_secret_key = generate_secret_encoded()
database_url = encode_value(f"postgresql+asyncpg://postgres:postgres@postgres.twisterlab.svc.cluster.local:5432/twisterlab")
grafana_user = encode_value("admin")
grafana_password = encode_value("admin") # Change this for security

yaml_content = f"""apiVersion: v1
kind: Secret
metadata:
  name: twisterlab-secrets
  namespace: twisterlab
type: Opaque
data:
  SECRET_KEY: {secret_key}
  POSTGRES_PASSWORD: {postgres_password}
  REDIS_PASSWORD: {redis_password}
  JWT_SECRET_KEY: {jwt_secret_key}
  DATABASE_URL: {database_url}
  GRAFANA_ADMIN_USER: {grafana_user}
  GRAFANA_ADMIN_PASSWORD: {grafana_password}
"""

print(yaml_content)
