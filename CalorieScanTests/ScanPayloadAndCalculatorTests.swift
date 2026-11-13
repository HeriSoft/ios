import XCTest
@testable import CalorieScan

final class ScanPayloadTests: XCTestCase {
    func testPlainBarcode() {
        XCTAssertEqual(ScanPayload.classify("3017624010701"), .barcode("3017624010701"))
        XCTAssertEqual(ScanPayload.classify(" 5449000000996\n"), .barcode("5449000000996"))
    }

    func testOpenFoodFactsLink() {
        XCTAssertEqual(
            ScanPayload.classify("https://world.openfoodfacts.org/product/3017624010701/nutella"),
            .barcode("3017624010701")
        )
    }

    func testGS1DigitalLink() {
        XCTAssertEqual(ScanPayload.classify("https://id.gs1.org/01/09506000134352"), .barcode("9506000134352"))
    }

    func testOtherContent() {
        XCTAssertEqual(ScanPayload.classify("https://example.com"), .text("https://example.com"))
        XCTAssertEqual(ScanPayload.classify("WIFI:S:Home;T:WPA;P:secret;;"), .text("WIFI:S:Home;T:WPA;P:secret;;"))
        XCTAssertEqual(ScanPayload.classify("12345"), .text("12345"))
    }
}

final class CalorieCalculatorTests: XCTestCase {
    func testPer100g() {
        XCTAssertEqual(CalorieCalculator.kcal(per100g: 480, amount: 30), 144, accuracy: 0.001)
        XCTAssertEqual(CalorieCalculator.kcal(per100g: 480, amount: -5), 0)
    }

    func testPerServing() {
        XCTAssertEqual(CalorieCalculator.kcal(perServing: 80, servings: 2.5), 200, accuracy: 0.001)
    }

    func testEffectiveServing() {
        let product = ProductInfo(name: "X", servingGrams: 30, kcalPer100g: 480)
        XCTAssertEqual(product.effectiveKcalPerServing ?? 0, 144, accuracy: 0.001)
    }

    func testFormatting() {
        XCTAssertEqual(143.6.kcalText, "144 kcal")
    }
}
