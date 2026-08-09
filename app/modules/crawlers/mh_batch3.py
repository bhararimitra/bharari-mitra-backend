"""Maharashtra remaining departments / universities / municipal (batch 3)."""

from __future__ import annotations

from app.modules.crawlers.html_listing import HtmlListingCrawler


class MahaForestCrawler(HtmlListingCrawler):
    name = "mahaforest_crawler"
    source_url = "https://mahaforest.gov.in/Contentpage/index/RlBNc3Z1dFBTZnhTWlZFPQ%3D%3D"
    extra_pages = (
        "https://mahaforest.gov.in/",
        "https://mahaforest.gov.in/index.php/news",
    )
    base_url = "https://mahaforest.gov.in"
    apply_url = "https://mahaforest.gov.in/"
    organization_slug = "mahaforest"
    organization_name = "Maharashtra Forest Department"
    department_slug = "forest-recruitment"
    department_name = "Forest Recruitment"
    title_prefix = "MahaForest"
    max_jobs = 50


class AnimalHusbandryCrawler(HtmlListingCrawler):
    name = "animal_husbandry_crawler"
    source_url = "https://dahd.maharashtra.gov.in/en/"
    extra_pages = (
        "https://fisheries.maharashtra.gov.in/",
        "https://dairy.maharashtra.gov.in/",
    )
    base_url = "https://dahd.maharashtra.gov.in"
    apply_url = "https://dahd.maharashtra.gov.in/en/"
    organization_slug = "animal-husbandry-maharashtra"
    organization_name = "Animal Husbandry Dairy Development & Fisheries"
    department_slug = "ahd-recruitment"
    department_name = "AHDF Recruitment"
    title_prefix = "AHDF"
    max_jobs = 40


class HigherEducationCrawler(HtmlListingCrawler):
    name = "higher_education_crawler"
    source_url = "https://htedu.maharashtra.gov.in/Main/"
    extra_pages = ("https://htedu.maharashtra.gov.in/Main/Default",)
    base_url = "https://htedu.maharashtra.gov.in"
    apply_url = "https://htedu.maharashtra.gov.in/Main/"
    organization_slug = "higher-education-maharashtra"
    organization_name = "Higher & Technical Education Maharashtra"
    department_slug = "htedu-recruitment"
    department_name = "HTE Recruitment"
    title_prefix = "HTE MH"
    max_jobs = 40


class DmerOrgCrawler(HtmlListingCrawler):
    """DMER department site (dmer.maharashtra.gov.in) — complements application portal."""

    name = "dmer_org_crawler"
    source_url = "https://dmer.maharashtra.gov.in/"
    base_url = "https://dmer.maharashtra.gov.in"
    apply_url = "https://dmer.maharashtra.gov.in/"
    organization_slug = "dmer-org"
    organization_name = "DMER Maharashtra"
    department_slug = "dmer-notices"
    department_name = "DMER Notices"
    title_prefix = "DMER"
    max_jobs = 40


class MahaSwayamCrawler(HtmlListingCrawler):
    name = "mahaswayam_crawler"
    source_url = "https://www.mahaswayam.gov.in/"
    base_url = "https://www.mahaswayam.gov.in"
    apply_url = "https://www.mahaswayam.gov.in/"
    organization_slug = "mahaswayam"
    organization_name = "MahaSwayam Employment Portal"
    department_slug = "mahaswayam-vacancies"
    department_name = "MahaSwayam Vacancies"
    title_prefix = "MahaSwayam"
    max_jobs = 40


class MahaOnlineCrawler(HtmlListingCrawler):
    name = "mahaonline_crawler"
    source_url = "https://aaplesarkar.mahaonline.gov.in/"
    base_url = "https://aaplesarkar.mahaonline.gov.in"
    apply_url = "https://aaplesarkar.mahaonline.gov.in/"
    organization_slug = "mahaonline"
    organization_name = "MahaOnline / Aaple Sarkar"
    department_slug = "mahaonline-notices"
    department_name = "MahaOnline Notices"
    title_prefix = "MahaOnline"
    max_jobs = 20


class SetMaharashtraCrawler(HtmlListingCrawler):
    name = "set_maharashtra_crawler"
    source_url = "https://setexam.unipune.ac.in/"
    base_url = "https://setexam.unipune.ac.in"
    apply_url = "https://setexam.unipune.ac.in/"
    organization_slug = "set-maharashtra"
    organization_name = "Maharashtra State Eligibility Test (MH-SET)"
    department_slug = "mh-set"
    department_name = "MH-SET"
    title_prefix = "MH-SET"
    max_jobs = 30


class RtmnuCrawler(HtmlListingCrawler):
    name = "rtmnu_crawler"
    source_url = "https://www.nagpuruniversity.ac.in/"
    base_url = "https://www.nagpuruniversity.ac.in"
    apply_url = "https://www.nagpuruniversity.ac.in/"
    organization_slug = "rtmnu"
    organization_name = "RTM Nagpur University"
    department_slug = "rtmnu-recruitment"
    department_name = "RTMNU Recruitment"
    title_prefix = "RTMNU"
    max_jobs = 30


class BamuCrawler(HtmlListingCrawler):
    name = "bamu_crawler"
    source_url = "https://www.bamu.ac.in/"
    base_url = "https://www.bamu.ac.in"
    apply_url = "https://www.bamu.ac.in/"
    organization_slug = "bamu"
    organization_name = "Dr. Babasaheb Ambedkar Marathwada University"
    department_slug = "bamu-recruitment"
    department_name = "BAMU Recruitment"
    title_prefix = "BAMU"
    max_jobs = 30


class SgbauCrawler(HtmlListingCrawler):
    name = "sgbau_crawler"
    source_url = "https://www.sgbau.ac.in/"
    base_url = "https://www.sgbau.ac.in"
    apply_url = "https://www.sgbau.ac.in/"
    organization_slug = "sgbau"
    organization_name = "Sant Gadge Baba Amravati University"
    department_slug = "sgbau-recruitment"
    department_name = "SGBAU Recruitment"
    title_prefix = "SGBAU"
    max_jobs = 30


class ShivajiUniversityCrawler(HtmlListingCrawler):
    name = "shivaji_university_crawler"
    source_url = "https://www.unishivaji.ac.in/"
    base_url = "https://www.unishivaji.ac.in"
    apply_url = "https://www.unishivaji.ac.in/"
    organization_slug = "shivaji-university"
    organization_name = "Shivaji University Kolhapur"
    department_slug = "suk-recruitment"
    department_name = "SUK Recruitment"
    title_prefix = "Shivaji University"
    max_jobs = 30


class NmcNagpurCrawler(HtmlListingCrawler):
    name = "nmc_nagpur_crawler"
    source_url = "https://www.nmcnagpur.gov.in/"
    base_url = "https://www.nmcnagpur.gov.in"
    apply_url = "https://www.nmcnagpur.gov.in/"
    organization_slug = "nmc-nagpur"
    organization_name = "Nagpur Municipal Corporation"
    department_slug = "nmc-recruitment"
    department_name = "NMC Recruitment"
    title_prefix = "NMC Nagpur"
    max_jobs = 30


class BestUndertakingCrawler(HtmlListingCrawler):
    name = "best_undertaking_crawler"
    source_url = "https://www.bestundertaking.com/"
    base_url = "https://www.bestundertaking.com"
    apply_url = "https://www.bestundertaking.com/"
    organization_slug = "best"
    organization_name = "BEST Undertaking Mumbai"
    department_slug = "best-recruitment"
    department_name = "BEST Recruitment"
    title_prefix = "BEST"
    max_jobs = 30


class MswcCrawler(HtmlListingCrawler):
    name = "mswc_crawler"
    source_url = "https://mswarehousing.com/"
    extra_pages = ("https://mswarehousing.com/MSwhs/",)
    base_url = "https://mswarehousing.com"
    apply_url = "https://mswarehousing.com/"
    organization_slug = "mswb"
    organization_name = "Maharashtra State Warehousing Corporation"
    department_slug = "mswc-recruitment"
    department_name = "MSWC Recruitment"
    title_prefix = "MSWC"
    max_jobs = 30
