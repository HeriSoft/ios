import SwiftUI

struct ProductLookupView: View {
    let barcode: String
    @Binding var path: [ScanRoute]

    @Environment(\.productLookup) private var lookup
    @State private var state: LoadState = .loading
    @State private var hasLoaded = false

    enum LoadState {
        case loading
        case found(ProductInfo)
        case notFound
        case failed(String)
    }

    var body: some View {
        content
            .task {
                guard !hasLoaded else { return }
                hasLoaded = true
                await load()
            }
    }

    @ViewBuilder
    private var content: some View {
        switch state {
        case .loading:
            ProgressView("Đang tra cứu mã \(barcode)…")
                .navigationTitle("Tra cứu")
        case .found(let product):
            ProductDetailView(product: product, onSaved: { path.removeAll() })
        case .notFound:
            ContentUnavailableView {
                Label("Không tìm thấy sản phẩm", systemImage: "questionmark.app")
            } description: {
                Text("Mã \(barcode) chưa có trong cơ sở dữ liệu Open Food Facts. Bạn có thể quét nhãn dinh dưỡng hoặc tự nhập lượng calo.")
            } actions: {
                Button("Quét nhãn dinh dưỡng") { path.append(.label(barcode: barcode)) }
                    .buttonStyle(.borderedProminent)
                Button("Nhập thủ công") { path.append(.manualProduct(barcode: barcode)) }
            }
            .navigationTitle("Không tìm thấy")
        case .failed(let message):
            ContentUnavailableView {
                Label("Không tra cứu được", systemImage: "wifi.exclamationmark")
            } description: {
                Text(message)
            } actions: {
                Button("Thử lại") { Task { await load() } }
                    .buttonStyle(.borderedProminent)
                Button("Nhập thủ công") { path.append(.manualProduct(barcode: barcode)) }
            }
            .navigationTitle("Lỗi")
        }
    }

    @MainActor
    private func load() async {
        state = .loading
        do {
            if let product = try await lookup.product(forBarcode: barcode) {
                state = .found(product)
            } else {
                state = .notFound
            }
        } catch {
            state = .failed(error.localizedDescription)
        }
    }
}
