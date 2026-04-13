#!/bin/sh

# Skriver siste del av HTTP-hodet
echo "Content-Type:text/plain;charset=utf-8"
echo

# Avslutter om HTTP-forespørsel ikke er en POST
if [ "$REQUEST_METHOD" != "POST" ]; then exit; fi

# Omgår bug i httpd
CONTENT_LENGTH=$HTTP_CONTENT_LENGTH$CONTENT_LENGTH

# Henter data fra HTTP-kroppen
KROPP=$(head -c "$CONTENT_LENGTH")

# Fikser alfakrøll (intet annet)
KROPP=$(echo "$KROPP" | sed 's/%40/@/g')

# Til loggen
echo "app fikk dette i kroppen: $KROPP" >&2

# Fordeler inndataene i variabler
for I in $(echo "$KROPP" | tr '&' ' '); do
    FELT=$(echo "$I" | cut -f1 -d=)
    VERDI=$(echo "$I" | cut -f2- -d=)

    if [ "$FELT" = "epost"            ]; then E="$VERDI"; fi
    if [ "$FELT" = "passord"          ]; then P="$VERDI"; fi
    if [ "$FELT" = "kommentar"        ]; then K="$VERDI"; fi
    if [ "$FELT" = "offentlig_nokkel" ]; then O="$VERDI"; fi
    if [ "$FELT" = "tittel"           ]; then T="$VERDI"; fi
    if [ "$FELT" = "tekst"            ]; then X="$VERDI"; fi
    if [ "$FELT" = "handling"         ]; then H="$VERDI"; fi
done

# Leser krypteringsnøkkel fra miljøvariabel satt via Kubernetes Secret
MASTER_KEY="${MASTER_KEY:-}"

## 1. HENTER PSEUDONYM ##

XML="<pseudonym>             \
        <epost>$E</epost>    \
       <passord>$P</passord> \
     </pseudonym>"

URL='http://pseudonym-db.pseudonymrom.svc.cluster.local:83/cgi-bin/index.cgi'

# Til loggen
echo "KROPP: $KROPP" >&2
echo "PN-URL: $URL" >&2
echo "PN-XML: $XML" >&2

# Henter pseudonym
PSEUDONYM=$(curl -s -d "$XML" "$URL")

## 2. KONTAKTER BIDRAG-DB ##

# Krypter kommentar ved Ny og Endre
if [ "$H" = "Ny" ] || [ "$H" = "Endre" ]; then
    if [ -n "$K" ] && [ -n "$MASTER_KEY" ]; then
        K=$(printf "%s" "$K" | openssl enc -aes-256-cbc -a -salt -pass env:MASTER_KEY 2>/dev/null)
    fi
fi

XML="<bidrag>\
<navn>$PSEUDONYM</navn>\
<passord>$P</passord>\
<kommentar>$K</kommentar>\
<offentlig_nokkel>$O</offentlig_nokkel>\
<tittel>$T</tittel>\
<tekst>$X</tekst>\
</bidrag>"

URL='http://bidrag-db.bidragsrom.svc.cluster.local:82/cgi-bin/index.cgi'

# Til loggen
echo "BIDRAG-URL: $URL" >&2
echo "BIDRAG-XML: $XML" >&2

# Sender forespørsel til databasen, avhengig av forespurt handling
if [ "$H" = "Slett" ]; then curl -s -X DELETE -d "$XML" "$URL"; fi
if [ "$H" = "Endre" ]; then curl -s -X PUT    -d "$XML" "$URL"; fi
if [ "$H" = "Ny"    ]; then curl -s -X POST   -d "$XML" "$URL"; fi
if [ "$H" = "Liste" ]; then curl -s -X GET              "$URL"; fi