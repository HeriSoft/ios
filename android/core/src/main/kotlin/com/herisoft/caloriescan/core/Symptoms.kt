package com.herisoft.caloriescan.core

enum class Symptom(val title: String) {
    fever("Sốt"), cough("Ho"), soreThroat("Đau họng"), runnyNose("Sổ/nghẹt mũi"),
    shortnessOfBreath("Khó thở"), chestPain("Đau/tức ngực"), headache("Đau đầu"), dizziness("Chóng mặt"),
    nausea("Buồn nôn/nôn"), diarrhea("Tiêu chảy"), abdominalPain("Đau bụng"), constipation("Táo bón"),
    heartburn("Ợ nóng/đau thượng vị"), fatigue("Mệt mỏi"), muscleAche("Đau mỏi cơ"), jointPain("Đau khớp"),
    backPain("Đau lưng"), rash("Phát ban/ngứa"), painfulUrination("Tiểu buốt/rắt"), insomnia("Mất ngủ"),
}

/** Dấu hiệu nguy hiểm: có bất kỳ dấu hiệu nào là cần cấp cứu. */
enum class RedFlag(val title: String) {
    chestPainSpreading("Đau thắt ngực, lan ra tay/hàm/lưng, vã mồ hôi"),
    severeBreathing("Khó thở nặng, thở rít, môi tím tái"),
    strokeSigns("Méo miệng, nói khó, yếu/tê nửa người"),
    unconscious("Lơ mơ, ngất, co giật"),
    bleeding("Nôn ra máu, đi ngoài phân đen hoặc có máu"),
    severeAbdominal("Đau bụng dữ dội, bụng cứng"),
    feverStiffNeck("Sốt kèm cứng cổ, hoặc nốt xuất huyết dưới da, chảy máu cam/chân răng"),
    severeDehydration("Không đi tiểu trên 8 giờ, rất khát, lừ đừ"),
    allergicSwelling("Sưng môi, lưỡi, mặt sau khi ăn/dùng thuốc"),
    worstHeadache("Đau đầu dữ dội đột ngột, chưa từng bị như vậy"),
    selfHarm("Có ý nghĩ tự làm hại bản thân"),
}

enum class PatientGroup(val title: String) {
    adult("Người lớn"), childUnder5("Trẻ dưới 5 tuổi"), elderly("Trên 65 tuổi"), pregnant("Đang mang thai");

    /** Nhóm dễ diễn biến nặng. */
    val isVulnerable: Boolean get() = this != adult
}

enum class SymptomDuration(val title: String) {
    underOneDay("Dưới 1 ngày"), oneToThreeDays("1–3 ngày"), fourToSevenDays("4–7 ngày"), overOneWeek("Trên 1 tuần"),
}

enum class SymptomSeverity(val title: String) { mild("Nhẹ"), moderate("Vừa"), severe("Nặng") }

enum class CareLevel(val title: String, val detail: String) {
    selfCare("Có thể tự chăm sóc tại nhà", "Nghỉ ngơi, theo dõi triệu chứng. Đi khám nếu không đỡ sau 2–3 ngày hoặc nặng lên."),
    seeDoctor("Nên đi khám trong vài ngày tới", "Đặt lịch khám để bác sĩ kiểm tra và tìm nguyên nhân."),
    urgent("Nên đi khám trong hôm nay", "Đến phòng khám hoặc bệnh viện trong vòng 24 giờ, sớm hơn nếu nặng lên."),
    emergency("Cấp cứu ngay — gọi 115", "Gọi 115 hoặc đến khoa cấp cứu gần nhất ngay. Không tự lái xe nếu đang mệt nặng."),
}

/** Một nguyên nhân thường gặp, kèm cách chăm sóc an toàn. */
data class Condition(
    val id: String,
    val name: String,
    val summary: String,
    val symptoms: Set<Symptom>,
    val required: Set<Symptom>,
    val specialty: String,
    val minimumLevel: CareLevel,
    val selfCare: List<String>,
    val eatFoodIDs: List<String>,
    val avoidFoodIDs: List<String>,
    val otcMedicines: List<String>,
    val homeRemedies: List<String>,
    val seeDoctorIf: List<String>,
)

object ConditionLibrary {
    val all: List<Condition> = listOf(

        Condition(
            id = "common-cold", name = "Cảm lạnh thông thường",
            summary = "Nhiễm virus đường hô hấp trên, thường tự khỏi sau 7–10 ngày.",
            symptoms = setOf(Symptom.runnyNose, Symptom.soreThroat, Symptom.cough, Symptom.fever, Symptom.fatigue, Symptom.headache),
            required = setOf(), specialty = "Nội tổng quát hoặc Tai Mũi Họng", minimumLevel = CareLevel.selfCare,
            selfCare = listOf("Nghỉ ngơi, ngủ đủ giấc", "Uống nhiều nước ấm", "Súc họng bằng nước muối ấm", "Rửa mũi bằng nước muối sinh lý"),
            eatFoodIDs = listOf("chao", "pho-ga", "cam", "oi"), avoidFoodIDs = listOf("kem", "nuoc-ngot"),
            otcMedicines = listOf("Thuốc hạ sốt, giảm đau chứa paracetamol khi sốt hoặc đau nhức", "Nước muối sinh lý nhỏ/rửa mũi"),
            homeRemedies = listOf("Nước ấm pha mật ong và chanh (không dùng mật ong cho trẻ dưới 1 tuổi)", "Trà gừng ấm", "Xông hơi nước ấm (cẩn thận bỏng, không xông cho trẻ nhỏ)"),
            seeDoctorIf = listOf("Sốt trên 3 ngày hoặc sốt cao trên 39 °C", "Khó thở, thở nhanh", "Không đỡ sau 10 ngày")
        ),
        Condition(
            id = "flu", name = "Cúm",
            summary = "Nhiễm virus cúm, khởi phát đột ngột với sốt và đau nhức toàn thân.",
            symptoms = setOf(Symptom.fever, Symptom.muscleAche, Symptom.headache, Symptom.cough, Symptom.fatigue, Symptom.soreThroat),
            required = setOf(Symptom.fever), specialty = "Nội tổng quát", minimumLevel = CareLevel.selfCare,
            selfCare = listOf("Nghỉ ngơi tại nhà, hạn chế tiếp xúc người khác", "Uống đủ nước, ăn đồ mềm dễ tiêu", "Đeo khẩu trang, rửa tay thường xuyên"),
            eatFoodIDs = listOf("chao", "pho-ga", "canh-chua", "cam", "nuoc-ep"), avoidFoodIDs = listOf("ga-ran", "nuoc-ngot"),
            otcMedicines = listOf("Thuốc hạ sốt, giảm đau chứa paracetamol"),
            homeRemedies = listOf("Trà gừng ấm", "Nước ấm pha mật ong và chanh (không dùng mật ong cho trẻ dưới 1 tuổi)"),
            seeDoctorIf = listOf("Thuộc nhóm nguy cơ (trẻ nhỏ, người già, mang thai, bệnh mạn tính) — nên khám sớm để được xem xét thuốc kháng virus", "Khó thở, đau ngực", "Sốt lại sau khi đã đỡ")
        ),
        Condition(
            id = "dengue", name = "Sốt xuất huyết (cần loại trừ)",
            summary = "Bệnh do muỗi truyền, phổ biến ở Việt Nam. Sốt cao đột ngột 2–7 ngày, có thể diễn biến nặng khi hết sốt.",
            symptoms = setOf(Symptom.fever, Symptom.headache, Symptom.muscleAche, Symptom.jointPain, Symptom.rash, Symptom.nausea, Symptom.fatigue),
            required = setOf(Symptom.fever), specialty = "Nội tổng quát hoặc Truyền nhiễm (xét nghiệm sốt xuất huyết)", minimumLevel = CareLevel.seeDoctor,
            selfCare = listOf("Đi khám và xét nghiệm để xác định", "Nghỉ ngơi, uống nhiều nước, oresol, nước trái cây", "Ngủ màn, diệt muỗi và lăng quăng quanh nhà", "Tránh đồ ăn uống màu đỏ, nâu đen để dễ theo dõi dấu hiệu xuất huyết"),
            eatFoodIDs = listOf("chao", "nuoc-ep", "dua-hau", "canh-chua"), avoidFoodIDs = listOf("nuoc-ngot", "ca-phe-sua"),
            otcMedicines = listOf("Chỉ dùng paracetamol để hạ sốt", "KHÔNG tự dùng ibuprofen, aspirin hay thuốc giảm đau chống viêm khác — có thể làm tăng nguy cơ chảy máu", "Dung dịch bù nước điện giải (oresol), pha đúng hướng dẫn"),
            homeRemedies = listOf("Chườm ấm, lau người bằng nước ấm khi sốt"),
            seeDoctorIf = listOf("Đau bụng, nôn nhiều, chảy máu cam/chân răng, nốt xuất huyết — đi cấp cứu ngay", "Li bì, vật vã, tay chân lạnh", "Đặc biệt theo dõi kỹ ngày thứ 3–7 khi bắt đầu hết sốt")
        ),
        Condition(
            id = "sore-throat", name = "Viêm họng",
            summary = "Thường do virus; một số trường hợp do vi khuẩn cần bác sĩ kê kháng sinh.",
            symptoms = setOf(Symptom.soreThroat, Symptom.fever, Symptom.cough, Symptom.headache),
            required = setOf(Symptom.soreThroat), specialty = "Tai Mũi Họng", minimumLevel = CareLevel.selfCare,
            selfCare = listOf("Súc họng nước muối ấm nhiều lần trong ngày", "Uống nước ấm, nói ít", "Tránh khói thuốc, đồ uống lạnh"),
            eatFoodIDs = listOf("chao", "pho-ga"), avoidFoodIDs = listOf("kem", "nuoc-ngot", "cha-gio"),
            otcMedicines = listOf("Thuốc giảm đau, hạ sốt chứa paracetamol", "Viên ngậm giảm đau họng"),
            homeRemedies = listOf("Mật ong pha nước ấm (không dùng cho trẻ dưới 1 tuổi)", "Trà gừng ấm"),
            seeDoctorIf = listOf("Sốt cao, có mủ trắng ở họng, nổi hạch cổ — có thể do vi khuẩn", "Khó nuốt, khó thở, chảy nước dãi", "Không đỡ sau 1 tuần", "Không tự mua kháng sinh — chỉ dùng khi bác sĩ kê")
        ),
        Condition(
            id = "bronchitis", name = "Viêm phế quản",
            summary = "Viêm đường thở, ho kéo dài có thể kèm đờm.",
            symptoms = setOf(Symptom.cough, Symptom.fever, Symptom.fatigue, Symptom.shortnessOfBreath, Symptom.soreThroat),
            required = setOf(Symptom.cough), specialty = "Hô hấp", minimumLevel = CareLevel.selfCare,
            selfCare = listOf("Uống nhiều nước ấm để loãng đờm", "Nghỉ ngơi, tránh khói thuốc và bụi", "Giữ ấm cổ ngực"),
            eatFoodIDs = listOf("chao", "pho-ga", "cam"), avoidFoodIDs = listOf("kem", "nuoc-ngot"),
            otcMedicines = listOf("Paracetamol khi sốt", "Thuốc long đờm — hỏi dược sĩ trước khi dùng"),
            homeRemedies = listOf("Mật ong pha nước ấm (không dùng cho trẻ dưới 1 tuổi)", "Hít hơi nước ấm"),
            seeDoctorIf = listOf("Ho trên 3 tuần", "Khó thở, thở khò khè, đau ngực", "Ho ra máu, sốt cao")
        ),
        Condition(
            id = "gastroenteritis", name = "Viêm dạ dày ruột / ngộ độc thực phẩm",
            summary = "Do virus, vi khuẩn hoặc thức ăn nhiễm bẩn. Nguy cơ chính là mất nước.",
            symptoms = setOf(Symptom.diarrhea, Symptom.nausea, Symptom.abdominalPain, Symptom.fever, Symptom.fatigue),
            required = setOf(), specialty = "Tiêu hóa hoặc Nội tổng quát", minimumLevel = CareLevel.selfCare,
            selfCare = listOf("Bù nước liên tục bằng oresol, uống từng ngụm nhỏ", "Ăn nhẹ, mềm, chia nhiều bữa khi đỡ nôn", "Rửa tay kỹ, ăn chín uống sôi"),
            eatFoodIDs = listOf("chao", "com-trang", "chuoi"), avoidFoodIDs = listOf("sua-tuoi", "ga-ran", "nuoc-ngot", "ca-phe-sua"),
            otcMedicines = listOf("Dung dịch bù nước điện giải (oresol), pha đúng hướng dẫn trên gói", "Không tự dùng thuốc cầm tiêu chảy cho trẻ em hoặc khi phân có máu, sốt cao"),
            homeRemedies = listOf("Nước cháo loãng", "Trà gừng ấm có thể giúp giảm buồn nôn"),
            seeDoctorIf = listOf("Phân có máu, sốt cao", "Nôn liên tục không uống được", "Dấu hiệu mất nước: ít tiểu, khát nhiều, mệt lả", "Tiêu chảy trên 3 ngày")
        ),
        Condition(
            id = "reflux", name = "Trào ngược dạ dày / viêm dạ dày",
            summary = "Axit dạ dày gây nóng rát thượng vị, ợ chua, đầy bụng.",
            symptoms = setOf(Symptom.heartburn, Symptom.nausea, Symptom.abdominalPain, Symptom.chestPain),
            required = setOf(Symptom.heartburn), specialty = "Tiêu hóa", minimumLevel = CareLevel.selfCare,
            selfCare = listOf("Ăn bữa nhỏ, ăn chậm, không ăn quá no", "Không nằm ngay trong 2–3 giờ sau ăn", "Kê cao đầu giường", "Hạn chế rượu bia, thuốc lá, đồ cay chua"),
            eatFoodIDs = listOf("chao", "chuoi", "du-du", "com-trang"), avoidFoodIDs = listOf("ca-phe-sua", "nuoc-ngot", "ga-ran", "khoai-tay-chien", "bia"),
            otcMedicines = listOf("Thuốc trung hòa axit dạ dày (antacid) — hỏi dược sĩ"),
            homeRemedies = listOf("Trà gừng ấm có thể giảm buồn nôn", "Nghệ pha mật ong (người đang dùng thuốc chống đông nên hỏi bác sĩ)"),
            seeDoctorIf = listOf("Đau kèm sụt cân, khó nuốt, nôn ra máu, phân đen", "Trên 40 tuổi mới bị lần đầu", "Dùng thuốc trên 2 tuần không đỡ")
        ),
        Condition(
            id = "constipation", name = "Táo bón",
            summary = "Thường do ăn ít chất xơ, uống ít nước, ít vận động.",
            symptoms = setOf(Symptom.constipation, Symptom.abdominalPain),
            required = setOf(Symptom.constipation), specialty = "Tiêu hóa", minimumLevel = CareLevel.selfCare,
            selfCare = listOf("Uống đủ 1,5–2 lít nước mỗi ngày", "Ăn nhiều rau xanh, trái cây", "Vận động, đi bộ mỗi ngày", "Đi vệ sinh vào giờ cố định"),
            eatFoodIDs = listOf("du-du", "rau-xao", "dua-hau", "chuoi"), avoidFoodIDs = listOf("oi", "khoai-tay-chien", "ga-ran"),
            otcMedicines = listOf("Chất xơ bổ sung hoặc thuốc nhuận tràng nhẹ — hỏi dược sĩ, không dùng kéo dài"),
            homeRemedies = listOf("Uống một cốc nước ấm khi mới ngủ dậy"),
            seeDoctorIf = listOf("Có máu trong phân, sụt cân", "Táo bón xen kẽ tiêu chảy kéo dài", "Đau bụng nhiều, chướng bụng, không trung tiện được")
        ),
        Condition(
            id = "headache", name = "Đau đầu do căng thẳng / đau nửa đầu",
            summary = "Thường liên quan căng thẳng, thiếu ngủ, bỏ bữa, nhìn màn hình lâu.",
            symptoms = setOf(Symptom.headache, Symptom.dizziness, Symptom.nausea, Symptom.insomnia, Symptom.fatigue),
            required = setOf(Symptom.headache), specialty = "Thần kinh", minimumLevel = CareLevel.selfCare,
            selfCare = listOf("Nghỉ ở nơi yên tĩnh, ít ánh sáng", "Ngủ đủ, ăn đúng bữa, uống đủ nước", "Giảm thời gian nhìn màn hình, thư giãn cổ vai"),
            eatFoodIDs = listOf("chuoi", "trung-luoc", "dua-hau"), avoidFoodIDs = listOf("ca-phe-sua", "bia"),
            otcMedicines = listOf("Thuốc giảm đau chứa paracetamol — không dùng quá 2–3 ngày/tuần để tránh đau đầu do lạm dụng thuốc"),
            homeRemedies = listOf("Chườm lạnh hoặc ấm vùng trán, gáy", "Xoa bóp nhẹ thái dương, cổ vai"),
            seeDoctorIf = listOf("Đau đầu ngày càng nặng hoặc thay đổi tính chất", "Kèm sốt, nôn vọt, nhìn mờ, yếu tay chân", "Đau đầu sau chấn thương")
        ),
        Condition(
            id = "dehydration", name = "Mất nước / say nắng",
            summary = "Thiếu nước khi trời nóng, vận động nhiều, nôn hoặc tiêu chảy.",
            symptoms = setOf(Symptom.dizziness, Symptom.fatigue, Symptom.headache, Symptom.nausea),
            required = setOf(Symptom.dizziness), specialty = "Nội tổng quát", minimumLevel = CareLevel.selfCare,
            selfCare = listOf("Vào chỗ mát, nới lỏng quần áo", "Uống nước hoặc oresol từng ngụm", "Chườm mát trán, nách, bẹn"),
            eatFoodIDs = listOf("dua-hau", "nuoc-ep", "canh-chua"), avoidFoodIDs = listOf("bia", "ca-phe-sua"),
            otcMedicines = listOf("Dung dịch bù nước điện giải (oresol)"),
            homeRemedies = listOf("Nước dừa hoặc nước pha chút muối và đường"),
            seeDoctorIf = listOf("Lú lẫn, ngất, co giật — cấp cứu ngay", "Sốt cao, da khô nóng", "Không đỡ sau 1 giờ nghỉ và uống nước")
        ),
        Condition(
            id = "allergy", name = "Dị ứng / mày đay",
            summary = "Phản ứng với thức ăn, thuốc, phấn hoa, bụi hoặc côn trùng đốt.",
            symptoms = setOf(Symptom.rash, Symptom.runnyNose),
            required = setOf(Symptom.rash), specialty = "Da liễu hoặc Dị ứng – Miễn dịch", minimumLevel = CareLevel.selfCare,
            selfCare = listOf("Tránh tác nhân nghi ngờ (món ăn, thuốc mới dùng)", "Tắm nước mát, mặc đồ thoáng", "Không gãi mạnh"),
            eatFoodIDs = listOf("rau-xao", "com-trang"), avoidFoodIDs = listOf("sushi", "bia"),
            otcMedicines = listOf("Thuốc kháng histamine chống dị ứng — hỏi dược sĩ, một số loại gây buồn ngủ"),
            homeRemedies = listOf("Chườm mát vùng ngứa"),
            seeDoctorIf = listOf("Sưng môi, lưỡi, mặt hoặc khó thở — cấp cứu ngay", "Ban lan rộng, kèm sốt", "Nổi mày đay trên 6 tuần")
        ),
        Condition(
            id = "uti", name = "Nhiễm trùng đường tiết niệu",
            summary = "Thường gặp ở nữ; cần bác sĩ khám và kê thuốc phù hợp.",
            symptoms = setOf(Symptom.painfulUrination, Symptom.abdominalPain, Symptom.fever, Symptom.backPain),
            required = setOf(Symptom.painfulUrination), specialty = "Thận – Tiết niệu (nữ có thể khám Phụ khoa)", minimumLevel = CareLevel.seeDoctor,
            selfCare = listOf("Uống nhiều nước", "Không nhịn tiểu", "Vệ sinh đúng cách từ trước ra sau"),
            eatFoodIDs = listOf("dua-hau", "nuoc-ep"), avoidFoodIDs = listOf("ca-phe-sua", "bia", "nuoc-ngot"),
            otcMedicines = listOf("Không tự dùng kháng sinh — bác sĩ sẽ kê loại và thời gian phù hợp"),
            homeRemedies = listOf(),
            seeDoctorIf = listOf("Sốt, rét run, đau hông lưng — có thể nhiễm trùng thận, khám ngay", "Đang mang thai", "Tiểu ra máu")
        ),
        Condition(
            id = "muscle-strain", name = "Căng cơ / đau lưng cơ học",
            summary = "Do sai tư thế, ngồi lâu, mang vác nặng hoặc vận động quá sức.",
            symptoms = setOf(Symptom.backPain, Symptom.muscleAche),
            required = setOf(), specialty = "Cơ Xương Khớp hoặc Phục hồi chức năng", minimumLevel = CareLevel.selfCare,
            selfCare = listOf("Vận động nhẹ nhàng, tránh nằm bất động lâu", "Chườm lạnh 1–2 ngày đầu, sau đó chườm ấm", "Ngồi đúng tư thế, nghỉ giải lao khi ngồi lâu"),
            eatFoodIDs = listOf("ca-kho", "sua-tuoi", "rau-xao"), avoidFoodIDs = listOf(),
            otcMedicines = listOf("Thuốc giảm đau chứa paracetamol", "Thuốc giảm đau dạng bôi ngoài da — hỏi dược sĩ"),
            homeRemedies = listOf("Xoa bóp nhẹ, giãn cơ", "Chườm ấm bằng túi chườm (tránh bỏng)"),
            seeDoctorIf = listOf("Tê yếu chân, rối loạn tiểu tiện — khám ngay", "Đau sau ngã hoặc chấn thương", "Kèm sốt, sụt cân", "Không đỡ sau 2 tuần")
        ),
        Condition(
            id = "joint-pain", name = "Đau khớp (thoái hóa, gút…)",
            summary = "Nhiều nguyên nhân; gút thường sưng nóng đỏ đột ngột ở ngón chân cái.",
            symptoms = setOf(Symptom.jointPain, Symptom.muscleAche, Symptom.fever),
            required = setOf(Symptom.jointPain), specialty = "Cơ Xương Khớp", minimumLevel = CareLevel.seeDoctor,
            selfCare = listOf("Nghỉ ngơi khớp đau, kê cao khi sưng", "Giữ cân nặng hợp lý", "Uống đủ nước"),
            eatFoodIDs = listOf("rau-xao", "cam", "dua-hau"), avoidFoodIDs = listOf("bia", "bit-tet", "sushi", "nuoc-ngot"),
            otcMedicines = listOf("Thuốc giảm đau chứa paracetamol"),
            homeRemedies = listOf("Chườm lạnh khi khớp sưng nóng"),
            seeDoctorIf = listOf("Khớp sưng nóng đỏ, sốt", "Đau nhiều khớp, cứng khớp buổi sáng kéo dài", "Đau sau chấn thương")
        ),
        Condition(
            id = "insomnia", name = "Mất ngủ / căng thẳng",
            summary = "Thường liên quan căng thẳng, thói quen ngủ, caffeine.",
            symptoms = setOf(Symptom.insomnia, Symptom.fatigue, Symptom.headache),
            required = setOf(Symptom.insomnia), specialty = "Thần kinh hoặc Tâm lý – Tâm thần", minimumLevel = CareLevel.selfCare,
            selfCare = listOf("Đi ngủ và thức dậy giờ cố định", "Không dùng điện thoại 1 giờ trước khi ngủ", "Không uống cà phê, trà sau 14 giờ", "Vận động ban ngày, thư giãn trước khi ngủ"),
            eatFoodIDs = listOf("chuoi", "sua-tuoi"), avoidFoodIDs = listOf("ca-phe-sua", "tra-sua", "nuoc-ngot", "bia"),
            otcMedicines = listOf("Không tự dùng thuốc ngủ — hỏi bác sĩ"),
            homeRemedies = listOf("Trà hoa cúc hoặc trà tâm sen ấm buổi tối", "Ngâm chân nước ấm"),
            seeDoctorIf = listOf("Mất ngủ trên 3 tuần ảnh hưởng công việc", "Buồn chán kéo dài, mất hứng thú", "Có ý nghĩ tự làm hại bản thân — tìm trợ giúp ngay")
        ),
        Condition(
            id = "anemia", name = "Thiếu máu / mệt mỏi kéo dài",
            summary = "Mệt, chóng mặt kéo dài có thể do thiếu sắt, thiếu ngủ hoặc bệnh khác cần xét nghiệm.",
            symptoms = setOf(Symptom.fatigue, Symptom.dizziness, Symptom.shortnessOfBreath, Symptom.headache),
            required = setOf(Symptom.fatigue), specialty = "Nội tổng quát (xét nghiệm máu)", minimumLevel = CareLevel.selfCare,
            selfCare = listOf("Ngủ đủ 7–8 giờ", "Ăn đủ đạm, thực phẩm giàu sắt", "Ăn kèm trái cây giàu vitamin C để hấp thu sắt tốt hơn"),
            eatFoodIDs = listOf("bit-tet", "trung-luoc", "rau-xao", "cam"), avoidFoodIDs = listOf("tra-sua", "ca-phe-sua"),
            otcMedicines = listOf("Viên sắt chỉ nên dùng khi đã xét nghiệm thiếu sắt — hỏi bác sĩ"),
            homeRemedies = listOf(),
            seeDoctorIf = listOf("Mệt kéo dài trên 2 tuần", "Da xanh, tim đập nhanh, khó thở khi gắng sức", "Sụt cân, sốt kéo dài")
        ),
    
    )
}

data class SymptomCheckInput(
    val symptoms: Set<Symptom> = emptySet(),
    val redFlags: Set<RedFlag> = emptySet(),
    val group: PatientGroup = PatientGroup.adult,
    val duration: SymptomDuration = SymptomDuration.oneToThreeDays,
    val severity: SymptomSeverity = SymptomSeverity.mild,
)

data class ConditionMatch(val condition: Condition, val matched: Int, val score: Double)

data class SymptomAssessment(
    val level: CareLevel,
    val reasons: List<String>,
    val matches: List<ConditionMatch>,
    /** Trẻ dưới 5 tuổi và phụ nữ mang thai: không gợi ý thuốc/thảo dược. */
    val showMedicationAdvice: Boolean,
)

/** Đánh giá mức độ cần đi khám từ triệu chứng (công cụ tham khảo, không phải chẩn đoán). */
object SymptomChecker {
    fun assess(input: SymptomCheckInput): SymptomAssessment {
        var level = CareLevel.selfCare
        val reasons = mutableListOf<String>()
        fun raise(newLevel: CareLevel, reason: String) {
            if (newLevel > level) level = newLevel
            reasons += reason
        }

        if (input.redFlags.isNotEmpty()) {
            raise(CareLevel.emergency, "Có dấu hiệu nguy hiểm: " + RedFlag.entries.filter { it in input.redFlags }.joinToString("; ") { it.title })
        }
        if (Symptom.chestPain in input.symptoms || Symptom.shortnessOfBreath in input.symptoms) {
            raise(CareLevel.urgent, "Đau ngực hoặc khó thở cần được bác sĩ kiểm tra sớm.")
        }
        if (input.severity == SymptomSeverity.severe) raise(CareLevel.urgent, "Triệu chứng ở mức nặng.")
        val feverOrFluidLoss = Symptom.fever in input.symptoms || Symptom.diarrhea in input.symptoms || Symptom.nausea in input.symptoms
        if (input.group.isVulnerable && feverOrFluidLoss) {
            raise(CareLevel.urgent, "${input.group.title} dễ diễn biến nặng khi sốt, nôn hoặc tiêu chảy.")
        }
        if (input.group == PatientGroup.pregnant && Symptom.abdominalPain in input.symptoms) {
            raise(CareLevel.urgent, "Đau bụng khi mang thai cần được bác sĩ sản khoa kiểm tra.")
        }
        if (Symptom.fever in input.symptoms && input.duration >= SymptomDuration.fourToSevenDays) {
            raise(CareLevel.urgent, "Sốt trên 3 ngày cần đi khám (ở Việt Nam cần loại trừ sốt xuất huyết).")
        }
        if (input.duration == SymptomDuration.overOneWeek) {
            raise(CareLevel.seeDoctor, "Triệu chứng kéo dài trên 1 tuần.")
        } else if (input.severity == SymptomSeverity.moderate && input.duration >= SymptomDuration.fourToSevenDays) {
            raise(CareLevel.seeDoctor, "Triệu chứng mức vừa kéo dài nhiều ngày.")
        }

        val matches = match(input.symptoms)
        val top = matches.firstOrNull()
        if (top != null && top.condition.minimumLevel > level) {
            raise(top.condition.minimumLevel, "\"${top.condition.name}\" thường cần bác sĩ khám để xác định và điều trị.")
        }
        if (reasons.isEmpty()) reasons += "Chưa thấy dấu hiệu cần đi khám gấp dựa trên thông tin bạn nhập."

        return SymptomAssessment(
            level = level,
            reasons = reasons,
            matches = matches,
            showMedicationAdvice = input.group != PatientGroup.childUnder5 && input.group != PatientGroup.pregnant,
        )
    }

    /** Xếp hạng các nguyên nhân thường gặp theo mức độ trùng triệu chứng. */
    fun match(selected: Set<Symptom>, limit: Int = 3): List<ConditionMatch> {
        if (selected.isEmpty()) return emptyList()
        return ConditionLibrary.all.mapNotNull { c ->
            if (!selected.containsAll(c.required)) return@mapNotNull null
            val matched = c.symptoms.intersect(selected).size
            if (matched == 0) return@mapNotNull null
            val coverage = matched.toDouble() / c.symptoms.size
            val precision = matched.toDouble() / selected.size
            val score = 0.6 * coverage + 0.4 * precision
            if (score >= 0.25) ConditionMatch(c, matched, score) else null
        }
            .sortedWith(compareByDescending<ConditionMatch> { it.score }.thenBy { it.condition.name })
            .take(limit)
    }
}
