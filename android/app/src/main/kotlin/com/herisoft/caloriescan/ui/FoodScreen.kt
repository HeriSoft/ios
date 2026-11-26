@file:OptIn(ExperimentalMaterial3Api::class)

package com.herisoft.caloriescan.ui

import android.net.Uri
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import coil.compose.AsyncImage
import com.herisoft.caloriescan.AppViewModel
import com.herisoft.caloriescan.core.FoodDatabase
import com.herisoft.caloriescan.core.FoodGuess
import com.herisoft.caloriescan.core.FoodItem
import com.herisoft.caloriescan.core.kcalText
import com.herisoft.caloriescan.labelImage
import kotlinx.coroutines.launch

/** Chụp ảnh món ăn bất kỳ, đoán món và tính calo theo bảng ước tính. */
@Composable
fun FoodScreen(vm: AppViewModel, nav: NavHostController) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var query by remember { mutableStateOf("") }
    var image by remember { mutableStateOf<Uri?>(null) }
    var processing by remember { mutableStateOf(false) }
    var guesses by remember { mutableStateOf<List<FoodGuess>?>(null) }
    var detected by remember { mutableStateOf<List<Pair<String, Float>>>(emptyList()) }
    var error by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) { vm.demoFoodGuesses?.let { guesses = it; vm.demoFoodGuesses = null } }

    fun open(food: FoodItem) {
        vm.selectProduct(food.productInfo, servings = true)
        nav.navigate("product")
    }

    val results = FoodDatabase.search(query)

    Column(Modifier.fillMaxSize()) {
        ScreenTopBar("Món ăn")
        OutlinedTextField(
            value = query, onValueChange = { query = it },
            placeholder = { Text("Tìm món: phở, cơm tấm, chuối…") },
            leadingIcon = { Icon(Icons.Filled.Search, contentDescription = null) },
            singleLine = true, modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 4.dp),
        )
        LazyColumn {
            if (query.isEmpty()) {
                item {
                    SectionCard(footer = "App đoán món từ ảnh (chạy trên máy, không cần mạng). Nếu đoán sai, hãy tìm món theo tên ở ô tìm kiếm.") {
                        image?.let {
                            AsyncImage(model = it, contentDescription = null, contentScale = ContentScale.Crop,
                                modifier = Modifier.fillMaxWidth().height(180.dp).clip(RoundedCornerShape(12.dp)))
                        }
                        PhotoButtons("Chụp món ăn") { uri ->
                            image = uri; processing = true; error = null
                            scope.launch {
                                try {
                                    val labels = labelImage(context, uri)
                                    detected = labels
                                    guesses = FoodDatabase.match(labels)
                                } catch (e: Exception) {
                                    guesses = emptyList(); error = "Không nhận diện được ảnh: ${e.message}"
                                }
                                processing = false
                            }
                        }
                        if (processing) Row(verticalAlignment = Alignment.CenterVertically) {
                            CircularProgressIndicator(Modifier.size(20.dp)); Spacer(Modifier.width(10.dp)); Text("Đang nhận diện món ăn…")
                        }
                        error?.let { Text(it, color = Red) }
                        if (detected.isNotEmpty()) {
                            Text("Nhận ra trong ảnh: " + detected.take(6).joinToString(", ") { "${it.first} ${(it.second * 100).toInt()}%" },
                                style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                }
                guesses?.takeIf { !processing }?.let { list ->
                    item {
                        SectionCard("Có thể là") {
                            if (list.isEmpty()) {
                                Text("Không nhận ra món ăn trong ảnh. Hãy tìm theo tên ở ô tìm kiếm phía trên.",
                                    color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                            list.forEach { guess -> FoodRow(guess.food, guess.confidence) { open(guess.food) } }
                        }
                    }
                }
            }
            item {
                Text(if (query.isEmpty()) "TẤT CẢ MÓN (${results.size})" else "KẾT QUẢ TÌM KIẾM",
                    style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(start = 20.dp, top = 12.dp, bottom = 4.dp))
                if (results.isEmpty()) Text("Không tìm thấy món \"$query\".", Modifier.padding(20.dp))
            }
            items(results, key = { it.id }) { food ->
                Column(Modifier.padding(horizontal = 16.dp)) {
                    FoodRow(food, null) { open(food) }
                    HorizontalDivider()
                }
            }
        }
    }
}

@Composable
private fun FoodRow(food: FoodItem, confidence: Float?, onClick: () -> Unit) {
    Row(Modifier.fillMaxWidth().clickable(onClick = onClick).padding(vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) {
            Text(food.name)
            Text("${food.portionName} ≈ ${food.portionGrams.toInt()} g", style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Column(horizontalAlignment = Alignment.End) {
            Text(food.kcalPerPortion.kcalText, fontWeight = FontWeight.SemiBold)
            confidence?.let { Text("${(it * 100).toInt()}% khớp", style = MaterialTheme.typography.bodySmall, color = Orange) }
        }
    }
}
