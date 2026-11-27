import { Ionicons } from "@expo/vector-icons";
import * as ImagePicker from "expo-image-picker";
import { router } from "expo-router";
import React, { useMemo, useState } from "react";
import { Image, Platform, Pressable, ScrollView, View } from "react-native";
import { COLORS, IconText, Section, Txt } from "../../src/components/kit";
import { Button, Input } from "../../src/components/ui";
import { kcalText } from "../../src/core/basics";
import { FoodGuess, FoodItem, foodProduct, kcalPerPortion, matchFoods, searchFoods } from "../../src/core/foods";
import { labelImage, mlAvailable } from "../../src/ml";
import { useStore } from "../../src/state/store";
import { useTheme } from "../../src/theme";
import { FoodRow } from "../../src/components/FoodRow";

export default function FoodScreen() {
  const store = useStore();
  const { theme } = useTheme();
  const [query, setQuery] = useState("");
  const [photo, setPhoto] = useState<string>();
  const [guesses, setGuesses] = useState<FoodGuess[]>();
  const [status, setStatus] = useState<string>();
  const results = useMemo(() => searchFoods(query), [query]);
  const canLabel = mlAvailable("labels");

  const open = (f: FoodItem) => { store.selectProduct(foodProduct(f), true); router.push("/product"); };

  async function analyze(fromCamera: boolean) {
    const opts: ImagePicker.ImagePickerOptions = { mediaTypes: ["images"], quality: 0.7 };
    const res = fromCamera ? await ImagePicker.launchCameraAsync(opts) : await ImagePicker.launchImageLibraryAsync(opts);
    if (res.canceled || !res.assets[0]) return;
    const uri = res.assets[0].uri;
    setPhoto(uri); setGuesses(undefined); setStatus("Đang nhận diện món ăn…");
    try {
      const g = matchFoods(await labelImage(uri));
      setGuesses(g);
      setStatus(g.length ? undefined : "Chưa nhận ra món này. Hãy tìm theo tên bên dưới.");
    } catch (e) {
      setStatus("Không nhận diện được ảnh: " + (e as Error).message);
    }
  }

  return (
    <ScrollView contentContainerStyle={{ padding: 16, gap: 16, maxWidth: 760, width: "100%", alignSelf: "center" }} keyboardShouldPersistTaps="handled">
      <Section title="Chụp món ăn">
        {canLabel ? (
          <>
            {photo ? <Image source={{ uri: photo }} style={{ height: 180, borderRadius: 12, backgroundColor: theme.colors.surfaceAlt }} resizeMode="cover" /> : null}
            <View style={{ flexDirection: "row", gap: 10 }}>
              {Platform.OS !== "web" ? <View style={{ flex: 1 }}><Button label="Chụp ảnh" onPress={() => analyze(true)} /></View> : null}
              <View style={{ flex: 1 }}><Button label="Chọn ảnh" variant="secondary" onPress={() => analyze(false)} /></View>
            </View>
            {status ? <Txt muted>{status}</Txt> : null}
            {guesses?.map((g) => <FoodRow key={g.food.id} food={g.food} note={`Độ tin cậy ${Math.round(g.confidence * 100)}% · ${g.food.portionName}`} onPress={() => open(g.food)} />)}
          </>
        ) : (
          <IconText icon="information-circle-outline" color={COLORS.blue}
            text="Nhận diện món ăn từ ảnh cần bản cài đặt (APK/IPA build native). Trên web và Expo Go, hãy tìm món theo tên bên dưới." />
        )}
      </Section>
      <Section title="Tìm món ăn" footer="Giá trị ước tính trung bình cho 1 phần ăn thông thường.">
        <Input placeholder="Ví dụ: phở, cơm tấm, bánh mì…" value={query} onChangeText={setQuery} />
        {results.map((f) => <FoodRow key={f.id} food={f} onPress={() => open(f)} />)}
        {results.length === 0 ? <Txt muted>Không tìm thấy món phù hợp. Bạn có thể nhập thủ công.</Txt> : null}
        <Button label="Nhập thủ công" variant="secondary" onPress={() => router.push("/manual")} />
      </Section>
    </ScrollView>
  );
}
