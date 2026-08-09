"""Crawlers module — all government website crawlers for BharariMitra.

Available crawlers:
    MpscCrawler    — mpsc.gov.in
    PoliceCrawler  — mahapolice.gov.in
    NhmCrawler     — nhm.maharashtra.gov.in
    MsrtcCrawler   — msrtc.maharashtra.gov.in
    MjpCrawler     — mjp.maharashtra.gov.in
    SscCrawler     — ssc.gov.in (central)
    UpscCrawler    — upsc.gov.in (central)
    IbpsCrawler    — ibps.in (central / banking)

To add a new crawler:
    1. Create a new file, e.g. app/modules/crawlers/zp.py
    2. Subclass BaseCrawler, implement fetch() and parse()
    3. Add the class path to scheduler.py CRAWLER_PATHS
    Done — nothing else changes.
"""

from app.modules.crawlers.base import BaseCrawler, RawJobData
from app.modules.crawlers.mpsc import MpscCrawler
from app.modules.crawlers.police import PoliceCrawler
from app.modules.crawlers.nhm import NhmCrawler
from app.modules.crawlers.msrtc import MsrtcCrawler
from app.modules.crawlers.mjp import MjpCrawler
from app.modules.crawlers.pavitra import PavitraCrawler
from app.modules.crawlers.dmer import DmerCrawler
from app.modules.crawlers.mo_recruitment import MoRecruitmentCrawler
from app.modules.crawlers.wcd import WcdCrawler
from app.modules.crawlers.maharashtra_gov import MaharashtraGovCrawler
from app.modules.crawlers.ssc import SscCrawler
from app.modules.crawlers.upsc import UpscCrawler
from app.modules.crawlers.ibps import IbpsCrawler

__all__ = [
    "BaseCrawler",
    "RawJobData",
    "MpscCrawler",
    "PoliceCrawler",
    "NhmCrawler",
    "MsrtcCrawler",
    "MjpCrawler",
    "PavitraCrawler",
    "DmerCrawler",
    "MoRecruitmentCrawler",
    "WcdCrawler",
    "MaharashtraGovCrawler",
    "SscCrawler",
    "UpscCrawler",
    "IbpsCrawler",
]
