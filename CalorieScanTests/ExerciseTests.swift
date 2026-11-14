import XCTest
@testable import CalorieScan

final class ExerciseTests: XCTestCase {
    func testCalorieFormula() throws {
        // MET 4.3 × 3,5 × 62 kg / 200 × 30 phút ≈ 140 kcal
        let walk = try XCTUnwrap(ExerciseLibrary.exercise("walk-brisk"))
        XCTAssertEqual(walk.kcal(weightKg: 62, minutes: 30), 139.97, accuracy: 0.01)
        XCTAssertEqual(ExerciseLibrary.kcal(met: 8, weightKg: 70, minutes: 60), 588, accuracy: 0.01)
        XCTAssertEqual(ExerciseLibrary.kcal(met: 8, weightKg: 70, minutes: -10), 0)
    }

    func testLibraryIsConsistent() {
        let ids = ExerciseLibrary.all.map(\.id)
        XCTAssertEqual(Set(ids).count, ids.count)
        for e in ExerciseLibrary.all {
            XCTAssertTrue((1.5...15).contains(e.met), "\(e.id): MET \(e.met)")
        }
        for category in ExerciseCategory.allCases {
            XCTAssertTrue(ExerciseLibrary.all.contains { $0.category == category }, "\(category) empty")
        }
        XCTAssertFalse(HomeMove.all.isEmpty)
        XCTAssertEqual(Set(HomeMove.all.map(\.id)).count, HomeMove.all.count)
    }

    func testSearch() {
        XCTAssertTrue(ExerciseLibrary.search("boi").contains { $0.id == "swim-easy" })
        XCTAssertTrue(ExerciseLibrary.search("Cầu lông").contains { $0.id == "badminton" })
        XCTAssertEqual(ExerciseLibrary.search("").count, ExerciseLibrary.all.count)
    }

    func testPlansReferenceKnownExercises() {
        for goal in WeightGoal.allCases {
            for category in [BMICategory.normal, .obese2] {
                let plan = WorkoutPlanner.plan(goal: goal, age: 30, category: category)
                XCTAssertEqual(plan.days.count, 7)
                XCTAssertTrue(plan.days.contains { $0.isRest }, "\(goal): needs a rest day")
                for day in plan.days {
                    for id in day.exerciseIDs {
                        XCTAssertNotNil(ExerciseLibrary.exercise(id), "\(goal) \(day.day): \(id)")
                    }
                }
            }
        }
    }

    func testLowImpactPlanAvoidsHighImpact() {
        for goal in WeightGoal.allCases {
            let plan = WorkoutPlanner.plan(goal: goal, age: 65, category: .normal)
            XCTAssertTrue(plan.lowImpact)
            let ids = plan.days.flatMap(\.exerciseIDs)
            XCTAssertFalse(ids.contains { ExerciseLibrary.exercise($0)?.highImpact == true }, "\(goal): \(ids)")
        }
        XCTAssertTrue(WorkoutPlanner.needsLowImpact(age: 30, category: .obese1))
        XCTAssertFalse(WorkoutPlanner.needsLowImpact(age: 30, category: .normal))
    }

    func testLosePlanMeetsWHOMinimum() {
        let plan = WorkoutPlanner.plan(goal: .lose, age: 30, category: .overweight)
        XCTAssertGreaterThanOrEqual(plan.weeklyMinutes, 150)
    }
}
