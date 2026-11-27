@file:OptIn(ExperimentalMaterial3Api::class)

package com.herisoft.caloriescan.ui

import android.Manifest
import android.content.pm.PackageManager
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.LocalHospital
import androidx.compose.material.icons.filled.PhotoCamera
import androidx.compose.material.icons.filled.PhotoLibrary
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.compose.foundation.isSystemInDarkTheme
import com.herisoft.caloriescan.createImageUri
import com.herisoft.caloriescan.core.shortText

val Orange = Color(0xFFF57C00)
val Green = Color(0xFF2E7D32)
val Red = Color(0xFFD32F2F)
val Blue = Color(0xFF1976D2)

@Composable
fun CalorieTheme(content: @Composable () -> Unit) {
    val colors = if (isSystemInDarkTheme()) {
        darkColorScheme(primary = Color(0xFFFFA040), secondary = Color(0xFFFFB74D))
    } else {
        lightColorScheme(primary = Orange, secondary = Color(0xFFFF9800))
    }
    MaterialTheme(colorScheme = colors, content = content)
}

@Composable
fun ScreenTopBar(title: String, onBack: (() -> Unit)? = null) {
    TopAppBar(
        title = { Text(title, maxLines = 1) },
        navigationIcon = {
            if (onBack != null) {
                IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Quay lại") }
            }
        },
        windowInsets = WindowInsets(0, 0, 0, 0),
    )
}

@Composable
fun SectionCard(title: String? = null, footer: String? = null, content: @Composable ColumnScope.() -> Unit) {
    Column(Modifier.padding(horizontal = 16.dp, vertical = 6.dp)) {
        if (title != null) {
            Text(title.uppercase(), style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(start = 4.dp, bottom = 4.dp))
        }
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceContainerLow),
        ) {
            Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(10.dp), content = content)
        }
        if (footer != null) {
            Text(footer, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(start = 4.dp, top = 4.dp, end = 4.dp))
        }
    }
}

@Composable
fun LabeledRow(label: String, value: String, valueColor: Color = Color.Unspecified, bold: Boolean = false) {
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Text(label, Modifier.weight(1f))
        Text(value, color = valueColor, fontWeight = if (bold) FontWeight.Bold else null)
    }
}

@Composable
fun IconText(text: String, icon: ImageVector, tint: Color = MaterialTheme.colorScheme.primary, textColor: Color = Color.Unspecified) {
    Row(verticalAlignment = Alignment.Top) {
        Icon(icon, contentDescription = null, tint = tint, modifier = Modifier.size(20.dp))
        Spacer(Modifier.width(10.dp))
        Text(text, style = MaterialTheme.typography.bodyMedium, color = textColor)
    }
}

/** Ô nhập số (cho phép dấu phẩy). Giá trị null khi để trống hoặc không hợp lệ. */
@Composable
fun NumberField(label: String, value: Double?, onValueChange: (Double?) -> Unit, suffix: String? = null, modifier: Modifier = Modifier) {
    var text by rememberSaveable(label) { mutableStateOf(value?.shortText ?: "") }
    // Chỉ đồng bộ khi giá trị bên ngoài thay đổi (ví dụ đổi đơn vị), không ghi đè khi người dùng đang xoá để gõ lại.
    LaunchedEffect(value) {
        if (text.replace(',', '.').toDoubleOrNull() != value) text = value?.shortText ?: ""
    }
    OutlinedTextField(
        value = text,
        onValueChange = { new ->
            val cleaned = new.filter { it.isDigit() || it == ',' || it == '.' }
            text = cleaned
            onValueChange(cleaned.replace(',', '.').toDoubleOrNull())
        },
        label = { Text(label) },
        suffix = suffix?.let { { Text(it) } },
        singleLine = true,
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
        modifier = modifier.fillMaxWidth(),
    )
}

@Composable
fun <T> DropdownPicker(label: String, options: List<T>, selected: T, title: (T) -> String, onSelect: (T) -> Unit) {
    var open by remember { mutableStateOf(false) }
    Column {
        Text(label, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        OutlinedButton(onClick = { open = true }, modifier = Modifier.fillMaxWidth()) {
            Text(title(selected), Modifier.weight(1f))
            Icon(Icons.Filled.ArrowDropDown, contentDescription = null)
        }
        DropdownMenu(expanded = open, onDismissRequest = { open = false }) {
            options.forEach { option ->
                DropdownMenuItem(text = { Text(title(option)) }, onClick = { onSelect(option); open = false })
            }
        }
    }
}

@Composable
fun <T> Segmented(options: List<T>, selected: T, title: (T) -> String, onSelect: (T) -> Unit) {
    SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
        options.forEachIndexed { index, option ->
            SegmentedButton(
                selected = option == selected,
                onClick = { onSelect(option) },
                shape = SegmentedButtonDefaults.itemShape(index, options.size),
            ) { Text(title(option), maxLines = 1) }
        }
    }
}

@Composable
fun Pill(text: String, color: Color) {
    Text(
        text,
        color = color,
        fontWeight = FontWeight.SemiBold,
        style = MaterialTheme.typography.labelLarge,
        modifier = Modifier
            .background(color.copy(alpha = 0.15f), RoundedCornerShape(50))
            .padding(horizontal = 10.dp, vertical = 4.dp),
    )
}

@Composable
fun MedicalDisclaimer() {
    IconText(
        "Thông tin chỉ để tham khảo, không phải chẩn đoán y khoa và không thay thế bác sĩ. Khi nghi ngờ, hãy đi khám. Trường hợp khẩn cấp gọi 115.",
        Icons.Filled.LocalHospital, tint = Red,
    )
}

/** Hai nút chụp ảnh (camera hệ thống) và chọn ảnh từ thư viện. */
@Composable
fun PhotoButtons(takeLabel: String, onImage: (Uri) -> Unit) {
    val context = LocalContext.current
    var pendingUri by remember { mutableStateOf<Uri?>(null) }
    val take = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { ok ->
        val uri = pendingUri
        if (ok && uri != null) onImage(uri)
    }
    val permission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) createImageUri(context).also { pendingUri = it; take.launch(it) }
    }
    val pick = rememberLauncherForActivityResult(ActivityResultContracts.PickVisualMedia()) { uri -> uri?.let(onImage) }

    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        OutlinedButton(onClick = {
            if (ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
                createImageUri(context).also { pendingUri = it; take.launch(it) }
            } else {
                permission.launch(Manifest.permission.CAMERA)
            }
        }, modifier = Modifier.weight(1f)) {
            Icon(Icons.Filled.PhotoCamera, contentDescription = null)
            Spacer(Modifier.width(6.dp))
            Text(takeLabel)
        }
        OutlinedButton(onClick = {
            pick.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly))
        }, modifier = Modifier.weight(1f)) {
            Icon(Icons.Filled.PhotoLibrary, contentDescription = null)
            Spacer(Modifier.width(6.dp))
            Text("Thư viện")
        }
    }
}

@Composable
fun SmallTextButton(text: String, onClick: () -> Unit) {
    TextButton(onClick = onClick) { Text(text) }
}
