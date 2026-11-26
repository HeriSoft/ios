package com.herisoft.caloriescan.core

import org.junit.Assert.*
import org.junit.Test

class OpenFoodFactsTests {
    @Test fun parsesCaloriesAndMacros() {
        val json = """
        {"code":"3017624010701","status":1,"product":{"product_name":"Nutella","brands":"Ferrero, Nutella",
        "quantity":"400 g","serving_size":"15 g","serving_quantity":"15",
        "nutriments":{"energy-kcal_100g":539,"energy-kcal_serving":80.9,"proteins_100g":6.3,
        "carbohydrates_100g":57.5,"sugars_100g":56.3,"fat_100g":30.9,"nova-group":4,"note":"abc","flag":true}}}
        """
        val p = OpenFoodFacts.parse(json, "3017624010701")!!
        assertEquals("Nutella", p.name)
        assertEquals("Ferrero", p.brand)
        assertEquals("400 g", p.quantityText)
        assertEquals(539.0, p.kcalPer100g!!, 0.0)
        assertEquals(15.0, p.servingGrams!!, 0.0)
        assertEquals(80.9, p.kcalPerServing!!, 0.001)
        assertEquals(6.3, p.protein100g!!, 0.0)
        assertEquals(ProductInfo.Source.openFoodFacts, p.source)
    }

    @Test fun numbersAsStringsAndKilojouleFallback() {
        val p = OpenFoodFacts.parse("""{"status":1,"product":{"product_name":"Test","nutriments":{"energy_100g":"2092"}}}""", "12345678")!!
        assertEquals(500.0, p.kcalPer100g!!, 0.1)
        assertNull(p.kcalPerServing)
    }

    @Test fun prefersVietnameseName() {
        val p = OpenFoodFacts.parse("""{"status":1,"product":{"product_name":"Fresh milk","product_name_vi":"Sữa tươi","nutriments":{}}}""", "12345678")!!
        assertEquals("Sữa tươi", p.name)
    }

    @Test fun missingNameFallsBackToBarcode() {
        val p = OpenFoodFacts.parse("""{"status":1,"product":{"product_name":"  ","brands":null,"nutriments":{}}}""", "12345678")!!
        assertEquals("Sản phẩm 12345678", p.name)
        assertNull(p.brand)
        assertNull(p.kcalPer100g)
    }

    @Test fun productNotFound() {
        assertNull(OpenFoodFacts.parse("""{"code":"000","status":0,"status_verbose":"product not found"}""", "000"))
    }

    @Test fun urlValidation() {
        assertNull(OpenFoodFacts.url("abc"))
        assertNull(OpenFoodFacts.url("12"))
        assertTrue(OpenFoodFacts.url("3017624010701")!!.startsWith("https://world.openfoodfacts.org/api/v2/product/3017624010701.json"))
    }
}

class NutritionLabelParserTests {
    @Test fun vietnameseLabelPer100g() {
        val r = NutritionLabelParser.parse(listOf("THÔNG TIN DINH DƯỠNG", "Giá trị dinh dưỡng trong 100 g", "Năng lượng 2008 kJ / 480 kcal", "Chất đạm 6,2 g"))
        assertEquals(480.0, r.kcal!!, 0.0)
        assertEquals(NutritionLabelResult.Basis.per100g, r.basis)
    }

    @Test fun kcalBeforeValue() {
        val r = NutritionLabelParser.parse(listOf("Energy (kcal) 250", "per 100ml"))
        assertEquals(250.0, r.kcal!!, 0.0)
        assertEquals(NutritionLabelResult.Basis.per100g, r.basis)
    }

    @Test fun usNutritionFacts() {
        val r = NutritionLabelParser.parse(listOf("Nutrition Facts", "Serving size 2/3 cup (55g)", "Calories 230", "Total Fat 8g",
            "2,000 calories a day is used for general nutrition advice."))
        assertEquals(230.0, r.kcal!!, 0.0)
        assertEquals(NutritionLabelResult.Basis.perServing, r.basis)
        assertEquals(55.0, r.servingGrams!!, 0.0)
    }

    @Test fun decimalComma() {
        assertEquals(52.5, NutritionLabelParser.parse(listOf("Năng lượng: 52,5 kcal/100ml")).kcal!!, 0.0)
    }

    @Test fun kilojouleOnly() {
        assertEquals(239.0, NutritionLabelParser.parse(listOf("Energy 1000 kJ per 100 g")).kcal!!, 0.1)
    }

    @Test fun twoColumns() {
        val r = NutritionLabelParser.parse(listOf("Trong 100 g | Khẩu phần 30 g", "Năng lượng 539 kcal 162 kcal"))
        assertEquals(539.0, r.kcal!!, 0.0)
        assertEquals(listOf(539.0, 162.0), r.allKcalValues)
        assertEquals(30.0, r.servingGrams!!, 0.0)
    }

    @Test fun noEnergyFound() {
        assertNull(NutritionLabelParser.parse(listOf("Hello world", "Thành phần: bột mì, đường")).kcal)
    }
}

class ScanPayloadTests {
    @Test fun plainBarcode() {
        assertEquals(ScanPayload.Barcode("3017624010701"), ScanPayload.classify("3017624010701"))
        assertEquals(ScanPayload.Barcode("5449000000996"), ScanPayload.classify(" 5449000000996\n"))
    }

    @Test fun openFoodFactsLink() {
        assertEquals(ScanPayload.Barcode("3017624010701"), ScanPayload.classify("https://world.openfoodfacts.org/product/3017624010701/nutella"))
    }

    @Test fun gs1DigitalLink() {
        assertEquals(ScanPayload.Barcode("9506000134352"), ScanPayload.classify("https://id.gs1.org/01/09506000134352"))
    }

    @Test fun otherContent() {
        assertEquals(ScanPayload.Text("https://example.com"), ScanPayload.classify("https://example.com"))
        assertEquals(ScanPayload.Text("WIFI:S:Home;T:WPA;P:secret;;"), ScanPayload.classify("WIFI:S:Home;T:WPA;P:secret;;"))
        assertEquals(ScanPayload.Text("12345"), ScanPayload.classify("12345"))
    }
}

class CalorieAndFoodTests {
    @Test fun calculator() {
        assertEquals(144.0, CalorieCalculator.kcalPer100g(480.0, 30.0), 0.001)
        assertEquals(0.0, CalorieCalculator.kcalPer100g(480.0, -5.0), 0.0)
        assertEquals(200.0, CalorieCalculator.kcalPerServing(80.0, 2.5), 0.001)
        assertEquals(144.0, ProductInfo(name = "X", servingGrams = 30.0, kcalPer100g = 480.0).effectiveKcalPerServing!!, 0.001)
    }

    @Test fun formatting() {
        assertEquals("144 kcal", 143.6.kcalText)
        assertEquals("6,2", 6.2.shortText)
        assertEquals("30", 30.0.shortText)
        assertEquals("2,2", 2.17.shortText)
    }

    @Test fun foodTableIsConsistent() {
        val ids = FoodDatabase.all.map { it.id }
        assertEquals(68, ids.size)
        assertEquals(ids.size, ids.toSet().size)
        for (f in FoodDatabase.all) {
            assertTrue(f.name, f.kcalPer100g in 10.0..950.0)
            assertTrue(f.name, f.portionGrams > 0)
            assertTrue(f.name, f.visionLabels.isNotEmpty())
        }
    }

    @Test fun matchSortsByConfidenceAndDeduplicates() {
        val g = FoodDatabase.match(listOf("banana" to 0.9f, "fruit" to 0.5f, "ramen" to 0.3f))
        assertEquals("chuoi", g.first().food.id)
        assertEquals(1, g.count { it.food.id == "chuoi" })
        assertTrue(g.any { it.food.id == "pho-bo" })
        assertTrue(g.size <= 6)
    }

    @Test fun matchIsCaseAndPluralInsensitive() {
        assertEquals("ga-ran", FoodDatabase.match(listOf("Fried_Chicken" to 0.8f)).first().food.id)
        assertTrue(FoodDatabase.match(listOf("Bananas" to 0.8f)).any { it.food.id == "chuoi" })
        assertTrue(FoodDatabase.match(listOf("Pizza" to 0.8f)).any { it.food.id == "pizza" })
        assertTrue(FoodDatabase.match(listOf("car" to 0.9f, "sky" to 0.8f)).isEmpty())
    }

    @Test fun searchIgnoresDiacritics() {
        assertTrue(FoodDatabase.search("pho").any { it.id == "pho-bo" })
        assertTrue(FoodDatabase.search("Cơm Tấm").any { it.id == "com-tam" })
        assertTrue(FoodDatabase.search("dua hau").any { it.id == "dua-hau" })
        assertTrue(FoodDatabase.search("banana").any { it.id == "chuoi" })
        assertEquals(FoodDatabase.all.size, FoodDatabase.search("").size)
        assertTrue(FoodDatabase.search("xyz123").isEmpty())
    }

    @Test fun portionCalories() {
        val pho = FoodDatabase.byId("pho-bo")!!
        assertEquals(450.0, pho.kcalPerPortion, 0.01)
        assertEquals(450.0, pho.productInfo.effectiveKcalPerServing!!, 0.01)
        assertEquals(ProductInfo.Source.estimate, pho.productInfo.source)
    }
}
