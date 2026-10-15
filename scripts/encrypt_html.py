#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cifra tutti i file .html di una cartella con una password.
Il file risultante è una pagina HTML che chiede la password e si
decifra nel browser (AES-256-GCM + PBKDF2, tramite Web Crypto).

Uso:
    HTML_PASSWORD="la-tua-password" python encrypt_html.py output
"""

import base64
import os
import sys
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITERAZIONI = 250_000
MARCATORE = "<!--ENCRYPTED-HTML-->"

TEMPLATE = """<!DOCTYPE html>
<!--ENCRYPTED-HTML-->
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Accesso protetto</title>
<style>
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
background:#0b0b12;color:#eee;font-family:system-ui,sans-serif}
form{display:flex;flex-direction:column;gap:12px;width:min(320px,86vw)}
input,button{padding:12px;border-radius:8px;border:1px solid #444;font-size:16px}
input{background:#161622;color:#eee}
button{background:#5b5bff;color:#fff;border:0;cursor:pointer}
#err{color:#ff6b6b;min-height:1.2em;font-size:14px}
</style>
</head>
<body>
<form id="f" style="display:none">
<input id="pw" type="password" placeholder="Password" autocomplete="current-password" autofocus>
<button type="submit">Entra</button>
<div id="err"></div>
</form>
<script>
const SALT="__SALT__", IV="__IV__", DATA="__DATA__", ITER=__ITER__;
const KEY="kbpw";
const b64=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
const f=document.getElementById("f"), err=document.getElementById("err"), pw=document.getElementById("pw");
async function decifra(password){
  const km=await crypto.subtle.importKey("raw",new TextEncoder().encode(password),"PBKDF2",false,["deriveKey"]);
  const key=await crypto.subtle.deriveKey({name:"PBKDF2",salt:b64(SALT),iterations:ITER,hash:"SHA-256"},km,{name:"AES-GCM",length:256},false,["decrypt"]);
  const buf=await crypto.subtle.decrypt({name:"AES-GCM",iv:b64(IV)},key,b64(DATA));
  return new TextDecoder().decode(buf);
}
function mostra(html){ document.open(); document.write(html); document.close(); }
async function auto(){
  let saved=null;
  try{ saved=sessionStorage.getItem(KEY); }catch(x){}
  if(saved){
    try{ mostra(await decifra(saved)); return; }
    catch(x){ try{ sessionStorage.removeItem(KEY); }catch(y){} }
  }
  f.style.display="flex"; pw.focus();
}
f.addEventListener("submit",async e=>{
  e.preventDefault(); err.textContent="";
  try{
    const html=await decifra(pw.value);
    try{ sessionStorage.setItem(KEY,pw.value); }catch(x){}
    mostra(html);
  }catch(x){ err.textContent="Password errata"; }
});
auto();
</script>
</body>
</html>
"""


def cifra_file(percorso: Path, password: str) -> bool:
    testo = percorso.read_text(encoding="utf-8")
    if MARCATORE in testo:
        print(f"= già cifrato, salto: {percorso}")
        return False

    salt = os.urandom(16)
    iv = os.urandom(12)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERAZIONI)
    chiave = kdf.derive(password.encode("utf-8"))
    cifrato = AESGCM(chiave).encrypt(iv, testo.encode("utf-8"), None)

    out = (
        TEMPLATE
        .replace("__SALT__", base64.b64encode(salt).decode())
        .replace("__IV__", base64.b64encode(iv).decode())
        .replace("__DATA__", base64.b64encode(cifrato).decode())
        .replace("__ITER__", str(ITERAZIONI))
    )
    percorso.write_text(out, encoding="utf-8")
    print(f"✅ cifrato: {percorso}")
    return True


def main():
    cartella = Path(sys.argv[1] if len(sys.argv) > 1 else "output")
    password = os.environ.get("HTML_PASSWORD", "")
    if not password:
        sys.exit("❌ Variabile d'ambiente HTML_PASSWORD mancante")
    if not cartella.is_dir():
        sys.exit(f"❌ Cartella non trovata: {cartella}")

    file_html = sorted(cartella.rglob("*.html"))
    if not file_html:
        print("⚠️ Nessun file .html trovato")
        return
    for f in file_html:
        cifra_file(f, password)


if __name__ == "__main__":
    main()
