# Local Kubernetes Testing (inventory namespace)

These steps match the current manifests (namespace `inventory`, image `inventory-app:local`). Run from the repo root. Replace `<...>` placeholders in secrets with real values.

## One-time prep
```bash
docker version
kubectl version --client
kind version            # if using Kind
minikube version        # if using Minikube

cp k8s/secrets-template.yaml k8s/secrets.yaml
$EDITOR k8s/secrets.yaml

# If you plan to run the backup CronJob, align the Spaces env names:
# - Either rename DO_SPACES_* keys in k8s/secrets.yaml to SPACES_*,
# - Or change the CronJob env names to DO_SPACES_* before applying.
```

## Option A: Kind
```bash
# 1) Create cluster + namespace
kind create cluster --name inventory-local
kubectl apply -f k8s/namespace.yaml

# 2) Build app image and load into cluster
docker build -t inventory-app:local .
kind load docker-image inventory-app:local --name inventory-local

# 3) Apply manifests
kubectl apply -n inventory -f k8s/configmap.yaml
kubectl apply -n inventory -f k8s/secrets.yaml
kubectl apply -n inventory -f k8s/pvc.yaml
kubectl apply -n inventory -f k8s/postgres-deployment.yaml
kubectl apply -n inventory -f k8s/deployment.yaml
kubectl apply -n inventory -f k8s/cronjob-backup.yaml

# 4) Smoke checks
kubectl get pods -n inventory -w
kubectl logs -n inventory deploy/inventory-deployment --tail=100

# 5) Port-forward to app
kubectl port-forward -n inventory svc/inventory-service 8080:80
# Visit http://localhost:8000

# 6) Optional: migrations
kubectl exec -n inventory deploy/inventory-deployment -- python manage.py migrate

# 7) Tear down
kind delete cluster --name inventory-local
```

## Option B: Minikube
```bash
# 1) Start cluster + namespace
minikube start --driver=docker
kubectl apply -f k8s/namespace.yaml

# 2) Use in-cluster Docker daemon to avoid pushing images
eval $(minikube docker-env)
minikube docker-env | Invoke-Expression // For windows
docker build -t inventory-app:local .

# 3) Apply manifests (no kind load needed)
kubectl apply -n inventory -f k8s/configmap.yaml
kubectl apply -n inventory -f k8s/secrets-template.yaml
kubectl apply -n inventory -f k8s/pvc.yaml
kubectl apply -n inventory -f k8s/postgres-deployment.yaml
kubectl apply -n inventory -f k8s/deployment.yaml
kubectl apply -n inventory -f k8s/cronjob-backup.yaml

# 4) Smoke checks
kubectl get pods -n inventory -w
kubectl logs -n inventory deploy/inventory-deployment --tail=100

# 5) Port-forward
kubectl port-forward -n inventory svc/inventory-service 8000:80

# 6) Optional: migrations
kubectl exec -n inventory deploy/inventory-deployment -- python manage.py migrate

# 7) Tear down
minikube delete
```

## Quick verification checklist
- Pods ready: `kubectl get pods -n inventory`
- Django responsive at http://localhost:8000 after port-forward
- Logs clean: `kubectl logs -n inventory deploy/inventory-deployment`
- DB: migrations run without errors
