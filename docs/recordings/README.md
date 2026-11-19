# Power BI walkthrough

[Watch or download the MP4](walkthrough.mp4)

This is a **step walkthrough assembled from actual native Power BI screenshots**, captured on 2026-11-19. It is not a continuous screen recording or footage of a person manually authoring the report. Each original screenshot is held for six seconds with a caption. No chart values, UI states or cursor movements are fabricated. The screenshots show the final programmatically generated project loaded, refreshed and inspected in Power BI Desktop.

| Time | View | What it demonstrates |
|---|---|---|
| 00–06s | SLA overview | 6,000 tickets; 79.6% response attainment; 199 overdue open tickets. |
| 06–12s | High-priority filter | 1,153 tickets; 56.3% response attainment; 37 overdue open. |
| 12–18s | Backlog and survey coverage | 227 unresolved tickets and 1,934 survey respondents; CSAT describes respondents only. |
| 18–24s | Relationships | Team and priority-policy dimensions filter the ticket fact. |
| 24–30s | Loaded tickets | 6,000 unique clean tickets loaded, with timestamps and eligibility flags. |
| 30–36s | Deadline policy | High: 4/24 hours; Normal: 8/72; Low: 24/168. All use calendar hours. |

The unmodified PNGs are in [screenshots](../screenshots). [Capture manifest](captures.json) records their SHA-256 hashes and descriptions. Rebuild the video using `python scripts/build_walkthrough.py` from the repository root, with FFmpeg on PATH. The video is silent; captions identify each step. GitHub may require downloading the MP4 to play it.
