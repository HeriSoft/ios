import ImageIO
import UIKit
import Vision

/// Nhận diện món ăn trong ảnh bằng bộ phân loại ảnh có sẵn của iOS (chạy trên máy, không cần mạng).
enum FoodClassifier {
    struct Label: Sendable {
        let identifier: String
        let confidence: Float
    }

    static func classify(_ image: UIImage) async throws -> [FoodGuess] {
        let labels = try await labels(in: image)
        return FoodDatabase.match(labels: labels.map { ($0.identifier, $0.confidence) })
    }

    static func labels(in image: UIImage) async throws -> [Label] {
        guard let cgImage = image.cgImage else { return [] }
        let orientation = CGImagePropertyOrientation(image.imageOrientation)
        return try await Task.detached(priority: .userInitiated) {
            let request = VNClassifyImageRequest()
            try VNImageRequestHandler(cgImage: cgImage, orientation: orientation).perform([request])
            return (request.results ?? [])
                .filter { $0.confidence >= 0.03 }
                .map { Label(identifier: $0.identifier, confidence: $0.confidence) }
        }.value
    }

    /// Các nhãn mà bộ phân loại hỗ trợ (dùng để kiểm tra bảng món ăn).
    static func supportedIdentifiers() -> [String] {
        (try? VNClassifyImageRequest().supportedIdentifiers()) ?? []
    }
}
