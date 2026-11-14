import SwiftUI

enum BodyRoute: Hashable {
    case symptoms
}

/// Tính chỉ số cơ thể (BMI, BMR, TDEE…), calo mục tiêu và gợi ý thực phẩm.
struct BodyTab: View {
    @AppStorage("body.sex") private var sex: Sex = .female
    @AppStorage("body.age") private var age: Int = 28
    @AppStorage("body.height") private var heightCm: Double = 158
    @AppStorage("body.weight") private var weightKg: Double = 62
    @AppStorage("body.activity") private var activity: ActivityLevel = .light
    @AppStorage("body.goal") private var goal: WeightGoal = .lose
    @AppStorage("body.waist") private var waistCm: Double = 0
    @AppStorage("dailyGoal") private var dailyGoal: Double = 2000

    private var profile: BodyProfile {
        BodyProfile(sex: sex, age: age, heightCm: heightCm, weightKg: weightKg,
                    activity: activity, goal: goal, waistCm: waistCm > 0 ? waistCm : nil)
    }

    private var waistBinding: Binding<Double?> {
        Binding(get: { waistCm > 0 ? waistCm : nil }, set: { waistCm = $0 ?? 0 })
    }

    @State private var path: [BodyRoute] = DemoMode.current == .symptoms ? [.symptoms] : []

    var body: some View {
        NavigationStack(path: $path) {
            Form {
                Section {
                    NavigationLink(value: BodyRoute.symptoms) {
                        Label {
                            VStack(alignment: .leading, spacing: 2) {
                                Text("Kiểm tra triệu chứng")
                                Text("Đánh giá mức độ cần đi khám và cách chăm sóc").font(.caption).foregroundStyle(.secondary)
                            }
                        } icon: {
                            Image(systemName: "stethoscope").foregroundStyle(.red)
                        }
                    }
                }
                inputSection
                if let report = HealthCalculator.report(for: profile) {
                    bodySection(report)
                    energySection(report)
                    adviceSections(NutritionAdvisor.advice(for: profile, report: report))
                } else {
                    Section {
                        Label("Hãy nhập tuổi (10–100), chiều cao (100–250 cm) và cân nặng (20–300 kg) hợp lệ.",
                              systemImage: "exclamationmark.triangle")
                            .foregroundStyle(.orange)
                    }
                }
                Section {
                    EmptyView()
                } footer: {
                    Text("Kết quả chỉ để tham khảo cho người trưởng thành khỏe mạnh. Không áp dụng cho phụ nữ mang thai, người có bệnh mạn tính hoặc vận động viên. Không thay thế tư vấn của bác sĩ hay chuyên gia dinh dưỡng.")
                }
            }
            .navigationTitle("Cơ thể")
            .navigationDestination(for: BodyRoute.self) { route in
                switch route {
                case .symptoms: SymptomCheckerView()
                }
            }
        }
    }

    // MARK: - Nhập thông tin

    private var inputSection: some View {
        Section("Thông tin của bạn") {
            Picker("Giới tính", selection: $sex) {
                ForEach(Sex.allCases) { Text($0.title).tag($0) }
            }
            .pickerStyle(.segmented)

            Stepper(value: $age, in: 10...100) {
                LabeledContent("Tuổi", value: "\(age)")
            }
            numberRow("Chiều cao", value: $heightCm, unit: "cm")
            numberRow("Cân nặng", value: $weightKg, unit: "kg")
            HStack {
                Text("Vòng eo (tuỳ chọn)")
                Spacer()
                TextField("—", value: waistBinding, format: .number)
                    .keyboardType(.decimalPad)
                    .multilineTextAlignment(.trailing)
                    .frame(width: 70)
                Text("cm").foregroundStyle(.secondary)
            }
            Picker("Vận động", selection: $activity) {
                ForEach(ActivityLevel.allCases) { Text($0.title).tag($0) }
            }
            Picker("Mục tiêu", selection: $goal) {
                ForEach(WeightGoal.allCases) { Text($0.title).tag($0) }
            }
            .pickerStyle(.segmented)
        }
    }

    private func numberRow(_ title: String, value: Binding<Double>, unit: String) -> some View {
        HStack {
            Text(title)
            Spacer()
            TextField(title, value: value, format: .number)
                .keyboardType(.decimalPad)
                .multilineTextAlignment(.trailing)
                .frame(width: 70)
            Text(unit).foregroundStyle(.secondary)
        }
    }

    // MARK: - Kết quả

    private func bodySection(_ r: BodyReport) -> some View {
        Section("Chỉ số cơ thể") {
            VStack(alignment: .leading, spacing: 10) {
                HStack(alignment: .firstTextBaseline) {
                    Text("BMI").font(.headline)
                    Text(r.bmi.formatted(.number.precision(.fractionLength(1))))
                        .font(.largeTitle.bold())
                    Spacer()
                    Text(r.category.title)
                        .font(.subheadline.weight(.semibold))
                        .padding(.horizontal, 10)
                        .padding(.vertical, 4)
                        .background(color(for: r.category).opacity(0.18), in: Capsule())
                        .foregroundStyle(color(for: r.category))
                }
                BMIScale(bmi: r.bmi)
            }
            .padding(.vertical, 4)

            LabeledContent("Cân nặng hợp lý",
                           value: "\(r.healthyWeightRange.lowerBound.shortText) – \(r.healthyWeightRange.upperBound.shortText) kg")
            if r.weightChangeToHealthy > 0 {
                LabeledContent("Cần tăng", value: "≈ \(r.weightChangeToHealthy.shortText) kg")
            } else if r.weightChangeToHealthy < 0 {
                LabeledContent("Cần giảm", value: "≈ \((-r.weightChangeToHealthy).shortText) kg")
            } else {
                LabeledContent("Cân nặng", value: "Đang trong khoảng hợp lý ✓")
            }
            if let fat = r.bodyFatPercent {
                LabeledContent("Mỡ cơ thể (ước tính)", value: "\(fat.shortText) %")
            }
            if let ratio = r.waistToHeight {
                LabeledContent("Eo / chiều cao", value: ratio.formatted(.number.precision(.fractionLength(2))) + (ratio > 0.5 ? " ⚠︎" : " ✓"))
            }
        }
    }

    private func energySection(_ r: BodyReport) -> some View {
        Section {
            LabeledContent("BMR (năng lượng khi nghỉ)", value: r.bmr.kcalText)
            LabeledContent("TDEE (tiêu hao mỗi ngày)", value: r.tdee.kcalText)
            HStack {
                Text("Nên ăn mỗi ngày").font(.headline)
                Spacer()
                Text(r.targetKcal.kcalText)
                    .font(.title2.bold())
                    .foregroundStyle(.orange)
            }
            HStack(spacing: 0) {
                macro("Đạm", r.proteinGrams, .red)
                macro("Béo", r.fatGrams, .yellow)
                macro("Tinh bột", r.carbGrams, .blue)
                macro("Nước", r.waterLiters, .cyan, unit: "lít")
            }
            .padding(.vertical, 4)
            Button {
                dailyGoal = r.targetKcal
            } label: {
                Label(dailyGoal == r.targetKcal ? "Đang là mục tiêu nhật ký" : "Dùng làm mục tiêu nhật ký",
                      systemImage: dailyGoal == r.targetKcal ? "checkmark.circle.fill" : "target")
            }
            .disabled(dailyGoal == r.targetKcal)
        } header: {
            Text("Năng lượng mỗi ngày")
        } footer: {
            Text("BMR theo công thức Mifflin-St Jeor; TDEE = BMR × hệ số vận động.")
        }
    }

    private func macro(_ title: String, _ value: Double, _ color: Color, unit: String = "g") -> some View {
        VStack(spacing: 2) {
            Text(unit == "g" ? "\(Int(value.rounded()))" : value.shortText)
                .font(.headline.monospacedDigit())
                .foregroundStyle(color)
            Text("\(title) (\(unit))")
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
    }

    @ViewBuilder
    private func adviceSections(_ advice: NutritionAdvice) -> some View {
        Section("Nên ăn thêm") {
            ForEach(advice.eatMore) { suggestionRow($0, icon: "plus.circle.fill", tint: .green) }
        }
        Section("Nên hạn chế") {
            ForEach(advice.limit) { suggestionRow($0, icon: "minus.circle.fill", tint: .red) }
        }
        Section("Lời khuyên") {
            ForEach(advice.tips, id: \.self) { tip in
                Label(tip, systemImage: "lightbulb")
                    .font(.subheadline)
            }
        }
    }

    private func suggestionRow(_ s: FoodSuggestion, icon: String, tint: Color) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: icon).foregroundStyle(tint)
            VStack(alignment: .leading, spacing: 2) {
                Text(s.food.name)
                Text(s.reason).font(.caption).foregroundStyle(.secondary)
            }
            Spacer()
            Text("\(s.food.kcalPerPortion.kcalText)\n\(s.food.portionName)")
                .font(.caption.monospacedDigit())
                .multilineTextAlignment(.trailing)
                .foregroundStyle(.secondary)
        }
    }

    private func color(for category: BMICategory) -> Color {
        switch category {
        case .underweight: return .blue
        case .normal: return .green
        case .overweight: return .orange
        case .obese1, .obese2: return .red
        }
    }
}

/// Thanh màu thể hiện vị trí BMI (15–35).
private struct BMIScale: View {
    let bmi: Double
    private let range = 15.0...35.0
    private let bands: [(upper: Double, color: Color)] = [
        (18.5, .blue), (23, .green), (25, .orange), (30, .red), (35, Color(red: 0.6, green: 0, blue: 0)),
    ]

    var body: some View {
        GeometryReader { geo in
            let width = geo.size.width
            let span = range.upperBound - range.lowerBound
            ZStack(alignment: .leading) {
                HStack(spacing: 2) {
                    ForEach(Array(bands.enumerated()), id: \.offset) { index, band in
                        let lower = index == 0 ? range.lowerBound : bands[index - 1].upper
                        band.color.opacity(0.8)
                            .frame(width: max(0, width * (band.upper - lower) / span - 2))
                    }
                }
                .frame(height: 8)
                .clipShape(Capsule())

                let clamped = min(max(bmi, range.lowerBound), range.upperBound)
                Circle()
                    .fill(Color(.systemBackground))
                    .overlay(Circle().stroke(Color.primary, lineWidth: 2))
                    .frame(width: 16, height: 16)
                    .offset(x: width * (clamped - range.lowerBound) / span - 8)
            }
            .frame(height: 16)
        }
        .frame(height: 16)
    }
}
