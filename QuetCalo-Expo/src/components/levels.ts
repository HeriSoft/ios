import { CareLevel } from "../core/symptoms";
import { COLORS } from "./kit";

export const LEVEL_COLOR: Record<CareLevel, string> = { selfCare: COLORS.green, seeDoctor: COLORS.yellow, urgent: COLORS.orange, emergency: COLORS.red };
