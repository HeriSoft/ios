export type Symptom =
  | "fever" | "cough" | "soreThroat" | "runnyNose" | "shortnessOfBreath" | "chestPain" | "headache" | "dizziness"
  | "nausea" | "diarrhea" | "abdominalPain" | "constipation" | "heartburn" | "fatigue" | "muscleAche" | "jointPain"
  | "backPain" | "rash" | "painfulUrination" | "insomnia";

export const SYMPTOMS: [Symptom, string][] = [
  ["fever", "Sốt"], ["cough", "Ho"], ["soreThroat", "Đau họng"], ["runnyNose", "Sổ/nghẹt mũi"],
  ["shortnessOfBreath", "Khó thở"], ["chestPain", "Đau/tức ngực"], ["headache", "Đau đầu"], ["dizziness", "Chóng mặt"],
  ["nausea", "Buồn nôn/nôn"], ["diarrhea", "Tiêu chảy"], ["abdominalPain", "Đau bụng"], ["constipation", "Táo bón"],
  ["heartburn", "Ợ nóng/đau thượng vị"], ["fatigue", "Mệt mỏi"], ["muscleAche", "Đau mỏi cơ"], ["jointPain", "Đau khớp"],
  ["backPain", "Đau lưng"], ["rash", "Phát ban/ngứa"], ["painfulUrination", "Tiểu buốt/rắt"], ["insomnia", "Mất ngủ"],
];

/** Dấu hiệu nguy hiểm: có bất kỳ dấu hiệu nào là cần cấp cứu. */
export type RedFlag =
  | "chestPainSpreading" | "severeBreathing" | "strokeSigns" | "unconscious" | "bleeding" | "severeAbdominal"
  | "feverStiffNeck" | "severeDehydration" | "allergicSwelling" | "worstHeadache" | "selfHarm";

export const RED_FLAGS: [RedFlag, string][] = [
  ["chestPainSpreading", "Đau thắt ngực, lan ra tay/hàm/lưng, vã mồ hôi"],
  ["severeBreathing", "Khó thở nặng, thở rít, môi tím tái"],
  ["strokeSigns", "Méo miệng, nói khó, yếu/tê nửa người"],
  ["unconscious", "Lơ mơ, ngất, co giật"],
  ["bleeding", "Nôn ra máu, đi ngoài phân đen hoặc có máu"],
  ["severeAbdominal", "Đau bụng dữ dội, bụng cứng"],
  ["feverStiffNeck", "Sốt kèm cứng cổ, hoặc nốt xuất huyết dưới da, chảy máu cam/chân răng"],
  ["severeDehydration", "Không đi tiểu trên 8 giờ, rất khát, lừ đừ"],
  ["allergicSwelling", "Sưng môi, lưỡi, mặt sau khi ăn/dùng thuốc"],
  ["worstHeadache", "Đau đầu dữ dội đột ngột, chưa từng bị như vậy"],
  ["selfHarm", "Có ý nghĩ tự làm hại bản thân"],
];

export type PatientGroup = "adult" | "childUnder5" | "elderly" | "pregnant";
export const GROUPS: [PatientGroup, string][] = [
  ["adult", "Người lớn"], ["childUnder5", "Trẻ dưới 5 tuổi"], ["elderly", "Trên 65 tuổi"], ["pregnant", "Đang mang thai"],
];
export type Duration = "underOneDay" | "oneToThreeDays" | "fourToSevenDays" | "overOneWeek";
export const DURATIONS: [Duration, string][] = [
  ["underOneDay", "Dưới 1 ngày"], ["oneToThreeDays", "1–3 ngày"], ["fourToSevenDays", "4–7 ngày"], ["overOneWeek", "Trên 1 tuần"],
];
const DURATION_RANK: Record<Duration, number> = { underOneDay: 0, oneToThreeDays: 1, fourToSevenDays: 2, overOneWeek: 3 };
export type Severity = "mild" | "moderate" | "severe";
export const SEVERITIES: [Severity, string][] = [["mild", "Nhẹ"], ["moderate", "Vừa"], ["severe", "Nặng"]];

export type CareLevel = "selfCare" | "seeDoctor" | "urgent" | "emergency";
const LEVEL_RANK: Record<CareLevel, number> = { selfCare: 0, seeDoctor: 1, urgent: 2, emergency: 3 };
export const CARE: Record<CareLevel, { title: string; detail: string }> = {
  selfCare: { title: "Có thể tự chăm sóc tại nhà", detail: "Nghỉ ngơi, theo dõi triệu chứng. Đi khám nếu không đỡ sau 2–3 ngày hoặc nặng lên." },
  seeDoctor: { title: "Nên đi khám trong vài ngày tới", detail: "Đặt lịch khám để bác sĩ kiểm tra và tìm nguyên nhân." },
  urgent: { title: "Nên đi khám trong hôm nay", detail: "Đến phòng khám hoặc bệnh viện trong vòng 24 giờ, sớm hơn nếu nặng lên." },
  emergency: { title: "Cấp cứu ngay — gọi 115", detail: "Gọi 115 hoặc đến khoa cấp cứu gần nhất ngay. Không tự lái xe nếu đang mệt nặng." },
};

/** Một nguyên nhân thường gặp, kèm cách chăm sóc an toàn. */
export interface Condition {
  id: string;
  name: string;
  summary: string;
  symptoms: Symptom[];
  required: Symptom[];
  specialty: string;
  minimumLevel: CareLevel;
  selfCare: string[];
  eatFoodIDs: string[];
  avoidFoodIDs: string[];
  otcMedicines: string[];
  homeRemedies: string[];
  seeDoctorIf: string[];
}

export const CONDITIONS: Condition[] = [

        {
            id: "common-cold", name: "Cảm lạnh thông thường",
            summary: "Nhiễm virus đường hô hấp trên, thường tự khỏi sau 7–10 ngày.",
            symptoms: ["runnyNose", "soreThroat", "cough", "fever", "fatigue", "headache"],
            required: [], specialty: "Nội tổng quát hoặc Tai Mũi Họng", minimumLevel: "selfCare",
            selfCare: ["Nghỉ ngơi, ngủ đủ giấc", "Uống nhiều nước ấm", "Súc họng bằng nước muối ấm", "Rửa mũi bằng nước muối sinh lý"],
            eatFoodIDs: ["chao", "pho-ga", "cam", "oi"], avoidFoodIDs: ["kem", "nuoc-ngot"],
            otcMedicines: ["Thuốc hạ sốt, giảm đau chứa paracetamol khi sốt hoặc đau nhức", "Nước muối sinh lý nhỏ/rửa mũi"],
            homeRemedies: ["Nước ấm pha mật ong và chanh (không dùng mật ong cho trẻ dưới 1 tuổi)", "Trà gừng ấm", "Xông hơi nước ấm (cẩn thận bỏng, không xông cho trẻ nhỏ)"],
            seeDoctorIf: ["Sốt trên 3 ngày hoặc sốt cao trên 39 °C", "Khó thở, thở nhanh", "Không đỡ sau 10 ngày"]
        },
        {
            id: "flu", name: "Cúm",
            summary: "Nhiễm virus cúm, khởi phát đột ngột với sốt và đau nhức toàn thân.",
            symptoms: ["fever", "muscleAche", "headache", "cough", "fatigue", "soreThroat"],
            required: ["fever"], specialty: "Nội tổng quát", minimumLevel: "selfCare",
            selfCare: ["Nghỉ ngơi tại nhà, hạn chế tiếp xúc người khác", "Uống đủ nước, ăn đồ mềm dễ tiêu", "Đeo khẩu trang, rửa tay thường xuyên"],
            eatFoodIDs: ["chao", "pho-ga", "canh-chua", "cam", "nuoc-ep"], avoidFoodIDs: ["ga-ran", "nuoc-ngot"],
            otcMedicines: ["Thuốc hạ sốt, giảm đau chứa paracetamol"],
            homeRemedies: ["Trà gừng ấm", "Nước ấm pha mật ong và chanh (không dùng mật ong cho trẻ dưới 1 tuổi)"],
            seeDoctorIf: ["Thuộc nhóm nguy cơ (trẻ nhỏ, người già, mang thai, bệnh mạn tính) — nên khám sớm để được xem xét thuốc kháng virus", "Khó thở, đau ngực", "Sốt lại sau khi đã đỡ"]
        },
        {
            id: "dengue", name: "Sốt xuất huyết (cần loại trừ)",
            summary: "Bệnh do muỗi truyền, phổ biến ở Việt Nam. Sốt cao đột ngột 2–7 ngày, có thể diễn biến nặng khi hết sốt.",
            symptoms: ["fever", "headache", "muscleAche", "jointPain", "rash", "nausea", "fatigue"],
            required: ["fever"], specialty: "Nội tổng quát hoặc Truyền nhiễm (xét nghiệm sốt xuất huyết)", minimumLevel: "seeDoctor",
            selfCare: ["Đi khám và xét nghiệm để xác định", "Nghỉ ngơi, uống nhiều nước, oresol, nước trái cây", "Ngủ màn, diệt muỗi và lăng quăng quanh nhà", "Tránh đồ ăn uống màu đỏ, nâu đen để dễ theo dõi dấu hiệu xuất huyết"],
            eatFoodIDs: ["chao", "nuoc-ep", "dua-hau", "canh-chua"], avoidFoodIDs: ["nuoc-ngot", "ca-phe-sua"],
            otcMedicines: ["Chỉ dùng paracetamol để hạ sốt", "KHÔNG tự dùng ibuprofen, aspirin hay thuốc giảm đau chống viêm khác — có thể làm tăng nguy cơ chảy máu", "Dung dịch bù nước điện giải (oresol), pha đúng hướng dẫn"],
            homeRemedies: ["Chườm ấm, lau người bằng nước ấm khi sốt"],
            seeDoctorIf: ["Đau bụng, nôn nhiều, chảy máu cam/chân răng, nốt xuất huyết — đi cấp cứu ngay", "Li bì, vật vã, tay chân lạnh", "Đặc biệt theo dõi kỹ ngày thứ 3–7 khi bắt đầu hết sốt"]
        },
        {
            id: "sore-throat", name: "Viêm họng",
            summary: "Thường do virus; một số trường hợp do vi khuẩn cần bác sĩ kê kháng sinh.",
            symptoms: ["soreThroat", "fever", "cough", "headache"],
            required: ["soreThroat"], specialty: "Tai Mũi Họng", minimumLevel: "selfCare",
            selfCare: ["Súc họng nước muối ấm nhiều lần trong ngày", "Uống nước ấm, nói ít", "Tránh khói thuốc, đồ uống lạnh"],
            eatFoodIDs: ["chao", "pho-ga"], avoidFoodIDs: ["kem", "nuoc-ngot", "cha-gio"],
            otcMedicines: ["Thuốc giảm đau, hạ sốt chứa paracetamol", "Viên ngậm giảm đau họng"],
            homeRemedies: ["Mật ong pha nước ấm (không dùng cho trẻ dưới 1 tuổi)", "Trà gừng ấm"],
            seeDoctorIf: ["Sốt cao, có mủ trắng ở họng, nổi hạch cổ — có thể do vi khuẩn", "Khó nuốt, khó thở, chảy nước dãi", "Không đỡ sau 1 tuần", "Không tự mua kháng sinh — chỉ dùng khi bác sĩ kê"]
        },
        {
            id: "bronchitis", name: "Viêm phế quản",
            summary: "Viêm đường thở, ho kéo dài có thể kèm đờm.",
            symptoms: ["cough", "fever", "fatigue", "shortnessOfBreath", "soreThroat"],
            required: ["cough"], specialty: "Hô hấp", minimumLevel: "selfCare",
            selfCare: ["Uống nhiều nước ấm để loãng đờm", "Nghỉ ngơi, tránh khói thuốc và bụi", "Giữ ấm cổ ngực"],
            eatFoodIDs: ["chao", "pho-ga", "cam"], avoidFoodIDs: ["kem", "nuoc-ngot"],
            otcMedicines: ["Paracetamol khi sốt", "Thuốc long đờm — hỏi dược sĩ trước khi dùng"],
            homeRemedies: ["Mật ong pha nước ấm (không dùng cho trẻ dưới 1 tuổi)", "Hít hơi nước ấm"],
            seeDoctorIf: ["Ho trên 3 tuần", "Khó thở, thở khò khè, đau ngực", "Ho ra máu, sốt cao"]
        },
        {
            id: "gastroenteritis", name: "Viêm dạ dày ruột / ngộ độc thực phẩm",
            summary: "Do virus, vi khuẩn hoặc thức ăn nhiễm bẩn. Nguy cơ chính là mất nước.",
            symptoms: ["diarrhea", "nausea", "abdominalPain", "fever", "fatigue"],
            required: [], specialty: "Tiêu hóa hoặc Nội tổng quát", minimumLevel: "selfCare",
            selfCare: ["Bù nước liên tục bằng oresol, uống từng ngụm nhỏ", "Ăn nhẹ, mềm, chia nhiều bữa khi đỡ nôn", "Rửa tay kỹ, ăn chín uống sôi"],
            eatFoodIDs: ["chao", "com-trang", "chuoi"], avoidFoodIDs: ["sua-tuoi", "ga-ran", "nuoc-ngot", "ca-phe-sua"],
            otcMedicines: ["Dung dịch bù nước điện giải (oresol), pha đúng hướng dẫn trên gói", "Không tự dùng thuốc cầm tiêu chảy cho trẻ em hoặc khi phân có máu, sốt cao"],
            homeRemedies: ["Nước cháo loãng", "Trà gừng ấm có thể giúp giảm buồn nôn"],
            seeDoctorIf: ["Phân có máu, sốt cao", "Nôn liên tục không uống được", "Dấu hiệu mất nước: ít tiểu, khát nhiều, mệt lả", "Tiêu chảy trên 3 ngày"]
        },
        {
            id: "reflux", name: "Trào ngược dạ dày / viêm dạ dày",
            summary: "Axit dạ dày gây nóng rát thượng vị, ợ chua, đầy bụng.",
            symptoms: ["heartburn", "nausea", "abdominalPain", "chestPain"],
            required: ["heartburn"], specialty: "Tiêu hóa", minimumLevel: "selfCare",
            selfCare: ["Ăn bữa nhỏ, ăn chậm, không ăn quá no", "Không nằm ngay trong 2–3 giờ sau ăn", "Kê cao đầu giường", "Hạn chế rượu bia, thuốc lá, đồ cay chua"],
            eatFoodIDs: ["chao", "chuoi", "du-du", "com-trang"], avoidFoodIDs: ["ca-phe-sua", "nuoc-ngot", "ga-ran", "khoai-tay-chien", "bia"],
            otcMedicines: ["Thuốc trung hòa axit dạ dày (antacid) — hỏi dược sĩ"],
            homeRemedies: ["Trà gừng ấm có thể giảm buồn nôn", "Nghệ pha mật ong (người đang dùng thuốc chống đông nên hỏi bác sĩ)"],
            seeDoctorIf: ["Đau kèm sụt cân, khó nuốt, nôn ra máu, phân đen", "Trên 40 tuổi mới bị lần đầu", "Dùng thuốc trên 2 tuần không đỡ"]
        },
        {
            id: "constipation", name: "Táo bón",
            summary: "Thường do ăn ít chất xơ, uống ít nước, ít vận động.",
            symptoms: ["constipation", "abdominalPain"],
            required: ["constipation"], specialty: "Tiêu hóa", minimumLevel: "selfCare",
            selfCare: ["Uống đủ 1,5–2 lít nước mỗi ngày", "Ăn nhiều rau xanh, trái cây", "Vận động, đi bộ mỗi ngày", "Đi vệ sinh vào giờ cố định"],
            eatFoodIDs: ["du-du", "rau-xao", "dua-hau", "chuoi"], avoidFoodIDs: ["oi", "khoai-tay-chien", "ga-ran"],
            otcMedicines: ["Chất xơ bổ sung hoặc thuốc nhuận tràng nhẹ — hỏi dược sĩ, không dùng kéo dài"],
            homeRemedies: ["Uống một cốc nước ấm khi mới ngủ dậy"],
            seeDoctorIf: ["Có máu trong phân, sụt cân", "Táo bón xen kẽ tiêu chảy kéo dài", "Đau bụng nhiều, chướng bụng, không trung tiện được"]
        },
        {
            id: "headache", name: "Đau đầu do căng thẳng / đau nửa đầu",
            summary: "Thường liên quan căng thẳng, thiếu ngủ, bỏ bữa, nhìn màn hình lâu.",
            symptoms: ["headache", "dizziness", "nausea", "insomnia", "fatigue"],
            required: ["headache"], specialty: "Thần kinh", minimumLevel: "selfCare",
            selfCare: ["Nghỉ ở nơi yên tĩnh, ít ánh sáng", "Ngủ đủ, ăn đúng bữa, uống đủ nước", "Giảm thời gian nhìn màn hình, thư giãn cổ vai"],
            eatFoodIDs: ["chuoi", "trung-luoc", "dua-hau"], avoidFoodIDs: ["ca-phe-sua", "bia"],
            otcMedicines: ["Thuốc giảm đau chứa paracetamol — không dùng quá 2–3 ngày/tuần để tránh đau đầu do lạm dụng thuốc"],
            homeRemedies: ["Chườm lạnh hoặc ấm vùng trán, gáy", "Xoa bóp nhẹ thái dương, cổ vai"],
            seeDoctorIf: ["Đau đầu ngày càng nặng hoặc thay đổi tính chất", "Kèm sốt, nôn vọt, nhìn mờ, yếu tay chân", "Đau đầu sau chấn thương"]
        },
        {
            id: "dehydration", name: "Mất nước / say nắng",
            summary: "Thiếu nước khi trời nóng, vận động nhiều, nôn hoặc tiêu chảy.",
            symptoms: ["dizziness", "fatigue", "headache", "nausea"],
            required: ["dizziness"], specialty: "Nội tổng quát", minimumLevel: "selfCare",
            selfCare: ["Vào chỗ mát, nới lỏng quần áo", "Uống nước hoặc oresol từng ngụm", "Chườm mát trán, nách, bẹn"],
            eatFoodIDs: ["dua-hau", "nuoc-ep", "canh-chua"], avoidFoodIDs: ["bia", "ca-phe-sua"],
            otcMedicines: ["Dung dịch bù nước điện giải (oresol)"],
            homeRemedies: ["Nước dừa hoặc nước pha chút muối và đường"],
            seeDoctorIf: ["Lú lẫn, ngất, co giật — cấp cứu ngay", "Sốt cao, da khô nóng", "Không đỡ sau 1 giờ nghỉ và uống nước"]
        },
        {
            id: "allergy", name: "Dị ứng / mày đay",
            summary: "Phản ứng với thức ăn, thuốc, phấn hoa, bụi hoặc côn trùng đốt.",
            symptoms: ["rash", "runnyNose"],
            required: ["rash"], specialty: "Da liễu hoặc Dị ứng – Miễn dịch", minimumLevel: "selfCare",
            selfCare: ["Tránh tác nhân nghi ngờ (món ăn, thuốc mới dùng)", "Tắm nước mát, mặc đồ thoáng", "Không gãi mạnh"],
            eatFoodIDs: ["rau-xao", "com-trang"], avoidFoodIDs: ["sushi", "bia"],
            otcMedicines: ["Thuốc kháng histamine chống dị ứng — hỏi dược sĩ, một số loại gây buồn ngủ"],
            homeRemedies: ["Chườm mát vùng ngứa"],
            seeDoctorIf: ["Sưng môi, lưỡi, mặt hoặc khó thở — cấp cứu ngay", "Ban lan rộng, kèm sốt", "Nổi mày đay trên 6 tuần"]
        },
        {
            id: "uti", name: "Nhiễm trùng đường tiết niệu",
            summary: "Thường gặp ở nữ; cần bác sĩ khám và kê thuốc phù hợp.",
            symptoms: ["painfulUrination", "abdominalPain", "fever", "backPain"],
            required: ["painfulUrination"], specialty: "Thận – Tiết niệu (nữ có thể khám Phụ khoa)", minimumLevel: "seeDoctor",
            selfCare: ["Uống nhiều nước", "Không nhịn tiểu", "Vệ sinh đúng cách từ trước ra sau"],
            eatFoodIDs: ["dua-hau", "nuoc-ep"], avoidFoodIDs: ["ca-phe-sua", "bia", "nuoc-ngot"],
            otcMedicines: ["Không tự dùng kháng sinh — bác sĩ sẽ kê loại và thời gian phù hợp"],
            homeRemedies: [],
            seeDoctorIf: ["Sốt, rét run, đau hông lưng — có thể nhiễm trùng thận, khám ngay", "Đang mang thai", "Tiểu ra máu"]
        },
        {
            id: "muscle-strain", name: "Căng cơ / đau lưng cơ học",
            summary: "Do sai tư thế, ngồi lâu, mang vác nặng hoặc vận động quá sức.",
            symptoms: ["backPain", "muscleAche"],
            required: [], specialty: "Cơ Xương Khớp hoặc Phục hồi chức năng", minimumLevel: "selfCare",
            selfCare: ["Vận động nhẹ nhàng, tránh nằm bất động lâu", "Chườm lạnh 1–2 ngày đầu, sau đó chườm ấm", "Ngồi đúng tư thế, nghỉ giải lao khi ngồi lâu"],
            eatFoodIDs: ["ca-kho", "sua-tuoi", "rau-xao"], avoidFoodIDs: [],
            otcMedicines: ["Thuốc giảm đau chứa paracetamol", "Thuốc giảm đau dạng bôi ngoài da — hỏi dược sĩ"],
            homeRemedies: ["Xoa bóp nhẹ, giãn cơ", "Chườm ấm bằng túi chườm (tránh bỏng)"],
            seeDoctorIf: ["Tê yếu chân, rối loạn tiểu tiện — khám ngay", "Đau sau ngã hoặc chấn thương", "Kèm sốt, sụt cân", "Không đỡ sau 2 tuần"]
        },
        {
            id: "joint-pain", name: "Đau khớp (thoái hóa, gút…)",
            summary: "Nhiều nguyên nhân; gút thường sưng nóng đỏ đột ngột ở ngón chân cái.",
            symptoms: ["jointPain", "muscleAche", "fever"],
            required: ["jointPain"], specialty: "Cơ Xương Khớp", minimumLevel: "seeDoctor",
            selfCare: ["Nghỉ ngơi khớp đau, kê cao khi sưng", "Giữ cân nặng hợp lý", "Uống đủ nước"],
            eatFoodIDs: ["rau-xao", "cam", "dua-hau"], avoidFoodIDs: ["bia", "bit-tet", "sushi", "nuoc-ngot"],
            otcMedicines: ["Thuốc giảm đau chứa paracetamol"],
            homeRemedies: ["Chườm lạnh khi khớp sưng nóng"],
            seeDoctorIf: ["Khớp sưng nóng đỏ, sốt", "Đau nhiều khớp, cứng khớp buổi sáng kéo dài", "Đau sau chấn thương"]
        },
        {
            id: "insomnia", name: "Mất ngủ / căng thẳng",
            summary: "Thường liên quan căng thẳng, thói quen ngủ, caffeine.",
            symptoms: ["insomnia", "fatigue", "headache"],
            required: ["insomnia"], specialty: "Thần kinh hoặc Tâm lý – Tâm thần", minimumLevel: "selfCare",
            selfCare: ["Đi ngủ và thức dậy giờ cố định", "Không dùng điện thoại 1 giờ trước khi ngủ", "Không uống cà phê, trà sau 14 giờ", "Vận động ban ngày, thư giãn trước khi ngủ"],
            eatFoodIDs: ["chuoi", "sua-tuoi"], avoidFoodIDs: ["ca-phe-sua", "tra-sua", "nuoc-ngot", "bia"],
            otcMedicines: ["Không tự dùng thuốc ngủ — hỏi bác sĩ"],
            homeRemedies: ["Trà hoa cúc hoặc trà tâm sen ấm buổi tối", "Ngâm chân nước ấm"],
            seeDoctorIf: ["Mất ngủ trên 3 tuần ảnh hưởng công việc", "Buồn chán kéo dài, mất hứng thú", "Có ý nghĩ tự làm hại bản thân — tìm trợ giúp ngay"]
        },
        {
            id: "anemia", name: "Thiếu máu / mệt mỏi kéo dài",
            summary: "Mệt, chóng mặt kéo dài có thể do thiếu sắt, thiếu ngủ hoặc bệnh khác cần xét nghiệm.",
            symptoms: ["fatigue", "dizziness", "shortnessOfBreath", "headache"],
            required: ["fatigue"], specialty: "Nội tổng quát (xét nghiệm máu)", minimumLevel: "selfCare",
            selfCare: ["Ngủ đủ 7–8 giờ", "Ăn đủ đạm, thực phẩm giàu sắt", "Ăn kèm trái cây giàu vitamin C để hấp thu sắt tốt hơn"],
            eatFoodIDs: ["bit-tet", "trung-luoc", "rau-xao", "cam"], avoidFoodIDs: ["tra-sua", "ca-phe-sua"],
            otcMedicines: ["Viên sắt chỉ nên dùng khi đã xét nghiệm thiếu sắt — hỏi bác sĩ"],
            homeRemedies: [],
            seeDoctorIf: ["Mệt kéo dài trên 2 tuần", "Da xanh, tim đập nhanh, khó thở khi gắng sức", "Sụt cân, sốt kéo dài"]
        },
    
];

export interface SymptomInput {
  symptoms: Symptom[];
  redFlags: RedFlag[];
  group: PatientGroup;
  duration: Duration;
  severity: Severity;
}
export const emptySymptomInput = (): SymptomInput => ({
  symptoms: [], redFlags: [], group: "adult", duration: "oneToThreeDays", severity: "mild",
});

export interface ConditionMatch { condition: Condition; matched: number; score: number }
export interface Assessment {
  level: CareLevel;
  reasons: string[];
  matches: ConditionMatch[];
  /** Trẻ dưới 5 tuổi và phụ nữ mang thai: không gợi ý thuốc/thảo dược. */
  showMedicationAdvice: boolean;
}

/** Xếp hạng nguyên nhân thường gặp theo mức độ trùng triệu chứng. */
export function matchConditions(selected: Symptom[], limit = 3): ConditionMatch[] {
  if (selected.length === 0) return [];
  const sel = new Set(selected);
  return CONDITIONS.flatMap((c) => {
    if (!c.required.every((s) => sel.has(s))) return [];
    const matched = c.symptoms.filter((s) => sel.has(s)).length;
    if (matched === 0) return [];
    const score = 0.6 * (matched / c.symptoms.length) + 0.4 * (matched / sel.size);
    return score >= 0.25 ? [{ condition: c, matched, score }] : [];
  })
    .sort((a, b) => b.score - a.score || a.condition.name.localeCompare(b.condition.name, "vi"))
    .slice(0, limit);
}

/** Đánh giá mức độ cần đi khám (công cụ tham khảo, không phải chẩn đoán). */
export function assess(input: SymptomInput): Assessment {
  let level: CareLevel = "selfCare";
  const reasons: string[] = [];
  const raise = (l: CareLevel, reason: string) => {
    if (LEVEL_RANK[l] > LEVEL_RANK[level]) level = l;
    reasons.push(reason);
  };
  const has = (s: Symptom) => input.symptoms.includes(s);
  if (input.redFlags.length > 0) {
    const titles = RED_FLAGS.filter(([f]) => input.redFlags.includes(f)).map(([, t]) => t);
    raise("emergency", "Có dấu hiệu nguy hiểm: " + titles.join("; "));
  }
  if (has("chestPain") || has("shortnessOfBreath")) raise("urgent", "Đau ngực hoặc khó thở cần được bác sĩ kiểm tra sớm.");
  if (input.severity === "severe") raise("urgent", "Triệu chứng ở mức nặng.");
  const groupTitle = GROUPS.find(([g]) => g === input.group)![1];
  if (input.group !== "adult" && (has("fever") || has("diarrhea") || has("nausea")))
    raise("urgent", `${groupTitle} dễ diễn biến nặng khi sốt, nôn hoặc tiêu chảy.`);
  if (input.group === "pregnant" && has("abdominalPain")) raise("urgent", "Đau bụng khi mang thai cần được bác sĩ sản khoa kiểm tra.");
  if (has("fever") && DURATION_RANK[input.duration] >= DURATION_RANK.fourToSevenDays)
    raise("urgent", "Sốt trên 3 ngày cần đi khám (ở Việt Nam cần loại trừ sốt xuất huyết).");
  if (input.duration === "overOneWeek") raise("seeDoctor", "Triệu chứng kéo dài trên 1 tuần.");
  else if (input.severity === "moderate" && DURATION_RANK[input.duration] >= DURATION_RANK.fourToSevenDays)
    raise("seeDoctor", "Triệu chứng mức vừa kéo dài nhiều ngày.");
  const matches = matchConditions(input.symptoms);
  // Xét mọi nguyên nhân được liệt kê, không chỉ nguyên nhân đứng đầu
  // (ví dụ sốt xuất huyết đứng thứ hai vẫn cần đi khám để loại trừ).
  for (const m of matches) {
    if (LEVEL_RANK[m.condition.minimumLevel] > LEVEL_RANK[level])
      raise(m.condition.minimumLevel, `Có thể là "${m.condition.name}": cần bác sĩ khám để xác định và điều trị.`);
  }
  if (reasons.length === 0) reasons.push("Chưa thấy dấu hiệu cần đi khám gấp dựa trên thông tin bạn nhập.");
  return { level, reasons, matches, showMedicationAdvice: input.group !== "childUnder5" && input.group !== "pregnant" };
}

export const levelAtLeast = (a: CareLevel, b: CareLevel) => LEVEL_RANK[a] >= LEVEL_RANK[b];
