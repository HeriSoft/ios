import SwiftData
import SwiftUI

struct LogView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \FoodEntry.date, order: .reverse) private var entries: [FoodEntry]
    @Query(sort: \WorkoutEntry.date, order: .reverse) private var workouts: [WorkoutEntry]
    @AppStorage("dailyGoal") private var dailyGoal: Double = 2000

    private struct DayGroup: Identifiable {
        let day: Date
        let foods: [FoodEntry]
        let workouts: [WorkoutEntry]
        var id: Date { day }
        var eaten: Double { foods.reduce(0) { $0 + $1.kcal } }
        var burned: Double { workouts.reduce(0) { $0 + $1.kcal } }
    }

    private var groups: [DayGroup] {
        let calendar = Calendar.current
        let foodsByDay = Dictionary(grouping: entries) { calendar.startOfDay(for: $0.date) }
        let workoutsByDay = Dictionary(grouping: workouts) { calendar.startOfDay(for: $0.date) }
        let days = Set(foodsByDay.keys).union(workoutsByDay.keys)
        return days
            .map { DayGroup(day: $0, foods: foodsByDay[$0] ?? [], workouts: workoutsByDay[$0] ?? []) }
            .sorted { $0.day > $1.day }
    }

    private var today: DayGroup? {
        groups.first { Calendar.current.isDateInToday($0.day) }
    }

    var body: some View {
        NavigationStack {
            List {
                Section {
                    TodaySummaryView(eaten: today?.eaten ?? 0, burned: today?.burned ?? 0, goal: dailyGoal)
                    Stepper(value: $dailyGoal, in: 1000...5000, step: 50) {
                        Text("Mục tiêu: \(Int(dailyGoal)) kcal/ngày")
                    }
                } footer: {
                    Text("Còn lại = mục tiêu − ăn vào + đốt khi tập. Nếu đã chọn mức vận động cao ở tab Cơ thể, một phần calo tập đã nằm trong mục tiêu.")
                }

                if entries.isEmpty && workouts.isEmpty {
                    ContentUnavailableView(
                        "Chưa có gì trong nhật ký",
                        systemImage: "fork.knife",
                        description: Text("Quét sản phẩm, chọn món ăn hoặc ghi buổi tập để bắt đầu.")
                    )
                }

                ForEach(groups) { group in
                    Section {
                        ForEach(group.foods) { EntryRow(entry: $0) }
                            .onDelete { offsets in
                                for index in offsets { modelContext.delete(group.foods[index]) }
                                try? modelContext.save()
                            }
                        ForEach(group.workouts) { WorkoutRow(entry: $0) }
                            .onDelete { offsets in
                                for index in offsets { modelContext.delete(group.workouts[index]) }
                                try? modelContext.save()
                            }
                    } header: {
                        HStack {
                            Text(title(for: group.day))
                            Spacer()
                            Text("+\(Int(group.eaten.rounded())) / −\(Int(group.burned.rounded())) kcal")
                                .monospacedDigit()
                        }
                    }
                }
            }
            .navigationTitle("Nhật ký calo")
        }
    }

    private func title(for day: Date) -> String {
        let calendar = Calendar.current
        if calendar.isDateInToday(day) { return "Hôm nay" }
        if calendar.isDateInYesterday(day) { return "Hôm qua" }
        return day.formatted(.dateTime.day().month().year())
    }
}

private struct EntryRow: View {
    let entry: FoodEntry

    var body: some View {
        HStack {
            Image(systemName: "fork.knife")
                .frame(width: 28)
                .foregroundStyle(.orange)
            VStack(alignment: .leading, spacing: 2) {
                Text(entry.name).font(.body)
                Text("\(entry.amount.shortText) \(entry.unit) · \(entry.date.formatted(date: .omitted, time: .shortened))")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            Text("+\(entry.kcal.kcalText)")
                .font(.body.monospacedDigit().weight(.semibold))
        }
    }
}

private struct TodaySummaryView: View {
    let eaten: Double
    let burned: Double
    let goal: Double

    private var budget: Double { goal + burned }
    private var remaining: Double { budget - eaten }
    private var progress: Double { budget > 0 ? min(eaten / budget, 1) : 0 }

    var body: some View {
        HStack(spacing: 20) {
            ZStack {
                Circle().stroke(Color.orange.opacity(0.2), lineWidth: 12)
                Circle()
                    .trim(from: 0, to: progress)
                    .stroke(remaining >= 0 ? Color.orange : Color.red,
                            style: StrokeStyle(lineWidth: 12, lineCap: .round))
                    .rotationEffect(.degrees(-90))
                VStack(spacing: 0) {
                    Text("\(Int(abs(remaining).rounded()))")
                        .font(.headline.monospacedDigit())
                    Text(remaining >= 0 ? "còn lại" : "vượt")
                        .font(.caption2)
                        .foregroundStyle(remaining >= 0 ? Color.secondary : Color.red)
                }
            }
            .frame(width: 96, height: 96)

            VStack(alignment: .leading, spacing: 6) {
                Text("Hôm nay").font(.subheadline).foregroundStyle(.secondary)
                Label("Ăn vào: \(eaten.kcalText)", systemImage: "fork.knife")
                    .foregroundStyle(.orange)
                Label("Đốt khi tập: \(burned.kcalText)", systemImage: "flame.fill")
                    .foregroundStyle(.green)
                Label("Mục tiêu: \(goal.kcalText)", systemImage: "target")
                    .foregroundStyle(.secondary)
            }
            .font(.subheadline.monospacedDigit())
        }
        .padding(.vertical, 8)
    }
}
