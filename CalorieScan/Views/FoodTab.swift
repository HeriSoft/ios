import PhotosUI
import SwiftUI

/// Chụp ảnh món ăn bất kỳ, đoán món và tính calo theo bảng ước tính.
struct FoodTab: View {
    @State private var path: [FoodItem] = DemoMode.initialFoodPath

    var body: some View {
        NavigationStack(path: $path) {
            FoodHomeView()
                .navigationTitle("Món ăn")
                .navigationDestination(for: FoodItem.self) { food in
                    ProductDetailView(product: food.productInfo, preferServings: true, onSaved: { path.removeAll() })
                }
        }
    }
}

private struct FoodHomeView: View {
    @State private var query = ""
    @State private var pickerItem: PhotosPickerItem?
    @State private var showCamera = false
    @State private var image: UIImage?
    @State private var isProcessing = false
    @State private var guesses: [FoodGuess] = []
    @State private var hasClassified = false
    @State private var errorMessage: String?

    private var results: [FoodItem] { FoodDatabase.search(query) }

    var body: some View {
        List {
            if query.isEmpty {
                Section {
                    if let image {
                        Image(uiImage: image)
                            .resizable()
                            .scaledToFill()
                            .frame(maxWidth: .infinity)
                            .frame(height: 200)
                            .clipped()
                            .listRowInsets(EdgeInsets())
                    }
                    if UIImagePickerController.isSourceTypeAvailable(.camera) {
                        Button { showCamera = true } label: {
                            Label("Chụp ảnh món ăn", systemImage: "camera")
                        }
                    }
                    PhotosPicker(selection: $pickerItem, matching: .images) {
                        Label("Chọn ảnh từ thư viện", systemImage: "photo.on.rectangle")
                    }
                    if isProcessing {
                        ProgressView("Đang nhận diện món ăn…")
                    }
                    if let errorMessage {
                        Text(errorMessage).foregroundStyle(.red)
                    }
                } footer: {
                    Text("App đoán món từ ảnh (chạy trên máy, không cần mạng). Nếu đoán sai, hãy tìm món theo tên ở ô tìm kiếm.")
                }

                if hasClassified && !isProcessing {
                    Section("Có thể là") {
                        if guesses.isEmpty {
                            Text("Không nhận ra món ăn trong ảnh. Hãy tìm theo tên ở ô tìm kiếm phía trên.")
                                .foregroundStyle(.secondary)
                        }
                        ForEach(guesses) { guess in
                            NavigationLink(value: guess.food) {
                                FoodRow(food: guess.food, confidence: guess.confidence)
                            }
                        }
                    }
                }
            }

            Section(query.isEmpty ? "Tất cả món (\(results.count))" : "Kết quả tìm kiếm") {
                if results.isEmpty {
                    Text("Không tìm thấy món \"\(query)\".").foregroundStyle(.secondary)
                }
                ForEach(results) { food in
                    NavigationLink(value: food) {
                        FoodRow(food: food, confidence: nil)
                    }
                }
            }
        }
        .searchable(text: $query, prompt: "Tìm món: phở, cơm tấm, chuối…")
        .onChange(of: pickerItem) { _, item in
            guard let item else { return }
            Task {
                if let data = try? await item.loadTransferable(type: Data.self), let picked = UIImage(data: data) {
                    await classify(picked)
                } else {
                    errorMessage = "Không mở được ảnh."
                }
            }
        }
        .fullScreenCover(isPresented: $showCamera) {
            CameraPicker { captured in
                Task { await classify(captured) }
            }
            .ignoresSafeArea()
        }
        .onAppear {
            if DemoMode.current == .food && !hasClassified {
                guesses = DemoData.foodGuesses
                hasClassified = true
            }
        }
    }

    @MainActor
    private func classify(_ newImage: UIImage) async {
        image = newImage
        errorMessage = nil
        isProcessing = true
        defer { isProcessing = false }
        do {
            guesses = try await FoodClassifier.classify(newImage)
        } catch {
            guesses = []
            errorMessage = "Không nhận diện được ảnh: \(error.localizedDescription)"
        }
        hasClassified = true
    }
}

private struct FoodRow: View {
    let food: FoodItem
    let confidence: Float?

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(food.name)
                Text("\(food.portionName) ≈ \(Int(food.portionGrams)) g")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 2) {
                Text(food.kcalPerPortion.kcalText)
                    .font(.body.monospacedDigit().weight(.semibold))
                if let confidence {
                    Text("\(Int((confidence * 100).rounded()))% khớp")
                        .font(.caption)
                        .foregroundStyle(.orange)
                }
            }
        }
    }
}
