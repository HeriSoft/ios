@file:OptIn(ExperimentalMaterial3Api::class)

package com.herisoft.caloriescan.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Restaurant
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.herisoft.caloriescan.AppViewModel
import com.herisoft.caloriescan.FoodLogEntry
import com.herisoft.caloriescan.WorkoutLogEntry
import com.herisoft.caloriescan.core.kcalText
import com.herisoft.caloriescan.core.roundHalfUp
import com.herisoft.caloriescan.core.shortText
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import kotlin.math.abs

private fun dayOf(time: Long): LocalDate = Instant.ofEpochMilli(time).atZone(ZoneId.systemDefault()).toLocalDate()

private fun dayTitle(day: LocalDate): String {
    val today = LocalDate.now()
    return when (day) {
        today -> "Hôm nay"
        today.minusDays(1) -> "Hôm qua"
        else -> day.format(DateTimeFormatter.ofPattern("dd/MM/yyyy"))
    }
}

@Composable
fun LogScreen(vm: AppViewModel) {
    val foodsByDay = vm.foods.groupBy { dayOf(it.time) }
    val workoutsByDay = vm.workouts.groupBy { dayOf(it.time) }
    val days = (foodsByDay.keys + workoutsByDay.keys).sortedDescending()
    val today = LocalDate.now()
    val eaten = foodsByDay[today].orEmpty().sumOf { it.kcal }
    val burned = workoutsByDay[today].orEmpty().sumOf { it.kcal }

    Column(Modifier.fillMaxSize()) {
        ScreenTopBar("Nhật ký calo")
        LazyColumn {
            item {
                SectionCard(footer = "Còn lại = mục tiêu − ăn vào + đốt khi tập. Nếu đã chọn mức vận động cao ở tab Cơ thể, một phần calo tập đã nằm trong mục tiêu.") {
                    TodaySummary(eaten, burned, vm.dailyGoal)
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("Mục tiêu: ${vm.dailyGoal.toInt()} kcal/ngày", Modifier.weight(1f))
                        OutlinedButton(onClick = { vm.updateGoal(vm.dailyGoal - 50) }) { Text("−") }
                        Spacer(Modifier.width(6.dp))
                        OutlinedButton(onClick = { vm.updateGoal(vm.dailyGoal + 50) }) { Text("+") }
                    }
                }
            }
            if (days.isEmpty()) item {
                SectionCard { Text("Chưa có gì trong nhật ký. Quét sản phẩm, chọn món ăn hoặc ghi buổi tập để bắt đầu.") }
            }
            days.forEach { day ->
                val foods = foodsByDay[day].orEmpty()
                val workouts = workoutsByDay[day].orEmpty()
                item(key = day.toString()) {
                    SectionCard("${dayTitle(day)}   +${foods.sumOf { it.kcal }.roundHalfUp().toInt()} / −${workouts.sumOf { it.kcal }.roundHalfUp().toInt()} kcal") {
                        foods.forEach { FoodRow(it) { vm.removeFood(it.id) } }
                        workouts.forEach { WorkoutRow(it) { vm.removeWorkout(it.id) } }
                    }
                }
            }
        }
    }
}

@Composable
private fun FoodRow(entry: FoodLogEntry, onDelete: () -> Unit) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Icon(Icons.Filled.Restaurant, contentDescription = null, tint = Orange)
        Spacer(Modifier.width(12.dp))
        Column(Modifier.weight(1f)) {
            Text(entry.name)
            Text("${entry.amount.shortText} ${entry.unit} · ${timeText(entry.time)}", style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Text("+${entry.kcal.kcalText}", fontWeight = FontWeight.SemiBold)
        IconButton(onClick = onDelete) { Icon(Icons.Filled.Delete, contentDescription = "Xoá") }
    }
}

@Composable
private fun TodaySummary(eaten: Double, burned: Double, goal: Double) {
    val budget = goal + burned
    val remaining = budget - eaten
    val progress = if (budget > 0) (eaten / budget).coerceIn(0.0, 1.0).toFloat() else 0f
    val ringColor = if (remaining >= 0) Orange else Red
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.size(100.dp), contentAlignment = Alignment.Center) {
            Canvas(Modifier.fillMaxSize().padding(6.dp)) {
                drawArc(Orange.copy(alpha = 0.2f), 0f, 360f, false, style = Stroke(12.dp.toPx()))
                drawArc(ringColor, -90f, 360f * progress, false, style = Stroke(12.dp.toPx(), cap = StrokeCap.Round))
            }
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text("${abs(remaining).roundHalfUp().toInt()}", fontWeight = FontWeight.Bold)
                Text(if (remaining >= 0) "còn lại" else "vượt", style = MaterialTheme.typography.labelSmall,
                    color = if (remaining >= 0) MaterialTheme.colorScheme.onSurfaceVariant else Red)
            }
        }
        Spacer(Modifier.width(16.dp))
        Column {
            Text("Ăn vào: ${eaten.kcalText}", color = Orange)
            Text("Đốt khi tập: ${burned.kcalText}", color = Green)
            Text("Mục tiêu: ${goal.kcalText}", color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}
