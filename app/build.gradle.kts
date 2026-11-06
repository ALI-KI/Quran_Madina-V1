plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}
android {
    namespace = "com.mahmoudelgamsy.madinaquran"
    compileSdk = 35
    defaultConfig {
        applicationId = "com.mahmoudelgamsy.madinaquran"
        minSdk = 26
        targetSdk = 35
        versionCode = 3
        versionName = "0.3.0-dev"
    }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
    buildTypes { release { isMinifyEnabled = false } }
}
