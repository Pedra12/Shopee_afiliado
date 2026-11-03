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
            install("httpx==0.28.1")
            install("jsonschema==4.25.1")
            install("starlette==1.7.0")
            install("uvicorn==0.38.0")
            install("python-dotenv==1.2.3")
            install("trendspyg==1.9.0")
        }
    }
    sourceSets {
        getByName("main").python.srcDir("../..")
        getByName("main").python.srcDir("../../vendor/shopee-br-affiliate-mcp/src")
    }
}
dependencies {
    implementation("androidx.core:core-ktx:1.17.0")
    implementation("androidx.appcompat:appcompat:1.7.1")
    implementation("com.google.android.material:material:1.13.0")
}
