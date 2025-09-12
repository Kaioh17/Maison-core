# Flutter NDK Version Mismatch on Windows

## Problem Description

When building a Flutter project for Android on Windows, the build failed with the following error:

```
A problem occurred configuring project ':app'.
> com.android.builder.errors.EvalIssueException: [CXX1104] 
NDK from ndk.dir at C:\Users\mubsk\AppData\Local\Android\Sdk\ndk\25.2.9519653 
had version [25.2.9519653] which disagrees with android.ndkVersion [27.0.12077973]
```

### Key Symptoms:

- CMake could not find clang.exe / clang++.exe because the installed NDK was built for Linux (linux-x86_64) instead of Windows (windows-x86_64)
- Even after installing the correct Windows NDK (r25b), the build system continued to request NDK 27 due to a mismatch in configuration
- In `build.gradle.kts`, the project was using:
  ```kotlin
  ndkVersion = flutter.ndkVersion
  ```
  which inherits the NDK version from Flutter's Gradle plugin. Flutter defaulted to 27.0.12077973, while the installed NDK was 25.2.9519653

## Root Cause

The Flutter Android Gradle plugin (`flutter.gradle`) enforces a specific NDK version (`flutter.ndkVersion`), which was set to 27.0.12077973.

The developer's local environment had only NDK 25.2.9519653 installed (the stable version recommended for Flutter on Windows).

This mismatch between `local.properties` (`ndk.dir`) and the Gradle config (`ndkVersion`) caused the build to fail.

## Resolution

Two approaches are possible:

### Option 1: Hardcode the NDK Version (Recommended)

In `android/build.gradle.kts` (app-level), inside the `android { }` block, replace:

```kotlin
ndkVersion = flutter.ndkVersion
```

with:

```kotlin
ndkVersion = "25.2.9519653"
```

This forces Gradle to use the installed NDK version and bypasses Flutter's default.

### Option 2: Match Flutter's Default NDK

1. Update Flutter to the latest stable:
   ```bash
   flutter upgrade
   ```

2. Install the Windows build of NDK 27.0.12077973 via Android Studio → SDK Manager → SDK Tools

3. Ensure `local.properties` points to the correct NDK path

## Final local.properties Example

```properties
sdk.dir=C:\\Users\\mubsk\\AppData\\Local\\Android\\Sdk
ndk.dir=C:\\Users\\mubsk\\AppData\\Local\\Android\\Sdk\\ndk\\25.2.9519653
```

## Commands to Clean and Rebuild

```bash
flutter clean
flutter pub get
flutter build apk
```

## Troubleshooting Steps

1. **Check NDK Installation**:
   - Open Android Studio
   - Go to Tools → SDK Manager → SDK Tools
   - Verify NDK is installed with Windows build tools

2. **Verify NDK Path**:
   - Check `android/local.properties` file
   - Ensure `ndk.dir` points to the correct NDK installation

3. **Check Flutter NDK Version**:
   ```bash
   flutter doctor -v
   ```
   Look for NDK version information in the output

4. **Clean Build Cache**:
   ```bash
   flutter clean
   cd android
   ./gradlew clean
   cd ..
   flutter pub get
   ```

## Prevention

- Always use the recommended NDK version for your Flutter version
- Keep Flutter and Android SDK tools updated
- Document the NDK version used in your project for team consistency

## Takeaway

- On Windows, ensure the NDK includes the `windows-x86_64` prebuilt toolchain (not `linux-x86_64`)
- `local.properties` sets the physical location of the SDK/NDK, but `build.gradle(.kts)` enforces which version is used
- For stability, NDK 25.2.9519653 (r25b) is recommended for Flutter builds on Windows
- If `flutter.ndkVersion` doesn't match your environment, override it by hardcoding `ndkVersion`

## Related Files

- `android/app/build.gradle.kts` - Main build configuration
- `android/local.properties` - Local SDK/NDK paths
- `android/gradle.properties` - Gradle properties
- `pubspec.yaml` - Flutter dependencies

## Additional Resources

- [Flutter Android Setup](https://docs.flutter.dev/get-started/install/windows#android-setup)
- [Android NDK Documentation](https://developer.android.com/ndk/guides)
- [Flutter Build Troubleshooting](https://docs.flutter.dev/deployment/android#troubleshooting)
