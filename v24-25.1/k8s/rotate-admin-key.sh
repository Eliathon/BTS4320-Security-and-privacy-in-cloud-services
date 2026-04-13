#!/bin/sh
set -eu

NAMESPACE="${1:-bidrag-system}"
SECRET_NAME="${2:-app-secrets}"

if ! command -v kubectl >/dev/null 2>&1; then
    echo "kubectl is required but not installed/in PATH." >&2
    exit 1
fi

if command -v openssl >/dev/null 2>&1; then
    ADMIN_LIST_KEY="$(openssl rand -hex 32)"
elif command -v xxd >/dev/null 2>&1; then
    ADMIN_LIST_KEY="$(head -c 32 /dev/urandom | xxd -p -c 256)"
else
    echo "Need either openssl or xxd to generate a secure random key." >&2
    exit 1
fi

kubectl get namespace "$NAMESPACE" >/dev/null 2>&1 || kubectl create namespace "$NAMESPACE"

kubectl -n "$NAMESPACE" create secret generic "$SECRET_NAME" \
  --from-literal=ADMIN_LIST_KEY="$ADMIN_LIST_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Updated secret '$SECRET_NAME' in namespace '$NAMESPACE'."
echo "Rolling restart app and bidrag-db to pick up new key..."
kubectl -n "$NAMESPACE" rollout restart deployment/app deployment/bidrag-db
kubectl -n "$NAMESPACE" rollout status deployment/app --timeout=120s
kubectl -n "$NAMESPACE" rollout status deployment/bidrag-db --timeout=120s

echo "Done."
