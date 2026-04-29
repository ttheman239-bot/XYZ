# 2D Graphics — Android App

Native Android (Kotlin + `Canvas`) port of the four-scene 2D graphics demo.

## Scenes

- **Particles** — particles attracted to your finger
- **Balls** — bouncing balls with gravity and elastic walls
- **Fractal** — recursive tree that sways
- **Waves** — layered sine waves with shifting hues

## Project layout

```
app/
  src/main/
    java/com/example/graphics2d/
      MainActivity.kt
      GraphicsView.kt        # all four scenes
    res/layout/activity_main.xml
    res/values/{strings,colors,themes}.xml
    AndroidManifest.xml
build.gradle.kts
settings.gradle.kts
```

The original web demo (`index.html`, `style.css`, `main.js`) is kept at the repo root for reference.

## Build

Open the project in Android Studio (Hedgehog or newer) and Run, or from the CLI:

```sh
./gradlew :app:assembleDebug
```

Min SDK 24, target SDK 34, Kotlin 1.9, AGP 8.5.
