# New Jersey Tap Water Sources and PFAS Results by Town (2025 reports)

Published by [Source & Tap](https://sourceandtap.com), an independent website that shows what is in New Jersey tap water, town by town.

This dataset links 41 New Jersey municipalities to the public water systems that serve them, and records the PFAS results those systems published in their 2025 Consumer Confidence Reports (CCRs). Every measurement row was checked by hand against the original utility report.

## Files

| File | One row per | Contents |
|---|---|---|
| `towns.csv` | municipality | Town, county, Census GEOID, population, primary water system, Source & Tap page |
| `town_systems.csv` | town × water system | Which systems serve which town, and each system's estimated share |
| `systems.csv` | water system | System name, CCR link, whether the CCR reports PFAS results |
| `measurements.csv` | reported value | PFAS values as printed in each CCR |

Files join on `pwsid` (EPA public water system ID) and `census_geoid`.

## measurements.csv columns

| Column | Meaning |
|---|---|
| `pwsid` | EPA public water system ID |
| `contaminant` | Standard abbreviation (PFOA, PFOS, PFNA, PFHxS, PFBS, PFHxA, PFPeA, PFHpA, PFBA, HFPO-DA, 6:2 FTS) |
| `table_type` | `compliance` (regulated results), `ucmr5` (EPA Fifth Unregulated Contaminant Monitoring Rule), `unregulated` (other unregulated PFAS tables), `voluntary` (utility's voluntary sampling) |
| `year_sampled` | Year printed in the report's "Year Sampled" column. Differs between rows of the same report |
| `value` | Value exactly as printed. May be a number, `ND` (not detected), `NA`, or a range where the report printed one |
| `unit` | Always ppt (ng/L) |
| `value_column_reported` | The report's own column header for the value |
| `value_statistic` | Normalized meaning of the value (see below) |
| `range_reported` | Range of results as printed |
| `compliance_achieved_reported` | The report's "Compliance Achieved" entry, where the table has one |
| `nj_mcl` / `federal_mcl` | New Jersey and federal maximum contaminant levels, in ppt, for PFOA, PFOS and PFNA (NJ) and PFOA and PFOS (federal) |
| `source_facility` | Treatment plant, entry point or interconnection named by the report, where given |
| `notes` | Report footnotes and known issues with the printed data |

### value_statistic

Utilities do not report PFAS the same way. Two numbers side by side in this file may measure different things.

- `highest_single_result`: the highest individual sample
- `highest_raa`: the highest running annual average, stated in the report or its footnotes
- `highest_compliance_result_unspecified`: labeled "Highest Compliance Result" without saying whether it is a single result or an average
- `average`: average of detections (typical for UCMR tables)
- `range_as_reported`: the report printed a range in the value column
- `not_detected`: all results below detection

## Read this before comparing values to limits

**A reported value above a limit is not a legal violation.** Federal compliance for PFOA and PFOS is determined by running annual averages at each sampling point, and the federal compliance deadline has not yet arrived. Every compliance row in this dataset is marked "Compliance Achieved: Yes" by the utility.

**Federal limits status (as of this release, September 2026).** EPA's April 2024 rule set enforceable limits of 4.0 ppt for PFOA and PFOS, with compliance due in April 2029. In May 2026 EPA proposed letting systems request two more years, to April 2031. That proposal was not final at the time of release. EPA has also moved to withdraw the 2024 limits for PFHxS, PFNA, HFPO-DA and the Hazard Index mixture, so this dataset lists federal limits for PFOA and PFOS only. New Jersey's limits (PFOA 14 ppt, PFOS 13 ppt, PFNA 13 ppt) are in effect.

## Methodology

1. **Town to system mapping.** Each municipality is matched to the water systems serving it using Census geography and population overlap. Three towns were verified by hand against utility sources, and their primary share is set to 1.0.
2. **Report collection.** 2025 CCRs were collected from each utility.
3. **Extraction.** PFAS values were extracted with an automated pipeline and every row in `measurements.csv` was then checked by hand against the original report. Values are reproduced as printed, including apparent errors (see `notes`).
4. **Population.** U.S. Census Bureau, Population Estimates Program, Vintage 2025 (July 1, 2025), county subdivision level.

## Known limitations

- **Coverage is not representative of New Jersey.** Towns were selected where one water system serves at least about 80% of residents. Towns with mixed supply are underrepresented.
- **Partial-source values.** For Mount Holly (NJ0323001) and Harrison (NJ0808001), the PFOA and PFOS compliance values come from the Delaware River Regional Water Treatment Plant section of the report. They describe the surface-water share of supply only. The reports give no PFAS compliance result for these systems' wells.
- **Systems without PFAS results.** The 2025 CCRs for Ocean City (NJ0508001) and Penns Grove (NJ1707001) contain no PFAS results for those systems.
- **Report errors are preserved.** Coastal North's report mislabels two compounds, and one Raritan row appears to have a unit inconsistency. These are flagged in `notes`.
- **Excluded data.** Pre-merger tables for Shorelands and Union Beach in the Coastal North report, and a table for NJAW Logan System printed in the Penns Grove report, are not included.

## License

CC BY 4.0. You may reuse and adapt this data with attribution to Source & Tap.

## Citation

Sertbaş, Y. (2026). *New Jersey Tap Water Sources and PFAS Results by Town (2025 reports)* [Data set]. Source & Tap. Zenodo.

## Contact

hello@sourceandtap.com. Source & Tap is not affiliated with any water utility, government agency or filter manufacturer.
