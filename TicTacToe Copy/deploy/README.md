# Delivery packaging

## Docker Compose

The Compose stack runs the FastAPI backend on port `8000` and the Vite production build behind Nginx on port `8080`. Nginx proxies `/api/*` to the backend, so the frontend image is portable between local Compose and Kubernetes.

```powershell
docker compose build
docker compose up
```

Open <http://localhost:8080>. Set `OPENAI_API_KEY` in the local ignored `.env` file when testing the runtime agent. The Compose backend exposes the Light Speed MCP endpoint at `/mcp` on port `8000`.

## Kubernetes

The manifests are intentionally local-image oriented and do not provision a cluster, registry, ingress, TLS, or persistent storage. Build the images, make them available to the cluster, then apply the manifest:

```powershell
docker build -f deploy/backend.Dockerfile -t tic-tac-toe-backend:local .
docker build --build-arg VITE_API_URL=/api -f deploy/frontend.Dockerfile -t tic-tac-toe-frontend:local .
kubectl apply -f deploy/k8s.yaml
```

For a local `kind` cluster, load the images before applying:

```powershell
kind load docker-image tic-tac-toe-backend:local tic-tac-toe-frontend:local
```

The optional runtime secret is deliberately not committed:

```powershell
kubectl create secret generic tic-tac-toe-secrets --from-literal=OPENAI_API_KEY="$env:OPENAI_API_KEY"
```

The frontend is exposed through NodePort `30080`. The backend service is internal to the cluster; Nginx proxies browser requests to it.
