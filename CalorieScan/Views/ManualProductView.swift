import SwiftUI

/// Tự nhập lượng calo khi sản phẩm không có trong cơ sở dữ liệu.
struct ManualProductView: View {
    var barcode: String?
    var onResult: (ProductInfo) -> Void

    @State private var name = ""
    @State private var kcalPer100: Double?
    @State private var servingGrams: Double?

    var body: some View {
        Form {
            Section {
                TextField("Tên sản phẩm", text: $name)
                HStack {
                    Text("Năng lượng / 100 g")
                    Spacer()
                    TextField("kcal", value: $kcalPer100, format: .number)
                        .keyboardType(.decimalPad)
                        .multilineTextAlignment(.trailing)
                        .frame(width: 90)
                }
                HStack {
                    Text("Khẩu phần (tuỳ chọn)")
                    Spacer()
                    TextField("g", value: $servingGrams, format: .number)
                        .keyboardType(.decimalPad)
                        .multilineTextAlignment(.trailing)
                        .frame(width: 90)
                }
            } footer: {
                Text("Xem số kcal trong bảng thông tin dinh dưỡng in trên bao bì.")
            }

            Section {
                Button("Tiếp tục tính calo") {
                    let trimmed = name.trimmingCharacters(in: .whitespacesAndNewlines)
                    onResult(ProductInfo(
                        barcode: barcode,
                        name: trimmed.isEmpty ? "Sản phẩm tự nhập" : trimmed,
                        servingSizeText: servingGrams.map { "\($0.shortText) g" },
                        servingGrams: servingGrams,
                        kcalPer100g: kcalPer100,
                        source: .manual
                    ))
                }
                .disabled(kcalPer100 == nil)
            }
        }
        .navigationTitle("Nhập thủ công")
        .navigationBarTitleDisplayMode(.inline)
    }
}
