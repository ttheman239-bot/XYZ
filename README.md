# XYZ — 3D USD Price Charts (Android)

Android app that renders a 3D scatter chart with all three axes denominated
in **USD**:

- **X axis** — `NIY/USD` (Nikkei 225 priced in USD; computed as `^N225 / (USD/JPY)`)
- **Y axis** — `SPY/USD` (S&P 500 ETF, already USD)
- **Z axis** — `SCBNK225/USD` (SCB Nikkei 225 fund NAV in USD; approximated, see note)

Each point is one trading day from the past year; points are connected by a
trajectory line so you can see the joint price path through 3D space.

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

## CI builds & download links

The workflow at `.github/workflows/android.yml` builds debug + release APKs on
every push and uploads them as workflow artifacts. Pushing a tag like `v1.0.0`
additionally creates a GitHub Release with the APKs attached.

Per-version download links once a release is published:

```
https://github.com/ttheman239-bot/xyz/releases/tag/<version>
https://github.com/ttheman239-bot/xyz/releases/download/<version>/xyz-release-<version>.apk
https://github.com/ttheman239-bot/xyz/releases/download/<version>/xyz-debug-<version>.apk
```

For non-tagged builds, grab the APK from the run's **Artifacts** section on
the Actions tab.
