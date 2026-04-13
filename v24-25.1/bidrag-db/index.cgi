#!/bin/sh

DB=../data/bidrag.db
<<<<<<< Updated upstream

sql_escape() {
    echo "$1" | sed "s/'/''/g"
}
=======
>>>>>>> Stashed changes

# Skriver slutten av HTTP-hodet og en tom linje
cat <<EOF
Access-Control-Allow-Origin: http://localhost:8080
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET,POST,PUT,DELETE
Access-Control-Allow-Headers: Content-Type
Content-Type:text/plain;charset=utf-8

EOF


# Omgår bug i httpd
CONTENT_LENGTH=${HTTP_CONTENT_LENGTH:-${CONTENT_LENGTH:-0}}

if [ "$REQUEST_METHOD" = "GET" ]; then
    for I in $(echo "$QUERY_STRING" | tr '&' ' '); do
        N=$(echo "$I" | cut -f1 -d=)
        V=$(echo "$I" | cut -f2- -d= | sed 's/+/ /g;s/%/\\x/g')
        V=$(printf '%b' "$V")
        if [ "$N" = "visning"       ]; then VISNING="$V"; fi
        if [ "$N" = "viser"         ]; then VISER="$V"; fi
        if [ "$N" = "admin_nokkel"  ]; then ADMIN_NOKKEL="$V"; fi
    done

    VISER_ESC=$(sql_escape "$VISER")

    if [ "$VISNING" = "admin" ] && [ "$ADMIN_LIST_KEY" != "" ] && [ "$ADMIN_NOKKEL" = "$ADMIN_LIST_KEY" ]; then
        sqlite3 -line $DB "SELECT pseudonym AS visning, tittel, tekst FROM Bidrag"
        exit
    fi

    if [ "$VISNING" = "bruker" ] && [ "$VISER_ESC" != "" ]; then
        sqlite3 -line $DB "SELECT CASE WHEN pseudonym='$VISER_ESC' THEN pseudonym ELSE 'anonymous' END AS visning, tittel, tekst FROM Bidrag"
        exit
    fi

    if [ "$VISNING" = "min" ] && [ "$VISER_ESC" != "" ]; then
        sqlite3 -line $DB "SELECT pseudonym AS visning, tittel, tekst, kommentar FROM Bidrag WHERE pseudonym='$VISER_ESC'"
        exit
    fi

    sqlite3 -line $DB "SELECT 'anonymous' AS visning, tittel, tekst FROM Bidrag"
    exit

elif [ "$REQUEST_METHOD" = "OPTIONS" ]; then
    exit

else
    KR=$(head -c "$CONTENT_LENGTH" )

    # Til loggen (kubctl logs pods/allpodd -c bidrag-db -f)
    echo bidrag-db fikk dette i kroppen: $KR >&2

    N=$( echo "$KR" | xmllint --xpath "/bidrag/navn/text()"             - 2>/dev/null)
    P=$( echo "$KR" | xmllint --xpath "/bidrag/passord/text()"          - 2>/dev/null)
    K=$( echo "$KR" | xmllint --xpath "/bidrag/kommentar/text()"        - 2>/dev/null)
    O=$( echo "$KR" | xmllint --xpath "/bidrag/offentlig_nokkel/text()" - 2>/dev/null)
    T=$( echo "$KR" | xmllint --xpath "/bidrag/tittel/text()"           - 2>/dev/null)
    X=$( echo "$KR" | xmllint --xpath "/bidrag/tekst/text()"            - 2>/dev/null)

fi

if [ "$N" = "" ]; then echo Pseudonym mangler!; exit; fi

if [ "$REQUEST_METHOD" = "POST" ]; then

    if [ "$N" != ""  -a  "$P" != "" ]; then

	# Lager et tilfeldig 11-sifret tall som salt
	S=$( for I in $(seq 11);do echo -n $(($RANDOM%9));done )

	# Lager en hashverdi av det skapte saltet og det innsendte passordet
	H=$( mkpasswd -m sha-256 -S $S $P | cut -f4 -d$ )

	# Setter inn ny post i databasen
<<<<<<< Updated upstream
        N_ESC=$(sql_escape "$N")
        K_ESC=$(sql_escape "$K")
        O_ESC=$(sql_escape "$O")
        T_ESC=$(sql_escape "$T")
        X_ESC=$(sql_escape "$X")
        sqlite3 $DB "INSERT INTO Bidrag VALUES ('$N_ESC','$S','$H','$K_ESC','$O_ESC','$T_ESC','$X_ESC')"
=======
        if sqlite3 $DB "INSERT OR REPLACE INTO Bidrag VALUES ('$N','$S','$H','$K','$O','$T','$X')"; then
            echo "Bidrag lagret."
        else
            echo "Kunne ikke lagre bidrag."
        fi
>>>>>>> Stashed changes

    else
        echo "Mangler pseudonym eller passord."
    fi
    exit
fi

# Henter lagret saltverdi
N_ESC=$(sql_escape "$N")
K_ESC=$(sql_escape "$K")
O_ESC=$(sql_escape "$O")
T_ESC=$(sql_escape "$T")
X_ESC=$(sql_escape "$X")
S=$( sqlite3 $DB "SELECT salt FROM Bidrag WHERE pseudonym='$N_ESC'" )
if [ "$S" = "" ]; then echo Salt mangler ; exit; fi

# Beregner hashverdi av innsendt passord
H1=$( mkpasswd -m sha-256 -S $S $P | cut -f4 -d$ )

# Sammenligner med lagret hashverdi
H2=$( sqlite3 $DB "SELECT passordhash FROM Bidrag WHERE pseudonym='$N_ESC'" )

# Avslutter om hashverdiene ikke er like 
if [ "$H1" != "$H2" ]; then echo Feil passord! >&2 ; exit; fi


if [ "$REQUEST_METHOD" = "DELETE" ]; then
    if [ "$N" != "" ]; then
<<<<<<< Updated upstream
	sqlite3 $DB "DELETE FROM Bidrag WHERE pseudonym='$N_ESC'"
=======
	if sqlite3 $DB "DELETE FROM Bidrag WHERE pseudonym='$N'"; then
            echo "Bidrag slettet."
        else
            echo "Kunne ikke slette bidrag."
        fi
>>>>>>> Stashed changes
    fi

elif [ "$REQUEST_METHOD" = "PUT" ]; then
    if sqlite3 $DB                \
       "UPDATE Bidrag SET      \
<<<<<<< Updated upstream
    	kommentar='$K_ESC',        \
    	offentlig_nokkel='$O_ESC', \
	tittel='$T_ESC',           \
        tekst='$X_ESC'             \
        WHERE pseudonym='$N_ESC'"
=======
    	kommentar='$K',        \
    	offentlig_nokkel='$O', \
	tittel='$T',           \
        tekst='$X'             \
        WHERE pseudonym='$N'"; then
        echo "Bidrag oppdatert."
    else
        echo "Kunne ikke oppdatere bidrag."
    fi
>>>>>>> Stashed changes
fi
