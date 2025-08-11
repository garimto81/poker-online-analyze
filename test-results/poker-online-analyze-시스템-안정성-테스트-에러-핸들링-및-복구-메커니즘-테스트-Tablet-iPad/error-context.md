# Page snapshot

```yaml
- banner:
  - heading "🎰 Online Poker Traffic Analysis" [level=1]
  - paragraph: Real-time poker site traffic data from PokerScout
- main:
  - button "🔄 Refresh Data"
  - button "🕷️ Trigger New Crawl"
  - text: "⚠️ Failed to fetch data. Tried API (https://poker-analyzer-api.vercel.app) and Firebase direct. Error: HTTP error! status: 429"
  - button "📊 Table View"
  - button "📈 Charts View"
  - table:
    - rowgroup:
      - row "Rank ▲ Site Name Category Players Online Share % Cash Players Share % 24h Peak 7-Day Avg":
        - cell "Rank ▲"
        - cell "Site Name"
        - cell "Category"
        - cell "Players Online"
        - cell "Share %"
        - cell "Cash Players"
        - cell "Share %"
        - cell "24h Peak"
        - cell "7-Day Avg"
    - rowgroup
  - heading "Summary" [level=3]
  - paragraph: "Total Sites: 0"
  - paragraph: "GG Poker Sites: 0"
  - paragraph: "Total Players Online: 0"
  - paragraph: "GG Poker Market Share: 0.00%"
```