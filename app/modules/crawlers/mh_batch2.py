"""Maharashtra department / PSU HTML listing crawlers (batch 2)."""

from __future__ import annotations

from app.modules.crawlers.html_listing import HtmlListingCrawler


class MsedclCrawler(HtmlListingCrawler):
    name = "msedcl_crawler"
    source_url = "https://www.mahadiscom.in/"
    base_url = "https://www.mahadiscom.in"
    apply_url = "https://www.mahadiscom.in/"
    organization_slug = "mahadiscom"
    organization_name = "MSEDCL (MahaVitaran)"
    department_slug = "msedcl-recruitment"
    department_name = "MSEDCL Recruitment"
    title_prefix = "MSEDCL"
    max_jobs = 40


class MahagencoCrawler(HtmlListingCrawler):
    name = "mahagenco_crawler"
    source_url = "https://www.mahagenco.in/career-advertisement"
    extra_pages = (
        "https://www.mahagenco.in/exam-process-related-notification",
        "https://www.mahagenco.in/",
    )
    base_url = "https://www.mahagenco.in"
    apply_url = "https://www.mahagenco.in/career-advertisement"
    organization_slug = "mahagenco"
    organization_name = "MAHAGENCO"
    department_slug = "mahagenco-recruitment"
    department_name = "MAHAGENCO Recruitment"
    title_prefix = "MAHAGENCO"
    max_jobs = 40


class MahatranscoCrawler(HtmlListingCrawler):
    name = "mahatransco_crawler"
    source_url = "https://www.mahatransco.in/career/active"
    extra_pages = ("https://www.mahatransco.in/",)
    base_url = "https://www.mahatransco.in"
    apply_url = "https://www.mahatransco.in/career/active"
    organization_slug = "mahatransco"
    organization_name = "MahaTransco (MSETCL)"
    department_slug = "mahatransco-recruitment"
    department_name = "MahaTransco Recruitment"
    title_prefix = "MahaTransco"
    max_jobs = 40


class MahametroCrawler(HtmlListingCrawler):
    name = "mahametro_crawler"
    source_url = "https://www.mahametro.org/Career.aspx"
    base_url = "https://www.mahametro.org"
    apply_url = "https://www.mahametro.org/Career.aspx"
    organization_slug = "mahametro"
    organization_name = "MahaMetro"
    department_slug = "mahametro-recruitment"
    department_name = "MahaMetro Careers"
    title_prefix = "MahaMetro"
    max_jobs = 50


class MmrdaCrawler(HtmlListingCrawler):
    name = "mmrda_crawler"
    source_url = "https://mmrda.maharashtra.gov.in/mr/recruitment-data"
    extra_pages = ("https://mmrda.maharashtra.gov.in/mr",)
    base_url = "https://mmrda.maharashtra.gov.in"
    apply_url = "https://mmrda.maharashtra.gov.in/mr/recruitment-data"
    organization_slug = "mmrda"
    organization_name = "MMRDA"
    department_slug = "mmrda-recruitment"
    department_name = "MMRDA Recruitment"
    title_prefix = "MMRDA"
    max_jobs = 40


class MidcCrawler(HtmlListingCrawler):
    name = "midc_crawler"
    source_url = "https://www.midcindia.org/recruitment/"
    extra_pages = ("https://recruitment.midcindia.org/default_2023.aspx",)
    base_url = "https://www.midcindia.org"
    apply_url = "https://www.midcindia.org/recruitment/"
    organization_slug = "midc"
    organization_name = "MIDC"
    department_slug = "midc-recruitment"
    department_name = "MIDC Recruitment"
    title_prefix = "MIDC"
    max_jobs = 30


class PwdCrawler(HtmlListingCrawler):
    name = "pwd_crawler"
    source_url = "https://pwd.maharashtra.gov.in/notice-category/%e0%a4%ad%e0%a4%b0%e0%a4%a4%e0%a5%80/"
    base_url = "https://pwd.maharashtra.gov.in"
    apply_url = "https://pwd.maharashtra.gov.in/"
    organization_slug = "pwd-maharashtra"
    organization_name = "PWD Maharashtra"
    department_slug = "pwd-recruitment"
    department_name = "PWD Recruitment"
    title_prefix = "PWD"
    max_jobs = 40


class WrdCrawler(HtmlListingCrawler):
    name = "wrd_crawler"
    source_url = "https://wrd.maharashtra.gov.in/Site/1521/DIRECT-RECRUITMENT-YEAR-2023"
    extra_pages = (
        "https://wrd.maharashtra.gov.in/Site/1520/Direct-Service-Recruitment-Year-2019",
        "https://wrd.maharashtra.gov.in/",
    )
    base_url = "https://wrd.maharashtra.gov.in"
    apply_url = "https://wrd.maharashtra.gov.in/"
    organization_slug = "wrd-maharashtra"
    organization_name = "Water Resources Department Maharashtra"
    department_slug = "wrd-recruitment"
    department_name = "WRD Recruitment"
    title_prefix = "WRD"
    max_jobs = 40


class AgricultureCrawler(HtmlListingCrawler):
    name = "agriculture_crawler"
    source_url = "https://krishi.maharashtra.gov.in/"
    base_url = "https://krishi.maharashtra.gov.in"
    apply_url = "https://krishi.maharashtra.gov.in/"
    organization_slug = "agriculture-maharashtra"
    organization_name = "Agriculture Department Maharashtra"
    department_slug = "agriculture-recruitment"
    department_name = "Agriculture Recruitment"
    title_prefix = "Agriculture MH"
    max_jobs = 30


class TribalCrawler(HtmlListingCrawler):
    name = "tribal_crawler"
    source_url = "https://tribal.maharashtra.gov.in/"
    base_url = "https://tribal.maharashtra.gov.in"
    apply_url = "https://tribal.maharashtra.gov.in/"
    organization_slug = "tribal-development"
    organization_name = "Tribal Development Department"
    department_slug = "tribal-recruitment"
    department_name = "Tribal Recruitment"
    title_prefix = "Tribal"
    max_jobs = 40


class SjsaCrawler(HtmlListingCrawler):
    name = "sjsa_crawler"
    source_url = "https://sjsa.maharashtra.gov.in/notice-category/%e0%a4%aa%e0%a4%a6%e0%a4%ad%e0%a4%b0%e0%a4%a4%e0%a5%80/"
    extra_pages = (
        "https://sjsa.maharashtra.gov.in/notice-category/%e0%a4%9c%e0%a4%be%e0%a4%b9%e0%a4%bf%e0%a4%b0%e0%a4%be%e0%a4%a4/",
    )
    base_url = "https://sjsa.maharashtra.gov.in"
    apply_url = "https://sjsa.maharashtra.gov.in/"
    organization_slug = "sjsa"
    organization_name = "Social Justice & Special Assistance"
    department_slug = "sjsa-recruitment"
    department_name = "SJSA Recruitment"
    title_prefix = "SJSA"
    max_jobs = 40


class HomeDeptCrawler(HtmlListingCrawler):
    name = "home_dept_crawler"
    source_url = "https://home.maharashtra.gov.in/notice-category/%e0%a4%ad%e0%a4%b0%e0%a4%a4%e0%a5%80/"
    base_url = "https://home.maharashtra.gov.in"
    apply_url = "https://home.maharashtra.gov.in/"
    organization_slug = "home-department"
    organization_name = "Home Department Maharashtra"
    department_slug = "home-recruitment"
    department_name = "Home Department Recruitment"
    title_prefix = "Home Dept"
    max_jobs = 40


class PrisonsCrawler(HtmlListingCrawler):
    name = "prisons_crawler"
    source_url = "https://mahaprisons.gov.in/notice-category/%e0%a4%ad%e0%a4%b0%e0%a4%a4%e0%a5%80/"
    base_url = "https://mahaprisons.gov.in"
    apply_url = "https://mahaprisons.gov.in/"
    organization_slug = "maharashtra-prisons"
    organization_name = "Maharashtra Prisons Department"
    department_slug = "prisons-recruitment"
    department_name = "Prisons Recruitment"
    title_prefix = "Prisons"
    max_jobs = 40


class CidcoCrawler(HtmlListingCrawler):
    name = "cidco_crawler"
    source_url = "https://cidco.maharashtra.gov.in/"
    base_url = "https://cidco.maharashtra.gov.in"
    apply_url = "https://cidco.maharashtra.gov.in/"
    organization_slug = "cidco"
    organization_name = "CIDCO"
    department_slug = "cidco-recruitment"
    department_name = "CIDCO Recruitment"
    title_prefix = "CIDCO"
    max_jobs = 30


class EducationDeptCrawler(HtmlListingCrawler):
    name = "education_dept_crawler"
    source_url = "https://education.maharashtra.gov.in"
    base_url = "https://education.maharashtra.gov.in"
    apply_url = "https://education.maharashtra.gov.in"
    organization_slug = "education-maharashtra"
    organization_name = "School Education Department Maharashtra"
    department_slug = "education-notices"
    department_name = "School Education Notices"
    title_prefix = "Education MH"
    max_jobs = 20


class MuhsCrawler(HtmlListingCrawler):
    name = "muhs_crawler"
    source_url = "https://www.chakra.muhs.ac.in/"
    extra_pages = ("https://www.muhs.ac.in/",)
    base_url = "https://www.muhs.ac.in"
    apply_url = "https://www.chakra.muhs.ac.in/"
    organization_slug = "muhs"
    organization_name = "MUHS Nashik"
    department_slug = "muhs-recruitment"
    department_name = "MUHS Recruitment"
    title_prefix = "MUHS"
    max_jobs = 30


class MumbaiUniversityCrawler(HtmlListingCrawler):
    name = "mumbai_university_crawler"
    source_url = "https://mu.ac.in/"
    base_url = "https://mu.ac.in"
    apply_url = "https://mu.ac.in/"
    organization_slug = "mumbai-university"
    organization_name = "University of Mumbai"
    department_slug = "mu-recruitment"
    department_name = "MU Recruitment"
    title_prefix = "Mumbai University"
    max_jobs = 30


class SppuCrawler(HtmlListingCrawler):
    name = "sppu_crawler"
    source_url = "https://www.unipune.ac.in/"
    base_url = "https://www.unipune.ac.in"
    apply_url = "https://www.unipune.ac.in/"
    organization_slug = "pune-university"
    organization_name = "Savitribai Phule Pune University"
    department_slug = "sppu-recruitment"
    department_name = "SPPU Recruitment"
    title_prefix = "SPPU"
    max_jobs = 30


class PcmcCrawler(HtmlListingCrawler):
    name = "pcmc_crawler"
    source_url = "https://www.pcmcindia.gov.in/"
    base_url = "https://www.pcmcindia.gov.in"
    apply_url = "https://www.pcmcindia.gov.in/"
    organization_slug = "pcmc"
    organization_name = "Pimpri Chinchwad Municipal Corporation"
    department_slug = "pcmc-recruitment"
    department_name = "PCMC Recruitment"
    title_prefix = "PCMC"
    max_jobs = 30


class PmcCrawler(HtmlListingCrawler):
    name = "pmc_crawler"
    source_url = "https://www.pmc.gov.in/"
    base_url = "https://www.pmc.gov.in"
    apply_url = "https://www.pmc.gov.in/"
    organization_slug = "pmc-pune"
    organization_name = "Pune Municipal Corporation"
    department_slug = "pmc-recruitment"
    department_name = "PMC Recruitment"
    title_prefix = "PMC"
    max_jobs = 30
