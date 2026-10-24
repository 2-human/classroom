#!/usr/bin/env python3
"""Build the password-protected copy of a lesson quiz: the quiz WITH the textbook images, encrypted.

Usage (from anywhere in the repo):
    python3 scripts/build_zasticeno.py tools/geografija/juzna-evropa-kviz

Why: the textbook crops are private (tools/{predmet}/_source/, gitignored) and the classroom repo is
public on GitHub Pages, so the public quiz shows no textbook images. This script renders the same quiz
with the crops embedded, gzips it and encrypts it with the gate password; only the ciphertext and a
small gate page are written, to zasticeno/{predmet}/{slug}/:
    bundle.enc   {"v":1,"kdf":"PBKDF2-SHA256","iter":600000,"salt","iv","ct"} — AES-256-GCM over gzip(html)
    index.html   asks for the password, decrypts in the browser (WebCrypto), shows the quiz
Same scheme as the Crēdo Marketing Hub gate (credo/tools/marketing-hub/encrypt-bundle.py). The derived
key (not the password) is kept in sessionStorage for that tab only.

Password: $CLASSROOM_GATE_PASSWORD, else the macOS Keychain item "classroom-zasticeno"
    security add-generic-password -U -s classroom-zasticeno -a classroom -w 'NOVA-LOZINKA'
It is never printed or written to the repo. Changing it = set the new one, rerun this script, commit.
"""
import base64
import gzip
import json
import os
import pathlib
import subprocess
import sys

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "shared" / "python"))
from lesson_quiz import load_spec, render_html  # noqa: E402
from hub_shell import SHELL_CSS, brand_and_crumbs  # noqa: E402

ITER = 600000
KEYCHAIN = "classroom-zasticeno"


def password():
    pw = os.environ.get("CLASSROOM_GATE_PASSWORD")
    if not pw:
        r = subprocess.run(["security", "find-generic-password", "-s", KEYCHAIN, "-w"], capture_output=True, text=True)
        pw = r.stdout.strip() if r.returncode == 0 else ""
    if not pw:
        raise SystemExit(f"No gate password: set CLASSROOM_GATE_PASSWORD or the Keychain item {KEYCHAIN!r} (see --help).")
    return pw.encode("utf-8")


GATE = r"""<!DOCTYPE html>
<html lang="sr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>__TITLE__ (zaštićeno)</title>
<style>
__SHELL_CSS__
 .gate{max-width:420px;margin:12vh auto 0;padding:26px 28px;background:#fff;border:1px solid #e6e0d2;border-radius:12px}
 .gate h1{font-size:20px;margin:0 0 8px;color:#3a3528}
 .gate p{color:#6b6456;font-size:14px;line-height:1.5;margin:0 0 14px}
 .gate input{width:100%;font:inherit;padding:9px 11px;border:1px solid #b9b2a0;border-radius:8px;margin:0 0 12px}
 .gate button{font:inherit;padding:9px 18px;border:1px solid #1f7a3a;background:#1f7a3a;color:#fff;border-radius:8px;cursor:pointer}
 .gate button:disabled{opacity:.5}
 .gate .msg{min-height:1.3em;color:#b1271f;font-size:13.5px;margin-top:10px}
</style>
</head>
<body class="app-body">
<header class="app-bar">__BRAND_CRUMBS__</header>
<main class="app-main">
 <form class="gate" id="gate">
  <h1>__TITLE__ — sa slikama iz udžbenika</h1>
  <p>Ova verzija kviza sadrži slike iz udžbenika i namenjena je samo učenicima. Upiši lozinku koju si dobio od nastavnika.</p>
  <input type="password" id="pw" autocomplete="current-password" placeholder="Lozinka" aria-label="Lozinka" autofocus>
  <button type="submit">Otvori kviz</button>
  <div class="msg" id="msg"></div>
 </form>
</main>
<script>
(function () {
  var KEY = 'classroom-gate:' + location.pathname;
  var b64 = function (s) { return Uint8Array.from(atob(s), function (c) { return c.charCodeAt(0); }); };
  var enc = function (u) { var s = ''; u.forEach(function (b) { s += String.fromCharCode(b); }); return btoa(s); };
  var form = document.getElementById('gate'), pw = document.getElementById('pw'), msg = document.getElementById('msg');
  function show(key, bundle) {
    return crypto.subtle.decrypt({ name: 'AES-GCM', iv: b64(bundle.iv) }, key, b64(bundle.ct))
      .then(function (gz) { return new Response(new Blob([gz]).stream().pipeThrough(new DecompressionStream('gzip'))).text(); })
      .then(function (html) { document.open(); document.write(html); document.close(); });
  }
  function derive(password, bundle) {
    return crypto.subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveKey'])
      .then(function (base) { return crypto.subtle.deriveKey({ name: 'PBKDF2', hash: 'SHA-256', salt: b64(bundle.salt), iterations: bundle.iter }, base, { name: 'AES-GCM', length: 256 }, true, ['decrypt']); });
  }
  // the form never submits natively: a password typed before the bundle arrives waits for it
  var bundleP = fetch('bundle.enc', { cache: 'no-store' }).then(function (r) { if (!r.ok) throw new Error(); return r.json(); });
  form.onsubmit = function (e) {
    e.preventDefault(); msg.textContent = 'Otvaram…'; form.querySelector('button').disabled = true;
    bundleP.then(function (bundle) {
      return derive(pw.value, bundle).then(function (k) {
        return crypto.subtle.exportKey('raw', k).then(function (raw) { try { sessionStorage.setItem(KEY, enc(new Uint8Array(raw))); } catch (e2) {} return show(k, bundle); });
      }).catch(function () { try { sessionStorage.removeItem(KEY); } catch (e3) {} msg.textContent = 'Lozinka nije tačna.'; form.querySelector('button').disabled = false; pw.select(); });
    }, function () {});
  };
  bundleP.then(function (bundle) {
    var saved = null; try { saved = sessionStorage.getItem(KEY); } catch (e) {}
    if (saved) crypto.subtle.importKey('raw', b64(saved), 'AES-GCM', true, ['decrypt']).then(function (k) { return show(k, bundle); })
      .catch(function () { try { sessionStorage.removeItem(KEY); } catch (e) {} });
  }).catch(function () { msg.textContent = 'Kviz nije dostupan (otvori ga preko veb adrese, ne kao fajl).'; form.querySelector('button').disabled = true; });
})();
</script>
</body>
</html>
"""


def main(tool):
    tool = (ROOT / tool).resolve() if not pathlib.Path(tool).is_absolute() else pathlib.Path(tool)
    spec = load_spec(tool / "spec.yaml")
    predmet, slug = tool.parent.name, tool.name
    out_dir = ROOT / "zasticeno" / predmet / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    page = out_dir / "index.html"

    html = render_html(spec, page, embed_images=True, write=False)
    n_img = html.count("data:image/jpeg;base64,")
    plain = gzip.compress(html.encode("utf-8"), mtime=0)
    salt, iv = os.urandom(16), os.urandom(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(password())
    ct = AESGCM(key).encrypt(iv, plain, None)
    b64 = lambda b: base64.b64encode(b).decode("ascii")
    (out_dir / "bundle.enc").write_text(json.dumps({"v": 1, "kdf": "PBKDF2-SHA256", "iter": ITER,
                                                    "salt": b64(salt), "iv": b64(iv), "ct": b64(ct)}), encoding="utf-8")
    title = spec.get("title_short") or spec["title"]
    gate = (GATE.replace("__SHELL_CSS__", SHELL_CSS)
                .replace("__BRAND_CRUMBS__", brand_and_crumbs(page, title, spec))
                .replace("__TITLE__", title))
    page.write_text(gate, encoding="utf-8")
    print(f"{n_img} slika ugrađeno; {len(plain) // 1024} KB gzip → {out_dir.relative_to(ROOT)}/bundle.enc + index.html")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        raise SystemExit(__doc__)
    main(sys.argv[1])
