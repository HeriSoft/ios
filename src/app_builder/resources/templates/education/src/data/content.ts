import { brand } from "../brand";

export type Lesson = { id: string; emoji: string; color: string; title: string; summary: string; steps: string[] };
export type GalleryItem = { id: string; emoji: string; name: string; group: string };
export type ScheduleDay = { day: string; slots: { time: string; title: string }[] };
export type Activity = { id: string; emoji: string; title: string };

const vi = {
  lessons: [
    { id: "colors", emoji: "🎨", color: "#F472B6", title: "Màu sắc", summary: "Nhận biết đỏ, vàng, xanh", steps: ["Xem 3 màu cơ bản", "Tìm đồ vật cùng màu trong phòng", "Tô màu bức tranh yêu thích"] },
    { id: "shapes", emoji: "🔺", color: "#60A5FA", title: "Hình khối", summary: "Tròn, vuông, tam giác", steps: ["Gọi tên các hình", "Ghép hình theo cặp", "Vẽ ngôi nhà từ các hình"] },
    { id: "animals", emoji: "🐘", color: "#34D399", title: "Con vật", summary: "Tên và tiếng kêu con vật", steps: ["Xem tranh con vật", "Bắt chước tiếng kêu", "Kể con vật em thích"] },
    { id: "numbers", emoji: "🔢", color: "#FBBF24", title: "Số đếm 1–10", summary: "Đếm đồ vật quanh em", steps: ["Đếm ngón tay", "Đếm đồ chơi", "Xếp số theo thứ tự"] },
    { id: "letters", emoji: "🔤", color: "#A78BFA", title: "Chữ cái", summary: "Làm quen chữ a, ă, â", steps: ["Nghe và đọc theo", "Tô chữ theo nét", "Tìm chữ trong tên mình"] },
  ] as Lesson[],
  gallery: [
    { id: "g1", emoji: "🐶", name: "Chó", group: "Con vật" }, { id: "g2", emoji: "🐱", name: "Mèo", group: "Con vật" },
    { id: "g3", emoji: "🦁", name: "Sư tử", group: "Con vật" }, { id: "g4", emoji: "🐟", name: "Cá", group: "Con vật" },
    { id: "g5", emoji: "🍎", name: "Táo", group: "Trái cây" }, { id: "g6", emoji: "🍌", name: "Chuối", group: "Trái cây" },
    { id: "g7", emoji: "🍉", name: "Dưa hấu", group: "Trái cây" }, { id: "g8", emoji: "🍇", name: "Nho", group: "Trái cây" },
    { id: "g9", emoji: "🚗", name: "Ô tô", group: "Phương tiện" }, { id: "g10", emoji: "🚲", name: "Xe đạp", group: "Phương tiện" },
    { id: "g11", emoji: "✈️", name: "Máy bay", group: "Phương tiện" }, { id: "g12", emoji: "🚢", name: "Tàu thủy", group: "Phương tiện" },
  ] as GalleryItem[],
  schedule: [
    { day: "Thứ Hai", slots: [{ time: "08:00", title: "Màu sắc" }, { time: "09:30", title: "Vận động" }] },
    { day: "Thứ Ba", slots: [{ time: "08:00", title: "Hình khối" }, { time: "09:30", title: "Âm nhạc" }] },
    { day: "Thứ Tư", slots: [{ time: "08:00", title: "Con vật" }, { time: "09:30", title: "Kể chuyện" }] },
    { day: "Thứ Năm", slots: [{ time: "08:00", title: "Số đếm" }, { time: "09:30", title: "Vẽ tranh" }] },
    { day: "Thứ Sáu", slots: [{ time: "08:00", title: "Chữ cái" }, { time: "09:30", title: "Trò chơi" }] },
  ] as ScheduleDay[],
  activities: [
    { id: "read", emoji: "📚", title: "Đọc truyện 10 phút" }, { id: "draw", emoji: "🖍️", title: "Vẽ một bức tranh" },
    { id: "move", emoji: "🤸", title: "Vận động ngoài trời" }, { id: "tidy", emoji: "🧸", title: "Cất đồ chơi gọn gàng" },
    { id: "sing", emoji: "🎵", title: "Hát một bài hát" },
  ] as Activity[],
};

const en: typeof vi = {
  lessons: [
    { id: "colors", emoji: "🎨", color: "#F472B6", title: "Colors", summary: "Red, yellow, blue", steps: ["Look at 3 basic colors", "Find objects of the same color", "Color your favorite picture"] },
    { id: "shapes", emoji: "🔺", color: "#60A5FA", title: "Shapes", summary: "Circle, square, triangle", steps: ["Name the shapes", "Match shapes in pairs", "Draw a house from shapes"] },
    { id: "animals", emoji: "🐘", color: "#34D399", title: "Animals", summary: "Names and sounds", steps: ["Look at animal pictures", "Imitate the sounds", "Tell us your favorite animal"] },
    { id: "numbers", emoji: "🔢", color: "#FBBF24", title: "Numbers 1–10", summary: "Count things around you", steps: ["Count your fingers", "Count your toys", "Put numbers in order"] },
    { id: "letters", emoji: "🔤", color: "#A78BFA", title: "Letters", summary: "Meet A, B, C", steps: ["Listen and repeat", "Trace the letters", "Find letters in your name"] },
  ],
  gallery: [
    { id: "g1", emoji: "🐶", name: "Dog", group: "Animals" }, { id: "g2", emoji: "🐱", name: "Cat", group: "Animals" },
    { id: "g3", emoji: "🦁", name: "Lion", group: "Animals" }, { id: "g4", emoji: "🐟", name: "Fish", group: "Animals" },
    { id: "g5", emoji: "🍎", name: "Apple", group: "Fruits" }, { id: "g6", emoji: "🍌", name: "Banana", group: "Fruits" },
    { id: "g7", emoji: "🍉", name: "Watermelon", group: "Fruits" }, { id: "g8", emoji: "🍇", name: "Grapes", group: "Fruits" },
    { id: "g9", emoji: "🚗", name: "Car", group: "Vehicles" }, { id: "g10", emoji: "🚲", name: "Bicycle", group: "Vehicles" },
    { id: "g11", emoji: "✈️", name: "Airplane", group: "Vehicles" }, { id: "g12", emoji: "🚢", name: "Ship", group: "Vehicles" },
  ],
  schedule: [
    { day: "Monday", slots: [{ time: "08:00", title: "Colors" }, { time: "09:30", title: "Movement" }] },
    { day: "Tuesday", slots: [{ time: "08:00", title: "Shapes" }, { time: "09:30", title: "Music" }] },
    { day: "Wednesday", slots: [{ time: "08:00", title: "Animals" }, { time: "09:30", title: "Storytime" }] },
    { day: "Thursday", slots: [{ time: "08:00", title: "Numbers" }, { time: "09:30", title: "Drawing" }] },
    { day: "Friday", slots: [{ time: "08:00", title: "Letters" }, { time: "09:30", title: "Games" }] },
  ],
  activities: [
    { id: "read", emoji: "📚", title: "Read a story for 10 minutes" }, { id: "draw", emoji: "🖍️", title: "Draw a picture" },
    { id: "move", emoji: "🤸", title: "Play outside" }, { id: "tidy", emoji: "🧸", title: "Tidy up toys" },
    { id: "sing", emoji: "🎵", title: "Sing a song" },
  ],
};

export const content = brand.language === "en" ? en : vi;
