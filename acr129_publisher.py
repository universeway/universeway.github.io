name: ACR129 Blog Auto-Publisher

on:
  schedule:
    # Every Tuesday (2) and Friday (5) at 16:00 UTC = 17:00 WAT (Nigerian time)
    - cron: '0 16 * * 2,5'
  workflow_dispatch:   # Allow manual trigger from GitHub UI

permissions:
  contents: write

jobs:
  publish-blog-post:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install requests beautifulsoup4 lxml

      - name: Search news and publish blog post
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python3 acr129_publisher.py

      - name: Commit and push updated website
        run: |
          git config --global user.email "action@github.com"
          git config --global user.name "ACR129 Blog Bot"
          git add docs/index.html
          git diff --staged --quiet || git commit -m "Blog: ACR129 update $(date +'%Y-%m-%d')"
          git push
