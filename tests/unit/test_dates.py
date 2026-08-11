from app.modules.crawlers.dates import dates_in_text, infer_last_date


def test_two_dates_use_the_later_deadline():
    assert infer_last_date("Advertisement 27/12/2024 09/01/2025") == "09/01/2025"


def test_explicit_last_date_hint():
    assert infer_last_date("Staff Nurse last date 14/08/2026") == "14/08/2026"


def test_single_unlabelled_date_is_not_a_deadline():
    assert infer_last_date("017/2026 Maharashtra Group C Services 25/06/2026") is None


def test_devanagari_digits():
    assert infer_last_date("अंतिम दिनांक १४/०८/२०२६") == "14/08/2026"


def test_english_month_range():
    assert infer_last_date("Apply from 01 Jul 2026 to 20 Aug 2026") == "20/08/2026"


def test_dates_in_text_dedupes():
    found = dates_in_text("01/06/2025 and 01/06/2025 and 10/07/2025")
    assert found == ["01/06/2025", "10/07/2025"]
