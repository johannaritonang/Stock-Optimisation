"""Helpers for the IT device stock optimisation notebook ('Too Much Stock, Wrong Places').

`load()` applies the same rules as the Power BI model: asset classes (workstation = laptop/desktop,
communication device = handheld/tablet), install status cleaning, ISO region lookup, device age at the as-of date and
stock usefulness (useful = age <= lifecycle - 1 year, reserved = within the last lifecycle year, being decomm = past lifecycle).
Sites are anonymised in every output ("Brazil · site 03"); people and asset names are never loaded.
"""
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- palette (matches the Power BI report)
NAVY, TEAL, TEAL_L, AMBER, CORAL, PLUM, SLATE, INK, MUTED, LINE = (
    "#14233C", "#197278", "#A7D3D5", "#F5A524", "#E05A47", "#9B59B6", "#64748B", "#1E293B", "#64748B", "#E2E8F0")


def style_charts():
    import matplotlib.pyplot as plt
    plt.rcParams.update({"figure.dpi": 110, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#CBD5E1",
                         "axes.titleweight": "bold", "axes.titlesize": 12, "axes.titlecolor": INK, "axes.labelcolor": MUTED,
                         "xtick.color": MUTED, "ytick.color": MUTED, "figure.facecolor": "white", "axes.facecolor": "white"})


def find_workbook(folders):
    """First .xlsx/.xlsb whose name mentions 'raw', 'testcase' or 'asset' in the given folders."""
    for folder in folders:
        folder = Path(folder)
        if folder.exists():
            hits = sorted(f for f in folder.iterdir() if f.suffix.lower() in (".xlsx", ".xlsb") and not f.name.startswith("~$")
                          and any(k in f.name.lower().replace(" ", "").replace("_", "") for k in ("raw", "testcase", "asset")))
            if hits:
                return hits[0]
    return None


CLASS = {"Laptop": "Workstation", "Desktop": "Workstation", "Mobile Device": "Communication Device",
         "Handheld": "Communication Device", "Tablet": "Communication Device", "Monitor": "Computer Peripheral"}
LIFECYCLE = {"Workstation": 4, "Communication Device": 3, "Computer Peripheral": 6}   # years (TPE lifecycle)
IN_USE = ("Live", "Lent Out")
COLUMNS = ["InstallStatus", "Type", "LocationName", "LocationCountry", "LocationCity", "SnCreatedDate", "SysUpdatedDate"]
ALIASES = {"TRINIDAD AND TOBAGO": "TRINIDAD,TOBAGO", "UNITED REPUBLIC OF TANZANIA": "TANZANIA"}


def _to_date(s):
    """Excel serial numbers (xlsb) or real dates (xlsx) -> Timestamp."""
    if pd.api.types.is_numeric_dtype(s):
        return pd.to_datetime("1899-12-30") + pd.to_timedelta(s, unit="D")
    return pd.to_datetime(s, errors="coerce")


def _country(x):
    if not isinstance(x, str) or not x.strip():
        return "Unknown"
    x = x.strip()
    return x.title() if (x.isupper() and len(x) > 3) else x


def load(path):
    path = Path(path)
    engine = "pyxlsb" if path.suffix.lower() == ".xlsb" else None
    raw = pd.read_excel(path, sheet_name="AssetData", usecols=lambda c: c in COLUMNS, engine=engine)
    iso = pd.read_excel(path, sheet_name="ISORegion", engine=engine)

    a = raw.copy()
    a["Type"] = a["Type"].astype(str).str.strip()
    a["asset_class"] = a["Type"].map(CLASS)
    a = a[a.asset_class.notna()].copy()
    a["created"] = _to_date(a.SnCreatedDate).dt.normalize()
    as_of = _to_date(a.SysUpdatedDate).max().normalize()
    a["status"] = a.InstallStatus.map(lambda v: str(v).strip() if isinstance(v, str) and v.strip() and str(v) != "-101" else "Unknown")
    a["country"] = a.LocationCountry.map(_country)
    a["site"] = a.LocationName.fillna("Unknown").astype(str).str.strip().replace("", "Unknown")
    a["city"] = a.LocationCity.fillna("Unknown").astype(str).str.strip().str.title()
    regions = {str(n).upper().strip(): r for n, r in zip(iso["Name"], iso["RegionGroupShortText"])}
    a["region"] = a.country.str.upper().map(lambda c: ALIASES.get(c, c)).map(regions).fillna("Unmapped")
    a["age_years"] = (as_of - a.created).dt.days / 365.25
    life = a.asset_class.map(LIFECYCLE)
    a["lifecycle_years"] = life
    use = np.select([a.status != "In Stock", a.age_years.isna(), a.age_years <= life - 1, a.age_years <= life],
                    ["Not in Stock", "Unknown Age", "Useful", "Reserved"], "Being Decomm")
    a["usefulness"] = use
    a["in_use"] = a.status.isin(IN_USE)
    a["in_stock"] = a.status == "In Stock"
    a["as_of"] = as_of

    # anonymised site label: country + rank of the site by fleet size within the country
    fleet = a[a.in_use].groupby(["country", "site"]).size()
    allsites = a.groupby(["country", "site"]).size().rename("n").to_frame().join(fleet.rename("fleet")).fillna(0)
    allsites = allsites.sort_values(["fleet", "n"], ascending=False)
    allsites["rank"] = allsites.groupby(level=0).cumcount() + 1
    labels = {k: f"{k[0]} · site {r:02d}" for k, r in allsites["rank"].items()}
    a["site_label"] = [labels[(c, s)] for c, s in zip(a.country, a.site)]
    return a[["status", "Type", "asset_class", "country", "region", "city", "site", "site_label", "created", "age_years",
              "lifecycle_years", "usefulness", "in_use", "in_stock", "as_of"]].rename(columns={"Type": "asset_type"})


def money(v):
    return f"${v / 1e6:,.1f}M" if abs(v) >= 1e6 else f"${v / 1e3:,.0f}K"
