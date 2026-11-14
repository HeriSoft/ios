import XCTest
@testable import CalorieScan

final class SymptomCheckerTests: XCTestCase {
    func testRedFlagMeansEmergency() {
        let a = SymptomChecker.assess(SymptomCheckInput(symptoms: [.headache], redFlags: [.strokeSigns]))
        XCTAssertEqual(a.level, .emergency)
        XCTAssertTrue(a.reasons.first?.contains("dấu hiệu nguy hiểm") ?? false)
    }

    func testRedFlagAloneWithoutSymptoms() {
        let a = SymptomChecker.assess(SymptomCheckInput(redFlags: [.selfHarm]))
        XCTAssertEqual(a.level, .emergency)
        XCTAssertTrue(a.matches.isEmpty)
    }

    func testChestPainIsAtLeastUrgent() {
        let a = SymptomChecker.assess(SymptomCheckInput(symptoms: [.chestPain]))
        XCTAssertGreaterThanOrEqual(a.level, .urgent)
    }

    func testMildColdIsSelfCare() {
        let a = SymptomChecker.assess(SymptomCheckInput(symptoms: [.runnyNose, .soreThroat, .cough], duration: .oneToThreeDays, severity: .mild))
        XCTAssertEqual(a.level, .selfCare)
        XCTAssertEqual(a.matches.first?.condition.id, "common-cold")
        XCTAssertTrue(a.showMedicationAdvice)
    }

    func testFeverWithAchesSuggestsDengueAndNeedsDoctor() {
        let a = SymptomChecker.assess(SymptomCheckInput(symptoms: [.fever, .headache, .muscleAche, .rash]))
        XCTAssertTrue(a.matches.contains { $0.condition.id == "dengue" })
        XCTAssertGreaterThanOrEqual(a.level, .seeDoctor)
    }

    func testLongFeverIsUrgent() {
        let a = SymptomChecker.assess(SymptomCheckInput(symptoms: [.fever], duration: .fourToSevenDays))
        XCTAssertEqual(a.level, .urgent)
    }

    func testVulnerableGroups() {
        let child = SymptomChecker.assess(SymptomCheckInput(symptoms: [.diarrhea], group: .childUnder5))
        XCTAssertEqual(child.level, .urgent)
        XCTAssertFalse(child.showMedicationAdvice)

        let pregnant = SymptomChecker.assess(SymptomCheckInput(symptoms: [.abdominalPain], group: .pregnant))
        XCTAssertEqual(pregnant.level, .urgent)
        XCTAssertFalse(pregnant.showMedicationAdvice)
    }

    func testUTIRequiresDoctor() {
        let a = SymptomChecker.assess(SymptomCheckInput(symptoms: [.painfulUrination]))
        XCTAssertEqual(a.matches.first?.condition.id, "uti")
        XCTAssertEqual(a.level, .seeDoctor)
    }

    func testRequiredSymptomsFilter() {
        // Không có "tiểu buốt" thì không gợi ý nhiễm trùng tiết niệu.
        let matches = SymptomChecker.match([.backPain, .fever])
        XCTAssertFalse(matches.contains { $0.condition.id == "uti" })
    }

    func testLongDurationNeedsDoctor() {
        let a = SymptomChecker.assess(SymptomCheckInput(symptoms: [.insomnia], duration: .overOneWeek))
        XCTAssertGreaterThanOrEqual(a.level, .seeDoctor)
    }

    func testLibraryIsConsistent() {
        let foodIDs = Set(FoodDatabase.all.map(\.id))
        let ids = ConditionLibrary.all.map(\.id)
        XCTAssertEqual(Set(ids).count, ids.count)
        for c in ConditionLibrary.all {
            XCTAssertTrue(c.required.isSubset(of: c.symptoms), c.id)
            XCTAssertFalse(c.selfCare.isEmpty, c.id)
            XCTAssertFalse(c.seeDoctorIf.isEmpty, c.id)
            for id in c.eatFoodIDs + c.avoidFoodIDs {
                XCTAssertTrue(foodIDs.contains(id), "\(c.id): unknown food \(id)")
            }
        }
        // Mọi triệu chứng đều có ít nhất một nguyên nhân gợi ý.
        let covered = Set(ConditionLibrary.all.flatMap(\.symptoms))
        XCTAssertEqual(covered, Set(Symptom.allCases))
    }

    func testDengueWarnsAgainstNSAIDs() throws {
        let dengue = try XCTUnwrap(ConditionLibrary.all.first { $0.id == "dengue" })
        XCTAssertTrue(dengue.otcMedicines.contains { $0.contains("ibuprofen") && $0.contains("KHÔNG") })
    }
}
