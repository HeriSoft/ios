package com.herisoft.caloriescan.core

import java.text.Normalizer
import kotlin.math.floor

/** Làm tròn kiểu thông thường (0,5 làm tròn lên), giống `rounded()` của Swift với số dương. */
fun Double.roundHalfUp(): Double = if (this >= 0) floor(this + 0.5) else -floor(-this + 0.5)

/** "144 kcal" */
val Double.kcalText: String get() = "${roundHalfUp().toLong()} kcal"

/** Tối đa 1 chữ số thập phân, dấu phẩy kiểu Việt Nam: 6,2 — 30 */
val Double.shortText: String
    get() {
        val r = (this * 10).roundHalfUp() / 10
        return if (r == floor(r)) r.toLong().toString() else String.format(java.util.Locale.ROOT, "%.1f", r).replace('.', ',')
    }

object TextKeys {
    /** Chữ thường, bỏ dấu tiếng Việt (kể cả đ) để tìm kiếm. */
    fun searchKey(text: String): String {
        val replaced = text.replace('đ', 'd').replace('Đ', 'D')
        val decomposed = Normalizer.normalize(replaced, Normalizer.Form.NFD)
        return decomposed.replace(Regex("\\p{M}+"), "").lowercase().trim()
    }
}

object CalorieCalculator {
    fun kcalPer100g(per100g: Double, amount: Double): Double = maxOf(0.0, per100g * amount / 100)
    fun kcalPerServing(perServing: Double, servings: Double): Double = maxOf(0.0, perServing * servings)
    fun kJToKcal(kilojoules: Double): Double = kilojoules / 4.184
}

/** Thông tin dinh dưỡng của một sản phẩm (từ Open Food Facts, từ nhãn, hoặc tự nhập). */
data class ProductInfo(
    val barcode: String? = null,
    val name: String,
    val brand: String? = null,
    val imageUrl: String? = null,
    val quantityText: String? = null,
    val servingSizeText: String? = null,
    val servingGrams: Double? = null,
    val kcalPer100g: Double? = null,
    val kcalPerServing: Double? = null,
    val protein100g: Double? = null,
    val carbs100g: Double? = null,
    val sugars100g: Double? = null,
    val fat100g: Double? = null,
    val source: Source = Source.manual,
) {
    enum class Source { openFoodFacts, label, manual, estimate }

    val effectiveKcalPerServing: Double?
        get() {
            kcalPerServing?.let { return it }
            val per100 = kcalPer100g ?: return null
            val grams = servingGrams ?: return null
            return if (grams > 0) CalorieCalculator.kcalPer100g(per100, grams) else null
        }
}

/** Phân loại nội dung đọc được từ mã vạch / mã QR. */
sealed class ScanPayload {
    data class Barcode(val code: String) : ScanPayload()
    data class Text(val text: String) : ScanPayload()

    companion object {
        fun classify(raw: String): ScanPayload {
            val trimmed = raw.trim()
            if (isBarcode(trimmed)) return Barcode(normalize(trimmed))
            val uri = runCatching { java.net.URI(trimmed) }.getOrNull()
            val scheme = uri?.scheme?.lowercase()
            if (uri != null && scheme != null && scheme.startsWith("http")) {
                val components = (uri.rawPath ?: "").split('/').filter { it.isNotEmpty() }
                components.asReversed().firstOrNull(::isBarcode)?.let { return Barcode(normalize(it)) }
                val query = uri.rawQuery ?: ""
                query.split('&').mapNotNull { it.substringAfter('=', "").ifEmpty { null } }
                    .firstOrNull(::isBarcode)?.let { return Barcode(normalize(it)) }
            }
            return Text(trimmed)
        }

        fun isBarcode(value: String): Boolean =
            value.length in 8..14 && value.all { it in '0'..'9' }

        /** GTIN-14 bắt đầu bằng 0 tương đương EAN-13. */
        private fun normalize(code: String): String =
            if (code.length == 14 && code.startsWith("0")) code.drop(1) else code
    }
}
