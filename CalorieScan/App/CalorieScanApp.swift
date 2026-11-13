import SwiftData
import SwiftUI

@main
struct CalorieScanApp: App {
    let container: ModelContainer = {
        // Chế độ demo (dùng để chụp màn hình trên CI) lưu dữ liệu trong bộ nhớ.
        let config = ModelConfiguration(isStoredInMemoryOnly: DemoMode.current != nil)
        do {
            return try ModelContainer(for: FoodEntry.self, configurations: config)
        } catch {
            fatalError("Không tạo được kho dữ liệu: \(error)")
        }
    }()

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .modelContainer(container)
    }
}
