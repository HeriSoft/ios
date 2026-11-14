import SwiftData
import SwiftUI

enum AppTab: Hashable {
    case scan
    case food
    case body
    case log
}

struct ContentView: View {
    @Environment(\.modelContext) private var modelContext
    @State private var selectedTab: AppTab = DemoMode.initialTab

    var body: some View {
        TabView(selection: $selectedTab) {
            ScanTab()
                .tabItem { Label("Quét", systemImage: "barcode.viewfinder") }
                .tag(AppTab.scan)

            FoodTab()
                .tabItem { Label("Món ăn", systemImage: "fork.knife") }
                .tag(AppTab.food)

            BodyTab()
                .tabItem { Label("Cơ thể", systemImage: "figure.stand") }
                .tag(AppTab.body)

            LogView()
                .tabItem { Label("Nhật ký", systemImage: "list.bullet.rectangle") }
                .tag(AppTab.log)
        }
        .tint(.orange)
        .task { DemoData.seedIfNeeded(modelContext) }
    }
}
