$dsn = "postgresql://twisterlab:postgres@postgres.twisterlab.svc.cluster.local:5432/twisterlab?sslmode=disable"
# Use kubectl to add the key via create --dry-run | apply
kubectl create secret generic postgres-exporter-secret `
  --from-literal=DATA_SOURCE_NAME="$dsn" `
  --namespace=twisterlab `
  --dry-run=client -o yaml | kubectl apply -f -
Write-Host "Done."
