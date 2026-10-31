# AI ocena za „Objasni svojim rečima”

Cloudflare Worker koji poredi učenikov odgovor sa uzornim i vraća `tacno`, `delimicno` (uz potpitanje) ili
`netacno`. Ključ za Claude API stoji samo ovde. Bez njega kviz radi kao pre: učenik sam štiklira ideje.

## Postavljanje (jednom)

```bash
cd workers/objasni && npm install && npx wrangler login
npx wrangler secret put ANTHROPIC_API_KEY
openssl rand -hex 24 | tee /dev/tty | npx wrangler secret put APP_TOKEN
npx wrangler deploy
```

`deploy` ispiše adresu oblika `https://classroom-objasni.….workers.dev`. Adresu i token sačuvaj u Keychain:

```bash
security add-generic-password -U -s classroom-ai-url -a classroom -w 'https://classroom-objasni.….workers.dev'
security add-generic-password -U -s classroom-ai-token -a classroom -w 'TOKEN'
```

Zatim ponovo napravi zaštićene kopije kvizova (`scripts/build_zasticeno.py`). Token ide samo u šifrovani deo.

Model se menja u `wrangler.toml` (`MODEL`). Svako ocenjivanje je jedan poziv Claude API-ja i naplaćuje se.
