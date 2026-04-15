#!/bin/sh

# Skriver HTTP-hoder (inkl. CORS for fetch fra web-klienten)
echo "Access-Control-Allow-Origin: http://localhost:8080"
echo "Access-Control-Allow-Credentials: true"
echo "Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS"
echo "Access-Control-Allow-Headers: Content-Type"
echo "Content-Type:text/plain;charset=utf-8"
echo

# Tillater preflight
if [ "$REQUEST_METHOD" = "OPTIONS" ]; then exit; fi

# Avslutter om HTTP-forespørsel ikke er en POST
if [ "$REQUEST_METHOD" != "POST" ]; then exit; fi

# Omgår bug i httpd
CONTENT_LENGTH=$HTTP_CONTENT_LENGTH$CONTENT_LENGTH

# Henter data fra HTTP-krpppen 
KROPP=$(head -c "$CONTENT_LENGTH")

# Til loggen (kubctl logs pods -c app -f)
echo app fikk dette i kroppen: $KROPP >&2

# URL-dekoder en verdi (%HH -> tegn, + -> mellomrom)
urldecode() {
    printf '%b' "$(echo "$1" | sed 's/+/ /g; s/%\([0-9A-Fa-f][0-9A-Fa-f]\)/\\x\1/g')"
}

# Fordeler inndataene i variabler
for I in $(echo $KROPP|tr '&' ' '); do

    N=$(echo "$I"|cut -f1 -d=)
    V=$(urldecode "${I#*=}")

    if [ "$N" = "epost"             ]; then  E="$V"; fi  
    if [ "$N" = "passord"           ]; then  P="$V"; fi  
    if [ "$N" = "kommentar"         ]; then  K="$V"; fi
    if [ "$N" = "tittel"            ]; then  T="$V"; fi
    if [ "$N" = "tekst"             ]; then  X="$V"; fi
    if [ "$N" = "handling"          ]; then  H="$V"; fi  

done

## 1. HENTER PSEUDONYM ##

# Dataene skal sendes i XML-format til pseudonym-databasen
XML="<pseudonym>             \
        <epost>$E</epost>    \
       <passord>$P</passord> \
     </pseudonym>"

# URL til pseudonym-databasen (egen pod, nådd via k8s-tjeneste)
URL='pseudonym-pod:83'

# Til loggen (kubctl logs pods/app-[...])
cat <<EOF >&2
KROPP: $KROPP
PN-URL:   $URL
PN-XML:
$XML
EOF


# Henter pseudonym
N=$(curl -s -d "$XML" $URL)


## 1. KONTAKTER BIDRAG-DB ##

# Dataene skal sendes i XML-format til bidrag-databasen
XML="<bidrag>\
<navn>$N</navn>\
<passord>$P</passord>\
<kommentar>$K</kommentar>\
<tittel>$T</tittel>\
<tekst>$X</tekst>\
</bidrag>"

# URL til bidrag-databasen (samme pod, nådd via localhost)
URL='localhost:82' 

 
# Sender forespørsel til databasen, avhengig av forespurt handling
if [ "$H" = "Slett" ]; then curl -s -X DELETE -d "$XML" $URL; fi     
if [ "$H" = "Endre" ]; then curl -s -X PUT    -d "$XML" $URL; fi
if [ "$H" = "Ny"    ]; then curl -s -X POST   -d "$XML" $URL; fi
if [ "$H" = "Liste" ]; then curl -s -X GET              $URL; fi


# Til loggen (kubctl logs pods/app-[...])
cat <<EOF >&2
BIDRAG-URL:   $URL
BIDRAG-XML:
$XML
EOF
