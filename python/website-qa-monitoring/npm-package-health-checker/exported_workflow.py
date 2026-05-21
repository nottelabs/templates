from __future__ import annotations

from notte_sdk import NotteClient
from pydantic import BaseModel

# Raw workflow exported from the successful Notte CLI exploration session.
# The final parameterized template lives in main.py.

class Model(BaseModel):
    packageName: str | None = None
    currentVersion: str | None = None
    weeklyDownloads: int | None = None
    license: str | None = None
    repositoryLink: str | None = None
    homepageLink: str | None = None
    lastPublish: str | None = None
    dependencyCount: int | None = None
    maintainers: list[str] | None = None
    securityIndicators: list[str] | None = None
    healthSignals: list[str] | None = None

class VisibleTopLevelFilesOrFolder1(BaseModel):
    name: str | None = None
    type: str | None = None
    size: str | None = None


class Model1(BaseModel):
    unpacked_size: str | None = None
    total_files: int | None = None
    visible_top_level_files_or_folders: list[VisibleTopLevelFilesOrFolder1] | None = None
    package_quality_details: list[str] | None = None

class Model2(BaseModel):
    dependencies_count: int | None = None
    dev_dependencies_count: int | None = None
    dependencies: list[str] | None = None
    dev_dependencies: list[str] | None = None

client = NotteClient()

def run():
    with client.Session(use_file_storage=True) as session:
        _ = session.execute(type='goto', url='https://example.com')
        _ = session.execute(type='goto', url='https://www.npmjs.com/package/react')
        _ = session.scrape(instructions='Extract package health facts for npm package react: package name, current version, weekly downloads if visible, unpacked size if visible, file count if visible, license, repository link, homepage link, last publish or publish status, dependency count, dev dependency count, maintainers, TypeScript support indicators, security or provenance indicators, and any tabs or sidebar health signals. Return concise structured JSON.', only_main_content=False, only_images=False, scrape_links=True, scrape_images=False, response_format=Model)
        _ = session.execute(type='click', selector={'css_selector': 'html > body > div:nth-of-type(1) > div > div:nth-of-type(2) > main > div > ul > li:nth-of-type(2) > a._38ce9a85.link.db.ph4.fw6[href="?activeTab=code"][role="tab"][id="package-tab-code"]', 'xpath_selector': 'html/body/div[1]/div/div[2]/main/div/ul/li[2]/a', 'playwright_selector': 'internal:role=tab[name="Code Beta"i]'})
        _ = session.scrape(instructions='On the npm Code tab for react, extract code/package file metadata: unpacked size, total files, visible top-level files or folders, and any package quality details. Return concise JSON.', only_main_content=False, only_images=False, scrape_links=True, scrape_images=False, response_format=Model1)
        _ = session.execute(type='click', selector={'css_selector': 'html > body > div:nth-of-type(1) > div > div:nth-of-type(2) > main > div > ul > li:nth-of-type(3) > a._38ce9a85.link.db.ph4.fw6[href="?activeTab=dependencies"][role="tab"][id="package-tab-dependencies"]', 'xpath_selector': 'html/body/div[1]/div/div[2]/main/div/ul/li[3]/a', 'playwright_selector': 'internal:role=tab[name="Dependencies"i]'})
        return session.scrape(instructions='On the npm Dependencies tab for react, extract dependencies and dev dependencies counts and any visible dependency list. Return concise JSON.', only_main_content=False, only_images=False, scrape_links=True, scrape_images=False, response_format=Model2)

if __name__ == "__main__":
    run()
