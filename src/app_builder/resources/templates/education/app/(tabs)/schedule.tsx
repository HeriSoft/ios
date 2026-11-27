import React from "react";
import { ScrollView, Text, View } from "react-native";
import { Card, Screen } from "../../src/components/ui";
import { content } from "../../src/data/content";
import { useTheme } from "../../src/theme";

export default function Schedule() {
  const { theme } = useTheme();
  const todayIndex = (new Date().getDay() + 6) % 7; // 0 = Thứ Hai
  return (
    <Screen>
      <ScrollView contentContainerStyle={{ gap: 12, paddingBottom: 24 }}>
        {content.schedule.map((d, i) => (
          <Card key={d.day} style={{ gap: 8, borderColor: i === todayIndex ? theme.colors.primary : theme.colors.border, borderWidth: i === todayIndex ? 2 : 1 }}>
            <Text style={{ color: i === todayIndex ? theme.colors.primary : theme.colors.text, fontSize: 17, fontWeight: "700" }}>{d.day}</Text>
            {d.slots.map((s) => (
              <View key={s.time + s.title} style={{ flexDirection: "row", gap: 12, alignItems: "center" }}>
                <Text style={{ color: theme.colors.textMuted, width: 52, fontVariant: ["tabular-nums"] }}>{s.time}</Text>
                <Text style={{ color: theme.colors.text, fontSize: 15 }}>{s.title}</Text>
              </View>
            ))}
          </Card>
        ))}
      </ScrollView>
    </Screen>
  );
}
