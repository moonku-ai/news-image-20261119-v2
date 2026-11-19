# news-image-20261119 v2 — The World in One Day

A pure-Python-stdlib program that draws a broadsheet front page summing up
Thursday 19 November 2026 and writes it to `/output/entry.png`
(1024x1024 PNG, under 1 MiB). No network, no third-party dependencies,
fully deterministic: two runs write byte-identical files.

Lead story: GTA VI rolls out worldwide at midnight local time, 13 years
after GTA V. Also: NASA marks Voyager 1 one light-day from Earth, Israel
launches its first ground operation in central Gaza since the October 2025
ceasefire, Cyclone Akvan nears India's east coast, the EU proposes a
45bn euro Ukraine loan, Democrats nominate Hakeem Jeffries for Speaker,
and Australia sanctions Israeli settlers.

Run locally:

    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py

Tests:

    python3 -m unittest test_draw -v
