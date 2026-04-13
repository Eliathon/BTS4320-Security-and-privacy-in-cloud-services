#!/bin/sh

DB=../data/pseudonym.db
<<<<<<< Updated upstream
=======

sql_escape() {
    echo "$1" | sed "s/'/''/g"
}

init_db() {
    sqlite3 "$DB" "CREATE TABLE IF NOT EXISTS Pseudonym (
      epost VARCHAR(200) PRIMARY KEY,
      pseudonym VARCHAR(200),
      salt VARCHAR(11),
      passordhash VARCHAR(44)
    );"
}

lag_pseudonym() {
    while true; do
        PN=$(tr -dc 'a-z' </dev/urandom | head -c 8)
        [ "${#PN}" -eq 8 ] || continue
        ANTALL=$(sqlite3 "$DB" "SELECT COUNT(*) FROM Pseudonym WHERE pseudonym='$(sql_escape "$PN")'")
        if [ "$ANTALL" = "0" ]; then
            echo "$PN"
            return
        fi
    done
}
>>>>>>> Stashed changes

echo 'Access-Control-Allow-Origin: http://localhost:8080'
echo 'Access-Control-Allow-Credentials: true'
echo 'Access-Control-Allow-Methods: GET,POST,PUT,DELETE'
echo 'Access-Control-Allow-Headers: Content-Type'

echo "Content-Type:text/plain;charset=utf-8"
echo

# Avslutter om HTTP-forespørsel ikke er en POST
if [ "$REQUEST_METHOD" != "POST" ]; then exit; fi

# Omgår bug i httpd
CONTENT_LENGTH=${HTTP_CONTENT_LENGTH:-${CONTENT_LENGTH:-0}}

KR=$(head -c "$CONTENT_LENGTH" )

# Til loggen (kubctl logs pods/allpodd -c pseudonym-db -f)
echo psudonym-db fikk dette i kroppen: $KR >&2 

E=$( echo "$KR" | xmllint --xpath "/pseudonym/epost/text()"   -  2> /dev/null)
P=$( echo "$KR" | xmllint --xpath "/pseudonym/passord/text()" -  2> /dev/null)
H=$( echo "$KR" | xmllint --xpath "/pseudonym/handling/text()" - 2> /dev/null)

E_ESC=$(sql_escape "$E")

init_db


# Henter lagret saltverdi
S=$( sqlite3 "$DB" "SELECT salt FROM Pseudonym WHERE epost='$E_ESC'" )
if [ "$S" = "" ]; then
    if [ "$H" != "Ny" ]; then
        echo "Fant ikke pseudonym for e-post."
        echo "Fant ikke pseudonym for e-post." >&2
        exit
    fi

    PN=$(lag_pseudonym)
    S=$( for I in $(seq 11); do echo -n $(($RANDOM%9)); done )
    H_NY=$( mkpasswd -m sha-256 -S "$S" "$P" | cut -f4 -d$ )
    PN_ESC=$(sql_escape "$PN")

    if ! sqlite3 "$DB" "INSERT INTO Pseudonym (epost, pseudonym, salt, passordhash) VALUES ('$E_ESC','$PN_ESC','$S','$H_NY')"; then
        echo "Kunne ikke lagre pseudonym."
        echo "Kunne ikke lagre pseudonym." >&2
        exit
    fi
fi

# Beregner hashverdi av innsendt passord
H1=$( mkpasswd -m sha-256 -S "$S" "$P" | cut -f4 -d$ )


# Sammenligner med lagret hashverdi
H2=$( sqlite3 "$DB" "SELECT passordhash FROM Pseudonym WHERE epost='$E_ESC'" )
if [ "$H1" != "$H2" ]; then
    echo "Feil passord!"
    echo "Feil passord!" >&2
    exit
fi

# Returnerer pseudonym
<<<<<<< Updated upstream
PN=$(echo "SELECT pseudonym FROM  Pseudonym WHERE epost='$E'" | \
	 sqlite3  ../data/pseudonym.db )
=======
PN=$(echo "SELECT pseudonym FROM Pseudonym WHERE epost='$E_ESC'" | \
	 sqlite3 "$DB" )
>>>>>>> Stashed changes
echo $PN >&2
echo $PN
