# Right Stock, Right Place · IT device stock optimisation

Python companion to the Power BI report *Too Much Stock, Wrong Places* (a global IT device fleet: laptops, desktops, handhelds and tablets in 91 countries and about 900 sites, snapshot Dec 2022).
The dashboard checks every site against a flat rule: spare stock = 10% of devices in use. This notebook estimates what each site really needs,
classifies sites with ABC–XYZ, sets safety stock per site, and uses a linear programme to move surplus stock to short sites before buying new devices.

| Question | Method |
|---|---|
| Where does demand for spares come from? | Lifecycle refresh dates, backlog of devices past lifecycle, break/fix + loss rate per device-year |
| Which sites should hold stock? | ABC by fleet size (80/15/5) × XYZ by dispersion of monthly refresh demand (steady vs waves) |
| What stock level is right? | Poisson safety stock: target = μL + z√(μL), service level by ABC class, compared with the 10% rule · sensitivity to lead time, service level and refresh policy |
| How much can be moved instead of bought? | Linear programme (scipy HiGHS) per device type: minimise transfer + purchase cost; scenarios within country, cross-border in region, and with the 10% rule as target |

## Headline results
* Stock is 28% of the fleet, not 10%, and 5,591 of the 17,591 devices in stock are reserved or past their lifecycle. None of the 750 handhelds in stock is usable.
* The sites need about 2,800 spare devices, against 12,000 useful on hand and 7,047 under the 10% rule. Small sites need about 32% of their fleet and hold 12%; sites with 1,000+ devices need about 1% and hold 19%.
* Moving surplus within countries covers 1,024 of 1,652 devices short and avoids about USD 1.0M of purchases for USD 69K of transport.
* 9,867 useful devices (about USD 10.4M) are not needed anywhere: about 13 months of laptop demand.

Device prices, transfer costs and the 1.5-month lead time are stated assumptions and can be changed in the notebook.

## Run it
```bash
pip install -r requirements.txt
jupyter notebook "Stock Optimisation Deep Dive.ipynb"
```
Put the raw asset workbook (.xlsx or .xlsb with the AssetData and ISORegion sheets) in the data folder. It is not included: the data belongs to the original test case.
Sites are anonymised in every output (`India · site 01`), and no person or asset names are loaded. Every chart is saved to the images folder.

## Files
```
Stock Optimisation Deep Dive/
├── Stock Optimisation Deep Dive.ipynb   the analysis, with outputs
├── Stock Optimisation Deep Dive.html    the same notebook as a static page
├── octools.py                           cleaning (same rules as the Power BI model) and site anonymisation
├── requirements.txt
├── data/                                raw asset workbook (not included)
├── images/                              key charts as PNG
└── powerbi/
    └── Too Much Stock Wrong Places.pbit companion Power BI report
```
