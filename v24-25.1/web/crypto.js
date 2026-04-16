async function deriveKey(password, salt) {
    const enc = new TextEncoder();
    const keyMaterial = await window.crypto.subtle.importKey(
        "raw", enc.encode(password), "PBKDF2", false, ["deriveKey"]
    );
    return crypto.subtle.deriveKey(
        {name: "PBKDF2", salt: enc.encode(salt), iterations: 100000, hash: "SHA-256"},
        keyMaterial,
        {name: "AES-GCM", length: 256},
        false,
        ["encrypt", "decrypt"]
    );
}

async function encrypt(plaintext, password, salt) {
    const key = await deriveKey(password, salt);
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const enc = new TextEncoder();
    const ciphertext = await crypto.subtle.encrypt(
        {name: "AES-GCM", iv},
        key,
        enc.encode(plaintext)
    );
    const combined = new Uint8Array(iv.byteLength + ciphertext.byteLength);
    combined.set(iv, 0);
    combined.set(new Uint8Array(ciphertext), iv.byteLength);
    return btoa(String.fromCharCode(...combined));
}

async function decrypt(base64, password, salt) {
    const combined = Uint8Array.from(atob(base64), c => c.charCodeAt(0));
    const iv = combined.slice(0, 12);
    const ciphertext = combined.slice(12);
    const key = await deriveKey(password, salt);
    const plaintext = await crypto.subtle.decrypt({name: "AES-GCM", iv}, key, ciphertext);
    return new TextDecoder().decode(plaintext);
}

function setListResult(text) {
    document.getElementById("listeResultat").textContent = text;
}

async function decryptKommentarLinjer(rawText, passord, epost) {
    const lines = rawText.split("\n");
    const decryptedLines = [];

    for (const line of lines) {
        if (!line.includes("kommentar =")) {
            decryptedLines.push(line);
            continue;
        }

        const encrypted = line.split("=").slice(1).join("=").trim();
        if (!encrypted) {
            continue;
        }

        try {
            const decrypted = await decrypt(encrypted, passord, epost);
            decryptedLines.push(`    kommentar = ${decrypted}`);
        } catch (error) {
            // Not our post — hide kommentar
        }
    }

    return decryptedLines.join("\n");
}

function isValidEmail(epost) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(epost);
}

function validateInput({ handling, epost, passord, tittel, kommentar, tekst }) {
    const gyldigeHandlinger = ["Ny", "Endre", "Slett", "Liste"];

    if (!gyldigeHandlinger.includes(handling)) {
        return "Ugyldig handling.";
    }

    if (!epost.trim()) {
        return "E-post må fylles ut.";
    }

    if (!isValidEmail(epost.trim())) {
        return "E-postadressen er ugyldig.";
    }

    if (!passord.trim()) {
        return "Passord må fylles ut.";
    }

    if (passord.length < 3) {
        return "Passord må være minst 3 tegn.";
    }

    if (tittel.length > 100) {
        return "Tittel kan ikke være lengre enn 100 tegn.";
    }

    if (kommentar.length > 500) {
        return "Kommentar kan ikke være lengre enn 500 tegn.";
    }

    if (tekst.length > 5000) {
        return "Tekst kan ikke være lengre enn 5000 tegn.";
    }

    if ((handling === "Ny" || handling === "Endre")) {
        if (!tittel.trim()) {
            return "Tittel må fylles ut.";
        }

        if (!tekst.trim()) {
            return "Tekst må fylles ut.";
        }
    }

    return null;
}

document.getElementById("bidragForm").addEventListener("submit", async function (event) {
    const handling = event.submitter?.value || "";
    const form = event.target;
    const kommentarEl = document.getElementById("kommentar");
    const passord = document.getElementById("passord").value;
    const epost = document.getElementById("epost").value;
    const tittel = document.getElementById("tittel").value;
    const tekst = document.getElementById("tekst").value;
    const kommentar = kommentarEl.value;

    if (!handling) return;

    event.preventDefault();

    const feil = validateInput({
        handling,
        epost,
        passord,
        tittel,
        kommentar,
        tekst
    });

    if (feil) {
        setListResult(feil);
        return;
    }

    const formData = new URLSearchParams(new FormData(form));
    formData.set("handling", handling);

    if ((handling === "Ny" || handling === "Endre") && kommentar.trim()) {
        formData.set("kommentar", await encrypt(kommentar, passord, epost));
    }

    const response = await fetch(form.action, {
        method: "POST",
        headers: {"Content-Type": "application/x-www-form-urlencoded"},
        body: formData.toString()
    });
    const rawText = await response.text();

    if (!response.ok) {
        setListResult(`Serverfeil (${response.status}): ${rawText || "ingen respons"}`);
        return;
    }

    if (handling === "Liste") {
        if (!rawText.trim()) {
            setListResult("Tom respons fra server.");
            return;
        }
        const decryptedText = await decryptKommentarLinjer(rawText, passord, epost);
        setListResult(decryptedText);
        return;
    }

    if (rawText.trim()) {
        setListResult(rawText);
    } else if (handling === "Ny") {
        setListResult("Bidrag lagret.");
    } else if (handling === "Endre") {
        setListResult("Bidrag oppdatert.");
    } else if (handling === "Slett") {
        setListResult("Bidrag slettet.");
    }
});