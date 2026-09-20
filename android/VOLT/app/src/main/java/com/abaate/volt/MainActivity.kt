package com.abaate.volt

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.*
import androidx.compose.runtime.*

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) { super.onCreate(savedInstanceState); setContent { VoltScreen() } }
}
@Composable fun VoltScreen() {
    var text by remember { mutableStateOf("") }
    MaterialTheme { Surface { Text("VOLT\n\nPC connection configured in Settings\n\n$text") } }
}
