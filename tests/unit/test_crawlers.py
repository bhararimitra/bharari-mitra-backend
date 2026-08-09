"""Unit tests for all four crawlers — parse logic only, no network calls."""

import pytest
from app.modules.crawlers.mpsc import MpscCrawler
from app.modules.crawlers.police import PoliceCrawler
from app.modules.crawlers.nhm import NhmCrawler
from app.modules.crawlers.msrtc import MsrtcCrawler
from app.modules.crawlers.base import RawJobData


class _DummyLogger:
    def info(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass


def _make(cls):
    crawler = object.__new__(cls)
    crawler._logger = _DummyLogger()
    return crawler


class TestMpscCrawler:
    SAMPLE_HTML = """
    <html><body>
    <table class="table dataTable">
      <tr><th>Sr</th><th>Advt. No.</th><th>Subject</th><th>Date of Publication</th><th>File</th></tr>
      <tr>
        <td>1</td>
        <td>017/2026</td>
        <td>Maharashtra Group-C Services Combine Preliminary Examination 2026</td>
        <td>01-08-2026</td>
        <td><a href="#"><img alt="pdficon"/></a></td>
      </tr>
      <tr>
        <td>2</td>
        <td>015/2026</td>
        <td>Bailiff cum Clerk Competitive Examination 2026</td>
        <td>27-07-2026</td>
        <td><a href="#"><img alt="pdficon"/></a></td>
      </tr>
    </table>
    </body></html>
    """

    @pytest.mark.asyncio
    async def test_parse_returns_jobs(self):
        crawler = _make(MpscCrawler)
        jobs = await crawler.parse(self.SAMPLE_HTML)
        assert len(jobs) == 2

    @pytest.mark.asyncio
    async def test_parse_extracts_title(self):
        crawler = _make(MpscCrawler)
        jobs = await crawler.parse(self.SAMPLE_HTML)
        assert "Group-C" in jobs[0].title
        assert "017/2026" in jobs[0].title

    @pytest.mark.asyncio
    async def test_parse_extracts_published_date(self):
        crawler = _make(MpscCrawler)
        jobs = await crawler.parse(self.SAMPLE_HTML)
        assert jobs[0].published_at == "01/08/2026"

    @pytest.mark.asyncio
    async def test_parse_builds_stable_url(self):
        crawler = _make(MpscCrawler)
        jobs = await crawler.parse(self.SAMPLE_HTML)
        assert "mpsc.gov.in/adv_notification/8" in jobs[0].notification_url
        assert "advt=017" in jobs[0].notification_url

    def test_normalize_extracts_year(self):
        crawler = _make(MpscCrawler)
        raw = RawJobData(
            title="MPSC State Services 2025",
            notification_url="https://mpsc.gov.in/n/1",
            organization_slug="mpsc",
            organization_name="MPSC",
            organization_url="https://mpsc.gov.in",
        )
        result = crawler.normalize(raw)
        assert result.published_at == "01/01/2025"


class TestPoliceCrawler:
    SAMPLE_HTML = """
    <html><body>
      <h4>Police Constable Recruitment 2025 Nagpur</h4>
      <a href="/uploads/police_recruitment/constable2025.pdf">Download</a>
      <h4>Sub-Inspector Recruitment 2025 Pune</h4>
      <a href="/uploads/police_recruitment/si2025.pdf">Download</a>
      <h4>Noise Medal Notice Should Skip</h4>
      <a href="/uploads/external_links/policeMedal.pdf">Medal</a>
    </body></html>
    """

    @pytest.mark.asyncio
    async def test_parse_returns_jobs(self):
        crawler = _make(PoliceCrawler)
        jobs = await crawler.parse(self.SAMPLE_HTML)
        assert len(jobs) == 2

    @pytest.mark.asyncio
    async def test_constable_dept_detected(self):
        crawler = _make(PoliceCrawler)
        jobs = await crawler.parse(self.SAMPLE_HTML)
        assert jobs[0].department_slug == "police-constable"

    @pytest.mark.asyncio
    async def test_si_dept_detected(self):
        crawler = _make(PoliceCrawler)
        jobs = await crawler.parse(self.SAMPLE_HTML)
        assert jobs[1].department_slug == "police-sub-inspector"

    @pytest.mark.asyncio
    async def test_pdf_url_set(self):
        crawler = _make(PoliceCrawler)
        jobs = await crawler.parse(self.SAMPLE_HTML)
        assert jobs[0].pdf_url.endswith("constable2025.pdf")

    @pytest.mark.asyncio
    async def test_organization_slug_is_police(self):
        crawler = _make(PoliceCrawler)
        jobs = await crawler.parse(self.SAMPLE_HTML)
        assert all(j.organization_slug == "maharashtra-police" for j in jobs)


class TestNhmCrawler:
    SAMPLE_HTML = """
    <html><body>
    <table>
      <tr><th>Sr</th><th>Title</th><th>Description</th><th>Start Date</th><th>End Date</th><th>File</th></tr>
      <tr>
        <td>1</td>
        <td>Staff Nurse Recruitment 2025 – 880 Posts</td>
        <td>Staff Nurse Recruitment 2025 – 880 Posts</td>
        <td>01/06/2025</td>
        <td>10/07/2025</td>
        <td><a href="/files/staff_nurse_2025.pdf">View</a></td>
      </tr>
      <tr>
        <td>2</td>
        <td>Medical Officer Recruitment 2025</td>
        <td>Medical Officer Recruitment 2025</td>
        <td>01/07/2025</td>
        <td>20/08/2025</td>
        <td><a href="/files/medical_officer_2025.pdf">View</a></td>
      </tr>
    </table>
    </body></html>
    """

    @pytest.mark.asyncio
    async def test_parse_returns_jobs(self):
        crawler = _make(NhmCrawler)
        jobs = await crawler.parse(self.SAMPLE_HTML)
        assert len(jobs) == 2

    @pytest.mark.asyncio
    async def test_nurse_qualification_detected(self):
        crawler = _make(NhmCrawler)
        jobs = await crawler.parse(self.SAMPLE_HTML)
        assert jobs[0].qualification_slug == "gnm-bsc-nursing"

    @pytest.mark.asyncio
    async def test_medical_officer_detected(self):
        crawler = _make(NhmCrawler)
        jobs = await crawler.parse(self.SAMPLE_HTML)
        assert jobs[1].department_slug == "nhm-medical-officer"

    @pytest.mark.asyncio
    async def test_dates_extracted(self):
        crawler = _make(NhmCrawler)
        jobs = await crawler.parse(self.SAMPLE_HTML)
        assert jobs[0].published_at == "01/06/2025"
        assert jobs[0].last_date == "10/07/2025"

    @pytest.mark.asyncio
    async def test_pdf_url_extracted(self):
        crawler = _make(NhmCrawler)
        jobs = await crawler.parse(self.SAMPLE_HTML)
        assert jobs[0].pdf_url is not None
        assert ".pdf" in jobs[0].pdf_url


class TestMsrtcCrawler:
    SAMPLE_HTML = """
    <html><body>
    <table>
      <tr>
        <td>MSRTC Driver Recruitment 2025 – 3000 Posts</td>
        <td><a href="/jobs/driver2025.pdf">Read Advertisement</a></td>
      </tr>
      <tr>
        <td>MSRTC Conductor Recruitment 2025 – 2765 Posts</td>
        <td><a href="/jobs/conductor2025.pdf">Read Advertisement</a></td>
      </tr>
    </table>
    </body></html>
    """

    @pytest.mark.asyncio
    async def test_parse_returns_jobs(self):
        crawler = _make(MsrtcCrawler)
        jobs = await crawler.parse(self.SAMPLE_HTML)
        assert len(jobs) == 2

    @pytest.mark.asyncio
    async def test_driver_dept_detected(self):
        crawler = _make(MsrtcCrawler)
        jobs = await crawler.parse(self.SAMPLE_HTML)
        assert jobs[0].department_slug == "msrtc-driver"

    @pytest.mark.asyncio
    async def test_conductor_dept_detected(self):
        crawler = _make(MsrtcCrawler)
        jobs = await crawler.parse(self.SAMPLE_HTML)
        assert jobs[1].department_slug == "msrtc-conductor"

    def test_normalize_strips_msrtc_prefix(self):
        crawler = _make(MsrtcCrawler)
        raw = RawJobData(
            title="MSRTC - Driver Recruitment 2025",
            notification_url="https://msrtc.maharashtra.gov.in/jobs/1",
            organization_slug="msrtc",
            organization_name="MSRTC",
            organization_url="https://msrtc.maharashtra.gov.in",
        )
        result = crawler.normalize(raw)
        assert not result.title.startswith("MSRTC")

    @pytest.mark.asyncio
    async def test_organization_slug_is_msrtc(self):
        crawler = _make(MsrtcCrawler)
        jobs = await crawler.parse(self.SAMPLE_HTML)
        assert all(j.organization_slug == "msrtc" for j in jobs)
