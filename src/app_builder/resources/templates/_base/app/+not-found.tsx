import { Link, Stack } from "expo-router";
import React from "react";
import { EmptyState, Screen } from "../src/components/ui";
import { t } from "../src/i18n";
import { useTheme } from "../src/theme";

export default function NotFound() {
  const { theme } = useTheme();
  return (
    <Screen>
      <Stack.Screen options={{ title: t("notFound") }} />
      <EmptyState
        icon="🧭"
        title={t("notFound")}
        action={<Link href="/" style={{ color: theme.colors.primary, fontWeight: "600" }}>{t("goHome")}</Link>}
      />
    </Screen>
  );
}
