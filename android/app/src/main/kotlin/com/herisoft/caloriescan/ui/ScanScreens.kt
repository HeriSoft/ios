@file:OptIn(ExperimentalMaterial3Api::class)

package com.herisoft.caloriescan.ui

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ExperimentalGetImage
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AddCircle
import androidx.compose.material.icons.filled.ContentCopy
import androidx.compose.material.icons.filled.DocumentScanner
import androidx.compose.material.icons.filled.Inventory2
import androidx.compose.material.icons.filled.Keyboard
import androidx.compose.material.icons.filled.NoPhotography
import androidx.compose.material.icons.filled.OpenInBrowser
import androidx.compose.material.icons.filled.SearchOff
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material.icons.filled.WifiOff
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.navigation.NavHostController
import coil.compose.AsyncImage
import com.google.mlkit.vision.barcode.BarcodeScannerOptions
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.common.InputImage
import com.herisoft.caloriescan.AppViewModel
import com.herisoft.caloriescan.FoodLogEntry
import com.herisoft.caloriescan.core.CalorieCalculator
import com.herisoft.caloriescan.core.NutritionLabelParser
import com.herisoft.caloriescan.core.NutritionLabelResult
import com.herisoft.caloriescan.core.ProductInfo
import com.herisoft.caloriescan.core.ScanPayload
import com.herisoft.caloriescan.core.kcalText
import com.herisoft.caloriescan.core.shortText
import com.herisoft.caloriescan.lookupProduct
import com.herisoft.caloriescan.recognizeTextLines
import kotlinx.coroutines.launch

private val samples = listOf("Nutella" to "3017624010701", "Coca-Cola" to "5449000000996")

@Composable
fun ScanScreen(vm: AppViewModel, nav: NavHostController, active: Boolean) {
    val context = LocalContext.current
    var hasCamera by remember {
        mutableStateOf(ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED)
    }
    val permission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { hasCamera = it }
    var showManual by remember { mutableStateOf(false) }
    var manualCode by remember { mutableStateOf("") }

    fun handle(raw: String) {
        if (nav.currentDestination?.route != "scan") return
        when (val payload = ScanPayload.classify(raw)) {
            is ScanPayload.Barcode -> nav.navigate("lookup/${payload.code}")
            is ScanPayload.Text -> { vm.scannedText = payload.text; nav.navigate("text") }
        }
    }

    Column(Modifier.fillMaxSize()) {
        ScreenTopBar("Quét sản phẩm")
        Column(Modifier.verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Box(
                Modifier.fillMaxWidth().height(320.dp).clip(RoundedCornerShape(20.dp))
                    .background(MaterialTheme.colorScheme.surfaceContainerHigh),
                contentAlignment = Alignment.Center,
            ) {
                if (hasCamera) {
                    BarcodeCamera(active = active, onScan = ::handle, modifier = Modifier.fillMaxSize())
                } else {
                    Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp),
                        modifier = Modifier.padding(16.dp)) {
                        Icon(Icons.Filled.NoPhotography, contentDescription = null, modifier = Modifier.size(44.dp))
                        Text("App cần quyền camera để quét mã vạch", textAlign = TextAlign.Center)
                        Button(onClick = { permission.launch(Manifest.permission.CAMERA) }) { Text("Cho phép camera") }
                    }
                }
            }
            Text("Đưa mã vạch hoặc mã QR trên bao bì vào khung hình để xem lượng calo.",
                style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center, modifier = Modifier.fillMaxWidth())
            Button(onClick = { nav.navigate("label") }, modifier = Modifier.fillMaxWidth()) {
                Icon(Icons.Filled.DocumentScanner, contentDescription = null); Spacer(Modifier.width(8.dp)); Text("Quét nhãn dinh dưỡng")
            }
            OutlinedButton(onClick = { showManual = true }, modifier = Modifier.fillMaxWidth()) {
                Icon(Icons.Filled.Keyboard, contentDescription = null); Spacer(Modifier.width(8.dp)); Text("Nhập mã vạch thủ công")
            }
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Thử mã mẫu:", style = MaterialTheme.typography.bodySmall)
                samples.forEach { (name, code) -> AssistChip(onClick = { handle(code) }, label = { Text(name) }) }
            }
        }
    }

    if (showManual) {
        AlertDialog(
            onDismissRequest = { showManual = false },
            title = { Text("Nhập mã vạch") },
            text = {
                OutlinedTextField(
                    value = manualCode, onValueChange = { manualCode = it.filter(Char::isDigit) },
                    label = { Text("Dãy số dưới mã vạch") }, singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                )
            },
            confirmButton = {
                TextButton(onClick = {
                    showManual = false
                    if (manualCode.isNotEmpty()) nav.navigate("lookup/$manualCode")
                    manualCode = ""
                }) { Text("Tra cứu") }
            },
            dismissButton = { TextButton(onClick = { showManual = false }) { Text("Huỷ") } },
        )
    }
}

/** Camera xem trước + đọc mã vạch/QR liên tục bằng ML Kit. */
@Composable
fun BarcodeCamera(active: Boolean, onScan: (String) -> Unit, modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val currentOnScan by rememberUpdatedState(onScan)
    val isActive = rememberUpdatedState(active)
    val holder = remember { arrayOfNulls<ProcessCameraProvider>(1) }

    DisposableEffect(Unit) {
        onDispose { holder[0]?.unbindAll() }
    }

    AndroidView(modifier = modifier, factory = { ctx ->
        val previewView = PreviewView(ctx)
        val providerFuture = ProcessCameraProvider.getInstance(ctx)
        providerFuture.addListener({
            // Máy không có camera hoặc camera đang bận: bỏ qua, không làm app bị lỗi.
            val provider = runCatching { providerFuture.get() }.getOrNull() ?: return@addListener
            holder[0] = provider
            val preview = Preview.Builder().build()
            preview.setSurfaceProvider(previewView.surfaceProvider)
            val scanner = BarcodeScanning.getClient(
                BarcodeScannerOptions.Builder().setBarcodeFormats(
                    Barcode.FORMAT_QR_CODE, Barcode.FORMAT_EAN_13, Barcode.FORMAT_EAN_8,
                    Barcode.FORMAT_UPC_A, Barcode.FORMAT_UPC_E, Barcode.FORMAT_CODE_128, Barcode.FORMAT_ITF,
                ).build()
            )
            val analysis = ImageAnalysis.Builder()
                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                .build()
            analysis.setAnalyzer(ContextCompat.getMainExecutor(ctx)) { proxy ->
                analyzeFrame(proxy, scanner) { value -> if (isActive.value) currentOnScan(value) }
            }
            runCatching {
                provider.unbindAll()
                provider.bindToLifecycle(lifecycleOwner, CameraSelector.DEFAULT_BACK_CAMERA, preview, analysis)
            }
        }, ContextCompat.getMainExecutor(ctx))
        previewView
    })
}

@androidx.annotation.OptIn(ExperimentalGetImage::class)
private fun analyzeFrame(proxy: ImageProxy, scanner: com.google.mlkit.vision.barcode.BarcodeScanner, onValue: (String) -> Unit) {
    val media = proxy.image
    if (media == null) { proxy.close(); return }
    val image = InputImage.fromMediaImage(media, proxy.imageInfo.rotationDegrees)
    scanner.process(image)
        .addOnSuccessListener { codes -> codes.firstNotNullOfOrNull { it.rawValue?.takeIf(String::isNotEmpty) }?.let(onValue) }
        .addOnCompleteListener { proxy.close() }
}

private sealed class LoadState {
    data object Loading : LoadState()
    data class Found(val product: ProductInfo) : LoadState()
    data object NotFound : LoadState()
    data class Failed(val message: String) : LoadState()
}

@Composable
fun LookupScreen(vm: AppViewModel, nav: NavHostController, code: String) {
    var state by remember { mutableStateOf<LoadState>(LoadState.Loading) }
    var attempt by remember { mutableStateOf(0) }
    LaunchedEffect(code, attempt) {
        state = LoadState.Loading
        state = try {
            lookupProduct(code)?.let { LoadState.Found(it) } ?: LoadState.NotFound
        } catch (e: Exception) {
            LoadState.Failed(e.message ?: "Không kết nối được. Kiểm tra mạng và thử lại.")
        }
    }
    when (val s = state) {
        is LoadState.Found -> ProductDetail(vm, nav, s.product, preferServings = false)
        else -> Column(Modifier.fillMaxSize()) {
            ScreenTopBar("Tra cứu", onBack = { nav.popBackStack() })
            Column(Modifier.fillMaxSize().padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(12.dp, Alignment.CenterVertically)) {
                when (s) {
                    LoadState.Loading -> { CircularProgressIndicator(); Text("Đang tra cứu mã $code…") }
                    LoadState.NotFound -> {
                        Icon(Icons.Filled.SearchOff, contentDescription = null, modifier = Modifier.size(48.dp))
                        Text("Không tìm thấy sản phẩm", style = MaterialTheme.typography.titleLarge)
                        Text("Mã $code chưa có trong cơ sở dữ liệu Open Food Facts. Bạn có thể quét nhãn dinh dưỡng hoặc tự nhập lượng calo.",
                            textAlign = TextAlign.Center)
                        Button(onClick = { nav.navigate("label?code=$code") }) { Text("Quét nhãn dinh dưỡng") }
                        OutlinedButton(onClick = { nav.navigate("manual?code=$code") }) { Text("Nhập thủ công") }
                    }
                    is LoadState.Failed -> {
                        Icon(Icons.Filled.WifiOff, contentDescription = null, modifier = Modifier.size(48.dp))
                        Text("Không tra cứu được", style = MaterialTheme.typography.titleLarge)
                        Text(s.message, textAlign = TextAlign.Center)
                        Button(onClick = { attempt++ }) { Text("Thử lại") }
                        OutlinedButton(onClick = { nav.navigate("manual?code=$code") }) { Text("Nhập thủ công") }
                    }
                    else -> {}
                }
            }
        }
    }
}

@Composable
fun ProductScreen(vm: AppViewModel, nav: NavHostController) {
    val product = vm.selectedProduct
    if (product == null) {
        Column { ScreenTopBar("Sản phẩm", onBack = { nav.popBackStack() }); Text("Chưa chọn sản phẩm", Modifier.padding(16.dp)) }
    } else {
        ProductDetail(vm, nav, product, vm.preferServings)
    }
}

private enum class AmountMode(val title: String) { grams("Gram / ml"), servings("Khẩu phần") }

@Composable
fun ProductDetail(vm: AppViewModel, nav: NavHostController, product: ProductInfo, preferServings: Boolean) {
    val useServings = (preferServings || product.kcalPer100g == null) && product.effectiveKcalPerServing != null
    var mode by remember(product) { mutableStateOf(if (useServings) AmountMode.servings else AmountMode.grams) }
    var amount by remember(product) { mutableStateOf<Double?>(if (useServings) 1.0 else product.servingGrams ?: 100.0) }
    var manualKcal100 by remember(product) { mutableStateOf<Double?>(null) }
    var saved by remember { mutableStateOf(false) }

    val kcal100 = product.kcalPer100g ?: manualKcal100
    val kcalServing = product.effectiveKcalPerServing
        ?: if (kcal100 != null && product.servingGrams != null) CalorieCalculator.kcalPer100g(kcal100, product.servingGrams!!) else null
    val total = amount?.let { a ->
        when (mode) {
            AmountMode.grams -> kcal100?.let { CalorieCalculator.kcalPer100g(it, a) }
            AmountMode.servings -> kcalServing?.let { CalorieCalculator.kcalPerServing(it, a) }
        }
    }

    Column(Modifier.fillMaxSize()) {
        ScreenTopBar(product.name, onBack = { nav.popBackStack() })
        Column(Modifier.verticalScroll(rememberScrollState()).padding(bottom = 16.dp)) {
            SectionCard {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(Modifier.size(72.dp).clip(RoundedCornerShape(12.dp)).background(MaterialTheme.colorScheme.surfaceContainerHigh),
                        contentAlignment = Alignment.Center) {
                        if (product.imageUrl != null) {
                            AsyncImage(model = product.imageUrl, contentDescription = null, contentScale = ContentScale.Fit, modifier = Modifier.fillMaxSize())
                        } else {
                            Icon(Icons.Filled.Inventory2, contentDescription = null)
                        }
                    }
                    Spacer(Modifier.width(14.dp))
                    Column {
                        Text(product.name, style = MaterialTheme.typography.titleMedium)
                        product.brand?.let { Text(it, color = MaterialTheme.colorScheme.onSurfaceVariant) }
                        Text(listOfNotNull(product.barcode, product.quantityText).joinToString(" · "),
                            style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }

            SectionCard("Giá trị dinh dưỡng") {
                if (product.kcalPer100g != null) {
                    LabeledRow("Năng lượng / 100 g", product.kcalPer100g!!.kcalText)
                } else {
                    NumberField("Năng lượng / 100 g", manualKcal100, { manualKcal100 = it }, suffix = "kcal")
                }
                kcalServing?.let { LabeledRow("Mỗi khẩu phần ${product.servingSizeText?.let { "($it)" } ?: ""}", it.kcalText) }
                product.protein100g?.let { LabeledRow("Chất đạm", "${it.shortText} g") }
                product.carbs100g?.let { LabeledRow("Carbohydrate", "${it.shortText} g") }
                product.sugars100g?.let { LabeledRow("   trong đó đường", "${it.shortText} g") }
                product.fat100g?.let { LabeledRow("Chất béo", "${it.shortText} g") }
            }

            SectionCard("Bạn ăn bao nhiêu?") {
                if (kcalServing != null) {
                    Segmented(AmountMode.entries, mode, { it.title }) {
                        mode = it
                        amount = if (it == AmountMode.grams) product.servingGrams ?: 100.0 else 1.0
                    }
                }
                Row(verticalAlignment = Alignment.CenterVertically) {
                    val step = if (mode == AmountMode.grams) 10.0 else 0.5
                    OutlinedButton(onClick = { amount = maxOf(0.0, (amount ?: 0.0) - step) }) { Text("−") }
                    NumberField("Số lượng", amount, { amount = it }, suffix = if (mode == AmountMode.grams) "g / ml" else "phần",
                        modifier = Modifier.weight(1f).padding(horizontal = 8.dp))
                    OutlinedButton(onClick = { amount = (amount ?: 0.0) + step }) { Text("+") }
                }
            }

            SectionCard(footer = when (product.source) {
                ProductInfo.Source.openFoodFacts -> "Dữ liệu từ Open Food Facts (cộng đồng đóng góp). Giá trị có thể chưa chính xác tuyệt đối."
                ProductInfo.Source.estimate -> "Giá trị ước tính trung bình. Lượng calo thực tế phụ thuộc cách chế biến và khẩu phần."
                else -> null
            }) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Tổng calo", style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                    Text(total?.kcalText ?: "—", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold, color = Orange)
                }
                Button(onClick = {
                    val t = total ?: return@Button
                    vm.addFood(FoodLogEntry(name = product.name, amount = amount ?: 0.0,
                        unit = if (mode == AmountMode.grams) "g" else "phần", kcal = t))
                    saved = true
                }, enabled = total != null, modifier = Modifier.fillMaxWidth()) {
                    Icon(Icons.Filled.AddCircle, contentDescription = null); Spacer(Modifier.width(8.dp)); Text("Thêm vào nhật ký")
                }
            }
        }
    }

    if (saved) {
        AlertDialog(
            onDismissRequest = { saved = false },
            title = { Text("Đã thêm vào nhật ký") },
            text = { Text("${product.name}: ${total?.kcalText ?: ""}") },
            confirmButton = {
                TextButton(onClick = {
                    saved = false
                    nav.popBackStack(nav.graph.startDestinationId, inclusive = false)
                }) { Text("OK") }
            },
        )
    }
}

@Composable
fun ScannedTextScreen(vm: AppViewModel, nav: NavHostController) {
    val context = LocalContext.current
    val clipboard = LocalClipboardManager.current
    val text = vm.scannedText
    val isLink = text.startsWith("http://", ignoreCase = true) || text.startsWith("https://", ignoreCase = true)
    Column(Modifier.fillMaxSize()) {
        ScreenTopBar("Mã QR", onBack = { nav.popBackStack() })
        SectionCard("Nội dung mã QR",
            footer = "Đây không phải mã sản phẩm nên không tra cứu được calo. Hãy quét mã vạch hoặc nhãn dinh dưỡng trên bao bì.") {
            Text(text)
        }
        SectionCard {
            if (isLink) {
                TextButton(onClick = { runCatching { context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(text))) } }) {
                    Icon(Icons.Filled.OpenInBrowser, contentDescription = null); Spacer(Modifier.width(8.dp)); Text("Mở liên kết")
                }
            }
            TextButton(onClick = { clipboard.setText(AnnotatedString(text)) }) {
                Icon(Icons.Filled.ContentCopy, contentDescription = null); Spacer(Modifier.width(8.dp)); Text("Sao chép")
            }
        }
    }
}

@Composable
fun LabelScanScreen(vm: AppViewModel, nav: NavHostController, barcode: String?) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var image by remember { mutableStateOf<Uri?>(null) }
    var processing by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var lines by remember { mutableStateOf<List<String>>(emptyList()) }
    var hasResult by remember { mutableStateOf(false) }
    var name by remember { mutableStateOf("") }
    var kcal by remember { mutableStateOf<Double?>(null) }
    var basis by remember { mutableStateOf(NutritionLabelResult.Basis.per100g) }
    var servingGrams by remember { mutableStateOf<Double?>(null) }
    var showText by remember { mutableStateOf(false) }

    fun apply(newLines: List<String>) {
        lines = newLines
        val r = NutritionLabelParser.parse(newLines)
        kcal = r.kcal; basis = r.basis; servingGrams = r.servingGrams
        hasResult = true
    }

    LaunchedEffect(Unit) { vm.demoLabelLines?.let { apply(it); vm.demoLabelLines = null } }

    Column(Modifier.fillMaxSize()) {
        ScreenTopBar("Quét nhãn dinh dưỡng", onBack = { nav.popBackStack() })
        Column(Modifier.verticalScroll(rememberScrollState()).padding(bottom = 16.dp)) {
            SectionCard(footer = "Chụp rõ bảng \"Thông tin dinh dưỡng\" trên bao bì. App tự tìm số kcal, bạn có thể sửa lại nếu sai.") {
                image?.let { AsyncImage(model = it, contentDescription = null, modifier = Modifier.fillMaxWidth().heightIn(max = 220.dp)) }
                PhotoButtons("Chụp nhãn") { uri ->
                    image = uri; processing = true; error = null
                    scope.launch {
                        try { apply(recognizeTextLines(context, uri)) } catch (e: Exception) { error = "Không đọc được chữ trên ảnh: ${e.message}" }
                        processing = false
                    }
                }
                if (processing) Row(verticalAlignment = Alignment.CenterVertically) {
                    CircularProgressIndicator(Modifier.size(20.dp)); Spacer(Modifier.width(10.dp)); Text("Đang đọc nhãn…")
                }
                error?.let { Text(it, color = Red) }
            }
            if (hasResult && !processing) {
                SectionCard("Kết quả") {
                    OutlinedTextField(name, { name = it }, label = { Text("Tên sản phẩm") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                    NumberField("Năng lượng", kcal, { kcal = it }, suffix = "kcal")
                    Text("Tính trên", style = MaterialTheme.typography.labelMedium)
                    Segmented(NutritionLabelResult.Basis.entries, basis,
                        { if (it == NutritionLabelResult.Basis.per100g) "100 g / ml" else "1 khẩu phần" }) { basis = it }
                    NumberField("Khẩu phần (nếu biết)", servingGrams, { servingGrams = it }, suffix = "g")
                    if (kcal == null) IconText("Không tìm thấy số kcal, hãy nhập tay.", Icons.Filled.Warning, tint = Orange, textColor = Orange)
                    Button(onClick = {
                        val value = kcal ?: return@Button
                        val per100 = if (basis == NutritionLabelResult.Basis.per100g) value
                            else servingGrams?.takeIf { it > 0 }?.let { value * 100 / it }
                        vm.selectProduct(ProductInfo(
                            barcode = barcode,
                            name = name.trim().ifEmpty { "Sản phẩm từ nhãn" },
                            servingSizeText = servingGrams?.let { "${it.shortText} g" },
                            servingGrams = servingGrams,
                            kcalPer100g = per100,
                            kcalPerServing = if (basis == NutritionLabelResult.Basis.perServing) value else null,
                            source = ProductInfo.Source.label,
                        ))
                        nav.navigate("product")
                    }, enabled = kcal != null, modifier = Modifier.fillMaxWidth()) { Text("Tiếp tục tính calo") }
                }
                if (lines.isNotEmpty()) {
                    SectionCard {
                        TextButton(onClick = { showText = !showText }) { Text(if (showText) "Ẩn văn bản đọc được" else "Xem văn bản đọc được") }
                        if (showText) {
                            HorizontalDivider()
                            Text(lines.joinToString("\n"), fontFamily = FontFamily.Monospace, style = MaterialTheme.typography.bodySmall)
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun ManualProductScreen(vm: AppViewModel, nav: NavHostController, barcode: String?) {
    var name by remember { mutableStateOf("") }
    var kcal100 by remember { mutableStateOf<Double?>(null) }
    var serving by remember { mutableStateOf<Double?>(null) }
    Column(Modifier.fillMaxSize()) {
        ScreenTopBar("Nhập thủ công", onBack = { nav.popBackStack() })
        SectionCard(footer = "Xem số kcal trong bảng thông tin dinh dưỡng in trên bao bì.") {
            OutlinedTextField(name, { name = it }, label = { Text("Tên sản phẩm") }, singleLine = true, modifier = Modifier.fillMaxWidth())
            NumberField("Năng lượng / 100 g", kcal100, { kcal100 = it }, suffix = "kcal")
            NumberField("Khẩu phần (tuỳ chọn)", serving, { serving = it }, suffix = "g")
            FilledTonalButton(onClick = {
                vm.selectProduct(ProductInfo(
                    barcode = barcode, name = name.trim().ifEmpty { "Sản phẩm tự nhập" },
                    servingSizeText = serving?.let { "${it.shortText} g" }, servingGrams = serving,
                    kcalPer100g = kcal100, source = ProductInfo.Source.manual,
                ))
                nav.navigate("product")
            }, enabled = kcal100 != null, modifier = Modifier.fillMaxWidth()) { Text("Tiếp tục tính calo") }
        }
    }
}
