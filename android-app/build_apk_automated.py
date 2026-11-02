import os
import subprocess
import time

# Paths
JDK_PATHS = [
    r"C:\Users\kalai\.jdks\jbr-21.0.11",
    r"C:\Program Files\Android\Android Studio\jbr"
]

JBR_PATH = None
for path in JDK_PATHS:
    if os.path.exists(path):
        JBR_PATH = path
        break

if not JBR_PATH:
    JBR_PATH = r"C:\Program Files\Android\Android Studio\jbr"

SDK_PATH = r"C:\Users\kalai\AppData\Local\Android\Sdk"
GRADLE_BAT = r"C:\Users\kalai\.gradle\wrapper\dists\gradle-8.14.3-all\10utluxaxniiv4wxiphsi49nj\gradle-8.14.3\bin\gradle.bat"
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Fallback: Check if gradle wrapper bat exists inside project
PROJECT_GRADLEW = os.path.join(APP_DIR, "gradlew.bat")
if not os.path.exists(GRADLE_BAT) and os.path.exists(PROJECT_GRADLEW):
    GRADLE_BAT = PROJECT_GRADLEW

print("===================================================")
print("🚀 AUTOMATED ANDROID APK BUILDER")
print("===================================================")

# Set environment variables
env = os.environ.copy()
env["JAVA_HOME"] = JBR_PATH
env["PATH"] = os.path.join(JBR_PATH, "bin") + os.path.pathsep + env.get("PATH", "")
env["ANDROID_HOME"] = SDK_PATH
env["ANDROID_SDK_ROOT"] = SDK_PATH
env["ANDROID_USER_HOME"] = r"C:\Users\kalai\.android"

# Fix ANDROID_PREFS_ROOT conflict
env.pop("ANDROID_PREFS_ROOT", None)

env["GRADLE_OPTS"] = f'-Dorg.gradle.java.home="{JBR_PATH.replace(os.sep, "/")}"'

print(f"Java Home: {env['JAVA_HOME']}")
print(f"Android SDK: {env['ANDROID_HOME']}")
print(f"Gradle Executable: {GRADLE_BAT}")

apk_path = os.path.join(APP_DIR, "app", "build", "outputs", "apk", "debug", "app-debug.apk")

# Delete old APK and stale build outputs to avoid false positives and file-lock errors on Windows.
for stale_path in [
    apk_path,
    os.path.join(APP_DIR, "app", "build"),
    os.path.join(APP_DIR, "build"),
]:
    if os.path.exists(stale_path):
        try:
            if os.path.isdir(stale_path):
                for root, dirs, files in os.walk(stale_path, topdown=False):
                    for name in files:
                        try:
                            os.chmod(os.path.join(root, name), 0o666)
                        except Exception:
                            pass
                    for name in dirs:
                        try:
                            os.chmod(os.path.join(root, name), 0o777)
                        except Exception:
                            pass
                os.system(f'cmd /c rmdir /s /q "{stale_path}"')
            else:
                os.remove(stale_path)
            print(f"🗑️ Removed stale build artifact: {stale_path}")
        except Exception as e:
            print(f"⚠️ Could not remove stale artifact {stale_path}: {e}")

# Stop Gradle daemon to release file locks
clean_cmd = [GRADLE_BAT, "--stop"]
subprocess.run(clean_cmd, cwd=APP_DIR, env=env)
time.sleep(2)

# Run assembleDebug
build_cmd = [GRADLE_BAT, "--no-daemon", "assembleDebug", "--stacktrace"]
print("\n🔨 Compiling Android APK...")
result = subprocess.run(build_cmd, cwd=APP_DIR, env=env)

build_gradle_apk = os.path.expanduser(r"~/.gradle_builds/nayagi/app/outputs/apk/debug/NANOVA_INFOTECH.apk")
target_apk_root = os.path.join(os.path.dirname(APP_DIR), "NANOVA_INFOTECH.apk")

if result.returncode == 0 and os.path.exists(build_gradle_apk):
    import shutil
    shutil.copy(build_gradle_apk, target_apk_root)
    shutil.copy(build_gradle_apk, os.path.join(APP_DIR, "NANOVA_INFOTECH.apk"))
    print("\n===================================================")
    print("🎉 SUCCESS! YOUR ANDROID APK IS READY AT:")
    print("📍 Root Directory:", target_apk_root)
    print("📍 Android App Directory:", os.path.join(APP_DIR, "NANOVA_INFOTECH.apk"))
    print("===================================================")
elif result.returncode == 0 and os.path.exists(apk_path):
    print("\n===================================================")
    print("🎉 SUCCESS! YOUR ANDROID APK IS READY AT:")
    print(apk_path)
    print("===================================================")
else:
    print("\n❌ Build failed with return code:", result.returncode)
