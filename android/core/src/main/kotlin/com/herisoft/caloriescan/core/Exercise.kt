package com.herisoft.caloriescan.core

enum class ExerciseCategory(val title: String) {
    cardio("Cardio"), strength("Sức mạnh"), sport("Thể thao"), flexibility("Dẻo dai & thư giãn"), daily("Hoạt động hằng ngày"),
}

/** Một môn tập với hệ số MET (theo Compendium of Physical Activities). */
data class Exercise(
    val id: String,
    val name: String,
    val aliases: List<String>,
    val met: Double,
    val category: ExerciseCategory,
    /** Tên biểu tượng SF Symbols của bản iOS (bản Android chọn icon theo nhóm). */
    val icon: String,
    /** Có chạy nhảy, tác động mạnh lên khớp. */
    val highImpact: Boolean,
) {
    fun kcal(weightKg: Double, minutes: Double): Double = ExerciseLibrary.kcal(met, weightKg, minutes)
}

object ExerciseLibrary {
    /** Calo đốt: MET × 3,5 × cân nặng (kg) / 200 × số phút. */
    fun kcal(met: Double, weightKg: Double, minutes: Double): Double = maxOf(0.0, met * 3.5 * weightKg / 200 * minutes)

    val all: List<Exercise> = listOf(

        // Cardio
        Exercise(id = "walk-slow", name = "Đi bộ chậm", aliases = listOf("walking", "di bo"), met = 2.8, category = ExerciseCategory.cardio, icon = "figure.walk", highImpact = false),
        Exercise(id = "walk-brisk", name = "Đi bộ nhanh", aliases = listOf("brisk walking", "di bo nhanh"), met = 4.3, category = ExerciseCategory.cardio, icon = "figure.walk.motion", highImpact = false),
        Exercise(id = "jog", name = "Chạy bộ chậm (~8 km/h)", aliases = listOf("jogging", "chay bo"), met = 8.3, category = ExerciseCategory.cardio, icon = "figure.run", highImpact = true),
        Exercise(id = "run", name = "Chạy bộ (~10 km/h)", aliases = listOf("running", "chay"), met = 9.8, category = ExerciseCategory.cardio, icon = "figure.run", highImpact = true),
        Exercise(id = "cycle-easy", name = "Đạp xe nhẹ", aliases = listOf("cycling", "xe dap"), met = 4.0, category = ExerciseCategory.cardio, icon = "figure.outdoor.cycle", highImpact = false),
        Exercise(id = "cycle-moderate", name = "Đạp xe vừa (~20 km/h)", aliases = listOf("cycling", "xe dap"), met = 8.0, category = ExerciseCategory.cardio, icon = "figure.outdoor.cycle", highImpact = false),
        Exercise(id = "swim-easy", name = "Bơi nhẹ nhàng", aliases = listOf("swimming", "boi"), met = 6.0, category = ExerciseCategory.cardio, icon = "figure.pool.swim", highImpact = false),
        Exercise(id = "swim-fast", name = "Bơi nhanh", aliases = listOf("swimming", "boi"), met = 9.8, category = ExerciseCategory.cardio, icon = "figure.pool.swim", highImpact = false),
        Exercise(id = "jump-rope", name = "Nhảy dây", aliases = listOf("jump rope", "nhay day"), met = 11.8, category = ExerciseCategory.cardio, icon = "figure.jumprope", highImpact = true),
        Exercise(id = "stairs", name = "Leo cầu thang", aliases = listOf("stairs", "cau thang"), met = 8.0, category = ExerciseCategory.cardio, icon = "figure.stairs", highImpact = false),
        Exercise(id = "aerobic", name = "Aerobic / Zumba", aliases = listOf("aerobic", "zumba"), met = 7.3, category = ExerciseCategory.cardio, icon = "figure.dance", highImpact = true),
        Exercise(id = "elliptical", name = "Máy tập elip", aliases = listOf("elliptical"), met = 5.0, category = ExerciseCategory.cardio, icon = "figure.elliptical", highImpact = false),

        // Sức mạnh
        Exercise(id = "gym", name = "Tập tạ / gym", aliases = listOf("weight lifting", "gym", "ta"), met = 5.0, category = ExerciseCategory.strength, icon = "dumbbell", highImpact = false),
        Exercise(id = "bodyweight", name = "Bài tập tại nhà (squat, chống đẩy…)", aliases = listOf("bodyweight", "calisthenics", "tai nha"), met = 3.8, category = ExerciseCategory.strength, icon = "figure.strengthtraining.functional", highImpact = false),
        Exercise(id = "hiit", name = "HIIT cường độ cao", aliases = listOf("hiit", "circuit"), met = 8.0, category = ExerciseCategory.strength, icon = "figure.highintensity.intervaltraining", highImpact = true),

        // Thể thao
        Exercise(id = "badminton", name = "Cầu lông", aliases = listOf("badminton", "cau long"), met = 5.5, category = ExerciseCategory.sport, icon = "figure.badminton", highImpact = true),
        Exercise(id = "football", name = "Bóng đá", aliases = listOf("soccer", "football", "da bong"), met = 7.0, category = ExerciseCategory.sport, icon = "figure.soccer", highImpact = true),
        Exercise(id = "basketball", name = "Bóng rổ", aliases = listOf("basketball"), met = 6.5, category = ExerciseCategory.sport, icon = "figure.basketball", highImpact = true),
        Exercise(id = "volleyball", name = "Bóng chuyền", aliases = listOf("volleyball"), met = 4.0, category = ExerciseCategory.sport, icon = "figure.volleyball", highImpact = true),
        Exercise(id = "tennis", name = "Quần vợt", aliases = listOf("tennis"), met = 7.3, category = ExerciseCategory.sport, icon = "figure.tennis", highImpact = true),
        Exercise(id = "table-tennis", name = "Bóng bàn", aliases = listOf("table tennis", "ping pong"), met = 4.0, category = ExerciseCategory.sport, icon = "figure.table.tennis", highImpact = false),
        Exercise(id = "martial-arts", name = "Võ thuật", aliases = listOf("martial arts", "vo", "boxing"), met = 10.3, category = ExerciseCategory.sport, icon = "figure.martial.arts", highImpact = true),

        // Dẻo dai
        Exercise(id = "yoga", name = "Yoga", aliases = listOf("yoga"), met = 2.5, category = ExerciseCategory.flexibility, icon = "figure.yoga", highImpact = false),
        Exercise(id = "stretching", name = "Giãn cơ", aliases = listOf("stretching", "gian co"), met = 2.3, category = ExerciseCategory.flexibility, icon = "figure.flexibility", highImpact = false),
        Exercise(id = "pilates", name = "Pilates", aliases = listOf("pilates"), met = 3.0, category = ExerciseCategory.flexibility, icon = "figure.pilates", highImpact = false),
        Exercise(id = "tai-chi", name = "Thái cực quyền / dưỡng sinh", aliases = listOf("tai chi", "duong sinh"), met = 3.0, category = ExerciseCategory.flexibility, icon = "figure.taichi", highImpact = false),

        // Hằng ngày
        Exercise(id = "housework", name = "Làm việc nhà (lau dọn)", aliases = listOf("housework", "don nha"), met = 3.3, category = ExerciseCategory.daily, icon = "house", highImpact = false),
        Exercise(id = "gardening", name = "Làm vườn", aliases = listOf("gardening"), met = 3.8, category = ExerciseCategory.daily, icon = "leaf", highImpact = false),
        Exercise(id = "dancing", name = "Khiêu vũ / nhảy", aliases = listOf("dancing", "khieu vu"), met = 5.0, category = ExerciseCategory.daily, icon = "figure.socialdance", highImpact = false),
        Exercise(id = "play-kids", name = "Chơi đùa cùng con", aliases = listOf("playing with kids"), met = 3.5, category = ExerciseCategory.daily, icon = "figure.and.child.holdinghands", highImpact = false),
    
    )

    fun exercise(id: String): Exercise? = all.firstOrNull { it.id == id }

    fun search(query: String): List<Exercise> {
        val q = TextKeys.searchKey(query)
        if (q.isEmpty()) return all
        return all.filter { e -> (listOf(e.name) + e.aliases).any { TextKeys.searchKey(it).contains(q) } }
    }
}

/** Động tác tập tại nhà không cần dụng cụ. */
data class HomeMove(
    val id: String,
    val name: String,
    val icon: String,
    val target: String,
    val reps: String,
    val steps: List<String>,
    val easier: String,
    val caution: String,
) {
    companion object {
        val all: List<HomeMove> = listOf(

        HomeMove(id = "squat", name = "Squat (ngồi xổm)", icon = "figure.strengthtraining.functional", target = "Đùi, mông",
                 reps = "3 hiệp × 10–15 lần",
                 steps = listOf("Đứng chân rộng bằng vai, mũi chân hơi mở", "Đẩy hông ra sau như ngồi xuống ghế, lưng thẳng", "Hạ đến khi đùi gần song song sàn rồi đứng lên"),
                 easier = "Ngồi xuống ghế thật rồi đứng lên", caution = "Đầu gối đi cùng hướng mũi chân, không chụm vào trong."),
        HomeMove(id = "pushup", name = "Chống đẩy", icon = "figure.strengthtraining.traditional", target = "Ngực, tay sau, vai",
                 reps = "3 hiệp × 8–12 lần",
                 steps = listOf("Hai tay rộng hơn vai, người thẳng từ đầu tới gót", "Hạ ngực xuống gần sàn, khuỷu tay chếch khoảng 45°", "Đẩy người lên"),
                 easier = "Chống đẩy tựa tường hoặc quỳ gối", caution = "Không võng lưng hay đẩy mông lên cao."),
        HomeMove(id = "plank", name = "Plank", icon = "figure.core.training", target = "Cơ bụng, lưng",
                 reps = "3 lần × 20–45 giây",
                 steps = listOf("Chống khuỷu tay dưới vai", "Người thẳng, siết bụng và mông", "Giữ và thở đều"),
                 easier = "Plank quỳ gối", caution = "Dừng nếu đau lưng dưới."),
        HomeMove(id = "lunge", name = "Lunge (chùng chân)", icon = "figure.step.training", target = "Đùi, mông, thăng bằng",
                 reps = "3 hiệp × 10 lần mỗi chân",
                 steps = listOf("Bước một chân lên trước", "Hạ người đến khi hai gối gập khoảng 90°", "Đẩy chân trước để về vị trí đứng"),
                 easier = "Vịn ghế hoặc tường để giữ thăng bằng", caution = "Gối trước không vượt quá mũi chân nhiều."),
        HomeMove(id = "bridge", name = "Glute bridge (nâng hông)", icon = "figure.cooldown", target = "Mông, lưng dưới",
                 reps = "3 hiệp × 12–15 lần",
                 steps = listOf("Nằm ngửa, co gối, bàn chân trên sàn", "Siết mông đẩy hông lên thành đường thẳng vai–gối", "Giữ 2 giây rồi hạ xuống"),
                 easier = "Giảm biên độ nâng hông", caution = "Không ưỡn lưng quá mức."),
        HomeMove(id = "jumping-jack", name = "Jumping jack (bật nhảy dang tay)", icon = "figure.mixed.cardio", target = "Tim mạch, toàn thân",
                 reps = "3 lần × 30–45 giây",
                 steps = listOf("Bật nhảy dang chân, đồng thời đưa tay lên cao", "Bật về khép chân, hạ tay"),
                 easier = "Bước sang ngang thay vì bật nhảy", caution = "Người thừa cân nhiều hoặc đau khớp gối nên dùng bản không nhảy."),
        HomeMove(id = "mountain-climber", name = "Mountain climber (leo núi tại chỗ)", icon = "figure.highintensity.intervaltraining", target = "Bụng, tim mạch",
                 reps = "3 lần × 20–30 giây",
                 steps = listOf("Tư thế chống đẩy tay thẳng", "Lần lượt kéo gối về phía ngực thật nhanh"),
                 easier = "Làm chậm, chống tay lên ghế", caution = "Giữ hông thấp, không nhổm mông."),
        HomeMove(id = "crunch", name = "Gập bụng (crunch)", icon = "figure.core.training", target = "Cơ bụng",
                 reps = "3 hiệp × 12–15 lần",
                 steps = listOf("Nằm ngửa, co gối, tay đặt nhẹ sau đầu", "Siết bụng nâng vai khỏi sàn", "Hạ xuống chậm"),
                 easier = "Giảm số lần, nâng thấp hơn", caution = "Không kéo cổ bằng tay."),
    
        )
    }
}

data class PlanDay(val day: String, val title: String, val exerciseIDs: List<String>, val minutes: Int) {
    val isRest: Boolean get() = exerciseIDs.isEmpty()
}

data class WorkoutPlan(val days: List<PlanDay>, val notes: List<String>, val lowImpact: Boolean) {
    val weeklyMinutes: Int get() = days.sumOf { it.minutes }
}

object WorkoutPlanner {
    /** Tập nhẹ nhàng cho khớp khi BMI béo phì hoặc từ 60 tuổi. */
    fun needsLowImpact(age: Int, category: BMICategory?): Boolean =
        age >= 60 || category == BMICategory.obese1 || category == BMICategory.obese2

    fun plan(goal: WeightGoal, age: Int, category: BMICategory?): WorkoutPlan {
        val low = needsLowImpact(age, category)
        val cardio = if (low) listOf("walk-brisk", "cycle-easy", "swim-easy") else listOf("walk-brisk", "jog", "cycle-moderate", "swim-easy")
        val intense = if (low) listOf("swim-easy", "elliptical") else listOf("hiit", "jump-rope", "run")
        val strength = listOf("bodyweight", "gym")
        val flex = if (low) listOf("tai-chi", "stretching") else listOf("yoga", "stretching")

        val days = when (goal) {
            WeightGoal.lose -> listOf(
                PlanDay("Thứ 2", "Cardio", cardio, 40),
                PlanDay("Thứ 3", "Sức mạnh toàn thân", strength, 30),
                PlanDay("Thứ 4", "Cardio", cardio, 40),
                PlanDay("Thứ 5", "Dẻo dai", flex, 30),
                PlanDay("Thứ 6", if (low) "Cardio nhẹ" else "Cardio cường độ cao", intense, if (low) 40 else 25),
                PlanDay("Thứ 7", "Sức mạnh toàn thân", strength, 30),
                PlanDay("Chủ nhật", "Nghỉ / đi bộ nhẹ", emptyList(), 0),
            )
            WeightGoal.maintain -> listOf(
                PlanDay("Thứ 2", "Cardio", cardio, 30),
                PlanDay("Thứ 3", "Sức mạnh", strength, 30),
                PlanDay("Thứ 4", "Nghỉ", emptyList(), 0),
                PlanDay("Thứ 5", "Cardio", cardio, 30),
                PlanDay("Thứ 6", "Sức mạnh", strength, 30),
                PlanDay("Thứ 7", "Thể thao / dẻo dai", if (low) flex else listOf("badminton", "football", "yoga"), 45),
                PlanDay("Chủ nhật", "Nghỉ", emptyList(), 0),
            )
            WeightGoal.gain -> listOf(
                PlanDay("Thứ 2", "Sức mạnh: thân dưới", strength, 45),
                PlanDay("Thứ 3", "Nghỉ", emptyList(), 0),
                PlanDay("Thứ 4", "Sức mạnh: thân trên", strength, 45),
                PlanDay("Thứ 5", "Cardio nhẹ", listOf("walk-brisk", "cycle-easy"), 20),
                PlanDay("Thứ 6", "Sức mạnh toàn thân", strength, 45),
                PlanDay("Thứ 7", "Dẻo dai", flex, 30),
                PlanDay("Chủ nhật", "Nghỉ", emptyList(), 0),
            )
        }

        val notes = mutableListOf(
            "WHO khuyến nghị người lớn tập 150–300 phút cường độ vừa mỗi tuần và ít nhất 2 buổi tăng cơ.",
            "Khởi động 5–10 phút trước khi tập và giãn cơ sau khi tập.",
            "Mới bắt đầu: tập 50–70% thời gian gợi ý rồi tăng dần mỗi tuần.",
        )
        notes += when (goal) {
            WeightGoal.lose -> "Giảm cân chủ yếu nhờ ăn uống; tập luyện giúp đốt thêm calo và giữ cơ."
            WeightGoal.gain -> "Tăng tạ hoặc số lần dần mỗi tuần, ăn đủ đạm và ngủ đủ để cơ phát triển."
            WeightGoal.maintain -> "Kết hợp cardio và sức mạnh để giữ sức khỏe tim mạch và cơ bắp."
        }
        if (low) notes += "Lịch đã chọn các môn ít tác động lên khớp (đi bộ, đạp xe, bơi). Tránh chạy nhảy nhiều khi mới bắt đầu."
        notes += "Dừng tập và đi khám nếu đau ngực, khó thở bất thường, chóng mặt. Người có bệnh tim, huyết áp, tiểu đường nên hỏi bác sĩ trước."
        return WorkoutPlan(days, notes, low)
    }
}
