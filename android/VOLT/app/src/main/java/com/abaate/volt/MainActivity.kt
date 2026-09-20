package com.abaate.volt

import android.content.*
import android.os.Bundle
import android.speech.*
import android.speech.tts.TextToSpeech
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.*
import okhttp3.*
import org.json.JSONObject
import java.util.*

class MainActivity : ComponentActivity(), TextToSpeech.OnInitListener {
 private val client=OkHttpClient(); private var socket: WebSocket?=null; private var tts: TextToSpeech?=null
 override fun onCreate(state: Bundle?) { super.onCreate(state); tts=TextToSpeech(this,this); setContent { VoltApp() } }
 override fun onInit(status:Int) { if(status==TextToSpeech.SUCCESS) tts?.language=Locale.getDefault() }
 override fun onDestroy(){ socket?.close(1000,"closed"); tts?.shutdown(); super.onDestroy() }
 private fun connect(host:String,token:String,device:String,session:String,onEvent:(String)->Unit){
  val url="${host.trimEnd('/')}/ws?token=${Uri.encode(token)}&device_id=${Uri.encode(device)}&session_id=${Uri.encode(session)}".replace("http://","ws://").replace("https://","wss://")
  socket=client.newWebSocket(Request.Builder().url(url).build(),object:WebSocketListener(){ override fun onOpen(w:WebSocket,r:Response){onEvent("connected")}; override fun onMessage(w:WebSocket,text:String){onEvent(text)}; override fun onFailure(w:WebSocket,t:Throwable,r:Response?){onEvent("error: ${t.message}")} })
 }
 @Composable fun VoltApp(){ var host by remember{mutableStateOf("http://10.0.2.2:8080")}; var token by remember{mutableStateOf("")}; var input by remember{mutableStateOf("")}; var output by remember{mutableStateOf("")}; var connected by remember{mutableStateOf(false)}
  MaterialTheme { Column(Modifier.padding(20.dp).fillMaxSize()){ Text("VOLT",style=MaterialTheme.typography.headlineLarge); Text(if(connected) "● connected" else "○ offline"); TextField(host,{host=it},label={Text("Server")}); TextField(token,{token=it},label={Text("Token")}); Button({connect(host,token,"android-phone","default"){e-> if(e=="connected")connected=true else { try{val j=JSONObject(e); if(j.optString("type")=="token")output+=j.optString("content") else if(j.optString("type")=="message_end")tts?.speak(output,TextToSpeech.QUEUE_FLUSH,null,"volt")}catch(_:Exception){} } }},{enabled=!connected}){Text("Connect")}; Text(output); TextField(input,{input=it},label={Text("Message")}); Button({socket?.send(JSONObject(mapOf("prompt" to input,"session_id" to "default","device_id" to "android-phone")).toString()); input=""}){Text("Send")}; Button({listen{recognized->input=recognized}}){Text("🎤 Speak")}; }
 }
 private fun listen(done:(String)->Unit){ val r=SpeechRecognizer.createSpeechRecognizer(this); val i=Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM); r.setRecognitionListener(object:RecognitionListener{override fun onResults(b:Bundle){done(b.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull()?:"");r.destroy()}; override fun onError(e:Int){r.destroy()}; override fun onReadyForSpeech(p:Bundle?){};override fun onBeginningOfSpeech(){};override fun onRmsChanged(v:Float){};override fun onBufferReceived(b:ByteArray?){};override fun onEndOfSpeech(){};override fun onPartialResults(b:Bundle?){};override fun onEvent(a:Int,b:Bundle?){} }); r.startListening(i) }
}
