# نبض · NABD

A browser-based internet speed test in Arabic (RTL), built as one self-contained
page. It reports download, upload and latency — but it is built around the parts a
single "Mbps" number hides: **latency under load**, **per-stream shaping**, and the
gap between a **local edge** and the **real international path**.

**Live:** [nabdnet.netlify.app](https://nabdnet.netlify.app) · **How it works:** [docs/METHODOLOGY.md](docs/METHODOLOGY.md)

![نبض — the test screen](docs/preview.jpg)

---

## What makes it different

A peak-download figure is easy to produce and says little about how a connection
behaves when you actually use it. نبض measures the rest, directly:

- **Latency under load.** Ping is measured *while the line is saturated*, not idle, so
  you see the bufferbloat that breaks calls and games — graded A+ to F.
- **Capacity from three independent angles.** Steady-state throughput, a
  1→2→4→8-connection concurrency sweep, and a congestion-window-independent
  packet-train dispersion estimate (Theil-Sen + pathrate-style mode). The three are
  cross-checked and reported as matching, close or divergent — never a single number
  dressed up as certainty.
- **Local vs. international.** Cloudflare's edge sits inside Iraq, so it measures the
  local path; jsDelivr/Fastly/gcore/unpkg ride real cross-border transit. A large gap
  between them is flagged as local-cache bias.
- **Honest throughput.** The headline is total bytes ÷ time over the steady window,
  not a lucky high percentile — with compression (wire vs decoded bytes) corrected
  out. The full reasoning is in [the methodology](docs/METHODOLOGY.md).

Test lengths: quick (~15 s), standard (~35 s), deep (~70 s).

## Built for the real web

- **One file.** The whole app — UI and measurement engine — is a single `index.html`.
  No build step, no backend, no tracking.
- **Installable (PWA).** Web app manifest and icons; installs to a phone home screen
  and opens full-screen.
- **Hardened.** Strict Content-Security-Policy and the usual security headers ship
  with it (`_headers`, `netlify.toml`).
- **Private by design.** No analytics, no accounts. Test history stays in the
  browser's local storage, on the device.
- **Arabic-first.** Fully right-to-left, written in natural Arabic, not translated.

## Run it

A static site — any static server works:

```bash
python3 -m http.server 8000
# open http://127.0.0.1:8000
```

Opening `index.html` from disk renders the page, but the measurement needs a real
`https` origin, and a VPN or ad-blocker can block the test requests.

### Deploy

Configured for [Netlify](https://www.netlify.com) (`netlify.toml` serves the folder
as-is); it also drops onto GitHub Pages, Cloudflare Pages or any static host with no
changes.

## Browser support

Current Chrome, Edge, Firefox and Safari. Upload needs `XMLHttpRequest` upload
progress (everywhere today); the streaming download reader uses the Fetch
`ReadableStream` API, with an `arrayBuffer` fallback where it is absent.

## Files

```
index.html             the whole app (UI + measurement engine)
docs/METHODOLOGY.md     how every figure is produced
docs/preview.jpg        the screenshot above
manifest.webmanifest    PWA manifest
icon-192 / icon-512     app icons   ·   apple-touch-icon, favicon-32
og.png                  social preview image
_headers, netlify.toml  security headers + Netlify config
robots.txt, sitemap.xml, 404.html
```

## Credit

Built by **Nizar Jasim Mohammed Al-Zubaidi**
([@NizarJasim1](https://github.com/NizarJasim1)), branded with the
[NJ BLACK CROW](https://t.me/NJBLACKCROW) channel.

## License

[MIT](LICENSE).
