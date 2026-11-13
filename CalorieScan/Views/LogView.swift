import SwiftData
import SwiftUI

struct LogView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \FoodEntry.date, order: .reverse) private var entries: [FoodEntry]
    @AppStorage("dailyGoal") private var dailyGoal: Double = 2000

    private struct DayGroup: Identifiable {
        let day: Date
        let items: [FoodEntry]
        var id: Date { day }
        var total: Double { items.reduce(0) { $0 + $1.kcal } }
    }

    private var groups: [DayGroup] {
        let calendar = Calendar.current
        return Dictionary(grouping: entries) { calendar.startOfDay(for: $0.date) }
            .map { DayGroup(day: $0.key, items: $0.value) }
            .sorted { $0.day > $1.day }
    }

    private var todayTotal: Double {
        entries.filter { Calendar.current.isDateInToday($0.date) }.reduce(0) { $0 + $1.kcal }
    }

    var body: some View {
        NavigationStack {
            List {
                Section {
                    TodaySummaryView(total: todayTotal, goal: dailyGoal)
                    Stepper(value: $dailyGoal, in: 1000...5000, step: 100) {
                        Text("Mục tiêu: \(Int(dailyGoal)) kcal/ngày")
                    }
                }

                if entries.isEmpty {
                    ContentUnavailableView(
                        "Chưa có món nào",
                        systemImage: "fork.knife",
                        description: Text("Quét sản phẩm và bấm \"Thêm vào nhật ký\" để bắt đầu.")
                    )
                }

                ForEach(groups) { group in
                    Section {
                        ForEach(group.items) { entry in
                            EntryRow(entry: entry)
                        }
                        .onDelete { offsets in
                            for index in offsets { modelContext.delete(group.items[index]) }
                            try? modelContext.save()
                        }
                    } header: {
                        HStack {
                            Text(title(for: group.day))
                            Spacer()
                            Text(group.total.kcalText)
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
            VStack(alignment: .leading, spacing: 2) {
                Text(entry.name).font(.body)
                Text("\(entry.amount.shortText) \(entry.unit) · \(entry.date.formatted(date: .omitted, time: .shortened))")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            Text(entry.kcal.kcalText)
                .font(.body.monospacedDigit().weight(.semibold))
        }
    }
}

private struct TodaySummaryView: View {
    let total: Double
    let goal: Double

    private var progress: Double { goal > 0 ? min(total / goal, 1) : 0 }
    private var remaining: Double { goal - total }

    var body: some View {
        HStack(spacing: 20) {
            ZStack {
                Circle().stroke(Color.orange.opacity(0.2), lineWidth: 12)
                Circle()
                    .trim(from: 0, to: progress)
                    .stroke(remaining >= 0 ? Color.orange : Color.red,
                            style: StrokeStyle(lineWidth: 12, lineCap: .round))
                    .rotationEffect(.degrees(-90))
                Text("\(Int((total / max(goal, 1) * 100).rounded()))%")
                    .font(.headline.monospacedDigit())
            }
            .frame(width: 90, height: 90)

            VStack(alignment: .leading, spacing: 4) {
                Text("Hôm nay").font(.subheadline).foregroundStyle(.secondary)
                Text(total.kcalText).font(.title.bold())
                Text(remaining >= 0 ? "Còn \(remaining.kcalText)" : "Vượt \((-remaining).kcalText)")
                    .font(.subheadline)
                    .foregroundStyle(remaining >= 0 ? Color.secondary : Color.red)
            }
        }
        .padding(.vertical, 8)
    }
}
