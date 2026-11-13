import SwiftUI

enum ScanRoute: Hashable {
    case barcode(String)
    case product(ProductInfo)
    case text(String)
    case label(barcode: String?)
    case manualProduct(barcode: String?)
}

struct ScanTab: View {
    @State private var path: [ScanRoute] = DemoMode.initialScanPath
    @State private var showManualEntry = false
    @State private var manualCode = ""

    var body: some View {
        NavigationStack(path: $path) {
            ScanHomeView(
                isScanning: path.isEmpty,
                onPayload: handle,
                onManual: { showManualEntry = true },
                onLabel: { path.append(.label(barcode: nil)) }
            )
            .navigationTitle("Quét sản phẩm")
            .navigationDestination(for: ScanRoute.self) { route in
                destination(for: route)
            }
            .alert("Nhập mã vạch", isPresented: $showManualEntry) {
                TextField("Ví dụ: 3017624010701", text: $manualCode)
                    .keyboardType(.numberPad)
                Button("Tra cứu") {
                    let code = manualCode.filter { $0.isASCII && $0.isNumber }
                    manualCode = ""
                    if !code.isEmpty { path.append(.barcode(code)) }
                }
                Button("Huỷ", role: .cancel) { manualCode = "" }
            } message: {
                Text("Nhập dãy số in dưới mã vạch trên bao bì.")
            }
        }
    }

    @ViewBuilder
    private func destination(for route: ScanRoute) -> some View {
        switch route {
        case .barcode(let code):
            ProductLookupView(barcode: code, path: $path)
        case .product(let product):
            ProductDetailView(product: product, onSaved: { path.removeAll() })
        case .text(let text):
            ScannedTextView(text: text)
        case .label(let barcode):
            LabelScanView(barcode: barcode) { product in path.append(.product(product)) }
        case .manualProduct(let barcode):
            ManualProductView(barcode: barcode) { product in path.append(.product(product)) }
        }
    }

    private func handle(_ raw: String) {
        guard path.isEmpty else { return }
        switch ScanPayload.classify(raw) {
        case .barcode(let code): path.append(.barcode(code))
        case .text(let text): path.append(.text(text))
        }
    }
}
