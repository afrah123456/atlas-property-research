---
title: Atlas Property Research
emoji: 🏙️
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Atlas Property Research

**Hosting correction:** Hugging Face returned HTTP 402 because Docker Space creation now requires a paid plan. The default deployment launcher now opens `DEPLOY-RENDER.md` for Render's documented Free Docker option. The older Hugging Face helper remains available only for users who already have an eligible paid plan; it is not a free-hosting path. No successful public deployment has been verified yet.

A source-grounded real-estate assistant for the DarGlobal Junior AI Engineer assignment. It searches a bounded collection of DarGlobal and Wasalt public pages, retrieves relevant evidence locally, and generates cited answers through zero-priced OpenRouter models.

## Current delivery status

- Working Streamlit interface, source library and multilingual hybrid retrieval.
- Included collection: 16 public-source pages (10 directly scraped Wasalt pages and 6 reviewed DarGlobal snapshots), producing 67 chunks with the current settings.
- 23 automated checks pass, including interface interaction, citation validation, source filtering, scraper extraction and mocked API failures.
- 12/12 retrieval checks find the expected source within the first three chunks. This is a small development set, not a general accuracy estimate; bilingual name expansion was refined using it.
- **Not yet tested:** real LLM responses. An owner-supplied OpenRouter key is required.
- **Not yet verified:** Docker image build/run or public deployment. Docker's local daemon was unavailable during development; the hosting script can build the actual container remotely.
- **Collection limitation:** direct DarGlobal HTTP requests encountered bot protection. Its six included records are short, reviewed snapshots derived from publicly readable browser/search text, with metadata stating this method. Wasalt's ten pages were successfully scraped using Python requests; those records retain their original Arabic text. Neither method is presented as a live inventory feed. `data/scrape_report.json` records successes and failures. Refresh DarGlobal through permitted direct access or authorized browser HTML exports before claiming fully automated collection from both websites.

## Architecture

```text
Allowlisted public URLs / authorized HTML exports
    -> scraper, cleaning, provenance and crawl report
    -> data/documents.json
    -> overlapping character chunks
    -> multilingual local ONNX embeddings + FAISS
       combined with lexical TF-IDF and bilingual name expansion
    -> top evidence excerpts with source IDs
    -> free OpenRouter model, server-side credential
    -> structured answer + validated citation IDs
    -> Streamlit chat and source expanders
```

This uses retrieval-augmented generation, not model fine-tuning. The multilingual embedding model is `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, executed using FastEmbed/ONNX, avoiding a PyTorch runtime. FAISS vectors and source text stay local to the app. Embeddings are normalized for inner-product similarity. A lexical component helps names, listing IDs and exact terms; simple name aliases support Arabic queries.

## Run locally

On this Windows workspace, double-click **Start-Atlas.cmd** to configure and open the local app; its terminal prompt hides the OpenRouter key. Double-click **Deploy-Atlas.cmd** for the corrected Render hosting instructions. Enter deployment secrets in the provider's settings, never in chat or GitHub files.

Use Python 3.12. From this directory:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe scripts/configure.py
.venv\Scripts\python.exe -m streamlit run app.py
```

If Python is managed with uv:

```powershell
uv python install 3.12
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
.venv\Scripts\python.exe scripts/configure.py
.venv\Scripts\python.exe -m streamlit run app.py
```

The local configuration script requests the OpenRouter key in a hidden terminal prompt, then writes an ignored `.env` file. Do not share that file. Without a key, the app clearly labels its behavior as **evidence search only**, not AI generation.

The first semantic search downloads approximately 220 MB of model assets; later requests reuse the cache. Set `RETRIEVAL_MODE=lexical` for a lightweight/offline retrieval fallback. This is explicitly identified as lexical-only mode.

### This workspace

The prepared development environment is at `../../work/dar-build/venv` relative to this folder. To launch it immediately:

```powershell
& '../../work/dar-build/venv/Scripts/python.exe' scripts/configure.py
& '../../work/dar-build/venv/Scripts/python.exe' -m streamlit run app.py
```

## OpenRouter configuration

| Variable | Meaning |
|---|---|
| `OPENROUTER_API_KEY` | Required server-side secret for AI generation |
| `OPENROUTER_MODEL` | Optional explicit free model ID; otherwise discover at request time |
| `RETRIEVAL_MODE` | `hybrid` (default) or `lexical` |
| `MAX_REQUESTS_PER_HOUR` | Process-wide API-attempt cap, default 40 |

The app queries OpenRouter's catalog, requires a `:free` suffix and zero prompt/completion pricing, and rejects a paid or no-longer-free configured model. Fallback attempts are limited to verified free models. There is no silent paid fallback. Quota, authentication, timeout and provider errors are shown clearly. Catalog verification is cached for 15 minutes. Free availability and provider policies can change.

Chat requests send the question, a bounded recent conversation and retrieved excerpts to OpenRouter and its selected provider. Do not enter personal or confidential information. The application does not persist chat transcripts; session state is in server memory.

## Collect or refresh data

```powershell
python scripts/scrape.py --max-pages 20 --merge
```

The scraper:

- Restricts HTTPS hosts to DarGlobal and Wasalt, and does not fetch arbitrary user-supplied URLs.
- Checks robots rules, respects crawl delay, follows only allowlisted redirects and uses a maximum page budget.
- Stops at access controls/bot challenges instead of bypassing them.
- Removes navigation, scripts and forms; skips recognizable phone/email lines; records URL, method, timestamp and text hash.
- Records skipped pages and preserves the current dataset if nothing can be collected.
- Returns exit code 2 when no documents were collected; that outcome is a collection limitation, not success.

Inspect collected text before publication: heuristic cleaning cannot guarantee removal of every personal or irrelevant detail. The checked-in snapshot contains no private contact fields.

### Authorized browser HTML exports

If permitted by the source site's rules, save a fully rendered public page as HTML in your browser. Create an export manifest alongside the file:

```json
[
  {
    "url": "https://darglobal.co.uk/the-astera",
    "file": "astera.html"
  }
]
```

Then run:

```powershell
python scripts/scrape.py --import-manifest exports/manifest.json --merge
python scripts/build_index.py
```

The import reuses the cleaner and records `authorized-browser-html-import` as its method. It does not authenticate to or bypass a website. Do not import login-only data. The current direct-HTTP report and reviewed snapshot are intentionally retained separately.

## Docker

```powershell
docker build -t atlas-property-research .
docker run --rm -p 7860:7860 --env-file .env atlas-property-research
```

Or run `docker compose up --build`. Open `http://localhost:7860`.

The image runs as a non-root user, exposes port 7860 and has a Streamlit health check. The API key is injected at runtime, never placed in the Dockerfile or image. The first query builds the local model/index cache; ephemeral hosts rebuild it after a restart. CPU hosting is sufficient for this small collection.

## Optional paid-plan deployment to Hugging Face Spaces

This path requires an existing eligible paid plan. For the documented free alternative, follow `DEPLOY-RENDER.md`. Do not purchase a plan merely because an earlier instruction described Docker Spaces as free.

Create a Hugging Face account and a write-capable token for creating your own Space. Keep tokens private. From an interactive terminal:

```powershell
python scripts/deploy.py --wait
```

The helper requests both tokens using hidden prompts, validates the OpenRouter key, creates a **new public Docker Space**, stores the OpenRouter key as a runtime secret, uploads the source and waits for hosting. It refuses to overwrite an existing Space. No token is stored in the repository or deployment record. The resulting public URL and state are saved to ignored `deployment.json`.

If uploading fails after Space creation, continue using that existing Space through the HF web interface rather than creating duplicates. Upload the project files there, excluding `.env`, `.venv`, model caches, index files and secrets. Confirm that the SDK is Docker and port is 7860.

The public Space repository exposes the application source and included public-data snapshot. Hosting costs, sleep/cold-start behavior and quotas depend on the selected HF plan. Use the free CPU option and verify the current plan before selecting hardware. Recruiters should not need their own API key or an account to use the public demo.

Before submission, open the actual URL in an incognito browser and verify:

1. The page loads without requiring recruiter login.
2. At least one DarGlobal and one Wasalt question produces a real model answer.
3. Displayed source links support the answer.
4. An unknown price/payment-plan question is handled honestly.
5. A follow-up question uses conversation context.
6. An Arabic question works.
7. Rate-limit/provider errors are actionable and do not reveal secrets.

Do not submit a local `localhost` URL or claim the unconfigured search-only mode fulfills the AI requirement.

## Tests and evaluation

```powershell
python -m pytest -q
python scripts/evaluate.py --mode hybrid
```

See `data/evaluation-hybrid.json` for retrieval results. Mocked OpenRouter tests establish request/error handling and citation-ID validation, **not** real-model answer quality. Source-ID checks do not prove that every sentence is entailed by the cited source. A manual real-model evaluation remains mandatory after credential setup; use `EVALUATION.md`.

## Known limitations

- Small, deliberately bounded snapshot, not exhaustive property search.
- Browser/search text may be cached; the review timestamp is not proof of original-site freshness.
- Direct DarGlobal access was blocked; its reproducible refresh needs permitted access or an authorized export. Wasalt collection succeeded on the recorded run but may be blocked or change later.
- Some source area values conflict. Conflicts are preserved, not silently corrected.
- Some Wasalt category excerpts do not explicitly show a currency. The chatbot must not infer it.
- No live pricing, inventory feed, financial suitability or legal/visa advice.
- Prompt instructions and citation checking reduce risks but do not eliminate hallucinations or prompt injection.
- Rate limiting is single-process/in-memory; production multi-replica hosting needs a shared rate limiter.
- Free model quotas and cold starts may affect recruiter testing. Check the deployment shortly before sharing.

## Source and technology references

- DarGlobal: https://darglobal.co.uk/
- Wasalt: https://wasalt.sa/ (wasalt.com redirects here)
- OpenRouter free models: https://openrouter.ai/docs/guides/routing/model-variants/free
- OpenRouter limits: https://openrouter.ai/docs/api/reference/limits
- Docker Spaces: https://huggingface.co/docs/hub/spaces-sdks-docker

Full per-page provenance is in `data/documents.json`. Source content remains the property of its respective owners. This is an independent recruitment demonstration.
