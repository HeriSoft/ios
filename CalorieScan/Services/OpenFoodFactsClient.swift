import Foundation
import SwiftUI

protocol ProductLookup: Sendable {
    /// Trả về `nil` nếu không tìm thấy sản phẩm.
    func product(forBarcode barcode: String) async throws -> ProductInfo?
}

enum LookupError: LocalizedError {
    case invalidBarcode
    case badResponse(Int)

    var errorDescription: String? {
        switch self {
        case .invalidBarcode: return "Mã vạch không hợp lệ."
        case .badResponse(let code): return "Máy chủ trả về lỗi (\(code)). Vui lòng thử lại."
        }
    }
}

/// Tra cứu sản phẩm qua API miễn phí của Open Food Facts (https://world.openfoodfacts.org).
struct OpenFoodFactsClient: ProductLookup {
    var session: URLSession = .shared

    static let fields = [
        "code", "product_name", "product_name_vi", "product_name_en", "brands",
        "image_front_small_url", "image_front_url", "quantity", "serving_size",
        "serving_quantity", "nutriments",
    ]

    func product(forBarcode barcode: String) async throws -> ProductInfo? {
        guard let url = Self.url(for: barcode) else { throw LookupError.invalidBarcode }
        var request = URLRequest(url: url)
        request.timeoutInterval = 15
        request.setValue("CalorieScan-iOS/0.1", forHTTPHeaderField: "User-Agent")

        let (data, response) = try await session.data(for: request)
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0
        if status == 404 { return nil }
        guard (200..<300).contains(status) else { throw LookupError.badResponse(status) }
        return try Self.parse(data, barcode: barcode)
    }

    static func url(for barcode: String) -> URL? {
        let digits = barcode.filter { $0.isASCII && $0.isNumber }
        guard (6...14).contains(digits.count), digits.count == barcode.count else { return nil }
        var components = URLComponents(string: "https://world.openfoodfacts.org/api/v2/product/\(digits).json")
        components?.queryItems = [URLQueryItem(name: "fields", value: fields.joined(separator: ","))]
        return components?.url
    }

    static func parse(_ data: Data, barcode: String) throws -> ProductInfo? {
        let response = try JSONDecoder().decode(OFFResponse.self, from: data)
        guard response.status != 0, let p = response.product else { return nil }
        let n = p.nutriments

        let kcal100 = n["energy-kcal_100g"]
            ?? n["energy-kj_100g"].map(CalorieCalculator.kJToKcal)
            ?? n["energy_100g"].map(CalorieCalculator.kJToKcal)
        let kcalServing = n["energy-kcal_serving"]
            ?? n["energy-kj_serving"].map(CalorieCalculator.kJToKcal)
            ?? n["energy_serving"].map(CalorieCalculator.kJToKcal)

        let brand = p.brands?
            .split(separator: ",")
            .first
            .map { $0.trimmingCharacters(in: .whitespaces) }

        return ProductInfo(
            barcode: barcode,
            name: p.productNameVi ?? p.productName ?? p.productNameEn ?? "Sản phẩm \(barcode)",
            brand: brand,
            imageURL: (p.imageFrontSmallURL ?? p.imageFrontURL).flatMap(URL.init(string:)),
            quantityText: p.quantity,
            servingSizeText: p.servingSize,
            servingGrams: p.servingQuantity.flatMap { $0 > 0 ? $0 : nil },
            kcalPer100g: kcal100,
            kcalPerServing: kcalServing,
            protein100g: n["proteins_100g"],
            carbs100g: n["carbohydrates_100g"],
            sugars100g: n["sugars_100g"],
            fat100g: n["fat_100g"],
            source: .openFoodFacts
        )
    }
}

// MARK: - Môi trường SwiftUI

private struct ProductLookupKey: EnvironmentKey {
    static let defaultValue: any ProductLookup = OpenFoodFactsClient()
}

extension EnvironmentValues {
    var productLookup: any ProductLookup {
        get { self[ProductLookupKey.self] }
        set { self[ProductLookupKey.self] = newValue }
    }
}

// MARK: - Giải mã JSON (chịu lỗi: số có thể là chuỗi, trường có thể thiếu)

struct OFFResponse: Decodable {
    let status: Int?
    let product: OFFProduct?

    enum CodingKeys: String, CodingKey { case status, product }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        status = (try? c.decodeIfPresent(Int.self, forKey: .status)) ?? nil
        product = (try? c.decodeIfPresent(OFFProduct.self, forKey: .product)) ?? nil
    }
}

struct OFFProduct: Decodable {
    var productName: String?
    var productNameVi: String?
    var productNameEn: String?
    var brands: String?
    var imageFrontSmallURL: String?
    var imageFrontURL: String?
    var quantity: String?
    var servingSize: String?
    var servingQuantity: Double?
    var nutriments: [String: Double]

    enum CodingKeys: String, CodingKey {
        case productName = "product_name"
        case productNameVi = "product_name_vi"
        case productNameEn = "product_name_en"
        case brands
        case imageFrontSmallURL = "image_front_small_url"
        case imageFrontURL = "image_front_url"
        case quantity
        case servingSize = "serving_size"
        case servingQuantity = "serving_quantity"
        case nutriments
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        func string(_ key: CodingKeys) -> String? {
            guard let value = (try? c.decodeIfPresent(String.self, forKey: key)) ?? nil else { return nil }
            let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
            return trimmed.isEmpty ? nil : trimmed
        }
        productName = string(.productName)
        productNameVi = string(.productNameVi)
        productNameEn = string(.productNameEn)
        brands = string(.brands)
        imageFrontSmallURL = string(.imageFrontSmallURL)
        imageFrontURL = string(.imageFrontURL)
        quantity = string(.quantity)
        servingSize = string(.servingSize)
        servingQuantity = ((try? c.decodeIfPresent(LossyDouble.self, forKey: .servingQuantity)) ?? nil)?.value
        nutriments = ((try? c.decodeIfPresent(LossyNumberDictionary.self, forKey: .nutriments)) ?? nil)?.values ?? [:]
    }
}

struct LossyDouble: Decodable {
    let value: Double?

    init(from decoder: Decoder) throws {
        let c = try decoder.singleValueContainer()
        if let number = try? c.decode(Double.self) {
            value = number
        } else if let text = try? c.decode(String.self) {
            value = Double(text.trimmingCharacters(in: .whitespaces).replacingOccurrences(of: ",", with: "."))
        } else {
            value = nil
        }
    }
}

struct LossyNumberDictionary: Decodable {
    let values: [String: Double]

    private struct AnyKey: CodingKey {
        var stringValue: String
        var intValue: Int?
        init?(stringValue: String) { self.stringValue = stringValue }
        init?(intValue: Int) { self.stringValue = String(intValue); self.intValue = intValue }
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: AnyKey.self)
        var result: [String: Double] = [:]
        for key in c.allKeys {
            if let lossy = try? c.decode(LossyDouble.self, forKey: key), let value = lossy.value {
                result[key.stringValue] = value
            }
        }
        values = result
    }
}
