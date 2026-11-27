import { Ionicons } from "@expo/vector-icons";
import React from "react";
import { Pressable, View } from "react-native";
import { kcalText } from "../core/basics";
import { FoodItem, kcalPerPortion } from "../core/foods";
import { useTheme } from "../theme";
import { COLORS, Txt } from "./kit";

export function FoodRow({ food, note, onPress }: { food: FoodItem; note?: string; onPress: () => void }) {
  const { theme } = useTheme();
  return (
    <Pressable onPress={onPress} accessibilityRole="button" style={{ flexDirection: "row", alignItems: "center", gap: 12, paddingVertical: 8 }}>
      <Ionicons name="restaurant-outline" size={20} color={COLORS.orange} />
      <View style={{ flex: 1 }}>
        <Txt>{food.name}</Txt>
        <Txt muted size={12}>{note ?? `${food.portionName} · ${food.portionGrams} g`}</Txt>
      </View>
      <Txt bold color={COLORS.orange}>{kcalText(kcalPerPortion(food))}</Txt>
      <Ionicons name="chevron-forward" size={16} color={theme.colors.textMuted} />
    </Pressable>
  );
}

