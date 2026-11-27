import AsyncStorage from "@react-native-async-storage/async-storage";
import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { useColorScheme } from "react-native";
import { brand } from "./brand";

export type ThemeMode = "system" | "light" | "dark";

export type Palette = {
  background: string;
  surface: string;
  surfaceAlt: string;
  text: string;
  textMuted: string;
  border: string;
  primary: string;
  primaryText: string;
  accent: string;
  danger: string;
  success: string;
};

export type Theme = {
  dark: boolean;
  colors: Palette;
  radius: number;
  spacing: number;
};

const light: Palette = {
  background: brand.backgroundLight,
  surface: "#FFFFFF",
  surfaceAlt: "#EEF2F7",
  text: "#0F172A",
  textMuted: "#64748B",
  border: "#E2E8F0",
  primary: brand.primary,
  primaryText: "#FFFFFF",
  accent: brand.accent,
  danger: "#DC2626",
  success: "#16A34A",
};

const dark: Palette = {
  background: brand.backgroundDark,
  surface: "#151C2C",
  surfaceAlt: "#1E2738",
  text: "#F1F5F9",
  textMuted: "#94A3B8",
  border: "#2A3446",
  primary: brand.primary,
  primaryText: "#FFFFFF",
  accent: brand.accent,
  danger: "#F87171",
  success: "#4ADE80",
};

type ThemeContextValue = {
  theme: Theme;
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
};

const STORAGE_KEY = "app.themeMode";
const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const system = useColorScheme();
  const [mode, setModeState] = useState<ThemeMode>("system");

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY)
      .then((v) => {
        if (v === "light" || v === "dark" || v === "system") setModeState(v);
      })
      .catch(() => undefined);
  }, []);

  const setMode = (m: ThemeMode) => {
    setModeState(m);
    AsyncStorage.setItem(STORAGE_KEY, m).catch(() => undefined);
  };

  const value = useMemo<ThemeContextValue>(() => {
    const isDark = mode === "system" ? system === "dark" : mode === "dark";
    return {
      mode,
      setMode,
      theme: { dark: isDark, colors: isDark ? dark : light, radius: brand.radius, spacing: brand.spacing },
    };
  }, [mode, system]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme phải nằm trong ThemeProvider");
  return ctx;
}
