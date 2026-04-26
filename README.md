# AutoVerse AI — Integrated Project

**Agentic AI + Generative AI + DevOps (CI/CD + Docker + Kubernetes)**

## What this project covers

| Course | Feature |
|--------|---------|
| Agentic AI (Course 2) | CrewAI Researcher + Writer agents, Tavily web search, ChromaDB RAG cache |
| Generative AI (Course 3) | Groq LLM generates design narratives + image prompts for custom car concepts |
| DevOps (Course 4) | Docker, GitHub Actions CI/CD, EC2 t3.small deployment, Kubernetes (local minikube) |

## Features

- **Tab 1 — Research a Car**: AI agents fetch live specs, generate a structured Markdown report
- **Tab 2 — Design a Concept**: Enter any concept → AI generates a design narrative + image prompt
- **Tab 3 — Compare Cars**: Two cars researched in parallel, side-by-side spec comparison table

## Local Setup

```bash
git clone <your-repo>
cd autoverse-ai

python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Fill in GROQ_API_KEY and TAVILY_API_KEY

streamlit run streamlit_app.py
```

App runs at http://localhost:8501

## Docker (local)

```bash
docker build -t autoverse-ai .
docker run -p 8501:8501 --env-file .env autoverse-ai
```

## Kubernetes (local minikube)

```bash
# Create secrets
kubectl create secret generic autoverse-secrets \
  --from-literal=GROQ_API_KEY=your_key \
  --from-literal=TAVILY_API_KEY=your_key

# Replace DOCKER_USERNAME in k8s/deployment.yaml, then:
kubectl apply -f k8s/deployment.yaml

minikube service autoverse-ai-service
```

## EC2 Deployment

### Instance setup
- AMI: Ubuntu 22.04 LTS
- Instance type: t3.small (2 vCPU, 2GB RAM)
- Storage: 20GB (expand from default 8GB — still within free tier)
- Security group: open ports 22 (SSH), 8501 (Streamlit), 80 (HTTP)

```bash
# On EC2 instance
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo usermod -aG docker ubuntu
```

### GitHub Secrets required

Go to your repo → Settings → Secrets and variables → Actions:

| Secret | Value |
|--------|-------|
| `DOCKER_USERNAME` | Your Docker Hub username |
| `DOCKER_PASSWORD` | Your Docker Hub password or token |
| `EC2_HOST` | Your EC2 public IP |
| `EC2_USER` | `ubuntu` |
| `EC2_SSH_KEY` | Your EC2 .pem key contents (entire file) |
| `GROQ_API_KEY` | From console.groq.com (free) |
| `TAVILY_API_KEY` | From tavily.com (free tier) |

### CI/CD Pipeline

On every push to `main`:
1. GitHub Actions builds Docker image
2. Pushes to Docker Hub
3. SSHs into EC2
4. Pulls latest image, restarts container

App accessible at: `http://<EC2_PUBLIC_IP>:8501`

## API Keys (free)

- **Groq**: https://console.groq.com — free, fast, no credit card
- **Tavily**: https://tavily.com — free tier (1000 searches/month)
