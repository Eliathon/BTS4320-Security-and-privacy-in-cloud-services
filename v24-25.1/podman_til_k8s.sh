#!/bin/sh
set -eu

# Rydder opp gamle port-forward-prosesser
pkill -f "kubectl port-forward" || true
pkill -f "port-forward" || true

# Rydder bort gammel allpodd-modell hvis den finnes
microk8s kubectl delete service allpodd --ignore-not-found=true
microk8s kubectl delete pod allpodd --ignore-not-found=true

########################################################
# Bygger konteinerbilder i Podmans konteinerbildearkiv #
########################################################

podman build --no-cache pseudonym-db -t pseudonym-db
podman build --no-cache bidrag-db    -t bidrag-db
podman build --no-cache app          -t app
podman build --no-cache web          -t web

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

microk8s kubectl apply -f identitet_og_tilgang/navnerom.yaml
microk8s kubectl apply -f identitet_og_tilgang/roller.yaml
microk8s kubectl apply -f identitet_og_tilgang/rolebindinger.yaml

##################################################################
# Deployer workloads separat                                     #
##################################################################

microk8s kubectl apply -f k8s/app-secret.yaml

# Slett eksisterende pods så de henter nye images
microk8s kubectl delete pod/pseudonym-db -n pseudonymrom --ignore-not-found=true
microk8s kubectl delete pod/bidrag-db    -n bidragsrom   --ignore-not-found=true
microk8s kubectl delete pod/app                          --ignore-not-found=true
microk8s kubectl delete pod/web                          --ignore-not-found=true

microk8s kubectl apply -f k8s/pseudonym-db.yaml
microk8s kubectl apply -f k8s/bidrag-db.yaml
microk8s kubectl apply -f k8s/app.yaml
microk8s kubectl apply -f k8s/web.yaml

##################################################################
# Venter på at pods skal bli klare                               #
##################################################################

microk8s kubectl wait --for=condition=Ready pod/pseudonym-db -n pseudonymrom --timeout=60s
microk8s kubectl wait --for=condition=Ready pod/bidrag-db -n bidragsrom --timeout=60s
microk8s kubectl wait --for=condition=Ready pod/app --timeout=60s
microk8s kubectl wait --for=condition=Ready pod/web --timeout=60s

##################################################################
# Port-forward for lokal testing                                 #
##################################################################

microk8s kubectl port-forward service/web 8080:80 &
microk8s kubectl port-forward service/app 8081:81 &

##################################################################
# Skriver ut info                                                #
##################################################################

echo
echo "Systemet er startet med separate Kubernetes-ressurser."
echo "Web: http://localhost:8080/index.html"
echo "App: http://localhost:8081"
echo
echo "RBAC-namespaces:"
microk8s kubectl get namespaces | grep -E "pseudonymrom|bidragsrom" || true
echo
echo "Pods:"
microk8s kubectl get pods
microk8s kubectl get pods -n pseudonymrom
microk8s kubectl get pods -n bidragsrom