import Foundation

/// Phân loại nội dung đọc được từ mã vạch / mã QR.
enum ScanPayload: Equatable {
    /// Mã sản phẩm (EAN/UPC/GTIN) có thể tra cứu.
    case barcode(String)
    /// Nội dung khác (link, văn bản…).
    case text(String)

    static func classify(_ raw: String) -> ScanPayload {
        let trimmed = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        if isBarcode(trimmed) { return .barcode(normalize(trimmed)) }

        if let url = URL(string: trimmed), let scheme = url.scheme?.lowercased(), scheme.hasPrefix("http") {
            // Ví dụ: https://world.openfoodfacts.org/product/3017624010701/nutella
            // hoặc GS1 Digital Link: https://id.gs1.org/01/09506000134352
            for component in url.pathComponents.reversed() where isBarcode(component) {
                return .barcode(normalize(component))
            }
            let items = URLComponents(url: url, resolvingAgainstBaseURL: false)?.queryItems ?? []
            for item in items {
                if let value = item.value, isBarcode(value) { return .barcode(normalize(value)) }
            }
        }
        return .text(trimmed)
    }

    static func isBarcode(_ value: String) -> Bool {
        (8...14).contains(value.count) && value.allSatisfy { $0.isASCII && $0.isNumber }
    }

    /// GTIN-14 bắt đầu bằng 0 tương đương EAN-13.
    private static func normalize(_ code: String) -> String {
        if code.count == 14, code.hasPrefix("0") { return String(code.dropFirst()) }
        return code
    }
}
