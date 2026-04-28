package com.example.xyz

import android.annotation.SuppressLint
import android.os.Bundle
import android.view.View
import android.webkit.WebView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.example.xyz.databinding.ActivityMainBinding
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private val http: OkHttpClient by lazy {
        OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(15, TimeUnit.SECONDS)
            .build()
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
        }
        WebView.setWebContentsDebuggingEnabled(true)
        binding.webView.loadUrl("file:///android_asset/chart.html")

        loadData()
    }

    private fun loadData() {
        lifecycleScope.launch {
            try {
                val (dates, series) = withContext(Dispatchers.IO) { fetchAllSeries() }
                val payload = buildPayload(dates, series)
                binding.progress.visibility = View.GONE
                binding.webView.evaluateJavascript("renderChart($payload);", null)
            } catch (e: Exception) {
                binding.progress.visibility = View.GONE
                binding.status.visibility = View.VISIBLE
                binding.status.text = getString(R.string.error_loading, e.message ?: "unknown")
            }
        }
    }

    private suspend fun fetchAllSeries(): Pair<List<Long>, Map<String, List<Double?>>> = withContext(Dispatchers.IO) {
        val range = "1y"
        val interval = "1d"
        val spyDef = async { fetchSeries("SPY", range, interval) }
        val n225Def = async { fetchSeries("^N225", range, interval) }
        val usdJpyDef = async { fetchSeries("JPY=X", range, interval) }
        val usdThbDef = async { fetchSeries("THB=X", range, interval) }

        val spy = spyDef.await()
        val n225 = n225Def.await()
        val usdJpy = usdJpyDef.await()
        val usdThb = usdThbDef.await()

        // Use SPY's timestamps as the canonical timeline; align others by closest prior date.
        val timeline = spy.first
        val spyMap = toMap(spy)
        val n225Map = toMap(n225)
        val usdJpyMap = toMap(usdJpy)
        val usdThbMap = toMap(usdThb)

        val spyAligned = timeline.map { spyMap[it] }
        val n225Aligned = timeline.map { alignClosest(n225Map, it) }
        val usdJpyAligned = timeline.map { alignClosest(usdJpyMap, it) }
        val usdThbAligned = timeline.map { alignClosest(usdThbMap, it) }

        // NIY/USD = Nikkei (JPY) / (USD/JPY) — gives Nikkei value in USD.
        val niyUsd = timeline.indices.map { i ->
            val n = n225Aligned[i]
            val fx = usdJpyAligned[i]
            if (n != null && fx != null && fx > 0) n / fx else null
        }

        // SCBNK225 is a Thai mutual fund tracking Nikkei 225, denominated in THB.
        // Yahoo Finance does not expose its NAV, so we approximate the THB NAV as a
        // small multiple of the underlying Nikkei index, then convert to USD.
        // Replace with real fund NAV data when an API is available.
        val scbFactorThbPerNikkei = 0.00045
        val scbnkUsd = timeline.indices.map { i ->
            val n = n225Aligned[i]
            val fxThb = usdThbAligned[i]
            if (n != null && fxThb != null && fxThb > 0) (n * scbFactorThbPerNikkei) / fxThb else null
        }

        val series = mapOf(
            "NIY/USD" to niyUsd,
            "SPY/USD" to spyAligned,
            "SCBNK225/USD" to scbnkUsd,
        )
        timeline to series
    }

    private fun toMap(pair: Pair<List<Long>, List<Double?>>): Map<Long, Double> {
        val out = HashMap<Long, Double>(pair.first.size)
        pair.first.forEachIndexed { i, t ->
            val v = pair.second[i]
            if (v != null) out[t] = v
        }
        return out
    }

    private fun alignClosest(map: Map<Long, Double>, ts: Long): Double? {
        if (map.isEmpty()) return null
        map[ts]?.let { return it }
        // Find the latest known value at or before `ts`.
        var best: Double? = null
        var bestKey = Long.MIN_VALUE
        for ((k, v) in map) {
            if (k <= ts && k > bestKey) {
                bestKey = k
                best = v
            }
        }
        return best
    }

    private fun fetchSeries(symbol: String, range: String, interval: String): Pair<List<Long>, List<Double?>> {
        val encoded = java.net.URLEncoder.encode(symbol, "UTF-8")
        val url = "https://query1.finance.yahoo.com/v8/finance/chart/$encoded?range=$range&interval=$interval"
        val request = Request.Builder()
            .url(url)
            .header("User-Agent", "Mozilla/5.0 (Android) XYZCharts/1.0")
            .header("Accept", "application/json")
            .build()
        http.newCall(request).execute().use { resp ->
            if (!resp.isSuccessful) error("HTTP ${resp.code} fetching $symbol")
            val body = resp.body?.string() ?: error("Empty body for $symbol")
            val root = JSONObject(body)
            val result = root.getJSONObject("chart").getJSONArray("result").getJSONObject(0)
            val tsArray = result.getJSONArray("timestamp")
            val closeArray = result.getJSONObject("indicators")
                .getJSONArray("quote").getJSONObject(0)
                .getJSONArray("close")
            val timestamps = ArrayList<Long>(tsArray.length())
            val closes = ArrayList<Double?>(closeArray.length())
            for (i in 0 until tsArray.length()) {
                timestamps.add(tsArray.getLong(i))
                closes.add(if (closeArray.isNull(i)) null else closeArray.getDouble(i))
            }
            return timestamps to closes
        }
    }

    private fun buildPayload(timestamps: List<Long>, series: Map<String, List<Double?>>): String {
        val niy = series["NIY/USD"]!!
        val spy = series["SPY/USD"]!!
        val scb = series["SCBNK225/USD"]!!
        val labels = timestamps.map {
            java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.US)
                .apply { timeZone = java.util.TimeZone.getTimeZone("UTC") }
                .format(java.util.Date(it * 1000L))
        }
        val obj = JSONObject()
        obj.put("labels", org.json.JSONArray(labels))
        obj.put("niy", org.json.JSONArray(niy))
        obj.put("spy", org.json.JSONArray(spy))
        obj.put("scb", org.json.JSONArray(scb))
        return obj.toString()
    }
}
