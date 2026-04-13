#!/bin/sh

# Skriver siste del av HTTP-hodet
echo "Content-Type:text/plain;charset=utf-8"
echo

# Avslutter om HTTP-forespørsel ikke er en POST
if [ "$REQUEST_METHOD" != "POST" ]; then exit; fi

# Omgår bug i httpd
CONTENT_LENGTH=$HTTP_CONTENT_LENGTH$CONTENT_LENGTH

# Henter data fra HTTP-krpppen 
KROPP=$(head -c "$CONTENT_LENGTH")

# Fikser alfakrøll (intet annet)
KROPP=$(echo $KROPP|sed "s/%40/@/")

# Til loggen (kubctl logs pods/allpodd -c app -f)
echo app fikk dette i kroppen: $KROPP >&2

  
# Fordeler inndataene i variabler
for I in $(echo $KROPP|tr '&' ' '); do

    N=$(echo "$I"|cut -f1 -d=)
    V=$(echo "$I"|cut -f2 -d=)

    if [ "$N" = "epost"             ]; then  E="$V"; fi  
    if [ "$N" = "passord"           ]; then  P="$V"; fi  
    if [ "$N" = "kommentar"         ]; then  K="$V"; fi
    if [ "$N" = "offentlig_nokkel"  ]; then  O="$V"; fi
    if [ "$N" = "tittel"            ]; then  T="$V"; fi
    if [ "$N" = "tekst"             ]; then  X="$V"; fi
    if [ "$N" = "handling"          ]; then  H="$V"; fi  

done

# Leser krypteringsnøkkel fra miljøvariabel satt via Kubernetes Secret
MASTER_KEY="${MASTER_KEY:-}"

## 1. HENTER PSEUDONYM ##

# Dataene skal sendes i XML-format til pseudonym-databasen
XML="<pseudonym>             \
        <epost>$E</epost>    \
       <passord>$P</passord> \
     </pseudonym>"

# URL til pseudonym-databasen
URL='http://pseudonym-db.pseudonymrom.svc.cluster.local:83/cgi-bin/index.cgi'

# Til loggen
cat <<EOF >&2
KROPP: $KROPP
PN-URL:   $URL
PN-XML:
$XML
EOF

# Henter pseudonym
N=$(curl -s -d "$XML" $URL)

## 2. KONTAKTER BIDRAG-DB ##

# Krypter kommentar ved Ny og Endre
if [ "$H" = "Ny" ] || [ "$H" = "Endre" ]; then
    if [ -n "$K" ] && [ -n "$MASTER_KEY" ]; then
        K=$(printf "%s" "$K" | openssl enc -aes-256-cbc -a -salt -pass env:MASTER_KEY 2>/dev/null)
    fi
fi
# Dataene skal sendes i XML-format til bidrag-databasen
XML="<bidrag>\
<navn>$N</navn>\
<passord>$P</passord>\
<kommentar>$K</kommentar>\
<offentlig_nokkel>$O</offentlig_nokkel>\
<tittel>$T</tittel>\
<tekst>$X</tekst>\
</bidrag>"

# URL til bidrag-databasen
URL='http://bidrag-db.bidragsrom.svc.cluster.local:82/cgi-bin/index.cgi'


 # Til loggen
 cat <<EOF >&2
 BIDRAG-URL:   $URL
 BIDRAG-XML:
 $XML
 EOF

# Sender forespørsel til databasen, avhengig av forespurt handling
if [ "$H" = "Slett" ]; then curl -s -X DELETE -d "$XML" "$URL"; fi
if [ "$H" = "Endre" ]; then curl -s -X PUT    -d "$XML" "$URL"; fi
if [ "$H" = "Ny"    ]; then curl -s -X POST   -d "$XML" "$URL"; fi
if [ "$H" = "Liste" ]; then curl -s -X GET              "$URL"; fi

