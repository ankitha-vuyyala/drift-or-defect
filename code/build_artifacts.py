"""Build reference artifacts from official sources: ACS occupation crosswalks (Census value labels), the TLC zone
lookup, and the news-section harmonisation tables (as maintained over time). usage: python code/build_artifacts.py"""
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.simplefilter("ignore")
from dod.domains import acs, news, tlc  # noqa: E402

print("acs occ_xwalk codes:", acs.build_occ_xwalks())
tlc.build_zone_artifact()
print("tlc zones: ok")
print("news harmonisation entries by year:", news.build_harmonise_artifacts())
