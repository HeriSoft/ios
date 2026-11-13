import SwiftData
import SwiftUI

enum AppTab: Hashable {
    case scan
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

            LogView()
                .tabItem { Label("Nhật ký", systemImage: "list.bullet.rectangle") }
                .tag(AppTab.log)
        }
        .tint(.orange)
        .task { DemoData.seedIfNeeded(modelContext) }
    }
}
