package com.nanova.infotech

import android.annotation.SuppressLint
import android.content.Intent
import android.graphics.Bitmap
import android.net.Uri
import android.os.Bundle
import android.view.KeyEvent
import android.view.View
import android.webkit.*
import android.widget.ProgressBar
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var progressBar: ProgressBar
    private var filePathCallback: ValueCallback<Array<Uri>>? = null

    // Nanova Infotech Vercel Production URL & Local Fallback
    private val PORTAL_URL = "https://nayagi-incubation-project.vercel.app/"

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContentView(createLayoutView())

        setupWebView()
        setupSwipeRefresh()

        webView.loadUrl(PORTAL_URL)
    }

    private fun createLayoutView(): View {
        val constraintLayout = androidx.constraintlayout.widget.ConstraintLayout(this)
        constraintLayout.layoutParams = android.view.ViewGroup.LayoutParams(
            android.view.ViewGroup.LayoutParams.MATCH_PARENT,
            android.view.ViewGroup.LayoutParams.MATCH_PARENT
        )

        swipeRefresh = SwipeRefreshLayout(this).apply {
            id = View.generateViewId()
            layoutParams = androidx.constraintlayout.widget.ConstraintLayout.LayoutParams(
                androidx.constraintlayout.widget.ConstraintLayout.LayoutParams.MATCH_PARENT,
                androidx.constraintlayout.widget.ConstraintLayout.LayoutParams.MATCH_PARENT
            )
        }

        webView = WebView(this).apply {
            id = View.generateViewId()
            layoutParams = android.view.ViewGroup.LayoutParams(
                android.view.ViewGroup.LayoutParams.MATCH_PARENT,
                android.view.ViewGroup.LayoutParams.MATCH_PARENT
            )
        }

        progressBar = ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal).apply {
            id = View.generateViewId()
            visibility = View.GONE
            max = 100
        }

        swipeRefresh.addView(webView)
        constraintLayout.addView(swipeRefresh)
        constraintLayout.addView(progressBar)

        return constraintLayout
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        val settings: WebSettings = webView.settings
        settings.javaScriptEnabled = true
        settings.domStorageEnabled = true
        settings.databaseEnabled = true
        settings.allowFileAccess = true
        settings.allowContentAccess = true
        settings.loadWithOverviewMode = true
        settings.useWideViewPort = true
        settings.builtInZoomControls = false
        settings.setSupportZoom(false)
        settings.userAgentString = settings.userAgentString + " NanovaInfotechAndroidApp"

        webView.webViewClient = object : WebViewClient() {
            override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) {
                super.onPageStarted(view, url, favicon)
                progressBar.visibility = View.VISIBLE
            }

            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                progressBar.visibility = View.GONE
                swipeRefresh.isRefreshing = false
            }

            override fun onReceivedError(
                view: WebView?,
                errorCode: Int,
                description: String?,
                failingUrl: String?
            ) {
                super.onReceivedError(view, errorCode, description, failingUrl)
                Toast.makeText(this@MainActivity, "Connection Error: $description", Toast.LENGTH_SHORT).show()
            }
        }

        webView.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView?, newProgress: Int) {
                progressBar.progress = newProgress
                if (newProgress == 100) {
                    progressBar.visibility = View.GONE
                } else {
                    progressBar.visibility = View.VISIBLE
                }
            }

            override fun onShowFileChooser(
                webView: WebView?,
                filePathCallback: ValueCallback<Array<Uri>>?,
                fileChooserParams: FileChooserParams?
            ): Boolean {
                this@MainActivity.filePathCallback?.onReceiveValue(null)
                this@MainActivity.filePathCallback = filePathCallback

                val intent = Intent(Intent.ACTION_GET_CONTENT).apply {
                    addCategory(Intent.CATEGORY_OPENABLE)
                    type = "*/*"
                }

                try {
                    startActivityForResult(Intent.createChooser(intent, "Select File"), 1001)
                } catch (e: Exception) {
                    this@MainActivity.filePathCallback = null
                    return false
                }
                return true
            }
        }
    }

    private fun setupSwipeRefresh() {
        swipeRefresh.setOnRefreshListener {
            webView.reload()
        }
    }

    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        if (keyCode == KeyEvent.KEYCODE_BACK && webView.canGoBack()) {
            webView.goBack()
            return true
        }
        return super.onKeyDown(keyCode, event)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == 1001) {
            if (filePathCallback != null) {
                val results = if (resultCode == RESULT_OK && data != null) {
                    val dataString = data.dataString
                    if (dataString != null) {
                        arrayOf(Uri.parse(dataString))
                    } else null
                } else null

                filePathCallback?.onReceiveValue(results)
                filePathCallback = null
            }
        }
    }
}
