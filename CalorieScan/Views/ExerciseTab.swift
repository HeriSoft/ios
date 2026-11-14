import SwiftData
import SwiftUI

enum ExerciseRoute: Hashable {
    case plan
    case homeWorkout
    case homeMove(HomeMove)
}

/// Thư viện bài tập, ghi lại buổi tập và lịch tập gợi ý.
struct ExerciseTab: View {
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \WorkoutEntry.date, order: .reverse) private var workouts: [WorkoutEntry]
    @AppStorage("body.weight") private var weightKg: Double = 62

    @State private var query = ""
    @State private var logging: Exercise?
    @State private var path: [ExerciseRoute] = DemoMode.current == .plan ? [.plan] : []

    private var todayWorkouts: [WorkoutEntry] {
        workouts.filter { Calendar.current.isDateInToday($0.date) }
    }

    var body: some View {
        NavigationStack(path: $path) {
            List {
                if query.isEmpty {
                    Section {
                        HStack(spacing: 0) {
                            stat("\(Int(todayWorkouts.reduce(0) { $0 + $1.kcal }.rounded()))", "kcal đã đốt", .orange)
                            stat("\(Int(todayWorkouts.reduce(0) { $0 + $1.minutes }))", "phút tập", .green)
                            stat("\(todayWorkouts.count)", "buổi", .blue)
                        }
                        .padding(.vertical, 6)
                    } header: {
                        Text("Hôm nay")
                    } footer: {
                        Text("Tính theo cân nặng \(weightKg.shortText) kg (sửa ở tab Cơ thể).")
                    }

                    Section {
                        NavigationLink(value: ExerciseRoute.plan) {
                            Label("Lịch tập gợi ý cho bạn", systemImage: "calendar")
                        }
                        NavigationLink(value: ExerciseRoute.homeWorkout) {
                            Label("Bài tập tại nhà (không dụng cụ)", systemImage: "house")
                        }
                    }

                    if !todayWorkouts.isEmpty {
                        Section("Đã tập hôm nay") {
                            ForEach(todayWorkouts) { WorkoutRow(entry: $0) }
                                .onDelete { offsets in
                                    for index in offsets { modelContext.delete(todayWorkouts[index]) }
                                    try? modelContext.save()
                                }
                        }
                    }

                    ForEach(ExerciseCategory.allCases) { category in
                        Section(category.title) {
                            ForEach(ExerciseLibrary.all.filter { $0.category == category }) { exerciseRow($0) }
                        }
                    }
                } else {
                    Section("Kết quả tìm kiếm") {
                        let results = ExerciseLibrary.search(query)
                        if results.isEmpty {
                            Text("Không tìm thấy \"\(query)\".").foregroundStyle(.secondary)
                        }
                        ForEach(results) { exerciseRow($0) }
                    }
                }
            }
            .searchable(text: $query, prompt: "Tìm môn: chạy, bơi, cầu lông…")
            .navigationTitle("Tập luyện")
            .navigationDestination(for: ExerciseRoute.self) { route in
                switch route {
                case .plan: WorkoutPlanView()
                case .homeWorkout: HomeWorkoutView()
                case .homeMove(let move): HomeMoveView(move: move)
                }
            }
            .sheet(item: $logging) { exercise in
                LogWorkoutSheet(exercise: exercise, weightKg: weightKg)
                    .presentationDetents([.medium])
            }
        }
    }

    private func exerciseRow(_ exercise: Exercise) -> some View {
        Button {
            logging = exercise
        } label: {
            HStack {
                Image(systemName: exercise.icon)
                    .frame(width: 28)
                    .foregroundStyle(.orange)
                Text(exercise.name).foregroundStyle(.primary)
                Spacer()
                Text("\(Int(exercise.kcal(weightKg: weightKg, minutes: 30).rounded())) kcal/30′")
                    .font(.caption.monospacedDigit())
                    .foregroundStyle(.secondary)
                Image(systemName: "plus.circle.fill").foregroundStyle(.orange)
            }
        }
    }

    private func stat(_ value: String, _ label: String, _ color: Color) -> some View {
        VStack(spacing: 2) {
            Text(value).font(.title2.bold().monospacedDigit()).foregroundStyle(color)
            Text(label).font(.caption).foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
    }
}

struct WorkoutRow: View {
    let entry: WorkoutEntry

    var body: some View {
        HStack {
            Image(systemName: ExerciseLibrary.exercise(entry.exerciseID)?.icon ?? "flame")
                .frame(width: 28)
                .foregroundStyle(.green)
            VStack(alignment: .leading, spacing: 2) {
                Text(entry.name)
                Text("\(Int(entry.minutes)) phút · \(entry.date.formatted(date: .omitted, time: .shortened))")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            Text("−\(entry.kcal.kcalText)")
                .font(.body.monospacedDigit().weight(.semibold))
                .foregroundStyle(.green)
        }
    }
}

private struct LogWorkoutSheet: View {
    let exercise: Exercise
    let weightKg: Double

    @Environment(\.modelContext) private var modelContext
    @Environment(\.dismiss) private var dismiss
    @State private var minutes: Double = 30

    private var kcal: Double { exercise.kcal(weightKg: weightKg, minutes: minutes) }

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Stepper(value: $minutes, in: 5...300, step: 5) {
                        LabeledContent("Thời gian", value: "\(Int(minutes)) phút")
                    }
                    HStack {
                        Text("Calo đốt (ước tính)").font(.headline)
                        Spacer()
                        Text(kcal.kcalText).font(.title2.bold()).foregroundStyle(.orange)
                    }
                } footer: {
                    Text("MET \(exercise.met.shortText) × 3,5 × \(weightKg.shortText) kg ÷ 200 × số phút. Con số thực tế thay đổi theo cường độ và thể trạng.")
                }
                if exercise.highImpact {
                    Section {
                        Label("Môn có chạy nhảy, tác động mạnh lên khớp. Khởi động kỹ; nếu thừa cân nhiều hoặc đau gối, hãy chọn môn nhẹ hơn.",
                              systemImage: "exclamationmark.triangle")
                            .font(.footnote)
                            .foregroundStyle(.orange)
                    }
                }
            }
            .navigationTitle(exercise.name)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Huỷ") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Ghi lại") {
                        modelContext.insert(WorkoutEntry(name: exercise.name, exerciseID: exercise.id, minutes: minutes, kcal: kcal))
                        try? modelContext.save()
                        dismiss()
                    }
                }
            }
        }
    }
}

struct WorkoutPlanView: View {
    @AppStorage("body.age") private var age: Int = 28
    @AppStorage("body.height") private var heightCm: Double = 158
    @AppStorage("body.weight") private var weightKg: Double = 62
    @AppStorage("body.goal") private var goal: WeightGoal = .lose

    private var category: BMICategory? {
        guard heightCm > 0 else { return nil }
        return BMICategory(bmi: HealthCalculator.bmi(weightKg: weightKg, heightCm: heightCm))
    }

    var body: some View {
        let plan = WorkoutPlanner.plan(goal: goal, age: age, category: category)
        List {
            Section {
                LabeledContent("Mục tiêu", value: goal.title)
                LabeledContent("Tổng thời gian", value: "\(plan.weeklyMinutes) phút/tuần")
                if plan.lowImpact {
                    Label("Ưu tiên môn nhẹ nhàng cho khớp", systemImage: "figure.walk")
                        .foregroundStyle(.blue)
                }
            } footer: {
                Text("Dựa trên tuổi, cân nặng và mục tiêu ở tab Cơ thể.")
            }

            Section("Lịch trong tuần") {
                ForEach(plan.days) { day in
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text(day.day).font(.headline).frame(width: 80, alignment: .leading)
                            Text(day.title)
                            Spacer()
                            if !day.isRest {
                                Text("\(day.minutes) phút").font(.subheadline.monospacedDigit()).foregroundStyle(.orange)
                            }
                        }
                        if !day.isRest {
                            Text("Chọn một: " + day.exerciseIDs.compactMap { ExerciseLibrary.exercise($0)?.name }.joined(separator: ", "))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                    .padding(.vertical, 2)
                    .opacity(day.isRest ? 0.6 : 1)
                }
            }

            Section("Lưu ý") {
                ForEach(plan.notes, id: \.self) { note in
                    Label(note, systemImage: "lightbulb").font(.subheadline)
                }
            }
        }
        .navigationTitle("Lịch tập gợi ý")
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct HomeWorkoutView: View {
    var body: some View {
        List {
            Section {
                ForEach(HomeMove.all) { move in
                    NavigationLink(value: ExerciseRoute.homeMove(move)) {
                        HStack {
                            Image(systemName: move.icon).frame(width: 28).foregroundStyle(.orange)
                            VStack(alignment: .leading, spacing: 2) {
                                Text(move.name)
                                Text("\(move.target) · \(move.reps)").font(.caption).foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            } footer: {
                Text("Gợi ý một buổi 20–30 phút: khởi động 5 phút, chọn 4–5 động tác làm vòng tròn, nghỉ 30–60 giây giữa các hiệp, giãn cơ 5 phút. Ghi lại bằng mục \"Bài tập tại nhà\" trong danh sách môn tập.")
            }
        }
        .navigationTitle("Bài tập tại nhà")
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct HomeMoveView: View {
    let move: HomeMove

    var body: some View {
        List {
            Section {
                LabeledContent("Nhóm cơ", value: move.target)
                LabeledContent("Gợi ý", value: move.reps)
            }
            Section("Cách tập") {
                ForEach(Array(move.steps.enumerated()), id: \.offset) { index, step in
                    Label(step, systemImage: "\(index + 1).circle.fill")
                }
            }
            Section("Bản dễ hơn") {
                Label(move.easier, systemImage: "tortoise")
            }
            Section("Lưu ý an toàn") {
                Label(move.caution, systemImage: "exclamationmark.triangle")
                    .foregroundStyle(.orange)
            }
        }
        .navigationTitle(move.name)
        .navigationBarTitleDisplayMode(.inline)
    }
}
