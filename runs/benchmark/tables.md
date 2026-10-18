# Benchmark tables

## acs
- periods: 11 (2014..2024); task binary; 16 model inputs; 7 components
- events: 2017 SERIALNO format: 13-digit year-prefixed id; 2017 SERIALNO format: 13-digit year-prefixed id; 2018 SERIALNO alphanumeric (GQ/HU); OCCP 2018 code list; 2018 SERIALNO alphanumeric (GQ/HU); 2019 RELP->RELSHIPP, WKW->WKWN, JWTR->JWTRNS; 2023 ST->STATE
- catalog:
  - acs.adapter_early_upgrade [B/benign] person_adapter: 2019-ready adapter deployed early (from 2014)
  - acs.join_nodedupe [B/benign] join_household: dedupe of the household side removed (keys are unique) (from 2014)
  - acs.clean_env_p30 [T2/defect] person_clean: pandas 3 upgrade: chained-assignment fill becomes a no-op (from 2014)
  - acs.clean_modernised [B/benign] person_clean: chained assignment -> .loc (from 2014)
  - acs.clean_modernised_p30 [T2b/benign] person_clean: pandas 3 upgrade of the modernised cleaning step (from 2014)
  - acs.occ_env_p30 [T2b/benign] occ_group: pandas 3 upgrade of the crosswalk step (from 2014)
  - acs.housing_env_p30 [T2b/benign] housing_adapter: pandas 3 upgrade of the housing adapter (from 2014)
  - acs.adjinc_ignored [T3/defect] features: income adjustment factor dropped (stale reference) (from 2014)
  - acs.wkhp_month [T3/defect] features: hours per week reported per month (unit change) (from 2014)
  - acs.veh_stuck_tx [T3/defect] features: vehicles feature stuck at 0 for Texas (upstream default) (from 2014)
  - acs.encoder_refit [T3/defect] encode: categorical codes re-fitted at serving time (training/serving skew) (from 2014)
  - acs.key_digits [T1/defect] join_household: alphanumeric SERIALNO 'fixed' by stripping letters (GQ/HU ids collide) (from 2018)
  - acs.key_numeric_stale [T1/defect] join_household: join keys still parsed as numbers after the id format change (from 2018)
  - acs.occ_xwalk_stale [T1/defect] occ_group: occupation crosswalk not refreshed for 2018 codes (from 2018)
  - acs.relp_minus20 [T1/defect] person_adapter: RELSHIPP codes shifted by -20 instead of the official crosswalk (from 2019)
  - acs.wkw_reversed [T1/defect] person_adapter: WKWN binned into WKW categories in reverse order (from 2019)
  - acs.wkw_passthrough [T1/defect] person_adapter: WKWN weeks passed through as WKW categories (from 2019)
  - acs.jwtr_rename [T1/defect] person_adapter: JWTRNS used as JWTR without recoding (subway/rail/streetcar codes permuted) (from 2019)
  - acs.adapter_refactor [B/benign] person_adapter: refactor of the 2019 adapter (from 2019)
  - acs.state_fill [T1/defect] person_adapter: missing ST column filled with the most common training state (from 2023)
- cases: {'dev|benign|none': 20, 'dev|clean|none': 20, 'dev|defect|T1': 94, 'dev|defect|T2': 20, 'dev|defect|T3': 80, 'dev|two|T1': 7, 'dev|two|T1+T2': 4, 'dev|two|T1+T3': 14, 'dev|two|T2+T3': 8, 'dev|two|T3': 7}

## tlc
- periods: 50 (2015-01..2026-07); task binary; 18 model inputs; 6 components
- events: 2018-07 passenger_count, RatecodeID published as double; 2019-01 congestion_surcharge populated; 2021-01 airport_fee populated; 2023-04 airport_fee renamed Airport_fee; VendorID/LocationIDs int32; 2025-01 cbd_congestion_fee column added; 2026-07 request_source column added
- catalog:
  - tlc.adapter_ci_early [B/benign] trip_adapter: case-insensitive column lookup deployed early (from 2015-01)
  - tlc.time_env_main [T2/defect] time_features: pandas 2.2 / pyarrow 25 upgrade: parquet timestamps keep microsecond unit; epoch math via astype(int64) (from 2015-01)
  - tlc.time_env_p30 [T2/defect] time_features: pandas 3 upgrade: epoch via astype(int64) changes resolution (from 2015-01)
  - tlc.time_modernised [B/benign] time_features: timedelta arithmetic in the upgraded environment (from 2015-01)
  - tlc.time_modernised_p30 [T2b/benign] time_features: pandas 3 upgrade of the modernised time step (from 2015-01)
  - tlc.clean_env_p30 [T2/defect] clean: pandas 3 upgrade: chained-assignment cleaning becomes a no-op (from 2015-01)
  - tlc.clean_modernised [B/benign] clean: chained assignment -> .loc (from 2015-01)
  - tlc.zone_env_p30 [T2b/benign] zone_join: pandas 3 upgrade of the zone join (from 2015-01)
  - tlc.tz_utc [T3/defect] time_features: timestamps shifted as if converted from UTC (from 2015-01)
  - tlc.do_key_bug [T3/defect] zone_join: dropoff zone joined on the pickup id (copy-paste key bug) (from 2015-01)
  - tlc.distance_km [T3/defect] fare_features: trip distance converted to km (unit change) (from 2015-01)
  - tlc.encoder_refit [T3/defect] encode: categorical codes re-fitted at serving time (training/serving skew) (from 2015-01)
  - tlc.ratecode_stale [T1/defect] trip_adapter: rate code key built from the published dtype ('1.0' after the double change) (from 2018-07)
  - tlc.airport_case_stale [T1/defect] trip_adapter: case-sensitive lookup misses the renamed Airport_fee column (filled with 0) (from 2023-04)
  - tlc.cbd_stale [T1/defect] trip_adapter: new congestion fee not separated; lands in other_charges (from 2025-01)
- cases: {'dev|benign|none': 9, 'dev|clean|none': 9, 'dev|defect|T1': 22, 'dev|defect|T2': 26, 'dev|defect|T3': 26, 'dev|two|T1+T2': 13, 'dev|two|T1+T3': 9, 'test|benign|none': 17, 'test|clean|none': 17, 'test|defect|T1': 22, 'test|defect|T2': 52, 'test|defect|T3': 78, 'test|two|T1+T2': 5, 'test|two|T1+T3': 4, 'test|two|T2': 3, 'test|two|T2+T3': 8, 'test|two|T3': 6}

## news
- periods: 11 (2012..2022); task multiclass; 1 model inputs; 4 components
- events: 2014 new category values: ['ARTS', 'COLLEGE', 'EDUCATION', 'FIFTY', 'GOOD NEWS', 'GREEN', 'HEALTHY LIVING', 'LATINO VOICES', 'MEDIA', 'PARENTS', 'POLITICS', 'RELIGION', 'STYLE', 'TASTE', 'WEIRD NEWS', 'WOMEN', 'WORLDPOST']; 2015 new category values: ['ARTS & CULTURE', 'THE WORLDPOST']; 2017 new category values: ['WORLD NEWS']; 2018 new category values: ['U.S. NEWS']
- catalog:
  - news.text_env_p30 [T2b/benign] text_norm: pandas 3 upgrade of text normalisation (astype(str) keeps missing values; none occur in this source) (from 2012)
  - news.ingest_env_p30 [T2b/benign] ingest: pandas 3 upgrade of ingestion (from 2012)
  - news.no_lower [T3/defect] text_norm: lower-casing step dropped (from 2012)
  - news.headline_only [T3/defect] text_norm: description dropped by a field-mapping bug (from 2012)
  - news.mojibake [T3/defect] text_norm: UTF-8 text decoded as Latin-1 upstream (from 2012)
  - news.vocab_refit [T3/defect] vectorize: vocabulary re-fitted at serving time (training/serving skew) (from 2012)
  - news.label_map_full_early [B/benign] label_map: complete harmonisation table deployed early (from 2012)
  - news.harmonise_stale [T1/defect] label_map: section harmonisation table not refreshed for new section names (from 2013)
- cases: {'dev|benign|none': 5, 'dev|clean|none': 5, 'dev|defect|T3': 26, 'test|benign|none': 8, 'test|clean|none': 8, 'test|defect|T1': 11, 'test|defect|T3': 26, 'test|two|T1+T3': 8, 'test|two|T3': 5}
