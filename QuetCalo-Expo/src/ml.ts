/**
 * Nhận diện trên máy bằng Google ML Kit (đọc chữ trên nhãn, gắn nhãn ảnh món ăn).
 * Cần bản build native (expo prebuild / EAS / development build). Trên web và Expo Go
 * module không có sẵn → mlAvailable() = false và màn hình chuyển sang nhập tay.
 */
import { NativeModules, Platform } from "react-native";

export type MLKind = "text" | "labels";

export function mlAvailable(kind: MLKind): boolean {
  if (Platform.OS === "web") return false;
  return Boolean(kind === "text" ? NativeModules.TextRecognition : NativeModules.ImageLabeling);
}

export async function recognizeTextLines(uri: string): Promise<string[]> {
  if (!mlAvailable("text")) throw new Error("ML Kit chưa có trong bản app này");
  const { default: TextRecognition } = await import("@react-native-ml-kit/text-recognition");
  const result = await TextRecognition.recognize(uri);
  return result.blocks.flatMap((b) => b.lines.map((l) => l.text));
}

export async function labelImage(uri: string): Promise<{ text: string; confidence: number }[]> {
  if (!mlAvailable("labels")) throw new Error("ML Kit chưa có trong bản app này");
  const { default: ImageLabeling } = await import("@react-native-ml-kit/image-labeling");
  const labels = await ImageLabeling.label(uri);
  return labels.map((l) => ({ text: l.text, confidence: l.confidence }));
}
