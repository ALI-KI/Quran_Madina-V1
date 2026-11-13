plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

// The CI supplies an increasing versionCode; ordinary local builds retain a safe default.
// Never regenerate the signing key in CI. The user-owned keystore is restored from GitHub Secrets.
android {
    namespace = "com.mahmoudelgamsy.madinaquran"
    compileSdk = 35
    defaultConfig {
        applicationId = "com.mahmoudelgamsy.madinaquran"
        minSdk = 26
        targetSdk = 35
        versionCode = providers.gradleProperty("appVersionCode").orNull?.toIntOrNull() ?: 7
        versionName = providers.gradleProperty("appVersionName").orNull ?: "0.7.0-dev"
    }
    signingConfigs {
        create("production") {
            val keystorePath = System.getenv("QURAN_SIGNING_KEYSTORE_PATH")
            if (!keystorePath.isNullOrBlank()) {
                storeFile = file(keystorePath)
                storePassword = System.getenv("QURAN_SIGNING_STORE_PASSWORD")
                keyAlias = System.getenv("QURAN_SIGNING_KEY_ALIAS")
                keyPassword = System.getenv("QURAN_SIGNING_KEY_PASSWORD")
            }
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
    buildTypes {
        getByName("release") {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("production")
        }
    }
}
