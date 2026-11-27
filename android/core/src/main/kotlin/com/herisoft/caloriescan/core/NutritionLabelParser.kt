package com.herisoft.caloriescan.core

data class NutritionLabelResult(
    val kcal: Double?,
    val basis: Basis,
    val servingGrams: Double?,
    /** Tất cả giá trị kcal tìm thấy (ví dụ cột 100 g và cột khẩu phần). */
    val allKcalValues: List<Double>,
) {
    enum class Basis { per100g, perServing }
}

/** Tìm số calo trong văn bản OCR của nhãn dinh dưỡng (tiếng Việt hoặc tiếng Anh). */
object NutritionLabelParser {
    private const val NUMBER = """(\d+(?:\.\d+)?)"""

    fun parse(lines: List<String>): NutritionLabelResult {
        val text = normalize(lines.joinToString(" \n "))

        val numberBeforeKcal = values(NUMBER + """\s*k\s?ca[l1i]""", text)
        val numberAfterKcal = values("""kca[l1i]\)?\s*[:\-/]?\s*""" + NUMBER, text)
        val calories = values("""calo(?:ries?)?\s*[:\-]?\s*""" + NUMBER, text)
        val kilojoules = values(NUMBER + """\s*kj""", text).map(CalorieCalculator::kJToKcal)

        val plausible = { v: Double -> v > 0 && v <= 2000 }
        val kcal = listOf(numberBeforeKcal, numberAfterKcal, calories, kilojoules)
            .map { list -> list.filter(plausible) }
            .firstOrNull { it.isNotEmpty() }?.first()

        val mentions100 = values("""(100)\s?(?:g|ml)\b""", text).isNotEmpty()
        val mentionsServing = Regex("serving|khau phan|phan an|moi phan|1 phan|per pack|portion").containsMatchIn(text)
        val basis = if (!mentions100 && mentionsServing) NutritionLabelResult.Basis.perServing else NutritionLabelResult.Basis.per100g

        val servingGrams = values(
            """(?:serving size|per serving|khau phan|phan an|moi phan|1 phan|portion)[\s\S]{0,40}?""" + NUMBER + """\s*(?:g|ml)\b""",
            text,
        ).firstOrNull { it > 0 && it < 2000 }

        return NutritionLabelResult(kcal, basis, servingGrams, numberBeforeKcal.filter(plausible))
    }

    /** Chữ thường, bỏ dấu tiếng Việt, đổi dấu phẩy thập phân thành dấu chấm. */
    fun normalize(text: String): String =
        TextKeys.searchKey(text).replace(Regex("""(\d),(\d)"""), "$1.$2")

    private fun values(pattern: String, text: String): List<Double> =
        Regex(pattern).findAll(text).mapNotNull { it.groupValues.getOrNull(1)?.toDoubleOrNull() }.toList()
}
