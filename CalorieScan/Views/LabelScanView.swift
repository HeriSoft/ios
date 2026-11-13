import PhotosUI
import SwiftUI

/// Chụp / chọn ảnh bảng dinh dưỡng, đọc chữ bằng OCR và tìm lượng calo.
struct LabelScanView: View {
    var barcode: String?
    var onResult: (ProductInfo) -> Void

    @State private var pickerItem: PhotosPickerItem?
    @State private var showCamera = false
    @State private var image: UIImage?
    @State private var isProcessing = false
    @State private var hasResult = false
    @State private var recognizedLines: [String] = []
    @State private var errorMessage: String?

    @State private var name = ""
    @State private var kcal: Double?
    @State private var basis: NutritionLabelResult.Basis = .per100g
    @State private var servingGrams: Double?

    var body: some View {
        Form {
            Section {
                if let image {
                    Image(uiImage: image)
                        .resizable()
                        .scaledToFit()
                        .frame(maxWidth: .infinity, maxHeight: 220)
                }
                if UIImagePickerController.isSourceTypeAvailable(.camera) {
                    Button { showCamera = true } label: {
                        Label("Chụp ảnh nhãn", systemImage: "camera")
                    }
                }
                PhotosPicker(selection: $pickerItem, matching: .images) {
                    Label("Chọn ảnh từ thư viện", systemImage: "photo.on.rectangle")
                }
                if isProcessing {
                    ProgressView("Đang đọc nhãn…")
                }
                if let errorMessage {
                    Text(errorMessage).foregroundStyle(.red)
                }
            } footer: {
                Text("Chụp rõ bảng \"Thông tin dinh dưỡng\" trên bao bì. Ứng dụng tự tìm số kcal, bạn có thể sửa lại nếu sai.")
            }

            if hasResult && !isProcessing {
                Section("Kết quả") {
                    TextField("Tên sản phẩm", text: $name)
                    HStack {
                        Text("Năng lượng")
                        Spacer()
                        TextField("kcal", value: $kcal, format: .number)
                            .keyboardType(.decimalPad)
                            .multilineTextAlignment(.trailing)
                            .frame(width: 90)
                        Text("kcal").foregroundStyle(.secondary)
                    }
                    Picker("Tính trên", selection: $basis) {
                        Text("100 g / ml").tag(NutritionLabelResult.Basis.per100g)
                        Text("1 khẩu phần").tag(NutritionLabelResult.Basis.perServing)
                    }
                    HStack {
                        Text("Khẩu phần")
                        Spacer()
                        TextField("không rõ", value: $servingGrams, format: .number)
                            .keyboardType(.decimalPad)
                            .multilineTextAlignment(.trailing)
                            .frame(width: 90)
                        Text("g").foregroundStyle(.secondary)
                    }
                    if kcal == nil {
                        Label("Không tìm thấy số kcal, hãy nhập tay.", systemImage: "exclamationmark.triangle")
                            .foregroundStyle(.orange)
                    }
                }

                Section {
                    Button {
                        onResult(makeProduct())
                    } label: {
                        Text("Tiếp tục tính calo").frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(kcal == nil || (basis == .perServing && servingGrams == nil && kcal == nil))
                }

                if !recognizedLines.isEmpty {
                    Section {
                        DisclosureGroup("Văn bản đọc được") {
                            Text(recognizedLines.joined(separator: "\n"))
                                .font(.caption.monospaced())
                                .textSelection(.enabled)
                        }
                    }
                }
            }
        }
        .navigationTitle("Quét nhãn dinh dưỡng")
        .navigationBarTitleDisplayMode(.inline)
        .onChange(of: pickerItem) { _, item in
            guard let item else { return }
            Task {
                if let data = try? await item.loadTransferable(type: Data.self), let picked = UIImage(data: data) {
                    await process(picked)
                } else {
                    errorMessage = "Không mở được ảnh."
                }
            }
        }
        .fullScreenCover(isPresented: $showCamera) {
            CameraPicker { captured in
                Task { await process(captured) }
            }
            .ignoresSafeArea()
        }
        .onAppear {
            if DemoMode.current == .label && !hasResult {
                apply(lines: DemoData.labelLines)
            }
        }
    }

    @MainActor
    private func process(_ newImage: UIImage) async {
        image = newImage
        errorMessage = nil
        isProcessing = true
        defer { isProcessing = false }
        do {
            apply(lines: try await TextRecognizer.recognizeLines(in: newImage))
        } catch {
            errorMessage = "Không đọc được chữ trên ảnh: \(error.localizedDescription)"
        }
    }

    private func apply(lines: [String]) {
        recognizedLines = lines
        let result = NutritionLabelParser.parse(lines: lines)
        kcal = result.kcal
        basis = result.basis
        servingGrams = result.servingGrams
        hasResult = true
    }

    private func makeProduct() -> ProductInfo {
        let value = kcal ?? 0
        let per100: Double?
        let perServing: Double?
        switch basis {
        case .per100g:
            per100 = value
            perServing = nil
        case .perServing:
            perServing = value
            per100 = servingGrams.flatMap { $0 > 0 ? value * 100 / $0 : nil }
        }
        let trimmed = name.trimmingCharacters(in: .whitespacesAndNewlines)
        return ProductInfo(
            barcode: barcode,
            name: trimmed.isEmpty ? "Sản phẩm từ nhãn" : trimmed,
            servingSizeText: servingGrams.map { "\($0.shortText) g" },
            servingGrams: servingGrams,
            kcalPer100g: per100,
            kcalPerServing: perServing,
            source: .label
        )
    }
}
