---
title: Atlas Property Research
sdk: docker
app_port: 7860
---

# Atlas Property Research

A real-estate chatbot built for the DarGlobal Junior AI Engineer assignment. It answers questions using information collected from DarGlobal and Wasalt, with links to the sources.

## Features

- Answers questions about projects, locations, property types and amenities.
- Searches English and Arabic content.
- Shows supporting source excerpts and links.
- Uses a free AI model through OpenRouter.
- Includes Docker packaging and Render deployment settings.

## How It Works

1. Collect and clean public website information.
2. Split the information into smaller sections.
3. Search for sections relevant to the user's question.
4. Send those sections to an OpenRouter model.
5. Display the answer with source references.

This approach is called Retrieval-Augmented Generation (RAG). The app searches existing information to help the model answer; it does not train a new model.

## Technology

| Tool | Purpose |
|---|---|
| Python | Application logic |
| Streamlit | Chat interface |
| Requests and BeautifulSoup | Website collection and cleaning |
| FastEmbed and FAISS | Search by meaning across languages |
| TF-IDF | Match exact words, project names and listing IDs |
| OpenRouter | Access free AI models |
| Docker | Package the application |
| Render | Intended public hosting platform |

## Data Sources

The included collection contains **16 source pages**:

- **10 Wasalt pages** collected directly using the Python scraper.
- **6 DarGlobal pages** included as short, reviewed browser-text snapshots because direct scraping was blocked.

Each record includes its source URL, collection date and collection method.

This is a limited snapshot, not a live property database. Prices, specifications and availability may change.

## Example Questions

- What amenities does The Astera offer?
- Compare Tierra Viva and Les Vagues.
- Where is AIDA located?
- Show examples of apartments listed in Jeddah.

## Run Locally

Use **Python 3.12**.

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Configure your OpenRouter key using the private terminal prompt:

```bash
python scripts/configure.py
```

Start the application:

```bash
python -m streamlit run app.py
```

Open **http://localhost:7860**.

On Windows, you can also use **Start-Atlas.cmd**.

The first semantic search downloads an embedding model and may take longer. Without an OpenRouter key, the app provides source search only, not AI-generated answers.

## Run with Docker

After configuring your local `.env` file:

```bash
docker build -t atlas-property-research .
docker run --rm -p 7860:7860 --env-file .env atlas-property-research
```

Open **http://localhost:7860**.


## Refresh the Data

```bash
python scripts/scrape.py --max-pages 20 --merge
```

The scraper checks robots rules, records blocked pages and does not bypass access controls. It also supports importing authorized saved HTML pages.

## Limitations and Privacy

- The chatbot covers only the collected pages.
- Answers may contain mistakes, even when source references are present.
- Confirm current prices and availability with the original provider.
- Free models have usage limits and may be temporarily unavailable.
- Questions and retrieved excerpts are sent to OpenRouter and its selected model provider.
- Never upload `.env` files or API keys to GitHub.

This is an independent recruitment demonstration, not an official DarGlobal or Wasalt service.
