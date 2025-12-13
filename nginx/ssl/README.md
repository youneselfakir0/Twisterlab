# SSL/TLS Placeholder

This directory will contain SSL certificates for production HTTPS.

## Local Development (Self-Signed Certificates)

Generate self-signed certificates:

```powershell
# Generate private key and certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
  -keyout nginx/ssl/key.pem `
  -out nginx/ssl/cert.pem `
  -subj "/C=US/ST=State/L=City/O=TwisterLab/CN=localhost"
```

## Production (Let's Encrypt)

For production, use Let's Encrypt certbot:

```powershell
# Install certbot
choco install certbot

# Generate certificate
certbot certonly --standalone -d yourdomain.com
```

## Kubernetes Deployment

For K8s, use cert-manager with Let's Encrypt:

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: twisterlab-tls
spec:
  secretName: twisterlab-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
    - twisterlab.example.com
```
