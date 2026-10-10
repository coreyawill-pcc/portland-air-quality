name: Update PurpleAir data

on:
  schedule:
    - cron: "*/15 * * * *"
  workflow_dispatch:

permissions:
  contents: write

concurrency:
  group: purpleair
  cancel-in-progress: false

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Get previous data (for rolling history)
        run: |
          mkdir -p out
          git fetch origin data --depth=1 && git show FETCH_HEAD:sensors.json > out/prev.json || echo '{}' > out/prev.json

      - name: Fetch PurpleAir sensors
        env:
          PURPLEAIR_API_KEY: ${{ secrets.PURPLEAIR_API_KEY }}
        run: python3 scripts/fetch_purpleair.py out/prev.json out/sensors.json

      - name: Publish to data branch (single commit, no history bloat)
        run: |
          cd out
          rm prev.json
          git init -q
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git checkout -q -b data
          git add sensors.json
          git commit -q -m "Update sensors $(date -u +%FT%TZ)"
          git push -f "https://x-access-token:${{ github.token }}@github.com/${{ github.repository }}.git" data
