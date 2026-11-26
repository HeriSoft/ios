package com.herisoft.caloriescan.core

import kotlin.math.pow

enum class Sex(val title: String) { male("Nam"), female("Nữ") }

enum class ActivityLevel(val factor: Double, val title: String) {
    sedentary(1.2, "Ít vận động (ngồi nhiều)"),
    light(1.375, "Nhẹ (tập 1–3 buổi/tuần)"),
    moderate(1.55, "Vừa (tập 3–5 buổi/tuần)"),
    active(1.725, "Nhiều (tập 6–7 buổi/tuần)"),
    veryActive(1.9, "Rất nhiều (lao động nặng)"),
}

enum class WeightGoal(val title: String) { lose("Giảm cân"), maintain("Giữ cân"), gain("Tăng cân") }

data class BodyProfile(
    val sex: Sex,
    val age: Int,
    val heightCm: Double,
    val weightKg: Double,
    val activity: ActivityLevel,
    val goal: WeightGoal,
    /** Vòng eo (cm), không bắt buộc. */
    val waistCm: Double? = null,
) {
    val isValid: Boolean get() = age in 10..100 && heightCm in 100.0..250.0 && weightKg in 20.0..300.0
}

/** Phân loại BMI cho người trưởng thành châu Á (Bộ Y tế Việt Nam áp dụng). */
enum class BMICategory(val title: String) {
    underweight("Thiếu cân"), normal("Bình thường"), overweight("Thừa cân"), obese1("Béo phì độ I"), obese2("Béo phì độ II");

    companion object {
        fun of(bmi: Double): BMICategory = when {
            bmi < 18.5 -> underweight
            bmi < 23 -> normal
            bmi < 25 -> overweight
            bmi < 30 -> obese1
            else -> obese2
        }
    }
}

data class BodyReport(
    val bmi: Double,
    val category: BMICategory,
    /** Cân nặng ứng với BMI 18,5–22,9. */
    val healthyWeightRange: ClosedFloatingPointRange<Double>,
    /** Dương = cần tăng, âm = cần giảm, 0 = đã hợp lý. */
    val weightChangeToHealthy: Double,
    val bmr: Double,
    val tdee: Double,
    val targetKcal: Double,
    val proteinGrams: Double,
    val fatGrams: Double,
    val carbGrams: Double,
    val waterLiters: Double,
    val bodyFatPercent: Double?,
    val waistToHeight: Double?,
    val isAdult: Boolean,
)

object HealthCalculator {
    val healthyBMI = 18.5..22.9

    fun bmi(weightKg: Double, heightCm: Double): Double {
        val m = heightCm / 100
        return weightKg / (m * m)
    }

    /** Năng lượng tiêu hao khi nghỉ (Mifflin-St Jeor). */
    fun bmr(p: BodyProfile): Double {
        val base = 10 * p.weightKg + 6.25 * p.heightCm - 5 * p.age
        return base + if (p.sex == Sex.male) 5 else -161
    }

    fun minimumKcal(sex: Sex): Double = if (sex == Sex.female) 1200.0 else 1500.0

    fun report(p: BodyProfile): BodyReport? {
        if (!p.isValid) return null
        val bmi = bmi(p.weightKg, p.heightCm)
        val m2 = (p.heightCm / 100).pow(2)
        val range = (healthyBMI.start * m2)..(healthyBMI.endInclusive * m2)
        val change = when {
            p.weightKg < range.start -> range.start - p.weightKg
            p.weightKg > range.endInclusive -> range.endInclusive - p.weightKg
            else -> 0.0
        }
        val bmr = bmr(p)
        val tdee = bmr * p.activity.factor
        val target = when (p.goal) {
            WeightGoal.lose -> minOf(tdee, maxOf(tdee - 500, minimumKcal(p.sex)))
            WeightGoal.maintain -> tdee
            WeightGoal.gain -> tdee + 300
        }
        val rounded = (target / 10).roundHalfUp() * 10
        val protein = (if (p.goal == WeightGoal.maintain) 1.2 else 1.6) * p.weightKg
        val fat = rounded * 0.27 / 9
        val carbs = maxOf(0.0, (rounded - protein * 4 - fat * 9) / 4)
        val adult = p.age >= 18
        val bodyFat = if (adult) maxOf(3.0, 1.2 * bmi + 0.23 * p.age - 10.8 * (if (p.sex == Sex.male) 1 else 0) - 5.4) else null
        return BodyReport(
            bmi = bmi, category = BMICategory.of(bmi), healthyWeightRange = range,
            weightChangeToHealthy = change, bmr = bmr, tdee = tdee, targetKcal = rounded,
            proteinGrams = protein, fatGrams = fat, carbGrams = carbs, waterLiters = p.weightKg * 0.035,
            bodyFatPercent = bodyFat, waistToHeight = p.waistCm?.takeIf { it > 0 }?.let { it / p.heightCm },
            isAdult = adult,
        )
    }
}

data class FoodSuggestion(val food: FoodItem, val reason: String)
data class NutritionAdvice(val eatMore: List<FoodSuggestion>, val limit: List<FoodSuggestion>, val tips: List<String>)

/** Gợi ý thực phẩm theo mục tiêu và chỉ số cơ thể (lời khuyên chung). */
object NutritionAdvisor {
    val eatMore: Map<WeightGoal, List<Pair<String, String>>> = mapOf(
        WeightGoal.lose to listOf(
            "trung-luoc" to "Nhiều đạm, ít calo, giúp no lâu",
            "canh-chua" to "Nhiều nước và rau, rất ít calo",
            "rau-xao" to "Chất xơ giúp no lâu, ít năng lượng",
            "goi-cuon" to "Nhiều rau, ít dầu mỡ hơn món chiên",
            "pho-ga" to "Đủ đạm; chọn tô nhỏ, ít bánh phở",
            "oi" to "Nhiều chất xơ và vitamin C",
            "du-du" to "Ít calo, tốt cho tiêu hóa",
            "dua-hau" to "Rất ít calo, nhiều nước",
        ),
        WeightGoal.maintain to listOf(
            "ca-kho" to "Cá cung cấp đạm và chất béo tốt",
            "rau-xao" to "Rau xanh mỗi bữa cho đủ chất xơ",
            "trung-luoc" to "Nguồn đạm rẻ và dễ chế biến",
            "com-trang" to "Tinh bột vừa đủ: khoảng 1–2 chén mỗi bữa",
            "canh-chua" to "Bổ sung rau và nước",
            "chuoi" to "Kali và năng lượng cho buổi tập",
            "cam" to "Vitamin C, ăn nguyên quả tốt hơn uống nước ép",
        ),
        WeightGoal.gain to listOf(
            "bo" to "Chất béo tốt, nhiều năng lượng trong khẩu phần nhỏ",
            "sinh-to" to "Dễ uống thêm calo giữa các bữa",
            "trung-chien" to "Đạm và năng lượng để tăng cơ",
            "com-tam" to "Nhiều năng lượng và đạm",
            "xoi" to "Tinh bột đậm đặc cho bữa sáng",
            "chuoi" to "Bữa phụ nhanh, nhiều năng lượng",
            "sua-tuoi" to "Thêm đạm và calo, uống sau khi tập",
            "banh-mi-thit" to "Bữa phụ tiện lợi, đủ đạm và tinh bột",
        ),
    )

    val limit: Map<WeightGoal, List<Pair<String, String>>> = mapOf(
        WeightGoal.lose to listOf(
            "tra-sua" to "Nhiều đường: 1 ly ≈ 1 bữa ăn",
            "nuoc-ngot" to "Calo rỗng, không giúp no",
            "ga-ran" to "Nhiều dầu mỡ",
            "khoai-tay-chien" to "Nhiều dầu, dễ ăn quá nhiều",
            "banh-ngot" to "Nhiều đường và chất béo",
            "cha-gio" to "Chiên ngập dầu",
        ),
        WeightGoal.maintain to listOf(
            "nuoc-ngot" to "Calo rỗng, dễ tăng cân khi uống thường xuyên",
            "tra-sua" to "Nhiều đường",
            "ga-ran" to "Nhiều dầu mỡ, nên ăn thỉnh thoảng",
        ),
        WeightGoal.gain to listOf(
            "nuoc-ngot" to "Calo rỗng, không giúp tăng cơ",
            "khoai-tay-chien" to "Nên tăng cân bằng thức ăn giàu đạm thay vì đồ chiên",
        ),
    )

    fun advice(profile: BodyProfile, report: BodyReport): NutritionAdvice {
        fun suggestions(list: List<Pair<String, String>>?) =
            list.orEmpty().mapNotNull { (id, reason) -> FoodDatabase.byId(id)?.let { FoodSuggestion(it, reason) } }

        val tips = mutableListOf<String>()
        if (!report.isAdult) tips += "Dưới 18 tuổi cần đánh giá theo biểu đồ tăng trưởng theo tuổi. Kết quả ở đây chỉ để tham khảo, hãy hỏi bác sĩ nhi khoa."
        if (profile.goal == WeightGoal.lose && report.category == BMICategory.underweight)
            tips += "Bạn đang thiếu cân, không nên giảm cân thêm. Hãy cân nhắc mục tiêu \"Giữ cân\" hoặc \"Tăng cân\"."
        if (profile.goal == WeightGoal.gain && (report.category == BMICategory.obese1 || report.category == BMICategory.obese2))
            tips += "Chỉ số BMI đang ở mức béo phì, nên hỏi ý kiến bác sĩ trước khi tăng cân."
        when (report.category) {
            BMICategory.obese1, BMICategory.obese2 -> tips += "BMI ở mức béo phì làm tăng nguy cơ tiểu đường, huyết áp cao và tim mạch. Nên khám sức khỏe định kỳ."
            BMICategory.underweight -> tips += "Thiếu cân kéo dài có thể do ăn chưa đủ hoặc vấn đề sức khỏe khác. Nếu sụt cân không rõ lý do, hãy đi khám."
            else -> {}
        }
        if ((report.waistToHeight ?: 0.0) > 0.5)
            tips += "Vòng eo lớn hơn một nửa chiều cao: mỡ bụng nhiều, tăng nguy cơ bệnh chuyển hóa. Ưu tiên giảm vòng eo."
        tips += when (profile.goal) {
            WeightGoal.lose -> "Giảm khoảng 0,5 kg mỗi tuần là an toàn. Đừng ăn dưới ${HealthCalculator.minimumKcal(profile.sex).toInt()} kcal/ngày nếu không có hướng dẫn của chuyên gia."
            WeightGoal.gain -> "Tăng cân kèm tập sức mạnh 2–3 buổi/tuần để tăng cơ thay vì tăng mỡ."
            WeightGoal.maintain -> "Giữ cân bằng cách ăn đủ bữa, nhiều rau và theo dõi cân nặng mỗi tuần."
        }
        tips += "Ăn khoảng ${report.proteinGrams.roundHalfUp().toInt()} g đạm mỗi ngày, chia đều các bữa (thịt, cá, trứng, đậu, sữa)."
        tips += "Uống khoảng ${report.waterLiters.shortText} lít nước mỗi ngày, nhiều hơn khi trời nóng hoặc tập luyện."
        return NutritionAdvice(suggestions(eatMore[profile.goal]), suggestions(limit[profile.goal]), tips)
    }
}
