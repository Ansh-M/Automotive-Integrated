# AutoVerse AI — Minikube Deployment

## Prerequisites
- [Minikube](https://minikube.sigs.k8s.io/) installed and running
- `kubectl` configured to talk to Minikube
- Docker available locally

---

## 1. Start Minikube

```bash
minikube start --memory=2048 --cpus=2
```

---

## 2. Build the image inside Minikube's Docker daemon

This avoids pushing to DockerHub for local development.

```bash
# Point your shell's Docker CLI at Minikube's daemon
eval $(minikube docker-env)

# Build the image (from project root)
docker build -t anshmundra/autoverse-ai:latest .

# Verify it's visible to Minikube
docker images | grep autoverse-ai
```

> **Note:** `imagePullPolicy: IfNotPresent` in the Deployment means Kubernetes
> will use the locally built image instead of trying to pull from DockerHub.

---

## 3. Create the Secrets

Never store real API keys in `secret.yaml`. Create the secret directly:

```bash
kubectl create secret generic autoverse-secrets \
  --namespace autoverse-ai \
  --from-literal=GROQ_API_KEY=<your_groq_api_key> \
  --from-literal=TAVILY_API_KEY=<your_tavily_api_key>
```

---

## 4. Apply all manifests

```bash
kubectl apply -k k8s/
```

Or apply individually:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

---

## 5. Wait for the pod to be ready

The first startup takes ~2–3 minutes because the ONNX embedding model
is downloaded into the persistent cache volume.

```bash
kubectl rollout status deployment/autoverse-ai -n autoverse-ai
# or watch live:
kubectl get pods -n autoverse-ai -w
```

---

## 6. Open in browser

```bash
minikube service autoverse-ai-service -n autoverse-ai
```

This prints the correct tunnel URL and opens your browser automatically.
The fixed nodePort is `30501`, so you can also visit:

```
http://$(minikube ip):30501
```

---

## Useful commands

```bash
# Logs
kubectl logs -f deployment/autoverse-ai -n autoverse-ai

# Shell into the running pod
kubectl exec -it deployment/autoverse-ai -n autoverse-ai -- /bin/bash

# Check PVC status
kubectl get pvc -n autoverse-ai

# Restart the pod (e.g. after a new image build)
kubectl rollout restart deployment/autoverse-ai -n autoverse-ai

# Tear everything down
kubectl delete -k k8s/

# Stop Minikube
minikube stop
```

---

## Updating the image

```bash
eval $(minikube docker-env)
docker build -t anshmundra/autoverse-ai:latest .
kubectl rollout restart deployment/autoverse-ai -n autoverse-ai
```

---

## Persistent data

| Volume | Mount in container | Purpose |
|---|---|---|
| `autoverse-chroma-pvc` | `/app/.chroma` | ChromaDB vector store |
| `autoverse-onnx-pvc` | `/app/.chroma_cache` | ONNX embedding model cache |

Both PVCs survive pod restarts. To wipe them:

```bash
kubectl delete pvc autoverse-chroma-pvc autoverse-onnx-pvc -n autoverse-ai
```
