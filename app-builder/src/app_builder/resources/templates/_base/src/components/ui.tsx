import React from "react";
import {
  ActivityIndicator,
  Alert,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TextInputProps,
  View,
  ViewStyle,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useTheme } from "../theme";
import { t } from "../i18n";

/** Khung màn hình: căn giữa, giới hạn bề rộng để responsive trên web/tablet. */
export function Screen({
  children,
  scroll = false,
  style,
}: {
  children: React.ReactNode;
  scroll?: boolean;
  style?: ViewStyle;
}) {
  const { theme } = useTheme();
  const inner = <View style={[styles.inner, { padding: theme.spacing }, style]}>{children}</View>;
  return (
    <SafeAreaView edges={["bottom", "left", "right"]} style={[styles.fill, { backgroundColor: theme.colors.background }]}>
      {scroll ? <ScrollView contentContainerStyle={styles.scroll}>{inner}</ScrollView> : inner}
    </SafeAreaView>
  );
}

export function Card({ children, style }: { children: React.ReactNode; style?: ViewStyle }) {
  const { theme } = useTheme();
  return (
    <View
      style={[
        {
          backgroundColor: theme.colors.surface,
          borderColor: theme.colors.border,
          borderWidth: StyleSheet.hairlineWidth,
          borderRadius: theme.radius,
          padding: theme.spacing,
        },
        style,
      ]}
    >
      {children}
    </View>
  );
}

export function Title({ children }: { children: React.ReactNode }) {
  const { theme } = useTheme();
  return <Text style={[styles.title, { color: theme.colors.text }]}>{children}</Text>;
}

export function Body({ children, muted = false }: { children: React.ReactNode; muted?: boolean }) {
  const { theme } = useTheme();
  return <Text style={{ color: muted ? theme.colors.textMuted : theme.colors.text, fontSize: 15, lineHeight: 22 }}>{children}</Text>;
}

export function Button({
  label,
  onPress,
  variant = "primary",
  disabled = false,
  accessibilityLabel,
}: {
  label: string;
  onPress: () => void;
  variant?: "primary" | "secondary" | "danger";
  disabled?: boolean;
  accessibilityLabel?: string;
}) {
  const { theme } = useTheme();
  const bg =
    variant === "primary" ? theme.colors.primary : variant === "danger" ? theme.colors.danger : theme.colors.surfaceAlt;
  const fg = variant === "secondary" ? theme.colors.text : theme.colors.primaryText;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? label}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        { backgroundColor: bg, borderRadius: theme.radius, opacity: disabled ? 0.5 : pressed ? 0.85 : 1 },
      ]}
    >
      <Text style={{ color: fg, fontWeight: "600", fontSize: 15 }}>{label}</Text>
    </Pressable>
  );
}

export function Input(props: TextInputProps & { label?: string }) {
  const { theme } = useTheme();
  const { label, style, ...rest } = props;
  return (
    <View style={{ gap: 6 }}>
      {label ? <Text style={{ color: theme.colors.textMuted, fontSize: 13, fontWeight: "600" }}>{label}</Text> : null}
      <TextInput
        placeholderTextColor={theme.colors.textMuted}
        accessibilityLabel={label}
        style={[
          styles.input,
          {
            color: theme.colors.text,
            backgroundColor: theme.colors.surface,
            borderColor: theme.colors.border,
            borderRadius: theme.radius - 4,
          },
          style,
        ]}
        {...rest}
      />
    </View>
  );
}

export function LoadingState({ label }: { label?: string }) {
  const { theme } = useTheme();
  return (
    <View style={styles.center} accessibilityLiveRegion="polite">
      <ActivityIndicator color={theme.colors.primary} size="large" />
      <Text style={{ color: theme.colors.textMuted, marginTop: 12 }}>{label ?? t("loading")}</Text>
    </View>
  );
}

export function EmptyState({ icon = "✨", title, message, action }: {
  icon?: string;
  title: string;
  message?: string;
  action?: React.ReactNode;
}) {
  const { theme } = useTheme();
  return (
    <View style={styles.center}>
      <Text style={{ fontSize: 48 }}>{icon}</Text>
      <Text style={[styles.title, { color: theme.colors.text, textAlign: "center", marginTop: 8 }]}>{title}</Text>
      {message ? <Text style={{ color: theme.colors.textMuted, textAlign: "center", marginTop: 6 }}>{message}</Text> : null}
      {action ? <View style={{ marginTop: 16 }}>{action}</View> : null}
    </View>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  const { theme } = useTheme();
  return (
    <View style={styles.center} accessibilityRole="alert">
      <Text style={{ fontSize: 40 }}>⚠️</Text>
      <Text style={[styles.title, { color: theme.colors.danger, marginTop: 8 }]}>{t("errorTitle")}</Text>
      <Text style={{ color: theme.colors.textMuted, textAlign: "center", marginTop: 6 }}>{message}</Text>
      {onRetry ? <View style={{ marginTop: 16 }}><Button label={t("retry")} onPress={onRetry} /></View> : null}
    </View>
  );
}

/** Hộp xác nhận chạy được trên cả web (window.confirm) và native (Alert). */
export function confirm(title: string, message: string): Promise<boolean> {
  if (Platform.OS === "web") {
    // eslint-disable-next-line no-alert
    return Promise.resolve(typeof window !== "undefined" ? window.confirm(`${title}\n\n${message}`) : false);
  }
  return new Promise((resolve) => {
    Alert.alert(title, message, [
      { text: t("cancel"), style: "cancel", onPress: () => resolve(false) },
      { text: t("ok"), style: "destructive", onPress: () => resolve(true) },
    ]);
  });
}

const styles = StyleSheet.create({
  fill: { flex: 1 },
  scroll: { flexGrow: 1 },
  inner: { flex: 1, width: "100%", maxWidth: 760, alignSelf: "center" },
  title: { fontSize: 20, fontWeight: "700" },
  button: { paddingVertical: 12, paddingHorizontal: 18, alignItems: "center", justifyContent: "center", minHeight: 44 },
  input: { borderWidth: 1, paddingHorizontal: 12, paddingVertical: 10, fontSize: 16, minHeight: 44 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24 },
});
