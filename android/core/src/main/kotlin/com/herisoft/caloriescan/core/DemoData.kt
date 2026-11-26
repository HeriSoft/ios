package com.herisoft.caloriescan.core

/** Dữ liệu mẫu cho chế độ demo (chụp màn hình trên CI). */
object DemoData {
    val sampleProduct = ProductInfo(
        barcode = "8930000000017",
        name = "Bánh quy bơ (mẫu)",
        brand = "Sản phẩm demo",
        quantityText = "300 g",
        servingSizeText = "30 g (3 cái)",
        servingGrams = 30.0,
        kcalPer100g = 480.0,
        protein100g = 6.2,
        carbs100g = 64.5,
        sugars100g = 22.0,
        fat100g = 21.4,
        source = ProductInfo.Source.openFoodFacts,
    )

    val labelLines = listOf(
        "THÔNG TIN DINH DƯỠNG",
        "Giá trị dinh dưỡng trong 100 g",
        "Năng lượng 2008 kJ / 480 kcal",
        "Chất đạm 6,2 g",
        "Carbohydrate 64,5 g",
        "Chất béo 21,4 g",
    )

    fun foodGuesses(): List<FoodGuess> = listOf(
        "pho-bo" to 0.62f, "bun-bo-hue" to 0.62f, "hu-tieu" to 0.62f, "mi-goi" to 0.41f, "canh-chua" to 0.18f,
    ).mapNotNull { (id, c) -> FoodDatabase.byId(id)?.let { FoodGuess(it, c) } }

    val symptomInput = SymptomCheckInput(
        symptoms = setOf(Symptom.fever, Symptom.headache, Symptom.muscleAche, Symptom.fatigue),
        duration = SymptomDuration.oneToThreeDays,
        severity = SymptomSeverity.moderate,
    )
}
