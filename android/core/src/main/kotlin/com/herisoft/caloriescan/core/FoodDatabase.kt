package com.herisoft.caloriescan.core

/** Một món ăn với lượng calo ước tính trung bình. */
data class FoodItem(
    val id: String,
    val name: String,
    val aliases: List<String>,
    val kcalPer100g: Double,
    val portionGrams: Double,
    val portionName: String,
    /** Nhãn nhận diện ảnh (tiếng Anh, chữ thường). */
    val visionLabels: List<String>,
) {
    val kcalPerPortion: Double get() = CalorieCalculator.kcalPer100g(kcalPer100g, portionGrams)

    val productInfo: ProductInfo
        get() = ProductInfo(
            name = name,
            servingSizeText = "$portionName ≈ ${portionGrams.toInt()} g",
            servingGrams = portionGrams,
            kcalPer100g = kcalPer100g,
            source = ProductInfo.Source.estimate,
        )
}

data class FoodGuess(val food: FoodItem, val confidence: Float)

/** Bảng calo ước tính cho các món phổ biến (giá trị trung bình, thay đổi theo cách chế biến). */
object FoodDatabase {
    val all: List<FoodItem> = listOf(

        // Món Việt
        FoodItem(id = "pho-bo", name = "Phở bò", aliases = listOf("pho", "beef noodle soup"), kcalPer100g = 90.0, portionGrams = 500.0, portionName = "1 tô", visionLabels = listOf("ramen", "soup", "beef")),
        FoodItem(id = "pho-ga", name = "Phở gà", aliases = listOf("chicken pho"), kcalPer100g = 80.0, portionGrams = 500.0, portionName = "1 tô", visionLabels = listOf("ramen", "soup", "poultry")),
        FoodItem(id = "bun-bo-hue", name = "Bún bò Huế", aliases = listOf("bun bo", "spicy beef noodle soup"), kcalPer100g = 95.0, portionGrams = 550.0, portionName = "1 tô", visionLabels = listOf("ramen", "soup", "beef")),
        FoodItem(id = "hu-tieu", name = "Hủ tiếu", aliases = listOf("hu tieu", "noodle soup"), kcalPer100g = 85.0, portionGrams = 500.0, portionName = "1 tô", visionLabels = listOf("ramen", "soup", "seafood")),
        FoodItem(id = "bun-cha", name = "Bún chả", aliases = listOf("grilled pork with noodles"), kcalPer100g = 125.0, portionGrams = 450.0, portionName = "1 phần", visionLabels = listOf("grill", "meatball", "satay", "spareribs")),
        FoodItem(id = "mi-xao", name = "Mì xào", aliases = listOf("fried noodles", "stir fried noodles"), kcalPer100g = 180.0, portionGrams = 300.0, portionName = "1 đĩa", visionLabels = listOf("stir fry", "pasta", "spaghetti")),
        FoodItem(id = "mi-goi", name = "Mì gói (đã nấu)", aliases = listOf("instant noodles", "mi tom", "mì tôm"), kcalPer100g = 140.0, portionGrams = 300.0, portionName = "1 tô", visionLabels = listOf("ramen")),
        FoodItem(id = "com-trang", name = "Cơm trắng", aliases = listOf("rice", "steamed rice"), kcalPer100g = 130.0, portionGrams = 150.0, portionName = "1 chén", visionLabels = listOf("rice", "grain")),
        FoodItem(id = "com-tam", name = "Cơm tấm sườn", aliases = listOf("broken rice", "com suon"), kcalPer100g = 150.0, portionGrams = 450.0, portionName = "1 đĩa", visionLabels = listOf("rice", "spareribs", "grill")),
        FoodItem(id = "com-chien", name = "Cơm chiên", aliases = listOf("fried rice"), kcalPer100g = 170.0, portionGrams = 350.0, portionName = "1 đĩa", visionLabels = listOf("rice", "stir fry", "risotto", "biryani")),
        FoodItem(id = "com-ga", name = "Cơm gà", aliases = listOf("chicken rice"), kcalPer100g = 160.0, portionGrams = 400.0, portionName = "1 đĩa", visionLabels = listOf("rice", "grilled chicken", "poultry")),
        FoodItem(id = "xoi", name = "Xôi", aliases = listOf("sticky rice", "xoi"), kcalPer100g = 200.0, portionGrams = 200.0, portionName = "1 gói", visionLabels = listOf("rice", "grain")),
        FoodItem(id = "chao", name = "Cháo", aliases = listOf("rice porridge", "congee"), kcalPer100g = 60.0, portionGrams = 400.0, portionName = "1 tô", visionLabels = listOf("oatmeal", "soup", "risotto")),
        FoodItem(id = "banh-mi-thit", name = "Bánh mì thịt", aliases = listOf("banh mi", "vietnamese sandwich"), kcalPer100g = 230.0, portionGrams = 200.0, portionName = "1 ổ", visionLabels = listOf("sandwich", "bread")),
        FoodItem(id = "banh-xeo", name = "Bánh xèo", aliases = listOf("vietnamese pancake"), kcalPer100g = 210.0, portionGrams = 200.0, portionName = "1 cái", visionLabels = listOf("crepe", "pancake", "omelet", "tortilla")),
        FoodItem(id = "goi-cuon", name = "Gỏi cuốn", aliases = listOf("spring roll", "fresh spring roll", "summer roll"), kcalPer100g = 115.0, portionGrams = 70.0, portionName = "1 cuốn", visionLabels = listOf("springroll", "dumpling", "burrito")),
        FoodItem(id = "cha-gio", name = "Chả giò", aliases = listOf("fried spring roll", "egg roll", "nem ran"), kcalPer100g = 250.0, portionGrams = 40.0, portionName = "1 cuốn", visionLabels = listOf("springroll", "tempura", "samosa")),
        FoodItem(id = "banh-cuon", name = "Bánh cuốn", aliases = listOf("steamed rice rolls"), kcalPer100g = 150.0, portionGrams = 300.0, portionName = "1 đĩa", visionLabels = listOf("dumpling", "crepe", "wonton")),
        FoodItem(id = "banh-bao", name = "Bánh bao", aliases = listOf("steamed bun", "bao"), kcalPer100g = 230.0, portionGrams = 120.0, portionName = "1 cái", visionLabels = listOf("dumpling", "bread", "baked goods")),
        FoodItem(id = "thit-kho", name = "Thịt kho trứng", aliases = listOf("braised pork with eggs"), kcalPer100g = 220.0, portionGrams = 200.0, portionName = "1 phần", visionLabels = listOf("meat", "casserole", "egg", "curry")),
        FoodItem(id = "ca-kho", name = "Cá kho", aliases = listOf("braised fish"), kcalPer100g = 180.0, portionGrams = 150.0, portionName = "1 khúc", visionLabels = listOf("fish", "seafood", "casserole")),
        FoodItem(id = "canh-chua", name = "Canh chua", aliases = listOf("sour soup"), kcalPer100g = 35.0, portionGrams = 300.0, portionName = "1 chén", visionLabels = listOf("soup")),
        FoodItem(id = "rau-xao", name = "Rau muống xào tỏi", aliases = listOf("stir fried vegetables", "morning glory"), kcalPer100g = 70.0, portionGrams = 200.0, portionName = "1 đĩa", visionLabels = listOf("vegetable", "stir fry", "spinach", "broccoli", "green beans")),
        FoodItem(id = "trung-chien", name = "Trứng chiên", aliases = listOf("fried egg", "omelette"), kcalPer100g = 196.0, portionGrams = 60.0, portionName = "1 quả", visionLabels = listOf("fried egg", "omelet", "scrambled eggs", "egg", "yolk")),
        FoodItem(id = "trung-luoc", name = "Trứng luộc", aliases = listOf("boiled egg"), kcalPer100g = 155.0, portionGrams = 50.0, portionName = "1 quả", visionLabels = listOf("egg", "yolk")),
        FoodItem(id = "che", name = "Chè", aliases = listOf("sweet soup", "dessert"), kcalPer100g = 150.0, portionGrams = 250.0, portionName = "1 ly", visionLabels = listOf("dessert", "pudding", "tapioca pearls", "jelly")),
        FoodItem(id = "ca-phe-sua", name = "Cà phê sữa đá", aliases = listOf("iced milk coffee", "ca phe sua"), kcalPer100g = 60.0, portionGrams = 200.0, portionName = "1 ly", visionLabels = listOf("coffee", "drink")),
        FoodItem(id = "tra-sua", name = "Trà sữa trân châu", aliases = listOf("bubble tea", "milk tea", "boba"), kcalPer100g = 70.0, portionGrams = 500.0, portionName = "1 ly", visionLabels = listOf("bubble tea", "tapioca pearls", "tea drink", "milkshake")),

        // Đồ ăn nhanh & món Âu
        FoodItem(id = "pizza", name = "Pizza", aliases = listOf("pizza"), kcalPer100g = 266.0, portionGrams = 110.0, portionName = "1 miếng", visionLabels = listOf("pizza", "pepperoni")),
        FoodItem(id = "hamburger", name = "Hamburger", aliases = listOf("burger", "hamburger"), kcalPer100g = 254.0, portionGrams = 200.0, portionName = "1 cái", visionLabels = listOf("hamburger")),
        FoodItem(id = "khoai-tay-chien", name = "Khoai tây chiên", aliases = listOf("french fries", "fries", "chips"), kcalPer100g = 312.0, portionGrams = 117.0, portionName = "1 phần vừa", visionLabels = listOf("fries")),
        FoodItem(id = "ga-ran", name = "Gà rán", aliases = listOf("fried chicken"), kcalPer100g = 260.0, portionGrams = 150.0, portionName = "1 miếng", visionLabels = listOf("fried chicken", "poultry")),
        FoodItem(id = "hot-dog", name = "Xúc xích kẹp (hot dog)", aliases = listOf("hot dog", "hotdog"), kcalPer100g = 290.0, portionGrams = 100.0, portionName = "1 cái", visionLabels = listOf("hotdog", "sausage")),
        FoodItem(id = "sandwich", name = "Sandwich", aliases = listOf("sandwich"), kcalPer100g = 250.0, portionGrams = 150.0, portionName = "1 cái", visionLabels = listOf("sandwich", "white bread")),
        FoodItem(id = "mi-y", name = "Mì Ý sốt bò", aliases = listOf("spaghetti", "pasta", "bolognese"), kcalPer100g = 160.0, portionGrams = 350.0, portionName = "1 đĩa", visionLabels = listOf("spaghetti", "pasta", "meatball")),
        FoodItem(id = "bit-tet", name = "Bít tết", aliases = listOf("steak", "beef steak"), kcalPer100g = 270.0, portionGrams = 200.0, portionName = "1 miếng", visionLabels = listOf("steak", "beef", "meat")),
        FoodItem(id = "sushi", name = "Sushi", aliases = listOf("sushi", "maki"), kcalPer100g = 150.0, portionGrams = 180.0, portionName = "6 miếng", visionLabels = listOf("sushi", "salmon", "tuna", "roe", "wasabi", "seafood")),
        FoodItem(id = "salad", name = "Salad rau trộn dầu giấm", aliases = listOf("salad", "green salad"), kcalPer100g = 80.0, portionGrams = 200.0, portionName = "1 đĩa", visionLabels = listOf("salad", "lettuce", "arugula", "coleslaw", "vegetable")),
        FoodItem(id = "banh-mi-sandwich", name = "Bánh mì sandwich (lát)", aliases = listOf("white bread", "toast"), kcalPer100g = 265.0, portionGrams = 30.0, portionName = "1 lát", visionLabels = listOf("white bread", "bread")),
        FoodItem(id = "banh-ngot", name = "Bánh kem", aliases = listOf("cake", "birthday cake"), kcalPer100g = 350.0, portionGrams = 80.0, portionName = "1 miếng", visionLabels = listOf("cake", "birthday cake", "cake regular", "cupcake", "cheesecake", "wedding cake", "dessert")),
        FoodItem(id = "banh-quy", name = "Bánh quy", aliases = listOf("cookie", "biscuit"), kcalPer100g = 480.0, portionGrams = 30.0, portionName = "3 cái", visionLabels = listOf("cookie", "biscuit", "chocolate chip")),
        FoodItem(id = "donut", name = "Bánh donut", aliases = listOf("donut", "doughnut"), kcalPer100g = 452.0, portionGrams = 60.0, portionName = "1 cái", visionLabels = listOf("donut")),
        FoodItem(id = "croissant", name = "Bánh sừng bò", aliases = listOf("croissant"), kcalPer100g = 406.0, portionGrams = 60.0, portionName = "1 cái", visionLabels = listOf("croissant", "pastry", "baked goods")),
        FoodItem(id = "kem", name = "Kem", aliases = listOf("ice cream"), kcalPer100g = 207.0, portionGrams = 100.0, portionName = "1 ly/2 viên", visionLabels = listOf("ice cream", "frozen dessert", "popsicle")),
        FoodItem(id = "nuoc-ngot", name = "Nước ngọt có ga", aliases = listOf("soda", "soft drink", "coke"), kcalPer100g = 42.0, portionGrams = 330.0, portionName = "1 lon", visionLabels = listOf("soda", "drink")),
        FoodItem(id = "sua-tuoi", name = "Sữa tươi có đường", aliases = listOf("milk"), kcalPer100g = 75.0, portionGrams = 180.0, portionName = "1 hộp", visionLabels = listOf("drink", "milkshake")),

        // Trái cây
        FoodItem(id = "chuoi", name = "Chuối", aliases = listOf("banana"), kcalPer100g = 89.0, portionGrams = 120.0, portionName = "1 quả", visionLabels = listOf("banana", "fruit")),
        FoodItem(id = "tao", name = "Táo", aliases = listOf("apple"), kcalPer100g = 52.0, portionGrams = 180.0, portionName = "1 quả", visionLabels = listOf("apple", "fruit")),
        FoodItem(id = "cam", name = "Cam", aliases = listOf("orange"), kcalPer100g = 47.0, portionGrams = 150.0, portionName = "1 quả", visionLabels = listOf("oranges", "citrus fruit", "mandarine", "fruit")),
        FoodItem(id = "xoai", name = "Xoài", aliases = listOf("mango"), kcalPer100g = 60.0, portionGrams = 200.0, portionName = "1 quả", visionLabels = listOf("mango", "fruit")),
        FoodItem(id = "dua-hau", name = "Dưa hấu", aliases = listOf("watermelon"), kcalPer100g = 30.0, portionGrams = 300.0, portionName = "1 miếng lớn", visionLabels = listOf("watermelon", "melon", "fruit")),
        FoodItem(id = "nho", name = "Nho", aliases = listOf("grape", "grapes"), kcalPer100g = 69.0, portionGrams = 100.0, portionName = "1 chùm nhỏ", visionLabels = listOf("grape", "fruit")),
        FoodItem(id = "dua", name = "Dứa (thơm)", aliases = listOf("pineapple"), kcalPer100g = 50.0, portionGrams = 150.0, portionName = "1 chén", visionLabels = listOf("pineapple", "fruit")),
        FoodItem(id = "du-du", name = "Đu đủ", aliases = listOf("papaya"), kcalPer100g = 43.0, portionGrams = 200.0, portionName = "1 chén", visionLabels = listOf("papaya", "fruit")),
        FoodItem(id = "thanh-long", name = "Thanh long", aliases = listOf("dragon fruit", "pitaya"), kcalPer100g = 60.0, portionGrams = 200.0, portionName = "1/2 quả", visionLabels = listOf("fruit")),
        FoodItem(id = "dau-tay", name = "Dâu tây", aliases = listOf("strawberry"), kcalPer100g = 32.0, portionGrams = 150.0, portionName = "1 chén", visionLabels = listOf("strawberry", "berry", "fruit")),
        // Thêm
        FoodItem(id = "xien-nuong", name = "Thịt xiên nướng", aliases = listOf("grilled skewers", "kebab", "satay"), kcalPer100g = 220.0, portionGrams = 100.0, portionName = "2 xiên", visionLabels = listOf("kebab", "satay", "grill", "meat")),
        FoodItem(id = "ha-cao", name = "Há cảo / sủi cảo", aliases = listOf("dumplings", "dim sum", "gyoza", "wonton"), kcalPer100g = 190.0, portionGrams = 120.0, portionName = "4 cái", visionLabels = listOf("dumpling", "gyoza", "wonton")),
        FoodItem(id = "banh-flan", name = "Bánh flan", aliases = listOf("flan", "caramel custard"), kcalPer100g = 145.0, portionGrams = 100.0, portionName = "1 hũ", visionLabels = listOf("flan", "pudding", "caramel", "dessert")),
        FoodItem(id = "sinh-to", name = "Sinh tố", aliases = listOf("smoothie", "sinh to bo"), kcalPer100g = 110.0, portionGrams = 300.0, portionName = "1 ly", visionLabels = listOf("smoothie", "milkshake", "juice", "drink")),
        FoodItem(id = "nuoc-ep", name = "Nước ép trái cây", aliases = listOf("juice", "orange juice"), kcalPer100g = 45.0, portionGrams = 250.0, portionName = "1 ly", visionLabels = listOf("juice", "drink")),
        FoodItem(id = "bia", name = "Bia", aliases = listOf("beer"), kcalPer100g = 43.0, portionGrams = 330.0, portionName = "1 lon", visionLabels = listOf("beer", "drink")),
        FoodItem(id = "sau-rieng", name = "Sầu riêng", aliases = listOf("durian"), kcalPer100g = 147.0, portionGrams = 100.0, portionName = "2 múi", visionLabels = listOf("durian", "fruit")),
        FoodItem(id = "chom-chom", name = "Chôm chôm", aliases = listOf("rambutan"), kcalPer100g = 82.0, portionGrams = 100.0, portionName = "6 quả", visionLabels = listOf("rambutan", "lychee", "fruit")),
        FoodItem(id = "mang-cut", name = "Măng cụt", aliases = listOf("mangosteen"), kcalPer100g = 73.0, portionGrams = 100.0, portionName = "3 quả", visionLabels = listOf("mangosteen", "fruit")),
        FoodItem(id = "vai", name = "Vải", aliases = listOf("lychee", "litchi"), kcalPer100g = 66.0, portionGrams = 100.0, portionName = "8 quả", visionLabels = listOf("lychee", "rambutan", "fruit")),
        FoodItem(id = "oi", name = "Ổi", aliases = listOf("guava"), kcalPer100g = 68.0, portionGrams = 150.0, portionName = "1 quả", visionLabels = listOf("guava", "fruit")),
        FoodItem(id = "bo", name = "Bơ", aliases = listOf("avocado"), kcalPer100g = 160.0, portionGrams = 100.0, portionName = "1/2 quả", visionLabels = listOf("avocado", "fruit")),
    
    )

    /** Nhãn chung chung được tính nửa điểm để nhãn cụ thể xếp trước. */
    val genericLabels: Set<String> = setOf(
        "food", "fruit", "drink", "meat", "dessert", "baked goods", "vegetable",
        "seafood", "grain", "frozen dessert", "beef", "poultry", "dish", "cuisine",
    )

    /**
     * Ghép nhãn nhận diện ảnh với các món trong bảng. Nhãn được so với nhãn Vision của món
     * và cả tên tiếng Anh (aliases), không phân biệt hoa thường, số ít/số nhiều.
     */
    fun match(labels: List<Pair<String, Float>>, limit: Int = 6): List<FoodGuess> {
        val best = mutableMapOf<String, Float>()
        for ((identifier, confidence) in labels) {
            val key = normalizeLabel(identifier)
            val variants = setOf(key, key.removeSuffix("s"), key + "s", key.removeSuffix("es"))
            val score = if (key in genericLabels) confidence * 0.5f else confidence
            for (food in all) {
                val keys = food.visionLabels + food.aliases.map(::normalizeLabel)
                if (keys.any { it in variants }) {
                    best[food.id] = maxOf(best[food.id] ?: 0f, score)
                }
            }
        }
        val byId = all.associateBy { it.id }
        return best.mapNotNull { (id, c) -> byId[id]?.let { FoodGuess(it, c) } }
            .sortedWith(compareByDescending<FoodGuess> { it.confidence }.thenBy { it.food.name })
            .take(limit)
    }

    /** Tìm món theo tên (không phân biệt dấu, hoa thường). */
    fun search(query: String): List<FoodItem> {
        val q = TextKeys.searchKey(query)
        val sorted = all.sortedWith(compareBy(java.text.Collator.getInstance(java.util.Locale("vi"))) { it.name })
        if (q.isEmpty()) return sorted
        return sorted.filter { food -> (listOf(food.name) + food.aliases).any { TextKeys.searchKey(it).contains(q) } }
    }

    fun normalizeLabel(identifier: String): String =
        identifier.lowercase().replace('_', ' ').trim()

    fun byId(id: String): FoodItem? = all.firstOrNull { it.id == id }
}
