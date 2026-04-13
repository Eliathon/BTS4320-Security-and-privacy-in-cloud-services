#!/bin/sh

# Skriver siste del av HTTP-hodet
echo "Content-Type:text/plain;charset=utf-8"
echo

# Avslutter om HTTP-forespørsel ikke er en POST
if [ "$REQUEST_METHOD" != "POST" ]; then exit; fi

urldecode() {
    printf '%b' "$(echo "$1" | sed 's/+/ /g;s/%/\\x/g')"
}

<<<<<<< Updated upstream
=======
xml_escape() {
    echo "$1" | sed -e 's/&/\&amp;/g' \
                   -e 's/</\&lt;/g' \
                   -e 's/>/\&gt;/g' \
                   -e "s/'/\&apos;/g" \
                   -e 's/"/\&quot;/g'
}

>>>>>>> Stashed changes
# Omgår bug i httpd
CONTENT_LENGTH=${HTTP_CONTENT_LENGTH:-${CONTENT_LENGTH:-0}}

# Henter data fra HTTP-krpppen 
KROPP=$(head -c "$CONTENT_LENGTH")

# Fikser alfakrøll (intet annet)
KROPP=$(echo $KROPP|sed "s/%40/@/")

# Til loggen (kubctl logs pods/allpodd -c app -f)
echo app fikk dette i kroppen: $KROPP >&2

# Fordeler inndataene i variabler
for I in $(echo $KROPP|tr '&' ' '); do

    N=$(echo "$I"|cut -f1 -d=)
    V=$(echo "$I"|cut -f2- -d=)
    V=$(urldecode "$V")

    if [ "$N" = "epost"             ]; then  E="$V"; fi  
    if [ "$N" = "passord"           ]; then  P="$V"; fi  
    if [ "$N" = "kommentar"         ]; then  K="$V"; fi
    if [ "$N" = "offentlig_nokkel"  ]; then  O="$V"; fi
    if [ "$N" = "tittel"            ]; then  T="$V"; fi
    if [ "$N" = "tekst"             ]; then  X="$V"; fi
    if [ "$N" = "handling"          ]; then  H="$V"; fi  
    if [ "$N" = "admin_token"       ]; then  A="$V"; fi

done

<<<<<<< Updated upstream
=======
# Escape XML-sensitive tegn i brukerinput før videresending.
E_XML=$(xml_escape "$E")
P_XML=$(xml_escape "$P")
K_XML=$(xml_escape "$K")
O_XML=$(xml_escape "$O")
T_XML=$(xml_escape "$T")
X_XML=$(xml_escape "$X")
H_XML=$(xml_escape "$H")

>>>>>>> Stashed changes
if [ "$H" = "Liste" -a "$E" = "" -a "$P" = "" ]; then
    curl -s -X GET bidrag-db:82
    exit
fi

if [ "$H" = "AdminListe" ]; then
    if [ "$ADMIN_LIST_KEY" = "" -o "$A" != "$ADMIN_LIST_KEY" ]; then
        echo "Mangler gyldig administrator-nokkel"
        exit
    fi
    curl -s -X GET "bidrag-db:82?visning=admin&admin_nokkel=$A"
    exit
fi

## 1. HENTER PSEUDONYM ##

# Dataene skal sendes i XML-format til pseudonym-databasen
XML="<pseudonym>             \
        <epost>$E_XML</epost>    \
       <passord>$P_XML</passord> \
      <handling>$H_XML</handling> \
     </pseudonym>"

<<<<<<< Updated upstream
# URL til pseudonym-databasen
URL='pseudonym-db:83' 
=======
# URL til pseudonym-databasen (samme pod => localhost)
URL='localhost:83/cgi-bin/index.cgi' 
>>>>>>> Stashed changes

# Til loggen (kubctl logs pods/app-[...])
cat <<EOF >&2
KROPP: $KROPP
PN-URL:   $URL
PN-XML:
$XML
EOF


# Henter pseudonym
PN_RESP=$(curl -sS -d "$XML" "$URL" 2>&1)
PN_STATUS=$?
if [ "$PN_STATUS" -ne 0 ]; then
    echo "Feil ved kontakt med pseudonym-db: $PN_RESP"
    exit
fi
N=$(echo "$PN_RESP" | tr -d '\r\n')

# Stopper tidlig med tydelig feil hvis pseudonymoppslag feiler.
if [ "$N" = "" ]; then
    echo "Fant ikke pseudonym. Sjekk e-post og passord. Svar fra pseudonym-db: $PN_RESP"
    exit
fi


## 1. KONTAKTER BIDRAG-DB ##

# Dataene skal sendes i XML-format til bidrag-databasen
XML="<bidrag>\
<navn>$N</navn>\
<passord>$P_XML</passord>\
<kommentar>$K_XML</kommentar>\
<offentlig_nokkel>$O_XML</offentlig_nokkel>\
<tittel>$T_XML</tittel>\
<tekst>$X_XML</tekst>\
</bidrag>"

<<<<<<< Updated upstream
# URL til bidrag-databasen
URL='bidrag-db:82' 
=======
# URL til bidrag-databasen (samme pod => localhost)
URL='localhost:82/cgi-bin/index.cgi' 
>>>>>>> Stashed changes

 
# Sender forespørsel til databasen, avhengig av forespurt handling
if [ "$H" = "Slett"   ]; then curl -s -X DELETE -d "$XML" $URL; fi
if [ "$H" = "Endre"   ]; then curl -s -X PUT    -d "$XML" $URL; fi
if [ "$H" = "Ny"      ]; then curl -s -X POST   -d "$XML" $URL; fi
if [ "$H" = "Liste"   ]; then curl -s -X GET "$URL?visning=bruker&viser=$N"; fi
if [ "$H" = "MinSide" ]; then curl -s -X GET "$URL?visning=min&viser=$N"; fi


# Til loggen (kubctl logs pods/app-[...])
cat <<EOF >&2
BIDRAG-URL:   $URL
BIDRAG-XML:
$XML
EOF
