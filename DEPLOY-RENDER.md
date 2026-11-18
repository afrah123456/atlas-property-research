# Publish Atlas with Render Free Docker hosting

Hugging Face returned HTTP 402 because creating a Docker Space now requires PRO. The app files were not lost. Do not subscribe just to continue this assignment.

Render's current documentation supports Free web services and Docker builds. We still need to verify a successful deployment on your account. This guide does not claim it is already online.

## First step

Create an account at https://dashboard.render.com/register. Signing in with GitHub makes it easier to connect the source repository in the next step. Select free options only; do not authorize a paid plan.

## Upload the project to GitHub

1. Create a new repository named `atlas-property-research` on your GitHub account. Public is simplest; the files are an independent demo with public-source data.
2. Upload the project files from this folder to the repository root, including `Dockerfile`, `app.py`, `requirements.txt`, `render.yaml`, `.streamlit/config.toml`, `src`, `scripts` and `data`.
3. Never upload `.env`, tokens, `.streamlit/secrets.toml`, `.venv`, `.runtime`, `.cache`, `data/model-cache`, `data/index` or `deployment.json`.
4. The clean source ZIP excludes those credentials and caches. After extracting it, upload the contents of `dar-property-assistant`, not the outer directory or the ZIP itself. Make sure GitHub displays `Dockerfile` at the repository's top level.

## Create the Render web service

1. In Render, select New, then Web Service.
2. Connect the GitHub repository you just created.
3. Choose Docker as the runtime/language. This is essential to satisfy the container deployment requirement.
4. Name the service `atlas-property-research` or another available name.
5. Select the Free instance type.
6. Add environment variable `OPENROUTER_API_KEY` with your actual key, entered privately in Render's environment settings. Do not put it in a file on GitHub.
7. Add `RETRIEVAL_MODE=hybrid`, `EMBEDDING_THREADS=1` and `MAX_REQUESTS_PER_HOUR=40`.
8. Set the health-check path to `/_stcore/health` if requested.
9. Deploy and follow its build logs. `scripts/serve.py` honors Render's assigned PORT.

If the dashboard offers a Blueprint deployment instead, this project's `render.yaml` declares `plan: free`, the Docker runtime and the required secret prompt. Never select a paid plan or add a payment method without deciding to do so yourself.

## Verify

- Wait for Live status and copy the exact URL returned by Render.
- Open it in a private/incognito browser and test one DarGlobal and one Wasalt question.
- Check that actual AI answers are generated, with supporting source links.
- The first semantic query downloads a public embedding model and builds the index. On a small free instance, measure startup time and memory before sharing. If memory is insufficient, change `RETRIEVAL_MODE` to `lexical` explicitly; it still retrieves source text for the OpenRouter AI model, but no longer provides semantic embeddings. Document the actual mode used.
- Free services sleep after 15 minutes without inbound traffic and take approximately a minute to wake, with possible additional model initialization. The runtime filesystem is ephemeral, so model caches can be lost. Open and test the URL shortly before sharing; tell reviewers about cold starts.
- Usage is capped. Without a payment method, Render documents suspension/disabling builds when applicable free allowances run out rather than billing supplemental usage. Account verification or eligibility may still prevent free deployment.

## Official references checked during the hosting correction

- https://render.com/docs/free
- https://render.com/docs/docker
- https://huggingface.co/docs/hub/spaces-overview
