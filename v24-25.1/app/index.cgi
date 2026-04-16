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

# Henter data fra HTTP-kroppen
KROPP=$(head -c "$CONTENT_LENGTH")

# Til loggen
echo app fikk dette i kroppen: $KROPP >&2

# URL-dekoder en verdi (%HH -> tegn, + -> mellomrom)
urldecode() {
    printf '%b' "$(echo "$1" | sed 's/+/ /g; s/%\([0-9A-Fa-f][0-9A-Fa-f]\)/\\x\1/g')"
}

# Escaper spesialtegn før de settes inn i XML
xml_escape() {
    printf '%s' "$1" | sed \
        -e 's/&/\&amp;/g' \
        -e 's/</\&lt;/g' \
        -e 's/>/\&gt;/g' \
        -e 's/"/\&quot;/g' \
        -e "s/'/\&apos;/g"
}

# Fordeler inndataene i variabler
for I in $(echo "$KROPP" | tr '&' ' '); do
    N=$(echo "$I" | cut -f1 -d=)
    V=$(urldecode "${I#*=}")

    if [ "$N" = "epost"            ]; then E="$V"; fi
    if [ "$N" = "passord"          ]; then P="$V"; fi
    if [ "$N" = "kommentar"        ]; then K="$V"; fi
    if [ "$N" = "offentlig_nokkel" ]; then O="$V"; fi
    if [ "$N" = "tittel"           ]; then T="$V"; fi
    if [ "$N" = "tekst"            ]; then X="$V"; fi
    if [ "$N" = "handling"         ]; then H="$V"; fi
done

# Enkel e-postvalidering
is_valid_email() {
    echo "$1" | grep -Eq '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'
}

# Lengdesjekk
is_too_long() {
    VAL="$1"
    MAX="$2"
    [ "${#VAL}" -gt "$MAX" ]
}

# Returner feilmelding og stopp
fail() {
    echo "$1"
    exit 0
}

# Valider handling
case "$H" in
    Ny|Endre|Slett|Liste) ;;
    *) fail "Ugyldig handling." ;;
esac

# Valider e-post og passord
[ -z "$E" ] && fail "E-post må fylles ut."
is_valid_email "$E" || fail "E-postadressen er ugyldig."
[ -z "$P" ] && fail "Passord må fylles ut."
[ "${#P}" -lt 3 ] && fail "Passord må være minst 3 tegn."

# Lengdegrenser
is_too_long "$T" 100 && fail "Tittel kan ikke være lengre enn 100 tegn."
is_too_long "$K" 500 && fail "Kommentar kan ikke være lengre enn 500 tegn."
is_too_long "$X" 5000 && fail "Tekst kan ikke være lengre enn 5000 tegn."

# Krav for Ny og Endre
if [ "$H" = "Ny" ] || [ "$H" = "Endre" ]; then
    [ -z "$T" ] && fail "Tittel må fylles ut."
    [ -z "$X" ] && fail "Tekst må fylles ut."
fi

## 1. HENTER PSEUDONYM ##

E_XML=$(xml_escape "$E")
P_XML=$(xml_escape "$P")

XML="<pseudonym>\
<epost>$E_XML</epost>\
<passord>$P_XML</passord>\
</pseudonym>"

URL='pseudonym-pod:83'

cat <<EOF >&2
KROPP: $KROPP
PN-URL: $URL
PN-XML:
$XML
EOF

N=$(curl -s -d "$XML" $URL)

## 2. KONTAKTER BIDRAG-DB ##

N_XML=$(xml_escape "$N")
P_XML=$(xml_escape "$P")
K_XML=$(xml_escape "$K")
O_XML=$(xml_escape "$O")
T_XML=$(xml_escape "$T")
X_XML=$(xml_escape "$X")

XML="<bidrag>\
<navn>$N_XML</navn>\
<passord>$P_XML</passord>\
<kommentar>$K_XML</kommentar>\
<offentlig_nokkel>$O_XML</offentlig_nokkel>\
<tittel>$T_XML</tittel>\
<tekst>$X_XML</tekst>\
</bidrag>"

URL='localhost:82'

# Sender forespørsel til databasen, avhengig av forespurt handling
if [ "$H" = "Slett" ]; then curl -s -X DELETE -d "$XML" $URL; fi
if [ "$H" = "Endre" ]; then curl -s -X PUT    -d "$XML" $URL; fi
if [ "$H" = "Ny"    ]; then curl -s -X POST   -d "$XML" $URL; fi
if [ "$H" = "Liste" ]; then curl -s -X GET              $URL; fi

# Til loggen
cat <<EOF >&2
BIDRAG-URL: $URL
BIDRAG-XML:
$XML
EOF