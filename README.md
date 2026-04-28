# XYZ — 3D USD Price Charts (Android)

Android app that renders a 3D scatter chart with all three axes denominated
in **USD**:

- **X axis** — `NIY/USD` (Nikkei 225 priced in USD; computed as `^N225 / (USD/JPY)`)
- **Y axis** — `SPY/USD` (S&P 500 ETF, already USD)
- **Z axis** — `SCBNK225/USD` (SCB Nikkei 225 fund NAV in USD; approximated, see note)

Each point is one trading day from the past year; points are connected by a
trajectory line so you can see the joint price path through 3D space.

## 📥 Download APK

Latest release (always the newest published version):

| Build   | Download |
|---------|----------|
| Release | **[xyz-release.apk](https://github.com/ttheman239-bot/XYZ/releases/latest/download/xyz-release.apk)** |
| Debug   | **[xyz-debug.apk](https://github.com/ttheman239-bot/XYZ/releases/latest/download/xyz-debug.apk)** |

All releases: <https://github.com/ttheman239-bot/XYZ/releases>

Per-version pinned URLs (replace `<version>` with the tag, e.g. `v1.0.0`):

```
https://github.com/ttheman239-bot/XYZ/releases/download/<version>/xyz-release-<version>.apk
https://github.com/ttheman239-bot/XYZ/releases/download/<version>/xyz-debug-<version>.apk
```

> The links above start working as soon as the first `v*` tag is pushed and
> the **Android Build** workflow finishes. Until then, grab the APK from the
> latest run's **Artifacts** section: <https://github.com/ttheman239-bot/XYZ/actions>

To cut a release:

```bash
git tag -a v1.0.0 -m "v1.0.0"
git push origin v1.0.0
```

## How it works

`MainActivity` fetches daily closes from Yahoo Finance for `SPY`, `^N225`,
`JPY=X`, and `THB=X`, aligns them onto a common timeline, derives the three
USD-denominated series, and hands the data to `assets/chart.html`, which
renders a Plotly 3D scatter.

> **Note on `SCBNK225/USD`:** Yahoo Finance does not expose Thai mutual fund
> NAVs, so the Z series is an approximation derived from `^N225` and `THB=X`.
> Replace the calculation in `MainActivity.fetchAllSeries()` with a real NAV
> source (e.g. SCBAM / Settrade) when one is available.

## Build locally

Requires JDK 17 and an Android SDK with platform 34.

```bash
./gradlew :app:assembleDebug
```

The APK lands at `app/build/outputs/apk/debug/app-debug.apk`.
