import Foundation

/// Một món ăn với lượng calo ước tính trung bình.
struct FoodItem: Identifiable, Hashable {
    let id: String
    /// Tên tiếng Việt.
    let name: String
    /// Tên khác (tiếng Anh, cách gọi khác) để tìm kiếm.
    let aliases: [String]
    let kcalPer100g: Double
    /// Khối lượng một khẩu phần thông thường (g hoặc ml).
    let portionGrams: Double
    /// Ví dụ: "1 tô", "1 đĩa", "1 quả".
    let portionName: String
    /// Nhãn của bộ nhận diện ảnh Vision (chữ thường, cách nhau bằng dấu cách).
    let visionLabels: [String]

    var kcalPerPortion: Double {
        CalorieCalculator.kcal(per100g: kcalPer100g, amount: portionGrams)
    }

    var productInfo: ProductInfo {
        ProductInfo(
            name: name,
            servingSizeText: "\(portionName) ≈ \(Int(portionGrams)) g",
            servingGrams: portionGrams,
            kcalPer100g: kcalPer100g,
            source: .estimate
        )
    }
}

/// Bảng calo ước tính cho các món phổ biến (giá trị trung bình, thay đổi theo cách chế biến).
enum FoodDatabase {
    static let all: [FoodItem] = [
        // Món Việt
        FoodItem(id: "pho-bo", name: "Phở bò", aliases: ["pho", "beef noodle soup"], kcalPer100g: 90, portionGrams: 500, portionName: "1 tô", visionLabels: ["noodles", "noodle soup", "ramen", "pho", "soup"]),
        FoodItem(id: "pho-ga", name: "Phở gà", aliases: ["chicken pho"], kcalPer100g: 80, portionGrams: 500, portionName: "1 tô", visionLabels: ["noodles", "noodle soup", "ramen", "pho", "soup"]),
        FoodItem(id: "bun-bo-hue", name: "Bún bò Huế", aliases: ["bun bo", "spicy beef noodle soup"], kcalPer100g: 95, portionGrams: 550, portionName: "1 tô", visionLabels: ["noodles", "noodle soup", "ramen", "soup"]),
        FoodItem(id: "hu-tieu", name: "Hủ tiếu", aliases: ["hu tieu", "noodle soup"], kcalPer100g: 85, portionGrams: 500, portionName: "1 tô", visionLabels: ["noodles", "noodle soup", "ramen", "soup"]),
        FoodItem(id: "bun-cha", name: "Bún chả", aliases: ["grilled pork with noodles"], kcalPer100g: 125, portionGrams: 450, portionName: "1 phần", visionLabels: ["noodles", "barbecue", "meat"]),
        FoodItem(id: "mi-xao", name: "Mì xào", aliases: ["fried noodles", "stir fried noodles"], kcalPer100g: 180, portionGrams: 300, portionName: "1 đĩa", visionLabels: ["noodles", "pasta", "chow mein"]),
        FoodItem(id: "mi-goi", name: "Mì gói (đã nấu)", aliases: ["instant noodles", "mi tom", "mì tôm"], kcalPer100g: 140, portionGrams: 300, portionName: "1 tô", visionLabels: ["noodles", "ramen", "instant noodles"]),
        FoodItem(id: "com-trang", name: "Cơm trắng", aliases: ["rice", "steamed rice"], kcalPer100g: 130, portionGrams: 150, portionName: "1 chén", visionLabels: ["rice", "grain"]),
        FoodItem(id: "com-tam", name: "Cơm tấm sườn", aliases: ["broken rice", "com suon"], kcalPer100g: 150, portionGrams: 450, portionName: "1 đĩa", visionLabels: ["rice", "meat", "pork", "barbecue"]),
        FoodItem(id: "com-chien", name: "Cơm chiên", aliases: ["fried rice"], kcalPer100g: 170, portionGrams: 350, portionName: "1 đĩa", visionLabels: ["rice", "fried rice"]),
        FoodItem(id: "com-ga", name: "Cơm gà", aliases: ["chicken rice"], kcalPer100g: 160, portionGrams: 400, portionName: "1 đĩa", visionLabels: ["rice", "chicken", "poultry"]),
        FoodItem(id: "xoi", name: "Xôi", aliases: ["sticky rice", "xoi"], kcalPer100g: 200, portionGrams: 200, portionName: "1 gói", visionLabels: ["rice", "sticky rice"]),
        FoodItem(id: "chao", name: "Cháo", aliases: ["rice porridge", "congee"], kcalPer100g: 60, portionGrams: 400, portionName: "1 tô", visionLabels: ["porridge", "soup", "oatmeal"]),
        FoodItem(id: "banh-mi-thit", name: "Bánh mì thịt", aliases: ["banh mi", "vietnamese sandwich"], kcalPer100g: 230, portionGrams: 200, portionName: "1 ổ", visionLabels: ["sandwich", "bread", "baguette", "sub sandwich"]),
        FoodItem(id: "banh-xeo", name: "Bánh xèo", aliases: ["vietnamese pancake"], kcalPer100g: 210, portionGrams: 200, portionName: "1 cái", visionLabels: ["pancake", "omelet", "crepe"]),
        FoodItem(id: "goi-cuon", name: "Gỏi cuốn", aliases: ["spring roll", "fresh spring roll", "summer roll"], kcalPer100g: 115, portionGrams: 70, portionName: "1 cuốn", visionLabels: ["spring roll", "dumpling", "burrito"]),
        FoodItem(id: "cha-gio", name: "Chả giò", aliases: ["fried spring roll", "egg roll", "nem ran"], kcalPer100g: 250, portionGrams: 40, portionName: "1 cuốn", visionLabels: ["spring roll", "egg roll", "fried food"]),
        FoodItem(id: "banh-cuon", name: "Bánh cuốn", aliases: ["steamed rice rolls"], kcalPer100g: 150, portionGrams: 300, portionName: "1 đĩa", visionLabels: ["dumpling", "rice"]),
        FoodItem(id: "banh-bao", name: "Bánh bao", aliases: ["steamed bun", "bao"], kcalPer100g: 230, portionGrams: 120, portionName: "1 cái", visionLabels: ["bun", "dumpling", "bread", "steamed bun"]),
        FoodItem(id: "thit-kho", name: "Thịt kho trứng", aliases: ["braised pork with eggs"], kcalPer100g: 220, portionGrams: 200, portionName: "1 phần", visionLabels: ["meat", "pork", "stew", "egg"]),
        FoodItem(id: "ca-kho", name: "Cá kho", aliases: ["braised fish"], kcalPer100g: 180, portionGrams: 150, portionName: "1 khúc", visionLabels: ["fish", "seafood", "stew"]),
        FoodItem(id: "canh-chua", name: "Canh chua", aliases: ["sour soup"], kcalPer100g: 35, portionGrams: 300, portionName: "1 chén", visionLabels: ["soup", "broth"]),
        FoodItem(id: "rau-xao", name: "Rau muống xào tỏi", aliases: ["stir fried vegetables", "morning glory"], kcalPer100g: 70, portionGrams: 200, portionName: "1 đĩa", visionLabels: ["vegetable", "greens", "leaf vegetable", "salad"]),
        FoodItem(id: "trung-chien", name: "Trứng chiên", aliases: ["fried egg", "omelette"], kcalPer100g: 196, portionGrams: 60, portionName: "1 quả", visionLabels: ["egg", "fried egg", "omelet", "omelette"]),
        FoodItem(id: "trung-luoc", name: "Trứng luộc", aliases: ["boiled egg"], kcalPer100g: 155, portionGrams: 50, portionName: "1 quả", visionLabels: ["egg", "boiled egg"]),
        FoodItem(id: "che", name: "Chè", aliases: ["sweet soup", "dessert"], kcalPer100g: 150, portionGrams: 250, portionName: "1 ly", visionLabels: ["dessert", "pudding", "parfait"]),
        FoodItem(id: "ca-phe-sua", name: "Cà phê sữa đá", aliases: ["iced milk coffee", "ca phe sua"], kcalPer100g: 60, portionGrams: 200, portionName: "1 ly", visionLabels: ["coffee", "iced coffee", "drink", "beverage"]),
        FoodItem(id: "tra-sua", name: "Trà sữa trân châu", aliases: ["bubble tea", "milk tea", "boba"], kcalPer100g: 70, portionGrams: 500, portionName: "1 ly", visionLabels: ["bubble tea", "tea", "drink", "beverage", "milkshake"]),

        // Đồ ăn nhanh & món Âu
        FoodItem(id: "pizza", name: "Pizza", aliases: ["pizza"], kcalPer100g: 266, portionGrams: 110, portionName: "1 miếng", visionLabels: ["pizza"]),
        FoodItem(id: "hamburger", name: "Hamburger", aliases: ["burger", "hamburger"], kcalPer100g: 254, portionGrams: 200, portionName: "1 cái", visionLabels: ["hamburger", "burger", "cheeseburger"]),
        FoodItem(id: "khoai-tay-chien", name: "Khoai tây chiên", aliases: ["french fries", "fries", "chips"], kcalPer100g: 312, portionGrams: 117, portionName: "1 phần vừa", visionLabels: ["french fries", "fries", "fried food"]),
        FoodItem(id: "ga-ran", name: "Gà rán", aliases: ["fried chicken"], kcalPer100g: 260, portionGrams: 150, portionName: "1 miếng", visionLabels: ["fried chicken", "chicken", "poultry", "fried food"]),
        FoodItem(id: "hot-dog", name: "Xúc xích kẹp (hot dog)", aliases: ["hot dog", "hotdog"], kcalPer100g: 290, portionGrams: 100, portionName: "1 cái", visionLabels: ["hotdog", "hot dog", "sausage"]),
        FoodItem(id: "sandwich", name: "Sandwich", aliases: ["sandwich"], kcalPer100g: 250, portionGrams: 150, portionName: "1 cái", visionLabels: ["sandwich", "sub sandwich", "bread"]),
        FoodItem(id: "mi-y", name: "Mì Ý sốt bò", aliases: ["spaghetti", "pasta", "bolognese"], kcalPer100g: 160, portionGrams: 350, portionName: "1 đĩa", visionLabels: ["spaghetti", "pasta", "noodles"]),
        FoodItem(id: "bit-tet", name: "Bít tết", aliases: ["steak", "beef steak"], kcalPer100g: 270, portionGrams: 200, portionName: "1 miếng", visionLabels: ["steak", "meat", "beef"]),
        FoodItem(id: "sushi", name: "Sushi", aliases: ["sushi", "maki"], kcalPer100g: 150, portionGrams: 180, portionName: "6 miếng", visionLabels: ["sushi", "sashimi", "seafood"]),
        FoodItem(id: "salad", name: "Salad rau trộn dầu giấm", aliases: ["salad", "green salad"], kcalPer100g: 80, portionGrams: 200, portionName: "1 đĩa", visionLabels: ["salad", "vegetable", "greens"]),
        FoodItem(id: "banh-mi-sandwich", name: "Bánh mì sandwich (lát)", aliases: ["white bread", "toast"], kcalPer100g: 265, portionGrams: 30, portionName: "1 lát", visionLabels: ["bread", "toast"]),
        FoodItem(id: "banh-ngot", name: "Bánh kem", aliases: ["cake", "birthday cake"], kcalPer100g: 350, portionGrams: 80, portionName: "1 miếng", visionLabels: ["cake", "dessert", "baked goods"]),
        FoodItem(id: "banh-quy", name: "Bánh quy", aliases: ["cookie", "biscuit"], kcalPer100g: 480, portionGrams: 30, portionName: "3 cái", visionLabels: ["cookie", "biscuit", "baked goods"]),
        FoodItem(id: "donut", name: "Bánh donut", aliases: ["donut", "doughnut"], kcalPer100g: 452, portionGrams: 60, portionName: "1 cái", visionLabels: ["donut", "doughnut", "baked goods"]),
        FoodItem(id: "croissant", name: "Bánh sừng bò", aliases: ["croissant"], kcalPer100g: 406, portionGrams: 60, portionName: "1 cái", visionLabels: ["croissant", "baked goods", "bread"]),
        FoodItem(id: "kem", name: "Kem", aliases: ["ice cream"], kcalPer100g: 207, portionGrams: 100, portionName: "1 ly/2 viên", visionLabels: ["ice cream", "frozen dessert", "dessert"]),
        FoodItem(id: "nuoc-ngot", name: "Nước ngọt có ga", aliases: ["soda", "soft drink", "coke"], kcalPer100g: 42, portionGrams: 330, portionName: "1 lon", visionLabels: ["soda", "soft drink", "drink", "beverage", "can"]),
        FoodItem(id: "sua-tuoi", name: "Sữa tươi có đường", aliases: ["milk"], kcalPer100g: 75, portionGrams: 180, portionName: "1 hộp", visionLabels: ["milk", "drink", "beverage"]),

        // Trái cây
        FoodItem(id: "chuoi", name: "Chuối", aliases: ["banana"], kcalPer100g: 89, portionGrams: 120, portionName: "1 quả", visionLabels: ["banana", "fruit"]),
        FoodItem(id: "tao", name: "Táo", aliases: ["apple"], kcalPer100g: 52, portionGrams: 180, portionName: "1 quả", visionLabels: ["apple", "fruit"]),
        FoodItem(id: "cam", name: "Cam", aliases: ["orange"], kcalPer100g: 47, portionGrams: 150, portionName: "1 quả", visionLabels: ["orange", "citrus fruit", "fruit"]),
        FoodItem(id: "xoai", name: "Xoài", aliases: ["mango"], kcalPer100g: 60, portionGrams: 200, portionName: "1 quả", visionLabels: ["mango", "fruit"]),
        FoodItem(id: "dua-hau", name: "Dưa hấu", aliases: ["watermelon"], kcalPer100g: 30, portionGrams: 300, portionName: "1 miếng lớn", visionLabels: ["watermelon", "melon", "fruit"]),
        FoodItem(id: "nho", name: "Nho", aliases: ["grape", "grapes"], kcalPer100g: 69, portionGrams: 100, portionName: "1 chùm nhỏ", visionLabels: ["grape", "grapes", "fruit"]),
        FoodItem(id: "dua", name: "Dứa (thơm)", aliases: ["pineapple"], kcalPer100g: 50, portionGrams: 150, portionName: "1 chén", visionLabels: ["pineapple", "fruit"]),
        FoodItem(id: "du-du", name: "Đu đủ", aliases: ["papaya"], kcalPer100g: 43, portionGrams: 200, portionName: "1 chén", visionLabels: ["papaya", "fruit"]),
        FoodItem(id: "thanh-long", name: "Thanh long", aliases: ["dragon fruit", "pitaya"], kcalPer100g: 60, portionGrams: 200, portionName: "1/2 quả", visionLabels: ["dragon fruit", "pitaya", "fruit"]),
        FoodItem(id: "dau-tay", name: "Dâu tây", aliases: ["strawberry"], kcalPer100g: 32, portionGrams: 150, portionName: "1 chén", visionLabels: ["strawberry", "berry", "fruit"]),
    ]

    /// Ghép nhãn Vision (kèm độ tin cậy) với các món trong bảng, sắp xếp theo độ tin cậy.
    static func match(labels: [(identifier: String, confidence: Float)], limit: Int = 6) -> [FoodGuess] {
        var best: [String: Float] = [:]
        for label in labels {
            let key = normalizeLabel(label.identifier)
            for food in all where food.visionLabels.contains(key) {
                best[food.id] = max(best[food.id] ?? 0, label.confidence)
            }
        }
        let byID = Dictionary(uniqueKeysWithValues: all.map { ($0.id, $0) })
        return best
            .compactMap { id, confidence in byID[id].map { FoodGuess(food: $0, confidence: confidence) } }
            .sorted { $0.confidence != $1.confidence ? $0.confidence > $1.confidence : $0.food.name < $1.food.name }
            .prefix(limit)
            .map { $0 }
    }

    /// Tìm món theo tên (không phân biệt dấu, hoa thường).
    static func search(_ query: String) -> [FoodItem] {
        let q = searchKey(query)
        let sorted = all.sorted { $0.name.localizedCompare($1.name) == .orderedAscending }
        guard !q.isEmpty else { return sorted }
        return sorted.filter { food in
            ([food.name] + food.aliases).contains { searchKey($0).contains(q) }
        }
    }

    static func normalizeLabel(_ identifier: String) -> String {
        identifier.lowercased().replacingOccurrences(of: "_", with: " ").trimmingCharacters(in: .whitespaces)
    }

    static func searchKey(_ text: String) -> String {
        text.replacingOccurrences(of: "đ", with: "d")
            .replacingOccurrences(of: "Đ", with: "D")
            .folding(options: [.diacriticInsensitive, .caseInsensitive], locale: Locale(identifier: "en_US_POSIX"))
            .lowercased()
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }
}

struct FoodGuess: Identifiable, Hashable {
    let food: FoodItem
    let confidence: Float
    var id: String { food.id }
}
