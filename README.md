# BTS4320-Security-and-privacy-in-cloud-services

### Group 2

Made by Even Unneberg, Sindre Novi, Kristian Thue, Patrik Pastor, Shaila Agatha

### Assignment text:
https://debbie.usn.no/bts4320/#prosjekt

## Security/privacy implementation notes

- `title` and `text` are publicly listable without authentication.
- Public listings expose contributions as `anonymous`.
- Authenticated user listings (`handling=Liste`) show the user's own pseudonym and keep other users anonymous.
- Administrator listings (`handling=AdminListe`) return pseudonyms only when a valid `ADMIN_LIST_KEY` is provided.
- `kommentar` is not included in public or admin listing output. It is intended to be client-side encrypted before storage.
- Database data is persisted on disk using SQLite files under `/var/www/data/`.

## Kubernetes orchestration

A Kubernetes manifest is provided at `v24-25.1/k8s/secure-stack.yaml` with:

- namespace isolation (`bidrag-system`)
- persistent volume claims for both databases
- least-privilege container security contexts
- default deny network policy plus explicit service-to-service allow rules
- secret-based administrator list key (`ADMIN_LIST_KEY`)

Apply with:

`kubectl apply -f v24-25.1/k8s/secure-stack.yaml`