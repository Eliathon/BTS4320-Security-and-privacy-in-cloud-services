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

document.getElementById("bidragForm").addEventListener("submit", async function (event) {
    const handling = event.submitter?.value;
    if (handling === "Liste" || handling === "Slett") return;

    const kommentar = document.getElementById("kommentar");
    if (!kommentar.value.trim()) return;

    event.preventDefault();

    const passord = document.getElementById("passord").value;
    const epost = document.getElementById("epost").value;

    kommentar.value = await encrypt(kommentar.value, passord, epost);

    event.target.submit();
});