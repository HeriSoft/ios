package com.herisoft.caloriescan

import android.content.Context
import android.net.Uri
import androidx.core.content.FileProvider
import com.google.android.gms.tasks.Task
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.label.ImageLabeling
import com.google.mlkit.vision.label.defaults.ImageLabelerOptions
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import com.herisoft.caloriescan.core.OpenFoodFacts
import com.herisoft.caloriescan.core.ProductInfo
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

class LookupException(message: String) : Exception(message)

/** Tra cứu sản phẩm trên Open Food Facts. Trả về null nếu không tìm thấy. */
suspend fun lookupProduct(barcode: String): ProductInfo? = withContext(Dispatchers.IO) {
    val url = OpenFoodFacts.url(barcode) ?: throw LookupException("Mã vạch không hợp lệ.")
    val connection = (URL(url).openConnection() as HttpURLConnection).apply {
        connectTimeout = 15_000
        readTimeout = 15_000
        setRequestProperty("User-Agent", "CalorieScan-Android/0.1")
    }
    try {
        when (val code = connection.responseCode) {
            404 -> null
            in 200..299 -> OpenFoodFacts.parse(connection.inputStream.bufferedReader().readText(), barcode)
            else -> throw LookupException("Máy chủ trả về lỗi ($code). Vui lòng thử lại.")
        }
    } finally {
        connection.disconnect()
    }
}

/** Chờ một Task của Google Play services / ML Kit trong coroutine. */
suspend fun <T> Task<T>.await(): T = suspendCancellableCoroutine { cont ->
    addOnSuccessListener { cont.resume(it) }
    addOnFailureListener { cont.resumeWithException(it) }
}

/** Đọc chữ trên ảnh (OCR) — chạy trên máy. */
suspend fun recognizeTextLines(context: Context, uri: Uri): List<String> {
    val image = InputImage.fromFilePath(context, uri)
    val recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
    return try {
        recognizer.process(image).await().textBlocks.flatMap { block -> block.lines.map { it.text } }
    } finally {
        recognizer.close()
    }
}

/** Gắn nhãn nội dung ảnh (ví dụ "Food", "Pizza") — chạy trên máy. */
suspend fun labelImage(context: Context, uri: Uri): List<Pair<String, Float>> {
    val image = InputImage.fromFilePath(context, uri)
    val labeler = ImageLabeling.getClient(ImageLabelerOptions.Builder().setConfidenceThreshold(0.2f).build())
    return try {
        labeler.process(image).await().map { it.text to it.confidence }
    } finally {
        labeler.close()
    }
}

/** Tạo file tạm để camera hệ thống lưu ảnh chụp. */
fun createImageUri(context: Context): Uri {
    val dir = File(context.cacheDir, "images").apply { mkdirs() }
    val file = File.createTempFile("photo_", ".jpg", dir)
    return FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
}
