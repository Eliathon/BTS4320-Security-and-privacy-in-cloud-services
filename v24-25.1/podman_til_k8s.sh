#!/bin/sh 

# Rydder opp (ved å drepe og fjerne poddene -- om de finnes)
podman pod kill pseudonym-pod 2>/dev/null
podman pod rm   pseudonym-pod 2>/dev/null
podman pod kill bidrag-pod 2>/dev/null
podman pod rm   bidrag-pod 2>/dev/null

pkill -f "kubectl port-forward" || true
pkill -f "port-forward" || true

########################################################
# Bygger konteinerbilder i Podmans konteinerbildearkiv #
# med kommandoer på følgende form:		       #
# 						       #
# podman build <katalog> -t <bildenavn>                #
########################################################

podman build pseudonym-db -t pseudonym-db
podman build bidrag-db    -t bidrag-db
podman build app          -t app
podman build web          -t web


##################################################################
# Overfører bilder fra Podman til Kubernetes	             #
# Referanser:						     #
# - https://docs.podman.io/en/latest/markdown/podman-save.1.html #
# - https://microk8s.io/docs/registry-images		     #
##################################################################

podman save  pseudonym-db:latest | microk8s ctr image import -
podman save  bidrag-db:latest    | microk8s ctr image import -
podman save  app:latest          | microk8s ctr image import -
podman save  web:latest          | microk8s ctr image import -


##########################################################
# Kopierer databasefiler fra kontainerbilder om nødvendig #
##########################################################

sudo mkdir -p /var/www

if [ ! -f /var/www/bidrag.db ] || [ ! -s /var/www/bidrag.db ]; then
  echo "Kopierer bidrag.db fra kontainerbilde til /var/www/"
  podman run --rm localhost/bidrag-db cat /var/www/bidrag.db | sudo tee /var/www/bidrag.db > /dev/null
fi

if [ ! -f /var/www/pseudonym.db ] || [ ! -s /var/www/pseudonym.db ]; then
  echo "Kopierer pseudonym.db fra kontainerbilde til /var/www/"
  podman run --rm localhost/pseudonym-db cat /var/www/pseudonym.db | sudo tee /var/www/pseudonym.db > /dev/null
fi


####################################
# Aktiverer RBAC i microk8s       #
####################################

microk8s enable rbac
microk8s stop
microk8s start
microk8s status --wait-ready

# Fjerner permissive ClusterRoleBindings som gir alle tjenestekontoer full tilgang
echo "Fjerner permissive standard-bindinger..."
for BINDING in $(microk8s kubectl get clusterrolebindings \
  -o jsonpath='{range .items[?(@.roleRef.name=="cluster-admin")]}{.metadata.name}{"\n"}{end}'); do
    SUBJECTS=$(microk8s kubectl get clusterrolebinding "$BINDING" -o jsonpath='{.subjects[*].name}')
    case "$SUBJECTS" in
        *system:serviceaccounts*)
            echo "  Sletter permissiv binding: $BINDING"
            microk8s kubectl delete clusterrolebinding "$BINDING"
            ;;
    esac
done


########################
# Starter opp systemet #
########################

# Stopper kjørende servicer og podder -- om de finnes
kubectl delete service/pseudonym-pod --grace-period=1 2>/dev/null
kubectl delete pod/pseudonym-pod     --grace-period=1 2>/dev/null
kubectl delete service/bidrag-pod   --grace-period=1 2>/dev/null
kubectl delete pod/bidrag-pod       --grace-period=1 2>/dev/null
kubectl delete -f rbac.yaml         --grace-period=1 2>/dev/null
kubectl delete -f network-policies.yaml --grace-period=1 2>/dev/null
kubectl delete secret api-key-secret --grace-period=1 2>/dev/null

# Genererer en tilfeldig API-nøkkel
API_KEY=$(openssl rand -hex 32)
echo "Generert API-nøkkel: $API_KEY"

# Oppretter Kubernetes Secret med API-nøkkelen
kubectl create secret generic api-key-secret --from-literal=service-key="$API_KEY"

# Starter poddene i Kubernetes
kubectl create -f pseudonym-pod.yaml
kubectl create -f bidrag-pod.yaml

# Oppretter RBAC (admin-brukere for hver pod)
kubectl apply -f rbac.yaml

# Bruker NetworkPolicies for å sikre at bare tillatt trafikk er åpnet
kubectl apply -f network-policies.yaml

kubectl wait --for=condition=Ready pod/pseudonym-pod --timeout=60s
kubectl wait --for=condition=Ready pod/bidrag-pod    --timeout=60s

# Genererer kubeconfig-filer for pod-administratorene
chmod +x lag_kubeconfig.sh
./lag_kubeconfig.sh

microk8s kubectl port-forward service/bidrag-pod 8080:80 &
microk8s kubectl port-forward service/bidrag-pod 8081:81 &

####################################################
# Skriver ut info for tilgang på lokal vertsmaskin #
####################################################

echo 
echo
echo "To podder kjører:"
echo "  pseudonym-pod  (pseudonym-db)  admin: pseudonym-admin"
echo "  bidrag-pod     (app, bidrag-db, web)  admin: bidrag-admin"
echo
echo "Kubeconfig-filer for administratorene ligger i ./admin/"
echo
echo "Gjør web (80) og app (81) tilgjengelig på localhost:"
echo 
echo "microk8s kubectl port-forward service/bidrag-pod 8080:80 &"
echo "microk8s kubectl port-forward service/bidrag-pod 8081:81 &"
echo 
echo "For å se i nettleser, gå til http://localhost:8080"
