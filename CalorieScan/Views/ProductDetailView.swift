import SwiftData
import SwiftUI

struct ProductDetailView: View {
    enum AmountMode: String, CaseIterable, Identifiable {
        case grams = "Gram / ml"
        case servings = "Khẩu phần"
        var id: Self { self }
    }

    let product: ProductInfo
    var onSaved: () -> Void

    @Environment(\.modelContext) private var modelContext
    @State private var mode: AmountMode
    @State private var amount: Double
    @State private var manualKcal100: Double?
    @State private var showSaved = false

    init(product: ProductInfo, onSaved: @escaping () -> Void) {
        self.product = product
        self.onSaved = onSaved
        let preferServings = product.kcalPer100g == nil && product.effectiveKcalPerServing != nil
        _mode = State(initialValue: preferServings ? .servings : .grams)
        _amount = State(initialValue: preferServings ? 1 : (product.servingGrams ?? 100))
    }

    private var kcalPer100: Double? { product.kcalPer100g ?? manualKcal100 }

    private var kcalPerServing: Double? {
        if let value = product.effectiveKcalPerServing { return value }
        if let kcalPer100, let grams = product.servingGrams {
            return CalorieCalculator.kcal(per100g: kcalPer100, amount: grams)
        }
        return nil
    }

    private var totalKcal: Double? {
        switch mode {
        case .grams:
            return kcalPer100.map { CalorieCalculator.kcal(per100g: $0, amount: amount) }
        case .servings:
            return kcalPerServing.map { CalorieCalculator.kcal(perServing: $0, servings: amount) }
        }
    }

    var body: some View {
        Form {
            Section {
                header
            }

            Section("Giá trị dinh dưỡng") {
                if let kcalPer100 {
                    LabeledContent("Năng lượng / 100 g", value: kcalPer100.kcalText)
                } else {
                    HStack {
                        Text("Năng lượng / 100 g")
                        Spacer()
                        TextField("Nhập", value: $manualKcal100, format: .number)
                            .keyboardType(.decimalPad)
                            .multilineTextAlignment(.trailing)
                            .frame(width: 80)
                        Text("kcal").foregroundStyle(.secondary)
                    }
                }
                if let kcalPerServing {
                    LabeledContent("Mỗi khẩu phần \(product.servingSizeText.map { "(\($0))" } ?? "")",
                                   value: kcalPerServing.kcalText)
                }
                macroRow("Chất đạm", product.protein100g)
                macroRow("Carbohydrate", product.carbs100g)
                macroRow("  trong đó đường", product.sugars100g)
                macroRow("Chất béo", product.fat100g)
            }

            Section("Bạn ăn bao nhiêu?") {
                if kcalPerServing != nil {
                    Picker("Đơn vị", selection: $mode) {
                        ForEach(AmountMode.allCases) { Text($0.rawValue).tag($0) }
                    }
                    .pickerStyle(.segmented)
                }
                Stepper(value: $amount, in: 0...5000, step: mode == .grams ? 10 : 0.5) {
                    HStack {
                        TextField("Số lượng", value: $amount, format: .number)
                            .keyboardType(.decimalPad)
                            .frame(maxWidth: 100)
                        Text(mode == .grams ? "g / ml" : "phần")
                            .foregroundStyle(.secondary)
                    }
                }
            }

            Section {
                HStack {
                    Text("Tổng calo").font(.headline)
                    Spacer()
                    Text(totalKcal?.kcalText ?? "—")
                        .font(.title.bold())
                        .foregroundStyle(.orange)
                        .contentTransition(.numericText())
                }
                Button {
                    save()
                } label: {
                    Label("Thêm vào nhật ký", systemImage: "plus.circle.fill")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .disabled(totalKcal == nil)
            } footer: {
                if product.source == .openFoodFacts {
                    Text("Dữ liệu từ Open Food Facts (cộng đồng đóng góp). Giá trị có thể chưa chính xác tuyệt đối.")
                }
            }
        }
        .navigationTitle(product.name)
        .navigationBarTitleDisplayMode(.inline)
        .animation(.default, value: totalKcal)
        .onChange(of: mode) { _, newMode in
            amount = newMode == .grams ? (product.servingGrams ?? 100) : 1
        }
        .alert("Đã thêm vào nhật ký", isPresented: $showSaved) {
            Button("OK", action: onSaved)
        } message: {
            Text("\(product.name): \(totalKcal?.kcalText ?? "")")
        }
    }

    private var header: some View {
        HStack(spacing: 14) {
            AsyncImage(url: product.imageURL) { phase in
                if let image = phase.image {
                    image.resizable().scaledToFit()
                } else {
                    Image(systemName: "shippingbox.fill")
                        .font(.title)
                        .foregroundStyle(.secondary)
                }
            }
            .frame(width: 72, height: 72)
            .background(Color(.secondarySystemBackground))
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))

            VStack(alignment: .leading, spacing: 4) {
                Text(product.name).font(.headline)
                if let brand = product.brand {
                    Text(brand).font(.subheadline).foregroundStyle(.secondary)
                }
                HStack(spacing: 6) {
                    if let barcode = product.barcode {
                        Label(barcode, systemImage: "barcode")
                    }
                    if let quantity = product.quantityText {
                        Text("· \(quantity)")
                    }
                }
                .font(.caption)
                .foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 4)
    }

    @ViewBuilder
    private func macroRow(_ title: String, _ value: Double?) -> some View {
        if let value {
            LabeledContent(title, value: "\(value.shortText) g")
        }
    }

    private func save() {
        guard let totalKcal else { return }
        let entry = FoodEntry(
            name: product.name,
            brand: product.brand,
            barcode: product.barcode,
            amount: amount,
            unit: mode == .grams ? "g" : "phần",
            kcal: totalKcal
        )
        modelContext.insert(entry)
        try? modelContext.save()
        showSaved = true
    }
}
