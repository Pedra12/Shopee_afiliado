plugins { id("com.android.application"); id("org.jetbrains.kotlin.android"); id("com.chaquo.python") }
android {
    namespace = "br.com.shopeeafiliado"
    compileSdk = 36
    defaultConfig {
        applicationId = "br.com.shopeeafiliado"
        minSdk = 24
        targetSdk = 35
        versionCode = 1
        versionName = "1.0.0"
        ndk { abiFilters += listOf("arm64-v8a", "armeabi-v7a") }
    }
}
chaquopy {
    defaultConfig {
        version = "3.11"
        buildPython("3.11")
        pip {
            install("-r", "../../vendor/shopee-br-affiliate-mcp/requirements.lock")
            install("trendspyg==1.9.0")
        }
    }
    sourceSets { getByName("main").python.srcDir("../..") }
}
dependencies {
    implementation("androidx.core:core-ktx:1.17.0")
    implementation("androidx.appcompat:appcompat:1.7.1")
    implementation("com.google.android.material:material:1.13.0")
}
