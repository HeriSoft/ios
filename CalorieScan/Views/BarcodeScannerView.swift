import SwiftUI
import VisionKit

/// Camera quét mã vạch / QR dùng VisionKit (cần iPhone thật có camera).
struct BarcodeScannerView: UIViewControllerRepresentable {
    var isScanning: Bool
    var onScan: (String) -> Void

    @MainActor
    static var isAvailable: Bool {
        DataScannerViewController.isSupported && DataScannerViewController.isAvailable
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(onScan: onScan)
    }

    func makeUIViewController(context: Context) -> DataScannerViewController {
        let controller = DataScannerViewController(
            recognizedDataTypes: [.barcode(symbologies: [.qr, .ean13, .ean8, .upce, .code128, .itf14])],
            qualityLevel: .balanced,
            recognizesMultipleItems: false,
            isHighlightingEnabled: true
        )
        controller.delegate = context.coordinator
        DispatchQueue.main.async {
            if isScanning { try? controller.startScanning() }
        }
        return controller
    }

    func updateUIViewController(_ controller: DataScannerViewController, context: Context) {
        context.coordinator.onScan = onScan
        if isScanning {
            if !controller.isScanning { try? controller.startScanning() }
        } else if controller.isScanning {
            controller.stopScanning()
        }
    }

    static func dismantleUIViewController(_ controller: DataScannerViewController, coordinator: Coordinator) {
        controller.stopScanning()
    }

    @MainActor
    final class Coordinator: NSObject, DataScannerViewControllerDelegate {
        var onScan: (String) -> Void

        init(onScan: @escaping (String) -> Void) {
            self.onScan = onScan
        }

        func dataScanner(_ dataScanner: DataScannerViewController, didAdd addedItems: [RecognizedItem], allItems: [RecognizedItem]) {
            for item in addedItems where report(item) { return }
        }

        func dataScanner(_ dataScanner: DataScannerViewController, didTapOn item: RecognizedItem) {
            _ = report(item)
        }

        private func report(_ item: RecognizedItem) -> Bool {
            guard case .barcode(let barcode) = item,
                  let payload = barcode.payloadStringValue, !payload.isEmpty else { return false }
            UIImpactFeedbackGenerator(style: .medium).impactOccurred()
            onScan(payload)
            return true
        }
    }
}
