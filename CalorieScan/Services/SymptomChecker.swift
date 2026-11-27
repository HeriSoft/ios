import Foundation

struct SymptomCheckInput: Equatable {
    var symptoms: Set<Symptom> = []
    var redFlags: Set<RedFlag> = []
    var group: PatientGroup = .adult
    var duration: SymptomDuration = .oneToThreeDays
    var severity: SymptomSeverity = .mild
}

struct ConditionMatch: Identifiable, Hashable {
    let condition: Condition
    let matched: Int
    let score: Double
    var id: String { condition.id }
}

struct SymptomAssessment {
    let level: CareLevel
    let reasons: [String]
    let matches: [ConditionMatch]
    /// Trẻ dưới 5 tuổi và phụ nữ mang thai: không gợi ý thuốc/thảo dược.
    let showMedicationAdvice: Bool
}

/// Đánh giá mức độ cần đi khám từ triệu chứng (công cụ tham khảo, không phải chẩn đoán).
enum SymptomChecker {
    static func assess(_ input: SymptomCheckInput) -> SymptomAssessment {
        var level = CareLevel.selfCare
        var reasons: [String] = []
        func raise(_ newLevel: CareLevel, _ reason: String) {
            level = max(level, newLevel)
            reasons.append(reason)
        }

        if !input.redFlags.isEmpty {
            raise(.emergency, "Có dấu hiệu nguy hiểm: " + RedFlag.allCases.filter(input.redFlags.contains).map(\.title).joined(separator: "; "))
        }
        if input.symptoms.contains(.chestPain) || input.symptoms.contains(.shortnessOfBreath) {
            raise(.urgent, "Đau ngực hoặc khó thở cần được bác sĩ kiểm tra sớm.")
        }
        if input.severity == .severe {
            raise(.urgent, "Triệu chứng ở mức nặng.")
        }
        let hasFeverOrFluidLoss = input.symptoms.contains(.fever) || input.symptoms.contains(.diarrhea) || input.symptoms.contains(.nausea)
        if input.group.isVulnerable && hasFeverOrFluidLoss {
            raise(.urgent, "\(input.group.title) dễ diễn biến nặng khi sốt, nôn hoặc tiêu chảy.")
        }
        if input.group == .pregnant && input.symptoms.contains(.abdominalPain) {
            raise(.urgent, "Đau bụng khi mang thai cần được bác sĩ sản khoa kiểm tra.")
        }
        if input.symptoms.contains(.fever) && input.duration >= .fourToSevenDays {
            raise(.urgent, "Sốt trên 3 ngày cần đi khám (ở Việt Nam cần loại trừ sốt xuất huyết).")
        }
        if input.duration == .overOneWeek {
            raise(.seeDoctor, "Triệu chứng kéo dài trên 1 tuần.")
        } else if input.severity == .moderate && input.duration >= .fourToSevenDays {
            raise(.seeDoctor, "Triệu chứng mức vừa kéo dài nhiều ngày.")
        }

        let matches = match(input.symptoms)
        // Xét mọi nguyên nhân được liệt kê, không chỉ nguyên nhân đứng đầu
        // (ví dụ sốt xuất huyết đứng thứ hai vẫn cần đi khám để loại trừ).
        for m in matches where m.condition.minimumLevel > level {
            raise(m.condition.minimumLevel, "Có thể là \"\(m.condition.name)\": cần bác sĩ khám để xác định và điều trị.")
        }
        if reasons.isEmpty {
            reasons.append("Chưa thấy dấu hiệu cần đi khám gấp dựa trên thông tin bạn nhập.")
        }

        return SymptomAssessment(
            level: level,
            reasons: reasons,
            matches: matches,
            showMedicationAdvice: input.group != .childUnder5 && input.group != .pregnant
        )
    }

    /// Xếp hạng các nguyên nhân thường gặp theo mức độ trùng triệu chứng.
    static func match(_ selected: Set<Symptom>, limit: Int = 3) -> [ConditionMatch] {
        guard !selected.isEmpty else { return [] }
        return ConditionLibrary.all
            .compactMap { condition -> ConditionMatch? in
                guard condition.required.isSubset(of: selected) else { return nil }
                let matched = condition.symptoms.intersection(selected).count
                guard matched > 0 else { return nil }
                let coverage = Double(matched) / Double(condition.symptoms.count)
                let precision = Double(matched) / Double(selected.count)
                let score = 0.6 * coverage + 0.4 * precision
                return score >= 0.25 ? ConditionMatch(condition: condition, matched: matched, score: score) : nil
            }
            .sorted { $0.score != $1.score ? $0.score > $1.score : $0.condition.name < $1.condition.name }
            .prefix(limit)
            .map { $0 }
    }
}
