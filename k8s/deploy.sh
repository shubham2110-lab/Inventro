#!/bin/bash

echo "Starting deployment..."

kubectl apply -f namespace.yaml

echo "Applying secrets and configs..."
kubectl apply -f config
kubectl apply -f secrets/django-secret.yaml
kubectl apply -f secrets/docker-reg.yaml
kubectl apply -f secrets/postgres-secret.yaml
kubectl apply -f secrets/secret.yaml

echo "Applying services, and postgres deployment..."
kubectl apply -f services
kubectl apply -f deployments/postgres-deployment.yaml

echo "Applying HPA and claim..."
kubectl apply -f hpa.yaml
kubectl apply -f claim.yaml

sleep 30
while [[ $(kubectl -n inventro get svc inventro-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}') == "" ]]; do
    echo "Waiting for service IP initialization..."
    sleep 15
done
echo "Service IP initialized."

ip=$(kubectl -n inventro get svc inventro-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')


kubectl -n inventro create secret generic inventro-url-secret --from-literal=CSRF_TRUSTED_ORIGIN="http://$ip" --from-literal=ALLOWED_HOST="$ip"

echo "Starting web deployments..."
kubectl apply -f deployments/web-deployment.yaml

while [[ $(kubectl -n inventro get pods -l app=inventro-web -o jsonpath='{.items[0].status.phase}') != "Running" ]]; do
    echo "Waiting for web pod readiness..."
    sleep 30
done

sleep 20
echo "Deployment complete. Access the application at http://$ip"

