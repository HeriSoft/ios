@file:OptIn(ExperimentalMaterial3Api::class)

package com.herisoft.caloriescan.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.DirectionsRun
import androidx.compose.material.icons.automirrored.filled.DirectionsWalk
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material.icons.filled.AddCircle
import androidx.compose.material.icons.filled.CalendarMonth
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.FitnessCenter
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material.icons.filled.SelfImprovement
import androidx.compose.material.icons.filled.SportsTennis
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableDoubleStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import com.herisoft.caloriescan.AppViewModel
import com.herisoft.caloriescan.WorkoutLogEntry
import com.herisoft.caloriescan.core.BMICategory
import com.herisoft.caloriescan.core.Exercise
import com.herisoft.caloriescan.core.ExerciseCategory
import com.herisoft.caloriescan.core.ExerciseLibrary
import com.herisoft.caloriescan.core.HealthCalculator
import com.herisoft.caloriescan.core.HomeMove
import com.herisoft.caloriescan.core.WorkoutPlanner
import com.herisoft.caloriescan.core.kcalText
import com.herisoft.caloriescan.core.roundHalfUp
import com.herisoft.caloriescan.core.shortText

fun ExerciseCategory.icon(): ImageVector = when (this) {
    ExerciseCategory.cardio -> Icons.AutoMirrored.Filled.DirectionsRun
    ExerciseCategory.strength -> Icons.Filled.FitnessCenter
    ExerciseCategory.sport -> Icons.Filled.SportsTennis
    ExerciseCategory.flexibility -> Icons.Filled.SelfImprovement
    ExerciseCategory.daily -> Icons.AutoMirrored.Filled.DirectionsWalk
}

@Composable
fun ExerciseScreen(vm: AppViewModel, nav: NavHostController) {
    var query by remember { mutableStateOf("") }
    var logging by remember { mutableStateOf<Exercise?>(null) }
    val weight = vm.profile.weightKg
    val today = vm.workouts.filter { isToday(it.time) }

    Column(Modifier.fillMaxSize()) {
        ScreenTopBar("Tập luyện")
        OutlinedTextField(query, { query = it }, placeholder = { Text("Tìm môn: chạy, bơi, cầu lông…") }, singleLine = true,
            modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 4.dp))
        LazyColumn {
            if (query.isEmpty()) {
                item {
                    SectionCard("Hôm nay", footer = "Tính theo cân nặng ${weight.shortText} kg (sửa ở tab Cơ thể).") {
                        Row(Modifier.fillMaxWidth()) {
                            Stat("${today.sumOf { it.kcal }.roundHalfUp().toInt()}", "kcal đã đốt", Orange, Modifier.weight(1f))
                            Stat("${today.sumOf { it.minutes }.toInt()}", "phút tập", Green, Modifier.weight(1f))
                            Stat("${today.size}", "buổi", Blue, Modifier.weight(1f))
                        }
                    }
                }
                item {
                    SectionCard {
                        NavRow("Lịch tập gợi ý cho bạn", Icons.Filled.CalendarMonth) { nav.navigate("plan") }
                        HorizontalDivider()
                        NavRow("Bài tập tại nhà (không dụng cụ)", Icons.Filled.Home) { nav.navigate("homeWorkout") }
                    }
                }
                if (today.isNotEmpty()) item {
                    SectionCard("Đã tập hôm nay") { today.forEach { WorkoutRow(it) { vm.removeWorkout(it.id) } } }
                }
                ExerciseCategory.entries.forEach { category ->
                    item {
                        SectionCard(category.title) {
                            ExerciseLibrary.all.filter { it.category == category }.forEach { ExerciseRow(it, weight) { logging = it } }
                        }
                    }
                }
            } else {
                val results = ExerciseLibrary.search(query)
                item {
                    SectionCard("Kết quả tìm kiếm") {
                        if (results.isEmpty()) Text("Không tìm thấy \"$query\".")
                        results.forEach { ExerciseRow(it, weight) { logging = it } }
                    }
                }
            }
        }
    }

    logging?.let { exercise ->
        var minutes by remember(exercise) { mutableDoubleStateOf(30.0) }
        val kcal = exercise.kcal(weight, minutes)
        AlertDialog(
            onDismissRequest = { logging = null },
            title = { Text(exercise.name) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        OutlinedButton(onClick = { minutes = maxOf(5.0, minutes - 5) }) { Text("−5") }
                        Text("${minutes.toInt()} phút", Modifier.weight(1f).padding(horizontal = 8.dp),
                            style = MaterialTheme.typography.titleMedium)
                        OutlinedButton(onClick = { minutes = minOf(300.0, minutes + 5) }) { Text("+5") }
                    }
                    LabeledRow("Calo đốt (ước tính)", kcal.kcalText, Orange, bold = true)
                    Text("MET ${exercise.met.shortText} × 3,5 × ${weight.shortText} kg ÷ 200 × số phút.",
                        style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    if (exercise.highImpact) {
                        IconText("Môn có chạy nhảy, tác động mạnh lên khớp. Khởi động kỹ; nếu thừa cân nhiều hoặc đau gối, hãy chọn môn nhẹ hơn.",
                            Icons.Filled.Warning, tint = Orange)
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    vm.addWorkout(WorkoutLogEntry(name = exercise.name, exerciseId = exercise.id, minutes = minutes, kcal = kcal))
                    logging = null
                }) { Text("Ghi lại") }
            },
            dismissButton = { TextButton(onClick = { logging = null }) { Text("Huỷ") } },
        )
    }
}

@Composable
private fun Stat(value: String, label: String, color: Color, modifier: Modifier) {
    Column(modifier, horizontalAlignment = Alignment.CenterHorizontally) {
        Text(value, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold, color = color)
        Text(label, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
fun NavRow(title: String, icon: ImageVector, subtitle: String? = null, tint: Color = Orange, onClick: () -> Unit) {
    Row(Modifier.fillMaxWidth().clickable(onClick = onClick).padding(vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
        Icon(icon, contentDescription = null, tint = tint)
        Spacer(Modifier.width(12.dp))
        Column(Modifier.weight(1f)) {
            Text(title)
            subtitle?.let { Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant) }
        }
        Icon(Icons.AutoMirrored.Filled.KeyboardArrowRight, contentDescription = null)
    }
}

@Composable
private fun ExerciseRow(exercise: Exercise, weight: Double, onClick: () -> Unit) {
    Row(Modifier.fillMaxWidth().clickable(onClick = onClick).padding(vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
        Icon(exercise.category.icon(), contentDescription = null, tint = Orange)
        Spacer(Modifier.width(12.dp))
        Text(exercise.name, Modifier.weight(1f))
        Text("${exercise.kcal(weight, 30.0).roundHalfUp().toInt()} kcal/30′", style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant)
        Spacer(Modifier.width(8.dp))
        Icon(Icons.Filled.AddCircle, contentDescription = "Ghi lại", tint = Orange)
    }
}

@Composable
fun WorkoutRow(entry: WorkoutLogEntry, onDelete: () -> Unit) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Icon(ExerciseLibrary.exercise(entry.exerciseId)?.category?.icon() ?: Icons.Filled.FitnessCenter, contentDescription = null, tint = Green)
        Spacer(Modifier.width(12.dp))
        Column(Modifier.weight(1f)) {
            Text(entry.name)
            Text("${entry.minutes.toInt()} phút · ${timeText(entry.time)}", style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Text("−${entry.kcal.kcalText}", color = Green, fontWeight = FontWeight.SemiBold)
        IconButton(onClick = onDelete) { Icon(Icons.Filled.Delete, contentDescription = "Xoá") }
    }
}

@Composable
fun PlanScreen(vm: AppViewModel, nav: NavHostController) {
    val p = vm.profile
    val category = if (p.heightCm > 0) BMICategory.of(HealthCalculator.bmi(p.weightKg, p.heightCm)) else null
    val plan = WorkoutPlanner.plan(p.goal, p.age, category)
    Column(Modifier.fillMaxSize()) {
        ScreenTopBar("Lịch tập gợi ý", onBack = { nav.popBackStack() })
        Column(Modifier.verticalScroll(rememberScrollState()).padding(bottom = 16.dp)) {
            SectionCard(footer = "Dựa trên tuổi, cân nặng và mục tiêu ở tab Cơ thể.") {
                LabeledRow("Mục tiêu", p.goal.title)
                LabeledRow("Tổng thời gian", "${plan.weeklyMinutes} phút/tuần")
                if (plan.lowImpact) IconText("Ưu tiên môn nhẹ nhàng cho khớp", Icons.AutoMirrored.Filled.DirectionsWalk, tint = Blue)
            }
            SectionCard("Lịch trong tuần") {
                plan.days.forEach { day ->
                    Column {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(day.day, fontWeight = FontWeight.Bold, modifier = Modifier.width(80.dp))
                            Text(day.title, Modifier.weight(1f))
                            if (!day.isRest) Text("${day.minutes} phút", color = Orange)
                        }
                        if (!day.isRest) {
                            Text("Chọn một: " + day.exerciseIDs.mapNotNull { ExerciseLibrary.exercise(it)?.name }.joinToString(", "),
                                style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                }
            }
            SectionCard("Lưu ý") { plan.notes.forEach { IconText(it, Icons.Filled.Lightbulb) } }
        }
    }
}

@Composable
fun HomeWorkoutScreen(nav: NavHostController) {
    Column(Modifier.fillMaxSize()) {
        ScreenTopBar("Bài tập tại nhà", onBack = { nav.popBackStack() })
        LazyColumn {
            item {
                SectionCard(footer = "Gợi ý một buổi 20–30 phút: khởi động 5 phút, chọn 4–5 động tác làm vòng tròn, nghỉ 30–60 giây giữa các hiệp, giãn cơ 5 phút. Ghi lại bằng mục \"Bài tập tại nhà\" trong danh sách môn tập.") {
                    HomeMove.all.forEach { move ->
                        NavRow(move.name, Icons.Filled.FitnessCenter, "${move.target} · ${move.reps}") { nav.navigate("move/${move.id}") }
                    }
                }
            }
        }
    }
}

@Composable
fun HomeMoveScreen(nav: NavHostController, id: String) {
    val move = HomeMove.all.firstOrNull { it.id == id } ?: return
    Column(Modifier.fillMaxSize()) {
        ScreenTopBar(move.name, onBack = { nav.popBackStack() })
        Column(Modifier.verticalScroll(rememberScrollState()).padding(bottom = 16.dp)) {
            SectionCard {
                LabeledRow("Nhóm cơ", move.target)
                LabeledRow("Gợi ý", move.reps)
            }
            SectionCard("Cách tập") {
                move.steps.forEachIndexed { i, step -> Text("${i + 1}. $step") }
            }
            SectionCard("Bản dễ hơn") { Text(move.easier) }
            SectionCard("Lưu ý an toàn") { IconText(move.caution, Icons.Filled.Warning, tint = Orange) }
        }
    }
}

fun isToday(time: Long): Boolean {
    val zone = java.time.ZoneId.systemDefault()
    return java.time.Instant.ofEpochMilli(time).atZone(zone).toLocalDate() == java.time.LocalDate.now(zone)
}

fun timeText(time: Long): String =
    java.time.Instant.ofEpochMilli(time).atZone(java.time.ZoneId.systemDefault()).toLocalTime()
        .format(java.time.format.DateTimeFormatter.ofPattern("HH:mm"))
