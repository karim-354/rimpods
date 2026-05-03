"""
fingerprint_check.py
Anti-AI Fingerprint Verifier untuk konten berbahasa Indonesia.

24 pola "robotik" yang dideteksi:
1. Konektor formal berlebihan: "namun demikian", "dengan demikian", "oleh karena itu"
2. Pembuka kalimat formal: "adapun", "sehubungan dengan", "perlu diketahui"
3. Filler korporat: "pada dasarnya", "secara fundamental", "dalam rangka", "demi mencapai", "guna"
4. Frasa "yang mana" berlebihan (>1x per 100 kata)
5. Pengulangan "merupakan" / "adalah" berlebihan
6. Pengulangan "hal ini" / "hal tersebut"
7. Negasi tidak natural: "tidak tidak", triple-negation, "bukan tidak"
8. Tanpa kontraksi/slang khas obrolan ("ga", "ngga", "udah", "aja")
9. Tanpa partikel khas Indonesia: sih, deh, kok, loh, dong, yah, nih, kan
10. Future tense "akan" berlebihan (>3x per paragraf)
11. Pertanyaan retoris berlebihan (>2 berturut-turut "Bukankah...?")
12. Em-dash / tanda baca eksotis berlebihan
13. Huruf kapital random (CAPS LOCK panjang)
14. Tanpa tanda tanya sama sekali (no engagement)
15. Tanpa tanda seru sama sekali (no energy)
16. Rata-rata kalimat > 25 kata
17. Variansi panjang kalimat sangat rendah (kalimat seragam)
18. Bullet-style dalam prosa mengalir
19. Tidak ada kata ganti orang pertama/kedua (aku, gue, kamu, lo, kita)
20. Penutup terlalu formal ("demikian", "sekian dan terima kasih", "atas perhatiannya")
21. Aksen/tanda baca hilang antar klausa panjang
22. Repetisi struktur paralel kaku
23. Diksi formal akademik di konteks marketing
24. Tidak ada angka/spesifik konkret (bahasa terlalu umum)

Aturan:
- Skor 0-100. Default 100, kurangi tiap pelanggaran.
- Skor lolos minimum: 55.
- Jika skor < 55 dan auto_fix=True, sisipkan 2-3 ekspresi natural otomatis.
- Frasa korporat sangat formal: blokir publish (return blocked=True).
"""

import re
import statistics
from typing import Dict, List, Tuple

# Pola
ROBOTIC_PATTERNS = {
    "konektor_formal": [
        r"\bnamun demikian\b",
        r"\bdengan demikian\b",
        r"\boleh karena itu\b",
        r"\bsehubungan dengan\b",
    ],
    "pembuka_formal": [
        r"(?:^|\n)\s*adapun\b",
        r"(?:^|\n)\s*perlu diketahui\b",
    ],
    "filler_korporat": [
        r"\bpada dasarnya\b",
        r"\bsecara fundamental\b",
        r"\bdalam rangka\b",
        r"\bdemi mencapai\b",
        r"\bguna meningkatkan\b",
        r"\bbersinergi\b",
        r"\bmengoptimalkan\b",
    ],
    "yang_mana": [r"\byang mana\b"],
    "merupakan_repeat": [r"\bmerupakan\b"],
    "hal_ini_repeat": [r"\bhal ini\b", r"\bhal tersebut\b"],
    "triple_negation": [
        r"\bbukan tidak\b",
        r"\btidak tidak\b",
        r"\btidaklah bukan\b",
    ],
    "akan_overuse": [r"\bakan\b"],
    "rhetorical_overuse": [r"\bbukankah\b"],
    "em_dash": [r"—"],
    "penutup_formal": [
        r"\bdemikian\s+(?:saja|kami sampaikan|adanya)\b",
        r"\bsekian dan terima kasih\b",
        r"\batas perhatiannya?\b",
    ],
    "diksi_akademik": [
        r"\beksistensi\b",
        r"\bkomprehensif\b",
        r"\bsignifikan\b",
        r"\bsubstansial\b",
        r"\bimplementasi\b",
        r"\bproblematika\b",
    ],
}

# Penanda manusiawi
HUMAN_MARKERS = [
    r"\bsih\b", r"\bdeh\b", r"\bkok\b", r"\bloh\b", r"\bdong\b",
    r"\byah\b", r"\bnih\b", r"\bkan\b", r"\bdoang\b",
    r"\bga\b", r"\bnggak\b", r"\bngga\b", r"\budah\b", r"\baja\b",
    r"\bgue\b", r"\baku\b", r"\bkamu\b", r"\blo\b", r"\bkita\b", r"\bkalian\b",
]

# Frasa blokir keras (langsung blocked)
HARD_BLOCK_PHRASES = [
    r"sehubungan dengan hal tersebut",
    r"demikian kami sampaikan,? atas perhatiannya",
    r"dalam rangka mengoptimalkan sinergi",
]

# Ekspresi natural untuk auto-injection
NATURAL_INJECTIONS = [
    "Beneran deh, ",
    "Jujur aja, ",
    "Eh tapi ya, ",
    "Nih ya, ",
    "Yang penting, ",
    "Soalnya, ",
]


def _split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def _count_matches(patterns: List[str], text: str) -> int:
    n = 0
    for p in patterns:
        n += len(re.findall(p, text, flags=re.IGNORECASE))
    return n


def check(text: str, auto_fix: bool = False) -> Dict:
    """
    Periksa fingerprint anti-AI pada teks Indonesia.
    Returns: dict berisi score, passed, blocked, issues, suggestions, fixed_text.
    """
    if not text or not text.strip():
        return {
            "score": 0,
            "passed": False,
            "blocked": True,
            "reason": "Teks kosong",
            "issues": [],
            "suggestions": [],
            "fixed_text": text,
        }

    issues: List[Tuple[str, int, int]] = []  # (label, count, penalty)
    score = 100

    # 1. Hard block check
    for hb in HARD_BLOCK_PHRASES:
        if re.search(hb, text, flags=re.IGNORECASE):
            return {
                "score": 10,
                "passed": False,
                "blocked": True,
                "reason": f"Frasa korporat sangat formal terdeteksi: '{hb}'",
                "issues": [("hard_block", 1, 90)],
                "suggestions": ["Hapus frasa formal korporat dan tulis ulang dengan gaya santai."],
                "fixed_text": text,
            }

    # 2. Pattern penalties
    penalty_map = {
        "konektor_formal": 6,
        "pembuka_formal": 5,
        "filler_korporat": 7,
        "yang_mana": 3,
        "triple_negation": 5,
        "rhetorical_overuse": 4,
        "em_dash": 2,
        "penutup_formal": 8,
        "diksi_akademik": 3,
    }
    for label, patterns in ROBOTIC_PATTERNS.items():
        count = _count_matches(patterns, text)
        if label == "merupakan_repeat" and count > 2:
            penalty = (count - 2) * 4
            issues.append((label, count, penalty))
            score -= penalty
        elif label == "hal_ini_repeat" and count > 2:
            penalty = (count - 2) * 3
            issues.append((label, count, penalty))
            score -= penalty
        elif label == "akan_overuse" and count > 5:
            penalty = (count - 5) * 2
            issues.append((label, count, penalty))
            score -= penalty
        elif label == "rhetorical_overuse" and count >= 2:
            penalty = count * penalty_map.get(label, 3)
            issues.append((label, count, penalty))
            score -= penalty
        elif label == "em_dash" and count > 2:
            penalty = (count - 2) * penalty_map.get(label, 2)
            issues.append((label, count, penalty))
            score -= penalty
        elif label == "yang_mana" and count >= 2:
            penalty = count * penalty_map.get(label, 3)
            issues.append((label, count, penalty))
            score -= penalty
        elif label not in ("merupakan_repeat", "hal_ini_repeat", "akan_overuse",
                           "rhetorical_overuse", "em_dash", "yang_mana") and count > 0:
            penalty = count * penalty_map.get(label, 4)
            issues.append((label, count, penalty))
            score -= penalty

    # 3. Sentence stats
    sentences = _split_sentences(text)
    word_counts = [len(s.split()) for s in sentences] or [0]
    avg_len = sum(word_counts) / max(1, len(word_counts))
    if avg_len > 25:
        penalty = int((avg_len - 25) * 1.5)
        issues.append(("kalimat_panjang", int(avg_len), penalty))
        score -= penalty

    if len(word_counts) >= 3:
        try:
            stdev = statistics.stdev(word_counts)
        except statistics.StatisticsError:
            stdev = 0
        if stdev < 2.5 and avg_len > 8:
            issues.append(("kalimat_seragam", int(stdev * 10), 6))
            score -= 6

    # 4. Engagement signals
    if "?" not in text and len(text) > 200:
        issues.append(("tanpa_tanda_tanya", 0, 5))
        score -= 5
    if "!" not in text and len(text) > 200:
        issues.append(("tanpa_tanda_seru", 0, 4))
        score -= 4

    # 5. Caps lock check
    caps_runs = re.findall(r"\b[A-Z]{5,}\b", text)
    if len(caps_runs) > 2:
        penalty = (len(caps_runs) - 2) * 3
        issues.append(("caps_berlebihan", len(caps_runs), penalty))
        score -= penalty

    # 6. Human markers presence
    human_count = _count_matches(HUMAN_MARKERS, text)
    if human_count == 0 and len(text) > 150:
        issues.append(("tanpa_partikel_natural", 0, 12))
        score -= 12
    elif human_count < 2 and len(text) > 300:
        issues.append(("partikel_natural_minim", human_count, 6))
        score -= 6

    # 7. Specific numbers/concrete
    if not re.search(r"\d", text) and len(text) > 200:
        issues.append(("tanpa_angka_konkret", 0, 3))
        score -= 3

    score = max(0, min(100, score))
    passed = score >= 55

    suggestions: List[str] = []
    for label, count, penalty in issues:
        if label == "konektor_formal":
            suggestions.append("Ganti 'namun demikian / oleh karena itu' dengan 'tapi' atau 'jadinya'.")
        elif label == "filler_korporat":
            suggestions.append("Buang filler korporat ('pada dasarnya', 'dalam rangka'). Langsung ke poin.")
        elif label == "merupakan_repeat":
            suggestions.append("Variasikan 'merupakan' dengan 'adalah', 'jadi', atau hilangkan saja.")
        elif label == "tanpa_partikel_natural":
            suggestions.append("Tambahin partikel obrolan: 'sih', 'kok', 'deh', 'yah', 'dong'.")
        elif label == "kalimat_panjang":
            suggestions.append("Pecah kalimat panjang. Target rata-rata 12-18 kata.")
        elif label == "penutup_formal":
            suggestions.append("Ganti penutup formal ('demikian, atas perhatiannya') dengan ajakan santai.")
        elif label == "tanpa_tanda_tanya":
            suggestions.append("Selipkan satu pertanyaan ke pembaca biar engaging.")

    # 8. Auto-fix injection
    fixed_text = text
    if auto_fix and not passed and not _is_blocked(issues):
        fixed_text = _inject_natural(text)

    return {
        "score": score,
        "passed": passed,
        "blocked": False,
        "avg_sentence_words": round(avg_len, 1),
        "human_marker_count": human_count,
        "issues": [{"label": l, "count": c, "penalty": p} for l, c, p in issues],
        "suggestions": list(dict.fromkeys(suggestions)),
        "fixed_text": fixed_text,
    }


def _is_blocked(issues) -> bool:
    return any(l == "hard_block" for l, _, _ in issues)


def _inject_natural(text: str) -> str:
    """Sisipkan 2-3 ekspresi natural di posisi acak antar paragraf/kalimat."""
    sentences = _split_sentences(text)
    if len(sentences) < 3:
        return text
    # Pilih 2-3 titik injeksi
    import random
    n_inject = min(3, max(2, len(sentences) // 4))
    positions = sorted(random.sample(range(1, len(sentences)), min(n_inject, len(sentences) - 1)))
    injections = random.sample(NATURAL_INJECTIONS, min(n_inject, len(NATURAL_INJECTIONS)))

    out = []
    for i, s in enumerate(sentences):
        if positions and i == positions[0] and injections:
            inj = injections.pop(0)
            # Lowercase first char of original sentence after injection
            s = inj + s[0].lower() + s[1:] if len(s) > 1 else inj + s
            positions.pop(0)
        out.append(s)
    return " ".join(out)


def verify_before_publish(text: str, auto_fix: bool = True) -> Dict:
    """
    Pre-publish gate. Jalankan sebelum konten dipublikasikan.
    Jika tidak lolos dan tidak bisa diperbaiki otomatis, return blocked=True.
    """
    result = check(text, auto_fix=auto_fix)
    if result.get("blocked"):
        result["publish_allowed"] = False
        return result

    if not result["passed"] and auto_fix:
        # Re-check fixed_text
        recheck = check(result["fixed_text"], auto_fix=False)
        if recheck["passed"]:
            result["publish_allowed"] = True
            result["score"] = recheck["score"]
            result["used_auto_fix"] = True
        else:
            result["publish_allowed"] = False
            result["used_auto_fix"] = True
    else:
        result["publish_allowed"] = result["passed"]

    return result


if __name__ == "__main__":
    import json
    import sys

    sample_robotic = (
        "Pada dasarnya, produk ini merupakan solusi komprehensif. "
        "Oleh karena itu, dengan demikian kami sampaikan bahwa hal ini akan "
        "mengoptimalkan eksistensi terumbu karang Anda. Sehubungan dengan hal tersebut, "
        "demi mencapai hasil substansial, perlu diketahui bahwa hal ini merupakan investasi. "
        "Demikian, atas perhatiannya kami ucapkan terima kasih."
    )
    sample_natural = (
        "Jujur ya, rotifer Rimpods ini bikin coral mekar gila-gilaan kok! "
        "Sekali tuang aja udah keliatan bedanya dalam 3 hari. "
        "Ada yang nanya, takarannya gimana sih? Gampang banget. "
        "Tank 400 liter cukup 2 liter rotifer, ditambah phyto sebotol. "
        "Worth it nggak? Lihat aja review 891 rating bintang 4.9 di Tokopedia."
    )

    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            txt = f.read()
        print(json.dumps(verify_before_publish(txt), ensure_ascii=False, indent=2))
    else:
        print("=== ROBOTIC SAMPLE ===")
        print(json.dumps(verify_before_publish(sample_robotic), ensure_ascii=False, indent=2))
        print("\n=== NATURAL SAMPLE ===")
        print(json.dumps(verify_before_publish(sample_natural), ensure_ascii=False, indent=2))
