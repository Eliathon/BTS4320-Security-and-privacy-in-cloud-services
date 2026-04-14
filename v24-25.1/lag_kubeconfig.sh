#!/bin/sh
#
# Genererer kubeconfig-filer for pod-administratorene.
# Hver admin får sin egen kubeconfig med et token knyttet til
# sin ServiceAccount, og kan bare administrere sin egen pod.
#
# Bruk:  ./lag_kubeconfig.sh
# Krev:  rbac.yaml allerede kjørt (kubectl apply -f rbac.yaml)
#

set -e

KUBE_API=$(microk8s kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')
CA_CERT=$(microk8s kubectl config view --raw --minify -o jsonpath='{.clusters[0].cluster.certificate-authority-data}')

generate_kubeconfig() {
    SA_NAME=$1
    OUTPUT_FILE=$2

    # Opprett et kortlivet token (24 timer) for tjenestekontoen
    TOKEN=$(microk8s kubectl create token "$SA_NAME" --duration=24h)

    cat > "$OUTPUT_FILE" <<EOF
apiVersion: v1
kind: Config
clusters:
- cluster:
    certificate-authority-data: ${CA_CERT}
    server: ${KUBE_API}
  name: microk8s-cluster
contexts:
- context:
    cluster: microk8s-cluster
    namespace: default
    user: ${SA_NAME}
  name: ${SA_NAME}-context
current-context: ${SA_NAME}-context
users:
- name: ${SA_NAME}
  user:
    token: ${TOKEN}
EOF

    echo "Kubeconfig skrevet til: $OUTPUT_FILE"
}

mkdir -p ./admin

generate_kubeconfig pseudonym-admin ./admin/pseudonym-admin.kubeconfig
generate_kubeconfig bidrag-admin    ./admin/bidrag-admin.kubeconfig

echo
echo "Ferdig! Administratorene kan nå bruke:"
echo
echo "  Pseudonym-admin:"
echo "  microk8s kubectl --kubeconfig=\$(pwd)/admin/pseudonym-admin.kubeconfig get pod pseudonym-pod"
echo "  microk8s kubectl --kubeconfig=\$(pwd)/admin/pseudonym-admin.kubeconfig logs pseudonym-pod"
echo "  microk8s kubectl --kubeconfig=\$(pwd)/admin/pseudonym-admin.kubeconfig exec -it pseudonym-pod -- sh"
echo
echo "  Bidrag-admin:"
echo "  microk8s kubectl --kubeconfig=\$(pwd)/admin/bidrag-admin.kubeconfig get pod bidrag-pod"
echo "  microk8s kubectl --kubeconfig=\$(pwd)/admin/bidrag-admin.kubeconfig logs bidrag-pod -c bidrag-db"
echo "  microk8s kubectl --kubeconfig=\$(pwd)/admin/bidrag-admin.kubeconfig exec -it bidrag-pod -c bidrag-db -- sh"
echo
echo "NB: Token varer i 24 timer. Kjør dette skriptet på nytt for nye token."
