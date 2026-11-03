package br.com.shopeeafiliado

import android.app.Activity
import android.app.AlertDialog
import android.app.DownloadManager
import android.content.Context
import android.net.Uri
import android.os.Bundle
import android.os.Environment
import android.view.Gravity
import android.view.View
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import org.json.JSONArray
import java.io.File

class MainActivity : Activity() {
    private lateinit var web: WebView
    private lateinit var detectButton: Button
    private var serverStarted = false
    private val prefs by lazy { getSharedPreferences("shopee_local_config", Context.MODE_PRIVATE) }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = android.graphics.Color.rgb(11, 16, 32)
        window.navigationBarColor = android.graphics.Color.rgb(11, 16, 32)
        buildLayout()
        if (prefs.getBoolean("configured", false)) startLocalApp() else showConfig()
    }

    private fun buildLayout() {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(0xFF0B1020.toInt())
        }
        val top = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(8, 4, 8, 4)
        }
        val title = TextView(this).apply {
            text = "SHOPEE GARIMPO"
            textSize = 15f
            setTextColor(0xFFFFFFFF.toInt())
            setPadding(8, 0, 4, 0)
        }
        detectButton = Button(this).apply {
            text = "Detectar vídeo"
            visibility = View.GONE
            setOnClickListener { detectVideos() }
        }
        val apiButton = Button(this).apply {
            text = "API"
            setOnClickListener { showConfig() }
        }
        top.addView(title, LinearLayout.LayoutParams(0, -2, 1f))
        top.addView(detectButton)
        top.addView(apiButton)

        web = WebView(this).apply {
            this.settings.javaScriptEnabled = true
            this.settings.domStorageEnabled = true
            this.settings.javaScriptCanOpenWindowsAutomatically = false
            this.settings.setSupportMultipleWindows(false)
            webChromeClient = WebChromeClient()
            addJavascriptInterface(VideoBridge(), "ShopeeNative")
            webViewClient = object : WebViewClient() {
                override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                    val uri = request.url
                    val host = uri.host ?: return true
                    if (uri.scheme == "http" && host == "127.0.0.1") return false
                    if (uri.scheme == "https" && (host == "shopee.com.br" || host.endsWith(".shopee.com.br"))) {
                        view.loadUrl(uri.toString())
                        return true
                    }
                    Toast.makeText(this@MainActivity, "Este link não é aberto dentro do aplicativo.", Toast.LENGTH_SHORT).show()
                    return true
                }

                override fun onPageFinished(view: WebView, url: String) {
                    detectButton.visibility = if (url.contains("shopee.com.br")) View.VISIBLE else View.GONE
                }
            }
        }
        root.addView(top)
        root.addView(web, LinearLayout.LayoutParams(-1, 0, 1f))
        setContentView(root)
    }

    private fun showConfig() {
        val fields = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(24, 8, 24, 0)
        }
        fun addField(label: String, value: String, secret: Boolean = false): EditText {
            val input = EditText(this).apply {
                hint = label
                setSingleLine(true)
                setText(value)
                if (secret) inputType = android.text.InputType.TYPE_CLASS_TEXT or android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD
            }
            fields.addView(input)
            return input
        }
        val appId = addField("Shopee App ID", prefs.getString("app_id", "") ?: "")
        val appSecret = addField("Shopee App Secret", prefs.getString("app_secret", "") ?: "", true)
        val account = addField("Referência da conta", prefs.getString("account", "") ?: "")
        AlertDialog.Builder(this)
            .setTitle("Configurar API Shopee")
            .setMessage("As credenciais ficam no armazenamento privado deste aparelho. Sem credenciais, o painel abre em modo de demonstração.")
            .setView(fields)
            .setPositiveButton("Salvar e abrir") { _, _ ->
                prefs.edit()
                    .putString("app_id", appId.text.toString().trim())
                    .putString("app_secret", appSecret.text.toString())
                    .putString("account", account.text.toString().trim())
                    .putBoolean("configured", true)
                    .apply()
                startLocalApp()
            }
            .setNegativeButton("Cancelar") { _, _ -> if (!serverStarted) finish() }
            .show()
    }

    private fun startLocalApp() {
        if (serverStarted) {
            web.loadUrl("http://127.0.0.1:5000")
            return
        }
        try {
            val appFiles = File(filesDir, "shopee").apply { mkdirs() }
            val template = File(appFiles, "index.html")
            assets.open("index.html").use { input ->
                template.outputStream().use { output -> input.copyTo(output) }
            }
            val profile = File(appFiles, "profile.official.json")
            assets.open("profile.official.json").use { input ->
                profile.outputStream().use { output -> input.copyTo(output) }
            }
            if (!Python.isStarted()) Python.start(AndroidPlatform(this))
            Python.getInstance().getModule("mobile_server").callAttr(
                "start_server",
                prefs.getString("app_id", "") ?: "",
                prefs.getString("app_secret", "") ?: "",
                prefs.getString("account", "") ?: "",
                appFiles.absolutePath,
                template.absolutePath
            )
            serverStarted = true
            web.postDelayed({ web.loadUrl("http://127.0.0.1:5000") }, 350)
        } catch (error: Exception) {
            AlertDialog.Builder(this)
                .setTitle("Não foi possível iniciar")
                .setMessage(error.message ?: "Falha ao iniciar o serviço local.")
                .setPositiveButton("Tentar novamente") { _, _ -> startLocalApp() }
                .show()
        }
    }

    private fun detectVideos() {
        val script = """
            (function() {
              const found = new Set();
              document.querySelectorAll('video').forEach(v => {
                const u = v.currentSrc || v.src;
                if (u && /^https:/.test(u) && /\.mp4([?#]|$)/i.test(u)) found.add(u);
              });
              document.querySelectorAll('script:not([src])').forEach(s => {
                const t = s.textContent || '';
                const re = /https?:\\?\/\\?\/[^"'\s]*?vod\.susercontent\.com[^"'\s]*?\.mp4[^"'\s]*/gi;
                let m;
                while ((m = re.exec(t)) !== null) {
                  found.add(m[0].replaceAll('\\/', '/').replaceAll('\\u0026', '&'));
                }
              });
              window.ShopeeNative.onVideos(JSON.stringify(Array.from(found)));
            })();
        """.trimIndent()
        web.evaluateJavascript(script, null)
    }

    inner class VideoBridge {
        @JavascriptInterface
        fun onVideos(json: String) {
            runOnUiThread {
                val urls = JSONArray(json)
                if (urls.length() == 0) {
                    Toast.makeText(this@MainActivity, "Nenhum vídeo MP4 detectado nesta página.", Toast.LENGTH_LONG).show()
                    return@runOnUiThread
                }
                val choices = Array(urls.length()) { index -> "Vídeo ${index + 1}" }
                AlertDialog.Builder(this@MainActivity)
                    .setTitle("Vídeos encontrados")
                    .setItems(choices) { _, selected -> downloadVideo(urls.getString(selected)) }
                    .setNegativeButton("Cancelar", null)
                    .show()
            }
        }
    }

    private fun downloadVideo(url: String) {
        val uri = Uri.parse(url)
        val host = uri.host ?: ""
        val validHost = host == "susercontent.com" || host.endsWith(".susercontent.com")
        if (uri.scheme != "https" || !validHost || !uri.toString().contains(".mp4")) {
            Toast.makeText(this, "Endereço de vídeo não reconhecido.", Toast.LENGTH_LONG).show()
            return
        }
        try {
            val request = DownloadManager.Request(uri)
                .setTitle("Vídeo de produto")
                .setDescription("Download iniciado manualmente")
                .setMimeType("video/mp4")
                .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                .setDestinationInExternalPublicDir(
                    Environment.DIRECTORY_DOWNLOADS,
                    "ShopeeVideos/video_${System.currentTimeMillis()}.mp4"
                )
                .setAllowedOverMetered(true)
                .setAllowedOverRoaming(false)
            (getSystemService(DOWNLOAD_SERVICE) as DownloadManager).enqueue(request)
            Toast.makeText(this, "Download iniciado. Confira Downloads/ShopeeVideos.", Toast.LENGTH_LONG).show()
        } catch (error: Exception) {
            Toast.makeText(this, "Falha no download: ${error.message}", Toast.LENGTH_LONG).show()
        }
    }

    @Suppress("DEPRECATION")
    override fun onBackPressed() {
        if (::web.isInitialized && web.canGoBack()) web.goBack() else super.onBackPressed()
    }
}
