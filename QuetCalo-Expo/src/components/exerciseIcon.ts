import { Ionicons } from "@expo/vector-icons";
import { ExerciseCategory } from "../core/exercise";

export const CATEGORY_ICON: Record<ExerciseCategory, keyof typeof Ionicons.glyphMap> = {
  cardio: "walk-outline", strength: "barbell-outline", sport: "football-outline", flexibility: "body-outline", daily: "home-outline",
};
