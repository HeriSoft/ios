import React, { useMemo, useState } from "react";
import { Modal, Pressable, ScrollView, Text, useWindowDimensions, View } from "react-native";
import { Button, Screen } from "../../src/components/ui";
import { content, GalleryItem } from "../../src/data/content";
import { t } from "../../src/i18n";
import { useTheme } from "../../src/theme";

export default function Gallery() {
  const { theme } = useTheme();
  const { width } = useWindowDimensions();
  const [selected, setSelected] = useState<GalleryItem | null>(null);
  const columns = width > 900 ? 6 : width > 600 ? 4 : 3;
  const groups = useMemo(() => Array.from(new Set(content.gallery.map((g) => g.group))), []);

  return (
    <Screen>
      <ScrollView contentContainerStyle={{ gap: 18, paddingBottom: 24 }}>
        {groups.map((group) => (
          <View key={group} style={{ gap: 10 }}>
            <Text style={{ color: theme.colors.text, fontSize: 18, fontWeight: "700" }}>{group}</Text>
            <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 10 }}>
              {content.gallery
                .filter((g) => g.group === group)
                .map((g) => (
                  <Pressable
                    key={g.id}
                    onPress={() => setSelected(g)}
                    accessibilityRole="imagebutton"
                    accessibilityLabel={g.name}
                    style={{
                      width: `${100 / columns - 3}%`,
                      aspectRatio: 1,
                      borderRadius: theme.radius,
                      backgroundColor: theme.colors.surface,
                      borderWidth: 1,
                      borderColor: theme.colors.border,
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Text style={{ fontSize: 38 }}>{g.emoji}</Text>
                    <Text style={{ color: theme.colors.textMuted, marginTop: 4 }}>{g.name}</Text>
                  </Pressable>
                ))}
            </View>
          </View>
        ))}
      </ScrollView>
      <Modal visible={!!selected} transparent animationType="fade" onRequestClose={() => setSelected(null)}>
        <View style={{ flex: 1, backgroundColor: "rgba(0,0,0,0.6)", alignItems: "center", justifyContent: "center", padding: 24 }}>
          <View style={{ backgroundColor: theme.colors.surface, borderRadius: theme.radius * 1.5, padding: 28, alignItems: "center", gap: 12, minWidth: 260 }}>
            <Text style={{ fontSize: 110 }}>{selected?.emoji}</Text>
            <Text style={{ color: theme.colors.text, fontSize: 26, fontWeight: "800" }}>{selected?.name}</Text>
            <Button label={t("close")} onPress={() => setSelected(null)} />
          </View>
        </View>
      </Modal>
    </Screen>
  );
}
