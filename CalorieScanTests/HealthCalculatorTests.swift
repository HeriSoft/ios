import XCTest
@testable import CalorieScan

final class HealthCalculatorTests: XCTestCase {
    private func profile(_ sex: Sex, age: Int, height: Double, weight: Double,
                         activity: ActivityLevel = .sedentary, goal: WeightGoal = .maintain,
                         waist: Double? = nil) -> BodyProfile {
        BodyProfile(sex: sex, age: age, heightCm: height, weightKg: weight,
                    activity: activity, goal: goal, waistCm: waist)
    }

    func testBMICategoriesUseAsianCutoffs() {
        XCTAssertEqual(BMICategory(bmi: 18.49), .underweight)
        XCTAssertEqual(BMICategory(bmi: 18.5), .normal)
        XCTAssertEqual(BMICategory(bmi: 22.99), .normal)
        XCTAssertEqual(BMICategory(bmi: 23), .overweight)
        XCTAssertEqual(BMICategory(bmi: 25), .obese1)
        XCTAssertEqual(BMICategory(bmi: 30), .obese2)
    }

    func testFemaleLosingWeight() throws {
        let r = try XCTUnwrap(HealthCalculator.report(for: profile(.female, age: 28, height: 158, weight: 62, activity: .light, goal: .lose)))
        XCTAssertEqual(r.bmi, 24.84, accuracy: 0.01)
        XCTAssertEqual(r.category, .overweight)
        XCTAssertEqual(r.bmr, 1306.5, accuracy: 0.01)          // 10*62 + 6.25*158 - 5*28 - 161
        XCTAssertEqual(r.tdee, 1796.44, accuracy: 0.01)        // × 1.375
        XCTAssertEqual(r.targetKcal, 1300)                     // TDEE - 500, làm tròn 10
        XCTAssertEqual(r.healthyWeightRange.lowerBound, 46.18, accuracy: 0.01)
        XCTAssertEqual(r.healthyWeightRange.upperBound, 57.17, accuracy: 0.01)
        XCTAssertEqual(r.weightChangeToHealthy, -4.83, accuracy: 0.01)
        XCTAssertEqual(r.proteinGrams, 99.2, accuracy: 0.01)   // 1,6 g/kg
        XCTAssertEqual(r.waterLiters, 2.17, accuracy: 0.01)
        XCTAssertTrue(r.isAdult)
        XCTAssertNotNil(r.bodyFatPercent)
    }

    func testMaleMaintaining() throws {
        let r = try XCTUnwrap(HealthCalculator.report(for: profile(.male, age: 30, height: 175, weight: 70, activity: .moderate)))
        XCTAssertEqual(r.bmr, 1648.75, accuracy: 0.01)
        XCTAssertEqual(r.targetKcal, 2560)
        XCTAssertEqual(r.category, .normal)
        XCTAssertEqual(r.weightChangeToHealthy, 0)
        // Năng lượng từ đạm + béo + tinh bột = mục tiêu.
        XCTAssertEqual(r.proteinGrams * 4 + r.fatGrams * 9 + r.carbGrams * 4, r.targetKcal, accuracy: 0.5)
    }

    func testLoseNeverBelowMinimumOrAboveTDEE() throws {
        let small = try XCTUnwrap(HealthCalculator.report(for: profile(.female, age: 60, height: 150, weight: 45, goal: .lose)))
        XCTAssertEqual(small.targetKcal, 1110)   // TDEE < 1200 nên giữ ở TDEE, không cắt thêm
        let r = try XCTUnwrap(HealthCalculator.report(for: profile(.female, age: 40, height: 155, weight: 58, goal: .lose)))
        XCTAssertGreaterThanOrEqual(r.targetKcal, 1200)
    }

    func testGainAddsSurplus() throws {
        let r = try XCTUnwrap(HealthCalculator.report(for: profile(.male, age: 20, height: 170, weight: 50, goal: .gain)))
        XCTAssertEqual(r.targetKcal, ((r.tdee + 300) / 10).rounded() * 10)
        XCTAssertEqual(r.category, .underweight)
        XCTAssertGreaterThan(r.weightChangeToHealthy, 0)
    }

    func testWaistAndMinors() throws {
        let r = try XCTUnwrap(HealthCalculator.report(for: profile(.male, age: 15, height: 160, weight: 50, waist: 85)))
        XCTAssertEqual(try XCTUnwrap(r.waistToHeight), 0.53, accuracy: 0.01)
        XCTAssertFalse(r.isAdult)
        XCTAssertNil(r.bodyFatPercent)
    }

    func testInvalidInput() {
        XCTAssertNil(HealthCalculator.report(for: profile(.male, age: 30, height: 0, weight: 70)))
        XCTAssertNil(HealthCalculator.report(for: profile(.male, age: 5, height: 110, weight: 20)))
    }
}

final class NutritionAdvisorTests: XCTestCase {
    func testAllSuggestedFoodsExist() {
        let ids = Set(FoodDatabase.all.map(\.id))
        for (goal, list) in NutritionAdvisor.eatMore {
            for (id, _) in list { XCTAssertTrue(ids.contains(id), "eatMore[\(goal)]: \(id)") }
        }
        for (goal, list) in NutritionAdvisor.limit {
            for (id, _) in list { XCTAssertTrue(ids.contains(id), "limit[\(goal)]: \(id)") }
        }
        XCTAssertEqual(Set(NutritionAdvisor.eatMore.keys), Set(WeightGoal.allCases))
    }

    func testWarnsWhenUnderweightWantsToLose() throws {
        let p = BodyProfile(sex: .female, age: 25, heightCm: 165, weightKg: 45, activity: .light, goal: .lose)
        let r = try XCTUnwrap(HealthCalculator.report(for: p))
        let advice = NutritionAdvisor.advice(for: p, report: r)
        XCTAssertTrue(advice.tips.contains { $0.contains("không nên giảm cân") })
        XCTAssertFalse(advice.eatMore.isEmpty)
        XCTAssertFalse(advice.limit.isEmpty)
    }

    func testWaistWarning() throws {
        let p = BodyProfile(sex: .male, age: 40, heightCm: 170, weightKg: 80, activity: .light, goal: .lose, waistCm: 100)
        let r = try XCTUnwrap(HealthCalculator.report(for: p))
        XCTAssertTrue(NutritionAdvisor.advice(for: p, report: r).tips.contains { $0.contains("mỡ bụng") })
    }
}
