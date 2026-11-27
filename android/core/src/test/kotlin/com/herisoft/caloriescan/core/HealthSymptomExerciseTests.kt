package com.herisoft.caloriescan.core

import org.junit.Assert.*
import org.junit.Test

class HealthCalculatorTests {
    private fun profile(sex: Sex, age: Int, h: Double, w: Double, activity: ActivityLevel = ActivityLevel.sedentary,
                        goal: WeightGoal = WeightGoal.maintain, waist: Double? = null) =
        BodyProfile(sex, age, h, w, activity, goal, waist)

    @Test fun bmiCategoriesUseAsianCutoffs() {
        assertEquals(BMICategory.underweight, BMICategory.of(18.49))
        assertEquals(BMICategory.normal, BMICategory.of(18.5))
        assertEquals(BMICategory.normal, BMICategory.of(22.99))
        assertEquals(BMICategory.overweight, BMICategory.of(23.0))
        assertEquals(BMICategory.obese1, BMICategory.of(25.0))
        assertEquals(BMICategory.obese2, BMICategory.of(30.0))
    }

    @Test fun femaleLosingWeight() {
        val r = HealthCalculator.report(profile(Sex.female, 28, 158.0, 62.0, ActivityLevel.light, WeightGoal.lose))!!
        assertEquals(24.84, r.bmi, 0.01)
        assertEquals(BMICategory.overweight, r.category)
        assertEquals(1306.5, r.bmr, 0.01)
        assertEquals(1796.44, r.tdee, 0.01)
        assertEquals(1300.0, r.targetKcal, 0.0)
        assertEquals(46.18, r.healthyWeightRange.start, 0.01)
        assertEquals(57.17, r.healthyWeightRange.endInclusive, 0.01)
        assertEquals(-4.83, r.weightChangeToHealthy, 0.01)
        assertEquals(99.2, r.proteinGrams, 0.01)
        assertEquals(2.17, r.waterLiters, 0.01)
        assertTrue(r.isAdult)
        assertNotNull(r.bodyFatPercent)
    }

    @Test fun maleMaintaining() {
        val r = HealthCalculator.report(profile(Sex.male, 30, 175.0, 70.0, ActivityLevel.moderate))!!
        assertEquals(1648.75, r.bmr, 0.01)
        assertEquals(2560.0, r.targetKcal, 0.0)
        assertEquals(BMICategory.normal, r.category)
        assertEquals(0.0, r.weightChangeToHealthy, 0.0)
        assertEquals(r.targetKcal, r.proteinGrams * 4 + r.fatGrams * 9 + r.carbGrams * 4, 0.5)
    }

    @Test fun loseNeverBelowMinimumOrAboveTDEE() {
        assertEquals(1110.0, HealthCalculator.report(profile(Sex.female, 60, 150.0, 45.0, goal = WeightGoal.lose))!!.targetKcal, 0.0)
        assertTrue(HealthCalculator.report(profile(Sex.female, 40, 155.0, 58.0, goal = WeightGoal.lose))!!.targetKcal >= 1200)
    }

    @Test fun gainAddsSurplus() {
        val r = HealthCalculator.report(profile(Sex.male, 20, 170.0, 50.0, goal = WeightGoal.gain))!!
        assertEquals(((r.tdee + 300) / 10).roundHalfUp() * 10, r.targetKcal, 0.0)
        assertEquals(BMICategory.underweight, r.category)
        assertTrue(r.weightChangeToHealthy > 0)
    }

    @Test fun waistAndMinors() {
        val r = HealthCalculator.report(profile(Sex.male, 15, 160.0, 50.0, waist = 85.0))!!
        assertEquals(0.53, r.waistToHeight!!, 0.01)
        assertFalse(r.isAdult)
        assertNull(r.bodyFatPercent)
    }

    @Test fun invalidInput() {
        assertNull(HealthCalculator.report(profile(Sex.male, 30, 0.0, 70.0)))
        assertNull(HealthCalculator.report(profile(Sex.male, 5, 110.0, 20.0)))
    }

    @Test fun advisorFoodsExistAndWarnings() {
        for ((_, list) in NutritionAdvisor.eatMore + NutritionAdvisor.limit) for ((id, _) in list) assertNotNull(id, FoodDatabase.byId(id))
        assertEquals(WeightGoal.entries.toSet(), NutritionAdvisor.eatMore.keys)
        val p = BodyProfile(Sex.female, 25, 165.0, 45.0, ActivityLevel.light, WeightGoal.lose)
        val a = NutritionAdvisor.advice(p, HealthCalculator.report(p)!!)
        assertTrue(a.tips.any { it.contains("không nên giảm cân") })
        val p2 = BodyProfile(Sex.male, 40, 170.0, 80.0, ActivityLevel.light, WeightGoal.lose, 100.0)
        assertTrue(NutritionAdvisor.advice(p2, HealthCalculator.report(p2)!!).tips.any { it.contains("mỡ bụng") })
    }
}

class SymptomCheckerTests {
    private fun assess(symptoms: Set<Symptom> = emptySet(), redFlags: Set<RedFlag> = emptySet(), group: PatientGroup = PatientGroup.adult,
                       duration: SymptomDuration = SymptomDuration.oneToThreeDays, severity: SymptomSeverity = SymptomSeverity.mild) =
        SymptomChecker.assess(SymptomCheckInput(symptoms, redFlags, group, duration, severity))

    @Test fun redFlagMeansEmergency() {
        val a = assess(setOf(Symptom.headache), setOf(RedFlag.strokeSigns))
        assertEquals(CareLevel.emergency, a.level)
        assertTrue(a.reasons.first().contains("dấu hiệu nguy hiểm"))
        assertEquals(CareLevel.emergency, assess(redFlags = setOf(RedFlag.selfHarm)).level)
    }

    @Test fun chestPainIsAtLeastUrgent() {
        assertTrue(assess(setOf(Symptom.chestPain)).level >= CareLevel.urgent)
    }

    @Test fun mildColdIsSelfCare() {
        val a = assess(setOf(Symptom.runnyNose, Symptom.soreThroat, Symptom.cough))
        assertEquals(CareLevel.selfCare, a.level)
        assertEquals("common-cold", a.matches.first().condition.id)
        assertTrue(a.showMedicationAdvice)
    }

    @Test fun feverWithAchesSuggestsDengue() {
        val a = assess(setOf(Symptom.fever, Symptom.headache, Symptom.muscleAche, Symptom.rash))
        assertTrue(a.matches.any { it.condition.id == "dengue" })
        assertTrue(a.level >= CareLevel.seeDoctor)
    }

    @Test fun dengueAnywhereInMatchesRaisesLevel() {
        // Cúm đứng đầu, sốt xuất huyết đứng sau: vẫn phải khuyên đi khám.
        val a = assess(setOf(Symptom.fever, Symptom.headache, Symptom.muscleAche, Symptom.fatigue), severity = SymptomSeverity.moderate)
        assertNotEquals("dengue", a.matches.first().condition.id)
        assertTrue(a.matches.any { it.condition.id == "dengue" })
        assertEquals(CareLevel.seeDoctor, a.level)
        assertTrue(a.reasons.any { it.contains("Sốt xuất huyết") })
    }

    @Test fun longFeverAndVulnerableGroups() {
        assertEquals(CareLevel.urgent, assess(setOf(Symptom.fever), duration = SymptomDuration.fourToSevenDays).level)
        val child = assess(setOf(Symptom.diarrhea), group = PatientGroup.childUnder5)
        assertEquals(CareLevel.urgent, child.level)
        assertFalse(child.showMedicationAdvice)
        val pregnant = assess(setOf(Symptom.abdominalPain), group = PatientGroup.pregnant)
        assertEquals(CareLevel.urgent, pregnant.level)
        assertFalse(pregnant.showMedicationAdvice)
    }

    @Test fun utiRequiresDoctorAndRequiredFilter() {
        val a = assess(setOf(Symptom.painfulUrination))
        assertEquals("uti", a.matches.first().condition.id)
        assertEquals(CareLevel.seeDoctor, a.level)
        assertFalse(SymptomChecker.match(setOf(Symptom.backPain, Symptom.fever)).any { it.condition.id == "uti" })
        assertTrue(assess(setOf(Symptom.insomnia), duration = SymptomDuration.overOneWeek).level >= CareLevel.seeDoctor)
    }

    @Test fun libraryIsConsistent() {
        assertEquals(16, ConditionLibrary.all.size)
        assertEquals(ConditionLibrary.all.size, ConditionLibrary.all.map { it.id }.toSet().size)
        for (c in ConditionLibrary.all) {
            assertTrue(c.id, c.symptoms.containsAll(c.required))
            assertTrue(c.id, c.selfCare.isNotEmpty() && c.seeDoctorIf.isNotEmpty())
            for (id in c.eatFoodIDs + c.avoidFoodIDs) assertNotNull("${c.id}: $id", FoodDatabase.byId(id))
        }
        assertEquals(Symptom.entries.toSet(), ConditionLibrary.all.flatMap { it.symptoms }.toSet())
        val dengue = ConditionLibrary.all.first { it.id == "dengue" }
        assertTrue(dengue.otcMedicines.any { it.contains("ibuprofen") && it.contains("KHÔNG") })
    }
}

class ExerciseTests {
    @Test fun calorieFormula() {
        assertEquals(139.97, ExerciseLibrary.exercise("walk-brisk")!!.kcal(62.0, 30.0), 0.01)
        assertEquals(588.0, ExerciseLibrary.kcal(8.0, 70.0, 60.0), 0.01)
        assertEquals(0.0, ExerciseLibrary.kcal(8.0, 70.0, -10.0), 0.0)
    }

    @Test fun libraryIsConsistent() {
        assertEquals(30, ExerciseLibrary.all.size)
        assertEquals(30, ExerciseLibrary.all.map { it.id }.toSet().size)
        for (e in ExerciseLibrary.all) assertTrue(e.id, e.met in 1.5..15.0)
        for (c in ExerciseCategory.entries) assertTrue(c.name, ExerciseLibrary.all.any { it.category == c })
        assertEquals(8, HomeMove.all.size)
    }

    @Test fun search() {
        assertTrue(ExerciseLibrary.search("boi").any { it.id == "swim-easy" })
        assertTrue(ExerciseLibrary.search("Cầu lông").any { it.id == "badminton" })
        assertEquals(ExerciseLibrary.all.size, ExerciseLibrary.search("").size)
    }

    @Test fun plans() {
        for (goal in WeightGoal.entries) {
            for (cat in listOf(BMICategory.normal, BMICategory.obese2)) {
                val plan = WorkoutPlanner.plan(goal, 30, cat)
                assertEquals(7, plan.days.size)
                assertTrue(plan.days.any { it.isRest })
                for (d in plan.days) for (id in d.exerciseIDs) assertNotNull(id, ExerciseLibrary.exercise(id))
            }
            val low = WorkoutPlanner.plan(goal, 65, BMICategory.normal)
            assertTrue(low.lowImpact)
            assertFalse(low.days.flatMap { it.exerciseIDs }.any { ExerciseLibrary.exercise(it)!!.highImpact })
        }
        assertTrue(WorkoutPlanner.plan(WeightGoal.lose, 30, BMICategory.overweight).weeklyMinutes >= 150)
    }
}
