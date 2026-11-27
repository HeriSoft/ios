package com.herisoft.caloriescan

import android.app.Application
import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableDoubleStateOf
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.AndroidViewModel
import com.herisoft.caloriescan.core.ActivityLevel
import com.herisoft.caloriescan.core.BodyProfile
import com.herisoft.caloriescan.core.FoodGuess
import com.herisoft.caloriescan.core.ProductInfo
import com.herisoft.caloriescan.core.Sex
import com.herisoft.caloriescan.core.SymptomCheckInput
import com.herisoft.caloriescan.core.WeightGoal
import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID

data class FoodLogEntry(
    val id: String = UUID.randomUUID().toString(),
    val time: Long = System.currentTimeMillis(),
    val name: String,
    val amount: Double,
    val unit: String,
    val kcal: Double,
)

data class WorkoutLogEntry(
    val id: String = UUID.randomUUID().toString(),
    val time: Long = System.currentTimeMillis(),
    val name: String,
    val exerciseId: String,
    val minutes: Double,
    val kcal: Double,
)

/** Trạng thái dùng chung của app, lưu trên máy bằng SharedPreferences (JSON). */
class AppViewModel(app: Application) : AndroidViewModel(app) {
    private val prefs = app.getSharedPreferences("calorie_scan", Context.MODE_PRIVATE)

    val foods = mutableStateListOf<FoodLogEntry>()
    val workouts = mutableStateListOf<WorkoutLogEntry>()
    var dailyGoal by mutableDoubleStateOf(prefs.getFloat("dailyGoal", 2000f).toDouble())
        private set
    var profile by mutableStateOf(loadProfile())
        private set

    // Dữ liệu tạm khi chuyển màn hình
    var selectedProduct by mutableStateOf<ProductInfo?>(null)
    var preferServings by mutableStateOf(false)
    var scannedText by mutableStateOf("")
    var symptomInput by mutableStateOf(SymptomCheckInput())
    var demoFoodGuesses by mutableStateOf<List<FoodGuess>?>(null)
    var demoLabelLines by mutableStateOf<List<String>?>(null)

    init {
        loadLog()
    }

    fun selectProduct(product: ProductInfo, servings: Boolean = false) {
        selectedProduct = product
        preferServings = servings
    }

    fun addFood(entry: FoodLogEntry) { foods.add(0, entry); saveLog() }
    fun removeFood(id: String) { foods.removeAll { it.id == id }; saveLog() }
    fun addWorkout(entry: WorkoutLogEntry) { workouts.add(0, entry); saveLog() }
    fun removeWorkout(id: String) { workouts.removeAll { it.id == id }; saveLog() }

    fun updateGoal(kcal: Double) {
        dailyGoal = kcal.coerceIn(1000.0, 5000.0)
        prefs.edit().putFloat("dailyGoal", dailyGoal.toFloat()).apply()
    }

    fun updateProfile(p: BodyProfile) {
        profile = p
        prefs.edit()
            .putString("sex", p.sex.name).putInt("age", p.age)
            .putFloat("height", p.heightCm.toFloat()).putFloat("weight", p.weightKg.toFloat())
            .putString("activity", p.activity.name).putString("goal", p.goal.name)
            .putFloat("waist", (p.waistCm ?: 0.0).toFloat())
            .apply()
    }

    private fun loadProfile(): BodyProfile = BodyProfile(
        sex = runCatching { Sex.valueOf(prefs.getString("sex", null)!!) }.getOrDefault(Sex.female),
        age = prefs.getInt("age", 28),
        heightCm = prefs.getFloat("height", 158f).toDouble(),
        weightKg = prefs.getFloat("weight", 62f).toDouble(),
        activity = runCatching { ActivityLevel.valueOf(prefs.getString("activity", null)!!) }.getOrDefault(ActivityLevel.light),
        goal = runCatching { WeightGoal.valueOf(prefs.getString("goal", null)!!) }.getOrDefault(WeightGoal.lose),
        waistCm = prefs.getFloat("waist", 0f).toDouble().takeIf { it > 0 },
    )

    private fun saveLog() {
        val f = JSONArray()
        foods.forEach {
            f.put(JSONObject().put("id", it.id).put("time", it.time).put("name", it.name)
                .put("amount", it.amount).put("unit", it.unit).put("kcal", it.kcal))
        }
        val w = JSONArray()
        workouts.forEach {
            w.put(JSONObject().put("id", it.id).put("time", it.time).put("name", it.name)
                .put("exerciseId", it.exerciseId).put("minutes", it.minutes).put("kcal", it.kcal))
        }
        prefs.edit().putString("foods", f.toString()).putString("workouts", w.toString()).apply()
    }

    private fun loadLog() {
        runCatching {
            val f = JSONArray(prefs.getString("foods", "[]"))
            for (i in 0 until f.length()) {
                val o = f.getJSONObject(i)
                foods.add(FoodLogEntry(o.getString("id"), o.getLong("time"), o.getString("name"),
                    o.getDouble("amount"), o.getString("unit"), o.getDouble("kcal")))
            }
            val w = JSONArray(prefs.getString("workouts", "[]"))
            for (i in 0 until w.length()) {
                val o = w.getJSONObject(i)
                workouts.add(WorkoutLogEntry(o.getString("id"), o.getLong("time"), o.getString("name"),
                    o.getString("exerciseId"), o.getDouble("minutes"), o.getDouble("kcal")))
            }
        }
    }

    /** Chế độ demo (chụp màn hình trên CI): dùng dữ liệu mẫu trong bộ nhớ, không lưu. */
    fun seedDemo(withLog: Boolean) {
        foods.clear(); workouts.clear()
        if (!withLog) return
        val dayMs = 24 * 60 * 60 * 1000L
        val now = System.currentTimeMillis()
        listOf(
            FoodLogEntry(time = now - 3 * 3600_000, name = "Sữa chua có đường", amount = 100.0, unit = "g", kcal = 99.0),
            FoodLogEntry(time = now - 3 * 3500_000, name = "Bánh mì sandwich", amount = 2.0, unit = "phần", kcal = 260.0),
            FoodLogEntry(time = now - 2 * 3600_000, name = "Mì ăn liền", amount = 1.0, unit = "phần", kcal = 350.0),
            FoodLogEntry(time = now - dayMs, name = "Ngũ cốc ăn sáng", amount = 40.0, unit = "g", kcal = 152.0),
        ).forEach { foods.add(it) }
        listOf(
            WorkoutLogEntry(time = now - 3600_000, name = "Đi bộ nhanh", exerciseId = "walk-brisk", minutes = 30.0, kcal = 140.0),
            WorkoutLogEntry(time = now - 1800_000, name = "Cầu lông", exerciseId = "badminton", minutes = 45.0, kcal = 268.0),
        ).forEach { workouts.add(it) }
    }
}
