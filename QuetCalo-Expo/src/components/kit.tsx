/** Thành phần giao diện riêng của Quét Calo (dựa trên theme của mẫu App Builder). */
import { Ionicons } from "@expo/vector-icons";
import React, { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { shortText } from "../core/basics";
import { useTheme } from "../theme";

export const COLORS = { orange: "#EA580C", green: "#16A34A", red: "#DC2626", blue: "#2563EB", yellow: "#CA8A04", cyan: "#0891B2" };

export function Section({ title, footer, children }: { title?: string; footer?: string; children: React.ReactNode }) {
  const { theme } = useTheme();
  return (
    <View style={{ gap: 6 }}>
      {title ? <Text style={[s.sectionTitle, { color: theme.colors.textMuted }]}>{title.toUpperCase()}</Text> : null}
      <View style={[s.card, { backgroundColor: theme.colors.surface, borderColor: theme.colors.border, borderRadius: theme.radius }]}>
        {children}
      </View>
      {footer ? <Text style={[s.footer, { color: theme.colors.textMuted }]}>{footer}</Text> : null}
    </View>
  );
}

export function Row({ label, value, color, bold }: { label: string; value: string; color?: string; bold?: boolean }) {
  const { theme } = useTheme();
  return (
    <View style={s.row}>
      <Text style={{ flex: 1, color: theme.colors.text, fontSize: 15 }}>{label}</Text>
      <Text style={{ color: color ?? theme.colors.text, fontSize: 15, fontWeight: bold ? "700" : "400" }}>{value}</Text>
    </View>
  );
}

export function Txt({ children, muted, size = 15, color, bold }: { children: React.ReactNode; muted?: boolean; size?: number; color?: string; bold?: boolean }) {
  const { theme } = useTheme();
  return <Text style={{ color: color ?? (muted ? theme.colors.textMuted : theme.colors.text), fontSize: size, fontWeight: bold ? "700" : "400", lineHeight: size * 1.4 }}>{children}</Text>;
}

export function IconText({ icon, text, color }: { icon: keyof typeof Ionicons.glyphMap; text: string; color?: string }) {
  const { theme } = useTheme();
  return (
    <View style={{ flexDirection: "row", gap: 10, alignItems: "flex-start" }}>
      <Ionicons name={icon} size={18} color={color ?? theme.colors.primary} style={{ marginTop: 2 }} />
      <Text style={{ flex: 1, color: color ?? theme.colors.text, fontSize: 14, lineHeight: 20 }}>{text}</Text>
    </View>
  );
}

export function NavRow({ icon, title, subtitle, onPress, color }: { icon: keyof typeof Ionicons.glyphMap; title: string; subtitle?: string; onPress: () => void; color?: string }) {
  const { theme } = useTheme();
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={({ pressed }) => [s.row, { opacity: pressed ? 0.7 : 1, paddingVertical: 4 }]}>
      <Ionicons name={icon} size={22} color={color ?? theme.colors.primary} />
      <View style={{ flex: 1, marginLeft: 12 }}>
        <Text style={{ color: theme.colors.text, fontSize: 15 }}>{title}</Text>
        {subtitle ? <Text style={{ color: theme.colors.textMuted, fontSize: 12, marginTop: 2 }}>{subtitle}</Text> : null}
      </View>
      <Ionicons name="chevron-forward" size={18} color={theme.colors.textMuted} />
    </Pressable>
  );
}

export function Pill({ text, color }: { text: string; color: string }) {
  return (
    <View style={{ backgroundColor: color + "26", borderRadius: 999, paddingHorizontal: 10, paddingVertical: 4 }}>
      <Text style={{ color, fontWeight: "700", fontSize: 13 }}>{text}</Text>
    </View>
  );
}

export function Segmented<T extends string>({ options, value, onChange }: { options: [T, string][]; value: T; onChange: (v: T) => void }) {
  const { theme } = useTheme();
  return (
    <View style={[s.segment, { borderColor: theme.colors.border, borderRadius: theme.radius - 4 }]}>
      {options.map(([v, label]) => {
        const on = v === value;
        return (
          <Pressable key={v} accessibilityRole="button" accessibilityState={{ selected: on }} onPress={() => onChange(v)}
            style={[s.segItem, { backgroundColor: on ? theme.colors.primary : "transparent" }]}>
            <Text numberOfLines={1} style={{ color: on ? theme.colors.primaryText : theme.colors.text, fontWeight: on ? "700" : "500", fontSize: 14 }}>{label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

export function Chip({ label, selected, onPress }: { label: string; selected?: boolean; onPress: () => void }) {
  const { theme } = useTheme();
  return (
    <Pressable accessibilityRole="button" accessibilityState={{ selected }} onPress={onPress}
      style={[s.chip, { maxWidth: "100%", borderColor: selected ? theme.colors.primary : theme.colors.border, backgroundColor: selected ? theme.colors.primary + "22" : theme.colors.surface }]}>
      <Text style={{ color: theme.colors.text, fontSize: 14, flexShrink: 1 }}>{label}</Text>
    </Pressable>
  );
}

/** Ô nhập số (cho phép dấu phẩy). Chỉ đồng bộ lại khi giá trị bên ngoài đổi. */
export function NumberField({ label, value, onChange, suffix }: { label: string; value?: number; onChange: (v?: number) => void; suffix?: string }) {
  const { theme } = useTheme();
  const [text, setText] = useState(value != null ? shortText(value) : "");
  useEffect(() => {
    const parsed = Number(text.replace(",", "."));
    if (text === "" ? value != null : parsed !== value) setText(value != null ? shortText(value) : "");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);
  return (
    <View style={{ gap: 6, flex: 1, minWidth: 0 }}>
      <Text style={{ color: theme.colors.textMuted, fontSize: 13, fontWeight: "600" }}>{label}</Text>
      <View style={[s.numberBox, { borderColor: theme.colors.border, borderRadius: theme.radius - 4, backgroundColor: theme.colors.surface }]}>
        <TextInput
          accessibilityLabel={label}
          keyboardType="decimal-pad"
          value={text}
          onChangeText={(t) => {
            const cleaned = t.replace(/[^0-9.,]/g, "");
            setText(cleaned);
            const n = Number(cleaned.replace(",", "."));
            onChange(cleaned === "" || !Number.isFinite(n) ? undefined : n);
          }}
          style={{ flex: 1, minWidth: 0, width: "100%", color: theme.colors.text, fontSize: 16, paddingVertical: 10 }}
        />
        {suffix ? <Text style={{ color: theme.colors.textMuted }}>{suffix}</Text> : null}
      </View>
    </View>
  );
}

export function SmallButton({ label, onPress }: { label: string; onPress: () => void }) {
  const { theme } = useTheme();
  return (
    <Pressable accessibilityRole="button" onPress={onPress}
      style={({ pressed }) => [s.small, { borderColor: theme.colors.border, borderRadius: theme.radius - 4, opacity: pressed ? 0.7 : 1 }]}>
      <Text style={{ color: theme.colors.primary, fontWeight: "700", fontSize: 18 }}>{label}</Text>
    </Pressable>
  );
}

export function Disclaimer() {
  return (
    <IconText icon="medkit" color={COLORS.red}
      text="Thông tin chỉ để tham khảo, không phải chẩn đoán y khoa và không thay thế bác sĩ. Khi nghi ngờ, hãy đi khám. Trường hợp khẩn cấp gọi 115." />
  );
}

export function Divider() {
  const { theme } = useTheme();
  return <View style={{ height: StyleSheet.hairlineWidth, backgroundColor: theme.colors.border }} />;
}

const s = StyleSheet.create({
  sectionTitle: { fontSize: 12, fontWeight: "700", letterSpacing: 0.5, marginLeft: 4 },
  card: { borderWidth: StyleSheet.hairlineWidth, padding: 14, gap: 10 },
  footer: { fontSize: 12, marginHorizontal: 4, lineHeight: 17 },
  row: { flexDirection: "row", alignItems: "center", gap: 8 },
  segment: { flexDirection: "row", borderWidth: 1, overflow: "hidden" },
  segItem: { flex: 1, paddingVertical: 9, alignItems: "center", paddingHorizontal: 4 },
  chip: { borderWidth: 1, borderRadius: 999, paddingHorizontal: 12, paddingVertical: 7 },
  numberBox: { flexDirection: "row", alignItems: "center", borderWidth: 1, paddingHorizontal: 12, gap: 6 },
  small: { borderWidth: 1, width: 44, height: 44, alignItems: "center", justifyContent: "center" },
});
