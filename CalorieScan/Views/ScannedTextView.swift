import SwiftUI

/// Hiển thị nội dung mã QR không phải mã sản phẩm.
struct ScannedTextView: View {
    let text: String

    private var url: URL? {
        guard let url = URL(string: text), let scheme = url.scheme?.lowercased(),
              scheme == "http" || scheme == "https" else { return nil }
        return url
    }

    var body: some View {
        Form {
            Section {
                Text(text).textSelection(.enabled)
            } header: {
                Text("Nội dung mã QR")
            } footer: {
                Text("Đây không phải mã sản phẩm nên không tra cứu được calo. Hãy quét mã vạch hoặc nhãn dinh dưỡng trên bao bì.")
            }
            Section {
                if let url {
                    Link(destination: url) { Label("Mở liên kết", systemImage: "safari") }
                }
                Button {
                    UIPasteboard.general.string = text
                } label: {
                    Label("Sao chép", systemImage: "doc.on.doc")
                }
                ShareLink(item: text) { Label("Chia sẻ", systemImage: "square.and.arrow.up") }
            }
        }
        .navigationTitle("Mã QR")
        .navigationBarTitleDisplayMode(.inline)
    }
}
