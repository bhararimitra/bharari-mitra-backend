"""Unit tests for notification title classification (English + Marathi)."""

from app.modules.crawlers.classify import classify_notification
from app.modules.jobs.models import NotificationType


def test_english_selection_list_is_merit_or_result():
    assert classify_notification("Final Selection List 2024-25") == NotificationType.MERIT_LIST
    assert classify_notification("Provisional Waiting List") == NotificationType.MERIT_LIST
    assert classify_notification("Exam Result Declared") == NotificationType.RESULT


def test_marathi_selection_and_waiting_lists():
    assert (
        classify_notification(
            "एसआरपीएफ (SRPF) गट २ पुणे - अंतिम निवड यादी आणि अंतिम प्रतीक्षा यादी २०२४-२५"
        )
        == NotificationType.MERIT_LIST
    )
    assert (
        classify_notification(
            "सशस्त्र पोलीस शिपाई भरती २०२४-२५: सुधारित अंतिम निवडसूची व प्रतीक्षासूची"
        )
        == NotificationType.MERIT_LIST
    )
    assert (
        classify_notification("पोलीस आयुक्तालय, नागपूर शहर कारागृह पोलीस भरती तात्पुरती निवड यादी")
        == NotificationType.MERIT_LIST
    )


def test_marathi_selection_cancellation_is_result():
    assert (
        classify_notification(
            "भारएब 2, रारापोबल गट क्र 15 गोंदिया पोलीस भरती मध्ये कागदपत्रे पडताळणी व गैरहजर उमेदवार यांची निवड रद्द बाबत"
        )
        == NotificationType.RESULT
    )


def test_marathi_advertisement_and_extension():
    assert classify_notification("जाहीरात सरळसेवा भरती महाव्यवस्थापक पदे.") == NotificationType.ADVERTISEMENT
    assert (
        classify_notification("जाहीरात क्र.०१/२०१९ सरळसेवा भरती (दि.१८.०२.२०१९ पर्यंत मुदत वाढ)")
        == NotificationType.CORRIGENDUM
    )


def test_marathi_document_verification_notice():
    assert (
        classify_notification(
            "राज्य राखीव पोलीस बल गट क्र.१ पुणे पोलीस शिपाई - कागदपत्र पडताळणी करिता उपस्थित राहणेबाबत"
        )
        == NotificationType.NOTICE
    )


def test_marks_lists_and_answer_key_marathi():
    assert (
        classify_notification("लेखी परीक्षेची अंतिम गुणांची यादी")
        == NotificationType.RESULT
    )
    assert (
        classify_notification("लेखी परीक्षात मिळालेल्या गुणांची तात्पुरती यादी")
        == NotificationType.MERIT_LIST
    )
    assert (
        classify_notification("लेखी परीक्षा तात्पुरती उत्तरतालिका")
        == NotificationType.ANSWER_KEY
    )


def test_appointment_and_exam_notices():
    assert (
        classify_notification("सशस्त्र पोलीस शिपाई पदावर नियुक्‍ती बाबत.")
        == NotificationType.NOTICE
    )
    assert classify_notification("संगणक पर्यवेक्षक पदाची परीक्षा.") == NotificationType.NOTICE


def test_application_call_stays_job():
    assert (
        classify_notification(
            "सेवानिवृत्त वर्ग -१ दर्जाच्या अधिकाऱ्यांची करार पद्धतीने नेमणूक करण्याकरिता अर्ज मागविणेबाबत"
        )
        == NotificationType.JOB
    )


def test_plain_recruitment_defaults_to_job():
    assert (
        classify_notification("महाराष्ट्र पोलीस शिपाई भरती २०२५ — अर्ज सुरु")
        == NotificationType.JOB
    )


def test_english_hall_ticket_and_answer_key():
    assert classify_notification("Download Hall Ticket") == NotificationType.HALL_TICKET
    assert classify_notification("Answer Key Released") == NotificationType.ANSWER_KEY
