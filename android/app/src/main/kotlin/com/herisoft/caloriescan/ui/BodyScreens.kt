@file:OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)

package com.herisoft.caloriescan.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AddCircle
import androidx.compose.material.icons.filled.CalendarMonth
import androidx.compose.material.icons.filled.Call
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Error
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.LocalHospital
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material.icons.filled.Medication
import androidx.compose.material.icons.filled.MedicalServices
import androidx.compose.material.icons.filled.RemoveCircle
import androidx.compose.material.icons.filled.Spa
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Checkbox
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import com.herisoft.caloriescan.AppViewModel
import com.herisoft.caloriescan.core.ActivityLevel
import com.herisoft.caloriescan.core.BMICategory
import com.herisoft.caloriescan.core.BodyReport
import com.herisoft.caloriescan.core.CareLevel
import com.herisoft.caloriescan.core.ConditionLibrary
import com.herisoft.caloriescan.core.FoodDatabase
import com.herisoft.caloriescan.core.FoodSuggestion
import com.herisoft.caloriescan.core.HealthCalculator
import com.herisoft.caloriescan.core.NutritionAdvisor
import com.herisoft.caloriescan.core.PatientGroup
import com.herisoft.caloriescan.core.RedFlag
import com.herisoft.caloriescan.core.Sex
import com.herisoft.caloriescan.core.Symptom
import com.herisoft.caloriescan.core.SymptomChecker
import com.herisoft.caloriescan.core.SymptomDuration
import com.herisoft.caloriescan.core.SymptomSeverity
import com.herisoft.caloriescan.core.WeightGoal
import com.herisoft.caloriescan.core.kcalText
import com.herisoft.caloriescan.core.roundHalfUp
import com.herisoft.caloriescan.core.shortText

fun BMICategory.color(): Color = when (this) {
    BMICategory.underweight -> Blue
    BMICategory.normal -> Green
    BMICategory.overweight -> Orange
    BMICategory.obese1, BMICategory.obese2 -> Red
}

@Composable
fun BodyScreen(vm: AppViewModel, nav: NavHostController) {
    val p = vm.profile
    val report = HealthCalculator.report(p)
    Column(Modifier.fillMaxSize()) {
        ScreenTopBar("Cơ thể")
        Column(Modifier.verticalScroll(rememberScrollState()).padding(bottom = 16.dp)) {
            SectionCard {
                NavRow("Kiểm tra triệu chứng", Icons.Filled.MedicalServices, "Đánh giá mức độ cần đi khám và cách chăm sóc", tint = Red) {
                    nav.navigate("symptoms")
                }
            }
            SectionCard("Thông tin của bạn") {
                Segmented(Sex.entries, p.sex, { it.title }) { vm.updateProfile(p.copy(sex = it)) }
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Tuổi", Modifier.weight(1f))
                    OutlinedButton(onClick = { vm.updateProfile(p.copy(age = maxOf(10, p.age - 1))) }) { Text("−") }
                    Text("${p.age}", Modifier.padding(horizontal = 16.dp), style = MaterialTheme.typography.titleMedium)
                    OutlinedButton(onClick = { vm.updateProfile(p.copy(age = minOf(100, p.age + 1))) }) { Text("+") }
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    NumberField("Chiều cao", p.heightCm, { it?.let { h -> vm.updateProfile(p.copy(heightCm = h)) } }, "cm", Modifier.weight(1f))
                    NumberField("Cân nặng", p.weightKg, { it?.let { w -> vm.updateProfile(p.copy(weightKg = w)) } }, "kg", Modifier.weight(1f))
                }
                NumberField("Vòng eo (tuỳ chọn)", p.waistCm, { vm.updateProfile(p.copy(waistCm = it)) }, "cm")
                DropdownPicker("Mức vận động", ActivityLevel.entries, p.activity, { it.title }) { vm.updateProfile(p.copy(activity = it)) }
                Text("Mục tiêu", style = MaterialTheme.typography.labelMedium)
                Segmented(WeightGoal.entries, p.goal, { it.title }) { vm.updateProfile(p.copy(goal = it)) }
            }
            if (report == null) {
                SectionCard {
                    IconText("Hãy nhập tuổi (10–100), chiều cao (100–250 cm) và cân nặng (20–300 kg) hợp lệ.", Icons.Filled.Warning, tint = Orange)
                }
            } else {
                BodyResults(vm, report)
            }
            SectionCard {
                Text("Kết quả chỉ để tham khảo cho người trưởng thành khỏe mạnh. Không áp dụng cho phụ nữ mang thai, người có bệnh mạn tính hoặc vận động viên. Không thay thế tư vấn của bác sĩ hay chuyên gia dinh dưỡng.",
                    style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}

@Composable
private fun BodyResults(vm: AppViewModel, r: BodyReport) {
    SectionCard("Chỉ số cơ thể") {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("BMI ", style = MaterialTheme.typography.titleMedium)
            Text(String.format(java.util.Locale.ROOT, "%.1f", r.bmi).replace('.', ','),
                style = MaterialTheme.typography.headlineLarge, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
            Pill(r.category.title, r.category.color())
        }
        BmiScale(r.bmi)
        LabeledRow("Cân nặng hợp lý", "${r.healthyWeightRange.start.shortText} – ${r.healthyWeightRange.endInclusive.shortText} kg")
        when {
            r.weightChangeToHealthy > 0 -> LabeledRow("Cần tăng", "≈ ${r.weightChangeToHealthy.shortText} kg")
            r.weightChangeToHealthy < 0 -> LabeledRow("Cần giảm", "≈ ${(-r.weightChangeToHealthy).shortText} kg")
            else -> LabeledRow("Cân nặng", "Đang trong khoảng hợp lý ✓")
        }
        r.bodyFatPercent?.let { LabeledRow("Mỡ cơ thể (ước tính)", "${it.shortText} %") }
        r.waistToHeight?.let {
            LabeledRow("Eo / chiều cao", String.format(java.util.Locale.ROOT, "%.2f", it).replace('.', ',') + if (it > 0.5) " ⚠︎" else " ✓")
        }
    }
    SectionCard("Năng lượng mỗi ngày", footer = "BMR theo công thức Mifflin-St Jeor; TDEE = BMR × hệ số vận động.") {
        LabeledRow("BMR (năng lượng khi nghỉ)", r.bmr.kcalText)
        LabeledRow("TDEE (tiêu hao mỗi ngày)", r.tdee.kcalText)
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Nên ăn mỗi ngày", style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
            Text(r.targetKcal.kcalText, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold, color = Orange)
        }
        Row(Modifier.fillMaxWidth()) {
            Macro("${r.proteinGrams.roundHalfUp().toInt()}", "Đạm (g)", Red, Modifier.weight(1f))
            Macro("${r.fatGrams.roundHalfUp().toInt()}", "Béo (g)", Color(0xFFF9A825), Modifier.weight(1f))
            Macro("${r.carbGrams.roundHalfUp().toInt()}", "Tinh bột (g)", Blue, Modifier.weight(1f))
            Macro(r.waterLiters.shortText, "Nước (lít)", Color(0xFF00ACC1), Modifier.weight(1f))
        }
        val isGoal = vm.dailyGoal == r.targetKcal
        FilledTonalButton(onClick = { vm.updateGoal(r.targetKcal) }, enabled = !isGoal, modifier = Modifier.fillMaxWidth()) {
            Text(if (isGoal) "Đang là mục tiêu nhật ký ✓" else "Dùng làm mục tiêu nhật ký")
        }
    }
    val advice = NutritionAdvisor.advice(vm.profile, r)
    SectionCard("Nên ăn thêm") { advice.eatMore.forEach { SuggestionRow(it, true) } }
    SectionCard("Nên hạn chế") { advice.limit.forEach { SuggestionRow(it, false) } }
    SectionCard("Lời khuyên") { advice.tips.forEach { IconText(it, Icons.Filled.Lightbulb) } }
}

@Composable
private fun Macro(value: String, label: String, color: Color, modifier: Modifier) {
    Column(modifier, horizontalAlignment = Alignment.CenterHorizontally) {
        Text(value, fontWeight = FontWeight.Bold, color = color, style = MaterialTheme.typography.titleMedium)
        Text(label, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun SuggestionRow(s: FoodSuggestion, eatMore: Boolean) {
    Row(verticalAlignment = Alignment.Top) {
        Icon(if (eatMore) Icons.Filled.AddCircle else Icons.Filled.RemoveCircle, contentDescription = null, tint = if (eatMore) Green else Red)
        Spacer(Modifier.width(10.dp))
        Column(Modifier.weight(1f)) {
            Text(s.food.name)
            Text(s.reason, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Column(horizontalAlignment = Alignment.End) {
            Text(s.food.kcalPerPortion.kcalText, style = MaterialTheme.typography.bodySmall)
            Text(s.food.portionName, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

/** Thanh màu thể hiện vị trí BMI (15–35). */
@Composable
private fun BmiScale(bmi: Double) {
    val bands = listOf(18.5 to Blue, 23.0 to Green, 25.0 to Orange, 30.0 to Red, 35.0 to Color(0xFF8E0000))
    val marker = MaterialTheme.colorScheme.onSurface
    Canvas(Modifier.fillMaxWidth().height(18.dp)) {
        val span = 20.0
        var lower = 15.0
        val barTop = size.height / 2 - 4.dp.toPx()
        bands.forEach { (upper, color) ->
            val x0 = (size.width * (lower - 15) / span).toFloat()
            val x1 = (size.width * (upper - 15) / span).toFloat()
            drawRect(color.copy(alpha = 0.8f), topLeft = Offset(x0, barTop), size = androidx.compose.ui.geometry.Size(x1 - x0 - 2f, 8.dp.toPx()))
            lower = upper
        }
        val x = (size.width * ((bmi.coerceIn(15.0, 35.0) - 15) / span)).toFloat()
        drawCircle(Color.White, radius = 8.dp.toPx(), center = Offset(x, size.height / 2))
        drawCircle(marker, radius = 8.dp.toPx(), center = Offset(x, size.height / 2), style = androidx.compose.ui.graphics.drawscope.Stroke(2.dp.toPx()))
    }
}

// MARK: - Kiểm tra triệu chứng

@Composable
fun SymptomInputScreen(vm: AppViewModel, nav: NavHostController) {
    val input = vm.symptomInput
    Column(Modifier.fillMaxSize()) {
        ScreenTopBar("Kiểm tra triệu chứng", onBack = { nav.popBackStack() })
        Column(Modifier.verticalScroll(rememberScrollState()).padding(bottom = 16.dp)) {
            SectionCard { MedicalDisclaimer() }
            SectionCard("Bạn đang có triệu chứng gì?") {
                FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    Symptom.entries.forEach { s ->
                        val selected = s in input.symptoms
                        FilterChip(
                            selected = selected,
                            onClick = {
                                vm.symptomInput = input.copy(symptoms = if (selected) input.symptoms - s else input.symptoms + s)
                            },
                            label = { Text(s.title) },
                        )
                    }
                }
            }
            SectionCard("Thông tin thêm") {
                DropdownPicker("Người bệnh", PatientGroup.entries, input.group, { it.title }) { vm.symptomInput = input.copy(group = it) }
                DropdownPicker("Đã bị bao lâu", SymptomDuration.entries, input.duration, { it.title }) { vm.symptomInput = input.copy(duration = it) }
                Text("Mức độ", style = MaterialTheme.typography.labelMedium)
                Segmented(SymptomSeverity.entries, input.severity, { it.title }) { vm.symptomInput = input.copy(severity = it) }
            }
            SectionCard("Có dấu hiệu nguy hiểm nào không?", footer = "Nếu có bất kỳ dấu hiệu nào ở trên, hãy gọi 115 hoặc đến cấp cứu ngay.") {
                RedFlag.entries.forEach { flag ->
                    val checked = flag in input.redFlags
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Checkbox(checked = checked, onCheckedChange = {
                            vm.symptomInput = input.copy(redFlags = if (checked) input.redFlags - flag else input.redFlags + flag)
                        })
                        Text(flag.title, style = MaterialTheme.typography.bodyMedium)
                    }
                }
            }
            Button(
                onClick = { nav.navigate("symptomResult") },
                enabled = input.symptoms.isNotEmpty() || input.redFlags.isNotEmpty(),
                modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp),
            ) { Text("Xem đánh giá") }
        }
    }
}

private fun CareLevel.color(): Color = when (this) {
    CareLevel.selfCare -> Green
    CareLevel.seeDoctor -> Color(0xFFF9A825)
    CareLevel.urgent -> Orange
    CareLevel.emergency -> Red
}

@Composable
fun SymptomResultScreen(vm: AppViewModel, nav: NavHostController) {
    val context = LocalContext.current
    val a = SymptomChecker.assess(vm.symptomInput)
    val color = a.level.color()
    Column(Modifier.fillMaxSize()) {
        ScreenTopBar("Đánh giá", onBack = { nav.popBackStack() })
        Column(Modifier.verticalScroll(rememberScrollState()).padding(bottom = 16.dp)) {
            Box(Modifier.padding(16.dp).fillMaxWidth().background(color.copy(alpha = 0.12f), RoundedCornerShape(16.dp)).padding(16.dp)) {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(when (a.level) {
                            CareLevel.selfCare -> Icons.Filled.Home
                            CareLevel.seeDoctor -> Icons.Filled.CalendarMonth
                            CareLevel.urgent -> Icons.Filled.LocalHospital
                            CareLevel.emergency -> Icons.Filled.Error
                        }, contentDescription = null, tint = color)
                        Spacer(Modifier.width(8.dp))
                        Text(a.level.title, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, color = color)
                    }
                    Text(a.level.detail)
                    if (a.level == CareLevel.emergency) {
                        Button(
                            onClick = { context.startActivity(Intent(Intent.ACTION_DIAL, Uri.parse("tel:115"))) },
                            colors = ButtonDefaults.buttonColors(containerColor = Red),
                            modifier = Modifier.fillMaxWidth(),
                        ) { Icon(Icons.Filled.Call, contentDescription = null); Spacer(Modifier.width(8.dp)); Text("Gọi 115") }
                    }
                }
            }
            SectionCard("Vì sao") { a.reasons.forEach { IconText(it, Icons.Filled.Info) } }
            if (a.matches.isNotEmpty()) {
                SectionCard("Có thể là",
                    footer = "Đây chỉ là các nguyên nhân thường gặp có triệu chứng tương tự, không phải chẩn đoán. Bấm vào từng mục để xem cách chăm sóc.") {
                    a.matches.forEachIndexed { i, m ->
                        if (i > 0) HorizontalDivider()
                        NavRow(m.condition.name, Icons.Filled.MedicalServices,
                            "${m.condition.summary}\nKhám: ${m.condition.specialty} · khớp ${m.matched}/${m.condition.symptoms.size}") {
                            nav.navigate("condition/${m.condition.id}/${if (a.showMedicationAdvice) 1 else 0}")
                        }
                    }
                }
            }
            SectionCard { MedicalDisclaimer() }
        }
    }
}

@Composable
fun ConditionScreen(nav: NavHostController, id: String, showMedication: Boolean) {
    val c = ConditionLibrary.all.firstOrNull { it.id == id } ?: return
    Column(Modifier.fillMaxSize()) {
        ScreenTopBar(c.name, onBack = { nav.popBackStack() })
        Column(Modifier.verticalScroll(rememberScrollState()).padding(bottom = 16.dp)) {
            SectionCard {
                Text(c.summary)
                LabeledRow("Chuyên khoa nên khám", c.specialty)
            }
            SectionCard("Đi khám ngay nếu") { c.seeDoctorIf.forEach { IconText(it, Icons.Filled.Error, tint = Red, textColor = Red) } }
            SectionCard("Nghỉ ngơi & chăm sóc") { c.selfCare.forEach { IconText(it, Icons.Filled.CheckCircle, tint = Green) } }
            val eat = c.eatFoodIDs.mapNotNull(FoodDatabase::byId)
            val avoid = c.avoidFoodIDs.mapNotNull(FoodDatabase::byId)
            if (eat.isNotEmpty() || avoid.isNotEmpty()) {
                SectionCard("Ăn uống") {
                    eat.forEach { IconText("Nên ăn: ${it.name}", Icons.Filled.AddCircle, tint = Green) }
                    avoid.forEach { IconText("Hạn chế: ${it.name}", Icons.Filled.RemoveCircle, tint = Red) }
                }
            }
            if (showMedication) {
                if (c.otcMedicines.isNotEmpty()) {
                    SectionCard("Thuốc không kê đơn thường dùng",
                        footer = "App không ghi liều lượng. Đọc kỹ hướng dẫn trên bao bì và hỏi dược sĩ. Người có bệnh gan, thận, dạ dày, đang dùng thuốc khác, cho con bú hoặc dị ứng thuốc cần hỏi bác sĩ trước. Không dùng chung nhiều thuốc cùng chứa paracetamol.") {
                        c.otcMedicines.forEach { IconText(it, Icons.Filled.Medication) }
                    }
                }
                if (c.homeRemedies.isNotEmpty()) {
                    SectionCard("Mẹo dân gian / thảo dược",
                        footer = "Chỉ hỗ trợ giảm khó chịu, không thay thế điều trị. Dừng lại nếu có dấu hiệu dị ứng hoặc triệu chứng nặng lên.") {
                        c.homeRemedies.forEach { IconText(it, Icons.Filled.Spa, tint = Green) }
                    }
                }
            } else {
                SectionCard {
                    IconText("Trẻ dưới 5 tuổi và phụ nữ mang thai không nên tự dùng thuốc hay thảo dược. Hãy hỏi bác sĩ hoặc dược sĩ trước khi dùng bất cứ thứ gì.",
                        Icons.Filled.Warning, tint = Orange, textColor = Orange)
                }
            }
            SectionCard { MedicalDisclaimer() }
        }
    }
}
