# 2D Graphics — Android

Native Android (Kotlin + `Canvas`) implementation of the four 2D graphics scenes
(Particles, Bouncing Balls, Fractal Tree, Waves).

Kept alongside the main Python project at the repo root; built by the
`Build Android APK` GitHub Actions workflow at `.github/workflows/android-apk.yml`.

## Build locally

```sh
# ครั้งแรกหลัง clone — ติดตั้ง wrapper jar (binary ไม่ได้ commit ลง repo)
gradle wrapper --gradle-version=8.7 --distribution-type=bin

./gradlew :app:assembleDebug
# APK → app/build/outputs/apk/debug/app-debug.apk
```

Requires Gradle 8+, Android SDK (any `cmdline-tools` install), JDK 17, and
network access to `maven.google.com` + `dl.google.com`.

## Build on CI

Push any change under `android-app/**` to this branch, or run the workflow
manually from the Actions tab. The APK is uploaded as a workflow artifact
on every build; tick the `release` option in `workflow_dispatch` to also
attach it to a GitHub Release.

Min SDK 24, target SDK 34, Kotlin 1.9, AGP 8.5.
