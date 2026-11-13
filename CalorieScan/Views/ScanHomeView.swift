import SwiftUI

struct ScanHomeView: View {
    let isScanning: Bool
    let onPayload: (String) -> Void
    let onManual: () -> Void
    let onLabel: () -> Void

    private let samples: [(name: String, code: String)] = [
        ("Nutella", "3017624010701"),
        ("Coca-Cola", "5449000000996"),
    ]

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                scannerArea
                    .frame(maxWidth: .infinity)
                    .frame(height: 340)
                    .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))

                Text("Đưa mã vạch hoặc mã QR trên bao bì vào khung hình để xem lượng calo.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)

                VStack(spacing: 12) {
                    Button(action: onLabel) {
                        Label("Quét nhãn dinh dưỡng", systemImage: "text.viewfinder")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)

                    Button(action: onManual) {
                        Label("Nhập mã vạch thủ công", systemImage: "keyboard")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.bordered)
                }
                .controlSize(.large)
            }
            .padding()
        }
    }

    @ViewBuilder
    private var scannerArea: some View {
        if BarcodeScannerView.isAvailable {
            BarcodeScannerView(isScanning: isScanning, onScan: onPayload)
        } else {
            ZStack {
                Color(.secondarySystemBackground)
                VStack(spacing: 12) {
                    Image(systemName: "camera.metering.unknown")
                        .font(.system(size: 44))
                        .foregroundStyle(.secondary)
                    Text("Camera không khả dụng trên thiết bị này")
                        .font(.headline)
                        .multilineTextAlignment(.center)
                    Text("Thử với mã sản phẩm mẫu:")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    HStack {
                        ForEach(samples, id: \.code) { sample in
                            Button(sample.name) { onPayload(sample.code) }
                                .buttonStyle(.bordered)
                        }
                    }
                }
                .padding()
            }
        }
    }
}
