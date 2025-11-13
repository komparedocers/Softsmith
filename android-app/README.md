# Software Maker Android App

Android application for tracking and managing software projects built by the Software Maker Platform.

## Features

- View all projects in real-time
- Create new projects from prompts
- Track progress with live updates
- View project details and logs
- Pause/resume projects
- Real-time status monitoring

## Setup

1. Open the project in Android Studio
2. Update the API base URL in `ApiClient.java` if needed
3. Build and run on emulator or device

## Requirements

- Android SDK 24+
- Android Studio Arctic Fox or later
- Internet permission

## API Configuration

By default, the app connects to `http://10.0.2.2:8000` (Android emulator localhost).

To change the API URL, edit `ApiClient.java`:

```java
private static final String BASE_URL = "https://your-api-url.com/";
```

## Build

```bash
./gradlew assembleDebug
```

## Install

```bash
./gradlew installDebug
```
