package com.herisoft.caloriescan.core

import org.json.JSONObject

/** Đọc dữ liệu sản phẩm từ API miễn phí của Open Food Facts. */
object OpenFoodFacts {
    val fields = listOf(
        "code", "product_name", "product_name_vi", "product_name_en", "brands",
        "image_front_small_url", "image_front_url", "quantity", "serving_size",
        "serving_quantity", "nutriments",
    )

    /** URL tra cứu, hoặc null nếu mã không hợp lệ. */
    fun url(barcode: String): String? {
        if (barcode.length !in 6..14 || !barcode.all { it in '0'..'9' }) return null
        return "https://world.openfoodfacts.org/api/v2/product/$barcode.json?fields=${fields.joinToString(",")}"
    }

    /** Trả về null khi không tìm thấy sản phẩm. */
    fun parse(json: String, barcode: String): ProductInfo? {
        val root = JSONObject(json)
        if (root.has("status") && lossyDouble(root.opt("status")) == 0.0) return null
        val p = root.optJSONObject("product") ?: return null

        val nutriments = mutableMapOf<String, Double>()
        p.optJSONObject("nutriments")?.let { n ->
            for (key in n.keys()) lossyDouble(n.opt(key))?.let { nutriments[key] = it }
        }
        val kcal100 = nutriments["energy-kcal_100g"]
            ?: nutriments["energy-kj_100g"]?.let(CalorieCalculator::kJToKcal)
            ?: nutriments["energy_100g"]?.let(CalorieCalculator::kJToKcal)
        val kcalServing = nutriments["energy-kcal_serving"]
            ?: nutriments["energy-kj_serving"]?.let(CalorieCalculator::kJToKcal)
            ?: nutriments["energy_serving"]?.let(CalorieCalculator::kJToKcal)

        return ProductInfo(
            barcode = barcode,
            name = p.str("product_name_vi") ?: p.str("product_name") ?: p.str("product_name_en") ?: "Sản phẩm $barcode",
            brand = p.str("brands")?.split(',')?.firstOrNull()?.trim(),
            imageUrl = p.str("image_front_small_url") ?: p.str("image_front_url"),
            quantityText = p.str("quantity"),
            servingSizeText = p.str("serving_size"),
            servingGrams = lossyDouble(p.opt("serving_quantity"))?.takeIf { it > 0 },
            kcalPer100g = kcal100,
            kcalPerServing = kcalServing,
            protein100g = nutriments["proteins_100g"],
            carbs100g = nutriments["carbohydrates_100g"],
            sugars100g = nutriments["sugars_100g"],
            fat100g = nutriments["fat_100g"],
            source = ProductInfo.Source.openFoodFacts,
        )
    }

    private fun JSONObject.str(key: String): String? {
        if (isNull(key)) return null
        val value = opt(key) as? String ?: return null
        return value.trim().ifEmpty { null }
    }

    /** Số có thể là number hoặc chuỗi ("15", "2,5"). */
    private fun lossyDouble(value: Any?): Double? = when (value) {
        is Boolean -> null
        is Number -> value.toDouble()
        is String -> value.trim().replace(',', '.').toDoubleOrNull()
        else -> null
    }
}
