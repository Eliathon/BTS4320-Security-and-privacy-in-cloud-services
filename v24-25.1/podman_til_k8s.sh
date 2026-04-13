#!/bin/sh
set -eu

# Rydder opp (ved å drepe og fjerne podden -- om den finnes)
podman pod kill allpodd || true
podman pod rm   allpodd || true

pkill -f "kubectl port-forward" || true
pkill -f "port-forward" || true

########################################################
# Bygger konteinerbilder i Podmans konteinerbildearkiv #
########################################################

podman build pseudonym-db -t pseudonym-db
podman build bidrag-db    -t bidrag-db
podman build app          -t app
podman build web          -t web

##################################################################
# Overfører bilder fra Podman til Kubernetes                     #
##################################################################

podman save pseudonym-db:latest | microk8s ctr image import -
podman save bidrag-db:latest    | microk8s ctr image import -
podman save app:latest          | microk8s ctr image import -
podman save web:latest          | microk8s ctr image import -

##################################################################
# RBAC: aktiverer RBAC og oppretter namespaces/roller/bindinger  #
##################################################################

microk8s enable rbac || true

kubectl apply -f identitet_og_tilgang/navnerom.yaml
kubectl apply -f identitet_og_tilgang/roller.yaml
kubectl apply -f identitet_og_tilgang/rolebindinger.yaml

echo "RBAC-ressurser opprettet:"
kubectl get namespaces | grep -E "pseudonymrom|bidragsrom" || true
kubectl get roles -n pseudonymrom || true
kubectl get roles -n bidragsrom || true
kubectl get rolebindings -n pseudonymrom || true
kubectl get rolebindings -n bidragsrom || true

##########################################################
# Lager og redigerer filen allpodd.yaml som brukes til å #
# iverksette systemet i Kubernetes (microk8s)            #
##########################################################

podman pod create --name allpodd -p 8080:80 -p 8081:81

mkdir -p ./data

if [ ! -f ./data/bidrag.db ] || [ ! -s ./data/bidrag.db ]; then
  echo "Copying from bidrag.db image"
  podman run --rm localhost/bidrag-db cat /var/www/bidrag.db > ./data/bidrag.db
fi

if [ ! -f ./data/pseudonym.db ] || [ ! -s ./data/pseudonym.db ]; then
  echo "Copying from pseudonym.db image"
  podman run --rm localhost/pseudonym-db cat /var/www/pseudonym.db > ./data/pseudonym.db
fi

podman run -dit --pod=allpodd --restart=always --name app \
  localhost/app

podman run -dit --pod=allpodd --restart=always --name bidrag-db \
  -v "$(pwd)/data/bidrag.db:/var/www/bidrag.db" \
  localhost/bidrag-db

podman run -dit --pod=allpodd --restart=always --name pseudonym-db \
  -v "$(pwd)/data/pseudonym.db:/var/www/pseudonym.db" \
  localhost/pseudonym-db

podman run -dit --pod=allpodd --restart=always --name web \
  localhost/web

rm -f ./allpodd.yaml
podman generate kube allpodd --service -f ./allpodd.yaml

sed -i "/image:/a \\    imagePullPolicy: Never" allpodd.yaml
sed -i '/bidrag\.db/s/name: [^ ]*/name: bidrag-db-vol/' allpodd.yaml
sed -i '/pseudonym\.db/s/name: [^ ]*/name: pseudonym-db-vol/' allpodd.yaml

podman pod kill allpodd || true
podman pod rm   allpodd || true

########################
# Starter opp systemet #
########################

kubectl delete service/allpodd --grace-period=1 --ignore-not-found=true
kubectl delete pod/allpodd     --grace-period=1 --ignore-not-found=true

kubectl create -f allpodd.yaml
kubectl wait --for=condition=Ready pod/allpodd --timeout=60s

microk8s kubectl port-forward service/allpodd 8080:80 &
microk8s kubectl port-forward service/allpodd 8081:81 &

echo
echo "Gjør web (80) og app (81) tilgjengelig på localhost:"
echo "microk8s kubectl port-forward service/allpodd 8080:80 &"
echo "microk8s kubectl port-forward service/allpodd 8081:81 &"
echo "For å se i nettleser, gå til http://localhost:8080"