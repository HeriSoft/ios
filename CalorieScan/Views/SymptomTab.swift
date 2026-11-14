import SwiftUI

/// Nhập triệu chứng → đánh giá mức độ khẩn cấp và gợi ý chăm sóc.
/// Được mở từ tab Cơ thể (nằm trong NavigationStack của tab đó).
struct SymptomCheckerView: View {
    @State private var input = DemoMode.initialSymptomInput
    @State private var showResult = DemoMode.current == .symptoms

    var body: some View {
        SymptomInputView(input: $input) { showResult = true }
            .navigationTitle("Kiểm tra triệu chứng")
            .navigationBarTitleDisplayMode(.inline)
            .navigationDestination(isPresented: $showResult) {
                SymptomResultView(assessment: SymptomChecker.assess(input))
            }
    }
}

private struct SymptomInputView: View {
    @Binding var input: SymptomCheckInput
    var onSubmit: () -> Void

    private let columns = [GridItem(.adaptive(minimum: 140), spacing: 8)]

    var body: some View {
        Form {
            Section {
                MedicalDisclaimer()
            }

            Section("Bạn đang có triệu chứng gì?") {
                LazyVGrid(columns: columns, spacing: 8) {
                    ForEach(Symptom.allCases) { symptom in
                        let selected = input.symptoms.contains(symptom)
                        Button {
                            if selected { input.symptoms.remove(symptom) } else { input.symptoms.insert(symptom) }
                        } label: {
                            Label(symptom.title, systemImage: symptom.icon)
                                .font(.subheadline)
                                .lineLimit(2)
                                .frame(maxWidth: .infinity, minHeight: 36, alignment: .leading)
                                .padding(.horizontal, 10)
                                .padding(.vertical, 6)
                                .background(selected ? Color.orange.opacity(0.2) : Color(.secondarySystemBackground),
                                            in: RoundedRectangle(cornerRadius: 10, style: .continuous))
                                .overlay(RoundedRectangle(cornerRadius: 10, style: .continuous)
                                    .stroke(selected ? Color.orange : .clear, lineWidth: 1.5))
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(.vertical, 4)
            }

            Section("Thông tin thêm") {
                Picker("Người bệnh", selection: $input.group) {
                    ForEach(PatientGroup.allCases) { Text($0.title).tag($0) }
                }
                Picker("Đã bị bao lâu", selection: $input.duration) {
                    ForEach(SymptomDuration.allCases) { Text($0.title).tag($0) }
                }
                Picker("Mức độ", selection: $input.severity) {
                    ForEach(SymptomSeverity.allCases) { Text($0.title).tag($0) }
                }
                .pickerStyle(.segmented)
            }

            Section {
                ForEach(RedFlag.allCases) { flag in
                    Toggle(isOn: Binding(
                        get: { input.redFlags.contains(flag) },
                        set: { on in if on { input.redFlags.insert(flag) } else { input.redFlags.remove(flag) } }
                    )) {
                        Text(flag.title).font(.subheadline)
                    }
                    .tint(.red)
                }
            } header: {
                Text("Có dấu hiệu nguy hiểm nào không?")
            } footer: {
                Text("Nếu có bất kỳ dấu hiệu nào ở trên, hãy gọi 115 hoặc đến cấp cứu ngay.")
            }

            Section {
                Button(action: onSubmit) {
                    Text("Xem đánh giá").frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
                .disabled(input.symptoms.isEmpty && input.redFlags.isEmpty)
            }
        }
    }
}

struct SymptomResultView: View {
    let assessment: SymptomAssessment

    var body: some View {
        List {
            Section {
                VStack(alignment: .leading, spacing: 8) {
                    Label(assessment.level.title, systemImage: icon)
                        .font(.title3.bold())
                        .foregroundStyle(color)
                    Text(assessment.level.detail)
                        .font(.subheadline)
                    if assessment.level == .emergency, let url = URL(string: "tel://115") {
                        Link(destination: url) {
                            Label("Gọi 115", systemImage: "phone.fill")
                                .font(.headline)
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 10)
                                .background(Color.red, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
                                .foregroundStyle(.white)
                        }
                        .padding(.top, 4)
                    }
                }
                .padding(.vertical, 6)
                .listRowBackground(color.opacity(0.12))
            }

            Section("Vì sao") {
                ForEach(assessment.reasons, id: \.self) { reason in
                    Label(reason, systemImage: "info.circle").font(.subheadline)
                }
            }

            if !assessment.matches.isEmpty {
                Section {
                    ForEach(assessment.matches) { match in
                        NavigationLink {
                            ConditionDetailView(condition: match.condition, showMedication: assessment.showMedicationAdvice)
                        } label: {
                            VStack(alignment: .leading, spacing: 3) {
                                HStack {
                                    Text(match.condition.name).font(.headline)
                                    Spacer()
                                    Text("khớp \(match.matched)/\(match.condition.symptoms.count)")
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                Text(match.condition.summary)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                Label(match.condition.specialty, systemImage: "stethoscope")
                                    .font(.caption)
                                    .foregroundStyle(.orange)
                            }
                            .padding(.vertical, 2)
                        }
                    }
                } header: {
                    Text("Có thể là")
                } footer: {
                    Text("Đây chỉ là các nguyên nhân thường gặp có triệu chứng tương tự, không phải chẩn đoán. Bấm vào từng mục để xem cách chăm sóc.")
                }
            }

            Section {
                MedicalDisclaimer()
            }
        }
        .navigationTitle("Đánh giá")
        .navigationBarTitleDisplayMode(.inline)
    }

    private var color: Color {
        switch assessment.level {
        case .selfCare: return .green
        case .seeDoctor: return .yellow
        case .urgent: return .orange
        case .emergency: return .red
        }
    }

    private var icon: String {
        switch assessment.level {
        case .selfCare: return "house.fill"
        case .seeDoctor: return "calendar.badge.clock"
        case .urgent: return "cross.case.fill"
        case .emergency: return "exclamationmark.triangle.fill"
        }
    }
}

struct ConditionDetailView: View {
    let condition: Condition
    let showMedication: Bool

    private func foods(_ ids: [String]) -> [FoodItem] {
        ids.compactMap { id in FoodDatabase.all.first { $0.id == id } }
    }

    var body: some View {
        List {
            Section {
                Text(condition.summary)
                LabeledContent("Chuyên khoa nên khám", value: condition.specialty)
            }

            Section {
                ForEach(condition.seeDoctorIf, id: \.self) { item in
                    Label(item, systemImage: "exclamationmark.circle.fill")
                        .foregroundStyle(.red)
                        .font(.subheadline)
                }
            } header: {
                Text("Đi khám ngay nếu")
            }

            Section("Nghỉ ngơi & chăm sóc") {
                ForEach(condition.selfCare, id: \.self) { item in
                    Label(item, systemImage: "checkmark.circle").font(.subheadline)
                }
            }

            let eat = foods(condition.eatFoodIDs)
            let avoid = foods(condition.avoidFoodIDs)
            if !eat.isEmpty || !avoid.isEmpty {
                Section("Ăn uống") {
                    ForEach(eat) { food in
                        Label("Nên ăn: \(food.name)", systemImage: "plus.circle.fill")
                            .foregroundStyle(.green)
                            .font(.subheadline)
                    }
                    ForEach(avoid) { food in
                        Label("Hạn chế: \(food.name)", systemImage: "minus.circle.fill")
                            .foregroundStyle(.red)
                            .font(.subheadline)
                    }
                }
            }

            if showMedication {
                if !condition.otcMedicines.isEmpty {
                    Section {
                        ForEach(condition.otcMedicines, id: \.self) { item in
                            Label(item, systemImage: "pills").font(.subheadline)
                        }
                    } header: {
                        Text("Thuốc không kê đơn thường dùng")
                    } footer: {
                        Text("App không ghi liều lượng. Đọc kỹ hướng dẫn trên bao bì và hỏi dược sĩ. Người có bệnh gan, thận, dạ dày, đang dùng thuốc khác, cho con bú hoặc dị ứng thuốc cần hỏi bác sĩ trước. Không dùng chung nhiều thuốc cùng chứa paracetamol.")
                    }
                }
                if !condition.homeRemedies.isEmpty {
                    Section {
                        ForEach(condition.homeRemedies, id: \.self) { item in
                            Label(item, systemImage: "leaf").font(.subheadline)
                        }
                    } header: {
                        Text("Mẹo dân gian / thảo dược")
                    } footer: {
                        Text("Chỉ hỗ trợ giảm khó chịu, không thay thế điều trị. Dừng lại nếu có dấu hiệu dị ứng hoặc triệu chứng nặng lên.")
                    }
                }
            } else {
                Section {
                    Label("Trẻ dưới 5 tuổi và phụ nữ mang thai không nên tự dùng thuốc hay thảo dược. Hãy hỏi bác sĩ hoặc dược sĩ trước khi dùng bất cứ thứ gì.",
                          systemImage: "exclamationmark.shield")
                        .font(.subheadline)
                        .foregroundStyle(.orange)
                }
            }

            Section {
                MedicalDisclaimer()
            }
        }
        .navigationTitle(condition.name)
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct MedicalDisclaimer: View {
    var body: some View {
        Label {
            Text("Thông tin chỉ để tham khảo, **không phải chẩn đoán y khoa** và không thay thế bác sĩ. Khi nghi ngờ, hãy đi khám. Trường hợp khẩn cấp gọi **115**.")
                .font(.footnote)
        } icon: {
            Image(systemName: "cross.case")
                .foregroundStyle(.red)
        }
    }
}
