# AI News Source Extractor

## Description
AI News Link Scraper extracts all URLs from the most recent AI News issue (from news.smol.ai) and prepares them for seamless import into Google's NotebookLM. It organizes sources into a dedicated folder, separates non-social URLs into a `sources.txt`, and generates individual markdown files for quoted tweet content.

## Features
* **Folder Generation:** Creates a timestamped folder for each issue’s sources.
* **sources.txt:** Lists all URLs from the issue, excluding `twitter.com`, `x.com`, and `discord.com`.
* **Tweet Markdown:** Saves the full text of each quoted tweet as a separate markdown file.
* **WebSync Ready:** `sources.txt` can be pasted directly into the [WebSync for NotebookLM](https://chromewebstore.google.com/detail/websync-full-site-importe/hjoonjdnhagnpfgifhjolheimamcafok) Chrome extension to auto-import into NotebookLM.

## Installation
```bash
git clone https://github.com/ThomsenDrake/ainews-source-extractor.git
cd ainews-source-extractor
python3 -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage
Simply run the main scraper:
```bash
python build_issue.py
```
This will:
1. Generate a folder named with the current date for the latest AI News issue.
2. Create `sources.txt` inside that folder, containing all non-social URLs.
3. Produce individual `.md` files for each tweet quoted in the issue.

## Roadmap
* Improve URL-filtering logic to separate `twitter.com`, `x.com`, and `discord.com` links.
* Build `discord_scraper.py` to fetch and save referenced Discord messages as markdown.
* Parameterize the output folder path and issue source URL for greater flexibility.

## Contributing
Contributions welcome! Fork, branch, and submit a pull request.
