import XCTest
@testable import CalorieScan

final class OpenFoodFactsParsingTests: XCTestCase {
    func testParsesCaloriesAndMacros() throws {
        let json = """
        {"code":"3017624010701","status":1,"product":{"product_name":"Nutella","brands":"Ferrero, Nutella",
        "quantity":"400 g","serving_size":"15 g","serving_quantity":"15",
        "nutriments":{"energy-kcal_100g":539,"energy-kcal_serving":80.9,"proteins_100g":6.3,
        "carbohydrates_100g":57.5,"sugars_100g":56.3,"fat_100g":30.9,"nova-group":4,"note":"abc","flag":true}}}
        """
        let product = try XCTUnwrap(OpenFoodFactsClient.parse(Data(json.utf8), barcode: "3017624010701"))
        XCTAssertEqual(product.name, "Nutella")
        XCTAssertEqual(product.brand, "Ferrero")
        XCTAssertEqual(product.quantityText, "400 g")
        XCTAssertEqual(product.kcalPer100g, 539)
        XCTAssertEqual(product.servingGrams, 15)
        XCTAssertEqual(product.kcalPerServing ?? 0, 80.9, accuracy: 0.001)
        XCTAssertEqual(product.protein100g, 6.3)
        XCTAssertEqual(product.fat100g, 30.9)
        XCTAssertEqual(product.source, .openFoodFacts)
    }

    func testNumbersAsStringsAndKilojouleFallback() throws {
        let json = #"{"status":1,"product":{"product_name":"Test","nutriments":{"energy_100g":"2092"}}}"#
        let product = try XCTUnwrap(OpenFoodFactsClient.parse(Data(json.utf8), barcode: "12345678"))
        XCTAssertEqual(product.kcalPer100g ?? 0, 500, accuracy: 0.1)
        XCTAssertNil(product.kcalPerServing)
    }

    func testPrefersVietnameseName() throws {
        let json = #"{"status":1,"product":{"product_name":"Fresh milk","product_name_vi":"Sữa tươi","nutriments":{}}}"#
        let product = try XCTUnwrap(OpenFoodFactsClient.parse(Data(json.utf8), barcode: "12345678"))
        XCTAssertEqual(product.name, "Sữa tươi")
    }

    func testMissingNameFallsBackToBarcode() throws {
        let json = #"{"status":1,"product":{"product_name":"  ","nutriments":{}}}"#
        let product = try XCTUnwrap(OpenFoodFactsClient.parse(Data(json.utf8), barcode: "12345678"))
        XCTAssertEqual(product.name, "Sản phẩm 12345678")
        XCTAssertNil(product.kcalPer100g)
    }

    func testProductNotFound() throws {
        let json = #"{"code":"000","status":0,"status_verbose":"product not found"}"#
        XCTAssertNil(try OpenFoodFactsClient.parse(Data(json.utf8), barcode: "000"))
    }

    func testURLValidation() {
        XCTAssertNil(OpenFoodFactsClient.url(for: "abc"))
        XCTAssertNil(OpenFoodFactsClient.url(for: "12"))
        let url = OpenFoodFactsClient.url(for: "3017624010701")
        XCTAssertEqual(url?.host, "world.openfoodfacts.org")
        XCTAssertTrue(url?.path.hasSuffix("/3017624010701.json") ?? false)
    }
}
