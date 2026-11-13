package com.mahmoudelgamsy.madinaquran

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.WindowInsets
import android.view.WindowManager
import android.view.View
import android.webkit.JavascriptInterface
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import java.io.File
import java.io.FileInputStream
import java.io.FilterInputStream
import java.io.InputStream
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors
import java.util.concurrent.ConcurrentHashMap

/**
 * Self-contained Quran reader web UI bundled with Android.
 * The native bridge downloads surah audio verse-by-verse into private app storage.
 * All application HTML/JS is served from the trusted https://app.local origin.
 * No Quran verse text is generated in code.
 */
class MainActivity : Activity() {
    private lateinit var browser: WebView
    private val workers = Executors.newSingleThreadExecutor()
    private val mainHandler = Handler(Looper.getMainLooper())
    private val activeDownloads = ConcurrentHashMap.newKeySet<String>()
    private val verseCount = intArrayOf(
        7,286,200,176,120,165,206,75,129,109,123,111,43,52,99,128,111,110,98,135,
        112,78,118,64,77,227,93,88,69,60,34,30,73,54,45,83,182,88,75,85,
        54,53,89,59,37,35,38,29,18,45,60,49,62,55,78,96,29,22,24,13,
        14,11,11,18,12,12,30,52,52,44,28,28,20,56,40,31,50,40,46,42,
        29,19,36,25,22,17,19,26,30,20,15,21,11,8,8,19,5,8,8,11,
        11,8,3,9,5,4,7,3,6,3,5,4,5,6
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        browser = WebView(this)
        browser.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = false
            allowContentAccess = false
            mediaPlaybackRequiresUserGesture = true
            setSupportZoom(false)
        }
        browser.addJavascriptInterface(QuranAudioBridge(), "AndroidBridge")
        browser.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val uri = request.url
                if (uri.host == "app.local" && uri.scheme == "https") return false
                if (request.isForMainFrame) {
                    try { startActivity(Intent(Intent.ACTION_VIEW, uri)) } catch (_: Exception) { }
                    return true
                }
                return false // allow mp3 network streaming by the HTML media element
            }
            override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest): WebResourceResponse? {
                val u = request.url
                if (u.scheme != "https" || u.host != "app.local") return null
                val path = u.path?.removePrefix("/")?.ifEmpty { "index.html" } ?: "index.html"
                if (path.startsWith("audio/") && path.endsWith(".mp3")) {
                    val rel = path.removePrefix("audio/")
                    val parts = rel.split("/")
                    if (parts.size != 2) return notFound()
                    val source = audioSources[parts[0]] ?: return notFound()
                    val filename = parts[1]
                    val matcher = if (source.second) Regex("[0-9]{3}\\.mp3") else Regex("[0-9]{6}\\.mp3")
                    if (!matcher.matches(filename)) return notFound()
                    val file = File(audioDir(parts[0]), filename)
                    if (!file.isFile) return notFound()
                    return serveAudio(file, request)
                }
                if (path.contains("..") || path.startsWith("/") || path.contains('\\')) return notFound()
                return try {
                    val mime = when {
                        path.endsWith(".js") -> "application/javascript"
                        path.endsWith(".css") -> "text/css"
                        path.endsWith(".ttf") -> "font/ttf"
                        path.endsWith(".svg") -> "image/svg+xml"
                        path.endsWith(".png") -> "image/png"
                        path.endsWith(".webp") -> "image/webp"
                        else -> "text/html"
                    }
                    WebResourceResponse(mime, if (path.endsWith(".ttf") || path.endsWith(".png") || path.endsWith(".webp")) null else "UTF-8", assets.open(path))
                } catch (_: Exception) { notFound() }
            }
        }
        setContentView(browser)
        hideTopStatusBar()
        browser.loadUrl("https://app.local/index.html")
    }

    @Suppress("DEPRECATION")
    private fun hideTopStatusBar() {
        // Android 15 enforces edge-to-edge at targetSdk 35. Explicitly hide the
        // phone status bar, rather than drawing the Mushaf below its icons.
        window.setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN, WindowManager.LayoutParams.FLAG_FULLSCREEN)
        if (android.os.Build.VERSION.SDK_INT >= 30) {
            window.decorView.windowInsetsController?.hide(WindowInsets.Type.statusBars())
        } else {
            window.decorView.systemUiVisibility = View.SYSTEM_UI_FLAG_FULLSCREEN
        }
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) hideTopStatusBar()
    }

    private fun notFound() = WebResourceResponse("text/plain", "UTF-8", 404, "Not Found", mapOf(), "Not found".byteInputStream())
    // IDs and hosts are strict allowlists. Never accept a URL from the JavaScript bridge.
    // Boolean means whole-surah recording rather than verse-by-verse.
    private val audioSources = mapOf(
        "minshawy" to Pair("https://everyayah.com/data/Minshawy_Murattal_128kbps/",false),
        "husary" to Pair("https://everyayah.com/data/Husary_128kbps/",false),
        "sudais" to Pair("https://everyayah.com/data/Abdurrahmaan_As-Sudais_192kbps/",false),
        "afasy" to Pair("https://everyayah.com/data/Alafasy_128kbps/",false),
        "ghamdi" to Pair("https://everyayah.com/data/Ghamadi_40kbps/",false),
        "maher" to Pair("https://everyayah.com/data/MaherAlMuaiqly128kbps/",false),
        "ali" to Pair("https://everyayah.com/data/Ali_Jaber_64kbps/",false),
        "arkani" to Pair("https://cdn.mp3quran.net/audio/abdulwali-arkani/r1/",true)
    )
    private fun audioDir(reciter: String) = File(filesDir, "audio/$reciter").apply { mkdirs() }
    private fun audioFile(reciter: String, surah: Int, ayah: Int): File {
        val wholeSurah = audioSources[reciter]?.second == true
        val name = if (wholeSurah) "%03d.mp3".format(java.util.Locale.US,surah)
                   else "%03d%03d.mp3".format(java.util.Locale.US,surah,ayah)
        return File(audioDir(reciter),name)
    }

    private fun serveAudio(file: File, request: WebResourceRequest): WebResourceResponse {
        val length = file.length()
        val range = request.requestHeaders["Range"]
        val start = range?.let { Regex("bytes=(\\d+)-").find(it)?.groupValues?.get(1)?.toLongOrNull() } ?: 0L
        if (start >= length) return WebResourceResponse("text/plain", "UTF-8", 416,"Range Not Satisfiable",mapOf("Content-Range" to "bytes */$length"),"".byteInputStream())
        val remaining = length-start
        val input = FileInputStream(file).also { it.channel.position(start) }
        val headers = mapOf("Accept-Ranges" to "bytes", "Content-Length" to remaining.toString(), "Content-Range" to "bytes $start-${length-1}/$length", "Access-Control-Allow-Origin" to "https://app.local")
        return WebResourceResponse("audio/mpeg", null, if (start > 0L) 206 else 200, if (start>0L) "Partial Content" else "OK", headers, input)
    }

    private inner class QuranAudioBridge {
        @JavascriptInterface fun hasAudio(reciter: String, surah: Int, ayah: Int): Boolean =
            audioSources.containsKey(reciter) && surah in 1..114 &&
            ayah in 1..verseCount[surah - 1] && audioFile(reciter,surah,ayah).length() > 1024

        @JavascriptInterface fun downloadSurah(reciter: String, surah: Int) {
            val info = audioSources[reciter] ?: return
            if (surah !in 1..114) return
            val key = "$reciter:$surah"
            if (!activeDownloads.add(key)) return
            workers.execute {
                var done = 0
                var failed = 0
                val total = if (info.second) 1 else verseCount[surah - 1]
                try {
                    for (ayah in 1..total) {
                        if (!hasAudio(reciter, surah, ayah) && !downloadAudio(reciter, surah, ayah)) failed++
                        done++
                        if (done % 3 == 0 || done == total) {
                            val script = "window.onNativeDownloadProgress?.('$reciter',$surah,$done,$total);"
                            mainHandler.post { browser.evaluateJavascript(script, null) }
                        }
                    }
                } finally {
                    activeDownloads.remove(key)
                    mainHandler.post { browser.evaluateJavascript("window.onNativeDownloadCompleted?.('$reciter',$surah,$failed);",null) }
                }
            }
        }

        private fun downloadAudio(reciter: String, surah: Int, ayah: Int): Boolean {
            val source = audioSources[reciter] ?: return false
            val target = audioFile(reciter,surah,ayah)
            val temp = File(audioDir(reciter),target.name + ".part")
            return try {
                val url = URL(source.first + target.name)
                val conn = (url.openConnection() as HttpURLConnection).apply {
                    connectTimeout = 15000; readTimeout = 40000
                    instanceFollowRedirects = true
                    setRequestProperty("User-Agent", "MadinaQuran/0.7 (Android)")
                }
                try {
                    if (conn.responseCode !in 200..299) return false
                    // Prevent an accidental HTML error response being accepted as audio.
                    val contentType = conn.contentType ?: ""
                    if (contentType.contains("html",ignoreCase=true)) return false
                    conn.inputStream.use { input -> temp.outputStream().use { output -> input.copyTo(output) } }
                    if (temp.length() < 1024) return false
                    if (!temp.renameTo(target)) temp.copyTo(target,overwrite=true)
                    target.length() > 1024
                } finally { conn.disconnect();temp.delete() }
            } catch (_: Exception) { temp.delete();false }
        }
    }
    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (browser.canGoBack()) browser.goBack() else super.onBackPressed()
    }
    override fun onDestroy() {workers.shutdownNow();browser.destroy();super.onDestroy()}
}
