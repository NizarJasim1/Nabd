# How نبض measures

Most speed tests return one number: peak download. نبض is built on the opposite
premise — that the single number is the least interesting thing about a connection,
and the parts that make a line feel slow (latency under load, per-stream shaping,
a path that only one connection can't fill) are measurable in a browser if you are
careful. This document describes exactly how each figure is produced, so the method
can be checked against the source in `index.html`.

Everything runs client-side. There is no backend of our own; the test drives public
CDN endpoints and reads the browser's own timing APIs.

## Endpoints, and why these ones

The measurement path is chosen, not incidental:

- **Local edge** — `speed.cloudflare.com`. Cloudflare has points of presence inside
  Iraq, so its `__down` / `__up` endpoints measure the *local* edge. It returns a
  colo code that is mapped to a city and classified محلي / إقليمي / دولي
  (local / regional / international).
- **International transit** — jsDelivr, Fastly, gcore and unpkg. These are not
  fronted from inside the country, so a download from them rides real cross-border
  transit. Four separate hostnames across three CDNs are used deliberately: the
  browser pools connections by origin, so each hostname is its own TCP/QUIC
  connection with its own congestion window — which is what lets the concurrency
  sweep below open many independent windows at once.
- **Optional self-hosted server** — any LibreSpeed backend
  (`garbage.php` / `empty.php` with `cors=true`) can be pinned as a full
  bidirectional server.

A health check probes each source before the run and falls back in order; if every
request is blocked (usually a VPN or ad-blocker), the test says so rather than
reporting zeros.

## The run

| Phase | What it does |
|---|---|
| Warm-up | A 120 KB fetch primes DNS/TCP/TLS and records the handshake breakdown (DNS, TCP, TLS, TTFB) and the negotiated protocol (h2/h3) from the Resource Timing API. |
| Idle latency | A burst of small fetches → p50/p95/p99, jitter and the minimum RTT, before any load. |
| Download | Object sizes ramp up across parallel streams; a ping loop runs *at the same time* to capture latency under load. |
| Single stream | One connection, sized to roughly 3× the estimated per-second throughput, recording every chunk's arrival time for the dispersion estimate below. |
| Upload | Same ramp, with an **incompressible random payload** so CDN compression can't inflate it; loaded latency is captured here too. |
| Concurrency sweep | 1→2→4→8 (→12 in deep mode) connections across the separate international origins. |
| Context | Cloudflare `/meta` (colo, region), ISP, IPv6 reachability, and a reachability panel (Cloudflare, jsDelivr, GitHub, DNS 1.1.1.1 and 8.8.8.8). |

## Throughput: a definition, not a high score

The headline figure is **total payload bytes ÷ elapsed time** over the steady-state
window (ramp-up discarded, tail trimmed to the active region). That is the physical
definition of throughput.

It is deliberately **not** a high percentile of short windows. A high percentile
picks the luckiest moments and reads high — which is what a "pick the fastest 70% of
samples" approach does, and why single-number tools, and an earlier build of this
one, over-reported. نبض cross-checks the window aggregate against a per-object
aggregate and, if the two disagree, lowers its confidence rather than taking the
larger figure.

Every leg also tracks **wire bytes vs decoded bytes** (`transferSize` vs
`decodedBodySize`). If the ratio falls in a real-compression band, throughput is
corrected to the on-the-wire figure; outside that band it is left alone.

## Latency under load (bufferbloat)

Idle latency is easy and nearly useless on its own. نبض measures latency *while the
line is saturated* — the ping loop runs through the download and upload phases — and
reports the increase over idle. That increase is graded:

| Added latency | Grade | Meaning |
|---|---|---|
| < 5 ms | A+ | unaffected under load |
| < 30 ms | A | stable |
| < 60 ms | B | slight delay when busy |
| < 200 ms | C | calls and games stutter during a download |
| < 400 ms | D | clearly affected — enable SQM/QoS |
| ≥ 400 ms | F | collapses under load |

This is the single most predictive number for how a connection *feels*, and it is
the one a peak-Mbps test cannot show.

## Capacity from three independent angles

A browser can't open raw sockets, so no single method is trusted. نبض computes three
views of the same link and reports how well they agree (متطابقة / متقاربة / متباعدة
— matching / close / divergent):

1. **Measured throughput** — the steady-state figure above.
2. **Concurrency sweep.** Throughput is measured at 1, 2, 4, 8 connections. A flat
   curve means one connection already fills the line and the single number is the
   truth; a climbing curve means the path is loss/RTT-limited and the plateau is the
   real capacity. The **knee** (first level within 95% of the best) is reported. This
   measures the thing a many-socket tool like Ookla hides inside its headline number
   instead of hiding it.
3. **Packet-train dispersion** — capacity from inter-chunk timing, independent of the
   congestion window (the blind spot of a single-connection browser test). Two
   estimators run:
   - a **Theil-Sen** regression (median of pairwise slopes) on the 5th-percentile
     lower envelope of serialization time per chunk size — delay is one-sided, so the
     floor of each size class is the clean signal;
   - a **pathrate-style mode** — the densest cluster of per-chunk rates in log space,
     not a percentile, because the bottleneck serializes packets at one rate.

   When the two disagree by more than ~25%, نبض publishes a **range** and takes the
   lower bound, rather than inventing a single figure. If the browser clock is too
   coarse (1 ms) or the sample is too short, the estimate is withheld with a stated
   reason.

From these it also derives the **bandwidth-delay product** (implied congestion
window = single-stream rate × RTT) to explain a window-limited path, flags
**shaping** when early-window throughput exceeds late-window by ≥25% (burst then
throttle), and flags **local bias** when the local figure exceeds the international
one by ≥1.6× (a local-cache result, not real cross-border throughput).

## Confidence and score

Each result carries a **confidence grade** (A–D) from how long the steady-state
window ran, how many independent 1-second blocks it held, the relative margin of
error (1.96·σ/√n), and the disagreement between the two throughput estimators. A
short sample is labelled as such instead of being dressed up.

The overall score (out of 100) is a weighted sum, chosen so latency behaviour counts
as much as raw speed:

| Component | Weight |
|---|---|
| Download | 30 |
| Ping (idle) | 20 |
| Latency under load | 20 |
| Upload | 15 |
| Jitter | 10 |
| Stability | 5 |

## Honest limits

A browser test is bounded by the browser. نبض is a diagnostic, not a lab instrument:

- JavaScript is single-threaded and there are no raw sockets, so on very fast links
  (multi-gigabit) the browser and CPU, not the line, can be the bottleneck. The
  concurrency sweep and dispersion estimate exist partly to detect when that happens.
- It depends on third-party CDN endpoints; their capacity and routing are part of
  what is being measured, and a blocked endpoint reduces coverage.
- Results vary with background traffic on the device and the local network. Run it on
  a quiet connection for the cleanest reading, and use the deep mode when you need the
  tightest confidence.

The goal is not to beat the headline number of other tools. It is to report a figure
you can defend and the diagnostics those tools leave out.
