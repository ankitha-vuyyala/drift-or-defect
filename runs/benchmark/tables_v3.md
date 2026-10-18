# Benchmark tables (nine domains)

## acs (round 1)
- periods: 11 (2014..2024); task binary; 16 model inputs; 7 components; 3,995,334 bronze rows in 22 files
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
- cases: 274 {'dev|benign|none': 20, 'dev|clean|none': 20, 'dev|defect|T1': 94, 'dev|defect|T2': 20, 'dev|defect|T3': 80, 'dev|two|T1': 7, 'dev|two|T1+T2': 4, 'dev|two|T1+T3': 14, 'dev|two|T2+T3': 8, 'dev|two|T3': 7}

## tlc (round 1)
- periods: 50 (2015-01..2026-07); task binary; 18 model inputs; 6 components; 7,502,536 bronze rows in 50 files
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
- cases: 326 {'dev|benign|none': 9, 'dev|clean|none': 9, 'dev|defect|T1': 22, 'dev|defect|T2': 26, 'dev|defect|T3': 26, 'dev|two|T1+T2': 13, 'dev|two|T1+T3': 9, 'test|benign|none': 17, 'test|clean|none': 17, 'test|defect|T1': 22, 'test|defect|T2': 52, 'test|defect|T3': 78, 'test|two|T1+T2': 5, 'test|two|T1+T3': 4, 'test|two|T2': 3, 'test|two|T2+T3': 8, 'test|two|T3': 6}

## news (round 1)
- periods: 11 (2012..2022); task multiclass; 1 model inputs; 4 components; 209,527 bronze rows in 11 files
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
- cases: 102 {'dev|benign|none': 5, 'dev|clean|none': 5, 'dev|defect|T3': 26, 'test|benign|none': 8, 'test|clean|none': 8, 'test|defect|T1': 11, 'test|defect|T3': 26, 'test|two|T1+T3': 8, 'test|two|T3': 5}

## divvy (round 2)
- periods: 51 (2014-Q1..2026-Q3); task binary; 13 model inputs; 5 components; 5,103,638 bronze rows in 52 files
- events: 2017-Q1 starttime/stoptime renamed start_time/end_time; 2017-Q4 timestamps published without seconds again; 2018-Q1 long-form column headers; ISO timestamps; trip duration with thousands separators; 2018-Q2 short column headers again; 2019-Q2 long-form column headers again; 2019-Q3 short column headers again; 2020-Q1 new layout: ride_id, rideable_type, started_at/ended_at, member_casual, coordinates; trip duration, gender and birth year removed; 2020-Q3 blank station ids (dockless trips); electric bikes; 2020-Q4 alphanumeric station ids; 2024-Q2 timestamps with fractional seconds
- catalog:
  - divvy.positional [B/benign] trip_adapter: columns taken by position in the 2014 order (from 2014-Q1)
  - divvy.dayfirst [T3r/defect] time_features: month/day order swapped when parsing M/D/Y timestamps (from 2014-Q1)
  - divvy.time_env_p30 [T2b/benign] time_features: pandas 3 upgrade: duration from epoch nanoseconds via astype(int64) changes resolution (from 2014-Q1)
  - divvy.adapter_env_p30 [T2b/benign] trip_adapter: pandas 3 upgrade of the adapter (from 2014-Q1)
  - divvy.end_key_bug [T3/defect] station_join: end coordinates looked up with the start station id (copy-paste key bug) (from 2014-Q1)
  - divvy.clean_env_main [T2b/benign] clean: pandas 2.2 upgrade of the cleaning step (from 2014-Q1)
  - divvy.clean_env_p30 [T2/defect] clean: pandas 3 upgrade: chained assignment blanking round-trip distances becomes a no-op (from 2014-Q1)
  - divvy.clean_modernised [B/benign] clean: chained assignment -> .loc (from 2014-Q1)
  - divvy.encoder_refit [T3/defect] encode: categorical codes re-fitted at serving time (training/serving skew) (from 2014-Q1)
  - divvy.unknown_as_reference [T3r/defect] encode: unseen categories encoded as the reference category (from 2014-Q1)
  - divvy.fmt_stale [T1/defect] time_features: timestamps parsed with the previous published format (from 2016-Q3)
  - divvy.commas_stale [T1/defect] time_features: trip duration with thousands separators parsed without removing them (from 2018-Q1)
  - divvy.user_recode_stale [T1/defect] trip_adapter: user type mapped with the Subscriber/Customer rule: every member/casual value becomes casual (from 2020-Q1)
  - divvy.coords_lookup_stale [T1/defect] station_join: station coordinates still taken from the 2017 station table instead of the records (from 2020-Q1)
  - divvy.blank_ids_stale [T1/defect] station_join: blank station ids of dockless trips compared as equal: counted as round trips (from 2020-Q3)
- cases: 396 {'test|benign|none': 35, 'test|clean|none': 35, 'test|defect|T1': 125, 'test|defect|T2': 56, 'test|defect|T3': 70, 'test|defect|T3r': 40, 'test|two|T1': 4, 'test|two|T1+T2': 3, 'test|two|T1+T3': 7, 'test|two|T1+T3r': 7, 'test|two|T2': 1, 'test|two|T2+T3': 3, 'test|two|T2+T3r': 6, 'test|two|T3': 2, 'test|two|T3+T3r': 2}

## hmda (round 2)
- periods: 14 (2012..2025); task binary; 14 model inputs; 4 components; 2,100,000 bronze rows in 14 files
- events: 2014 missing values published as blanks instead of 'NA'; 2015 missing values published as 'NA' again; 2017 numbers published without zero padding; 2018 record format rebuilt (Regulation C): loan amount in dollars; loan purpose, occupancy and property recoded; state as postal code, county as 5-digit FIPS; tract fields renamed; open-end, reverse-mortgage and business-purpose flags added; 2020 tract income percentage published with decimals; 2024 tract income percentage published as integers again
- catalog:
  - hmda.adapter_env_p30 [T2b/benign] lar_adapter: pandas 3 upgrade of the adapter (from 2012)
  - hmda.clean_env_main [T2b/benign] clean: pandas 2.2 upgrade of the cleaning step (chained assignment still effective) (from 2012)
  - hmda.clean_env_p30 [T2/defect] clean: pandas 3 upgrade: chained-assignment missing-income sentinel becomes a no-op (from 2012)
  - hmda.clean_modernised [B/benign] clean: chained assignment -> .loc (from 2012)
  - hmda.clean_numpy [B/benign] clean: sentinel via np.nan_to_num(x, nan=-1) (from 2012)
  - hmda.income_nan_zero [T3r/defect] clean: np.nan_to_num(x, -1): missing income becomes 0 instead of -1 (from 2012)
  - hmda.lti_inverted [T3/defect] features: loan-to-income ratio computed upside down (from 2012)
  - hmda.features_env_p30 [T2b/benign] features: pandas 3 upgrade of the feature step (from 2012)
  - hmda.encoder_refit [T3/defect] encode: categorical codes re-fitted at serving time (training/serving skew) (from 2012)
  - hmda.unknown_as_reference [T3r/defect] encode: unseen categories encoded as the reference category (from 2012)
  - hmda.amount_dollars [T1/defect] lar_adapter: new adapter keeps the loan amount in dollars (was thousands) (from 2018)
  - hmda.purpose_alias [T1/defect] lar_adapter: new loan-purpose codes 31/32/5 passed through instead of recoded (rename without recode) (from 2018)
  - hmda.occupancy_alias [T1/defect] lar_adapter: occupancy type read as the old owner-occupancy code (investment property becomes 'not applicable') (from 2018)
  - hmda.county_concat [T1/defect] lar_adapter: county key built the old way (state + county code) from the new 5-digit county code (from 2018)
  - hmda.ignore_coverage [T1/defect] lar_adapter: new open-end / reverse / business-purpose flags ignored: products outside the old scope enter the data (from 2018)
  - hmda.adapter_2018_env_p30 [T2b/benign] lar_adapter: pandas 3 upgrade of the new adapter (from 2018)
- cases: 280 {'test|benign|none': 25, 'test|clean|none': 25, 'test|defect|T1': 80, 'test|defect|T2': 25, 'test|defect|T3': 50, 'test|defect|T3r': 50, 'test|two|T1+T3': 3, 'test|two|T1+T3r': 8, 'test|two|T2+T3': 3, 'test|two|T2+T3r': 2, 'test|two|T3+T3r': 9}

## bts (round 2)
- periods: 47 (2015-01..2026-07); task binary; 12 model inputs; 5 components; 7,050,000 bronze rows in 47 files
- events: 
- catalog:
  - bts.adapter_env_p30 [T2b/benign] flight_adapter: pandas 3 upgrade of the adapter (from 2015-01)
  - bts.time_env_main [T2b/benign] time_features: pandas 2.2 upgrade of the time step (string dates still parse to nanoseconds) (from 2015-01)
  - bts.time_env_p30 [T2/defect] time_features: pandas 3 upgrade: day of year via astype(int64) changes resolution (from 2015-01)
  - bts.time_modernised [B/benign] time_features: day of year via .dt accessor (from 2015-01)
  - bts.hhmm_as_minutes [T3/defect] time_features: scheduled hhmm clock times read as minutes (from 2015-01)
  - bts.dow_from_date [B/benign] time_features: day of week from the date instead of the published field (same values) (from 2015-01)
  - bts.clean_env_main [T2b/benign] clean: pandas 2.2 upgrade of the cleaning step (from 2015-01)
  - bts.clean_env_p30 [T2/defect] clean: pandas 3 upgrade: chained-assignment overnight arrival fix becomes a no-op (from 2015-01)
  - bts.clean_modernised [B/benign] clean: chained assignment -> .loc (from 2015-01)
  - bts.label_from_delay [T3/defect] clean: label recomputed as delay > 15 instead of the published >= 15 flag (from 2015-01)
  - bts.keep_diverted [T3/defect] clean: diverted flights kept (scope filter bug) (from 2015-01)
  - bts.dest_key_bug [T3/defect] airport_join: destination size joined on the origin airport id (copy-paste key bug) (from 2015-01)
  - bts.distance_km [T3/defect] airport_join: distance converted to km (unit change) (from 2015-01)
  - bts.join_env_p30 [T2b/benign] airport_join: pandas 3 upgrade of the join (from 2015-01)
  - bts.encoder_refit [T3/defect] encode: categorical codes re-fitted at serving time (training/serving skew) (from 2015-01)
  - bts.unknown_as_reference [T3r/defect] encode: unseen categories encoded as the reference category (from 2015-01)
- cases: 324 {'test|benign|none': 27, 'test|clean|none': 27, 'test|defect|T2': 54, 'test|defect|T3': 162, 'test|defect|T3r': 27, 'test|two|T2': 1, 'test|two|T2+T3': 6, 'test|two|T2+T3r': 2, 'test|two|T3': 12, 'test|two|T3+T3r': 6}

## cabi (round 3)
- periods: 51 (2014-Q1..2026-Q3); task binary; 13 model inputs; 5 components; 5,100,000 bronze rows in 51 files
- events: 2020-Q2 new layout: ride_id, rideable_type, started_at/ended_at, member_casual, coordinates; duration and bike number removed; timestamps partly with fractional seconds; 2020-Q3 blank station ids (dockless trips); whole-second timestamps; 2020-Q4 rideable_type code 'classic_bike' introduced next to 'docked_bike'; 2023-Q4 rideable_type code 'docked_bike' retired; 2024-Q2 timestamps with fractional seconds
- catalog:
  - cabi.positional [B/benign] trip_adapter: columns taken by position in the original order (from 2014-Q1)
  - cabi.dayfirst [T3r/defect] time_features: day-first timestamp parsing (from 2014-Q1)
  - cabi.time_env_p30 [T2b/benign] time_features: pandas 3 upgrade: duration from epoch nanoseconds via astype(int64) changes resolution (from 2014-Q1)
  - cabi.adapter_env_p30 [T2b/benign] trip_adapter: pandas 3 upgrade of the adapter (from 2014-Q1)
  - cabi.end_key_bug [T3/defect] station_join: end coordinates looked up with the start station id (copy-paste key bug) (from 2014-Q1)
  - cabi.clean_env_main [T2b/benign] clean: pandas 2.2 upgrade of the cleaning step (from 2014-Q1)
  - cabi.clean_env_p30 [T2/defect] clean: pandas 3 upgrade: chained assignment blanking round-trip distances becomes a no-op (from 2014-Q1)
  - cabi.clean_modernised [B/benign] clean: chained assignment -> .loc (from 2014-Q1)
  - cabi.encoder_refit [T3/defect] encode: categorical codes re-fitted at serving time (training/serving skew) (from 2014-Q1)
  - cabi.unknown_as_reference [T3r/defect] encode: unseen categories encoded as the reference category (from 2014-Q1)
  - cabi.user_recode_stale [T1/defect] trip_adapter: user type mapped with the Member/Casual rule: every lowercase member becomes casual (from 2020-Q2)
  - cabi.coords_lookup_stale [T1/defect] station_join: station coordinates still taken from the station table instead of the records (from 2020-Q2)
  - cabi.fmt_stale [T1/defect] time_features: timestamps parsed with the previous published format (fractional seconds unparsed) (from 2020-Q2)
  - cabi.blank_ids_stale [T1/defect] station_join: blank station ids of dockless trips compared as equal: counted as round trips (from 2020-Q3)
- cases: 312 {'test|benign|none': 28, 'test|clean|none': 28, 'test|defect|T1': 88, 'test|defect|T2': 48, 'test|defect|T3': 56, 'test|defect|T3r': 36, 'test|two|T1': 3, 'test|two|T1+T2': 8, 'test|two|T1+T3': 4, 'test|two|T2': 1, 'test|two|T2+T3': 5, 'test|two|T2+T3r': 2, 'test|two|T3': 1, 'test|two|T3+T3r': 3, 'test|two|T3r': 1}

## fars (round 3)
- periods: 15 (2010..2024); task binary; 15 model inputs; 4 components; 509,887 bronze rows in 15 files
- events: 2015 ROAD_FNC replaced by RUR_URB and FUNC_SYS (new code list); label columns added; 2016 county and city name columns added; 2018 REL_ROAD code 12 (pedestrian refuge or traffic island) added; 2020 WEATHER1, WEATHER2 and CF1-CF3 removed; 2020 TYP_INT code 11 (other intersection type) added; 2021 first header published with a byte-order mark (STATE); 2023 byte-order mark removed; 2023 ROUTE (route signing) code list revised: new codes 0, 10-13, 95, 96, 99; frontage-road, 'other' and 'unknown' codes retired
- catalog:
  - fars.adapter_env_p30 [T2b/benign] crash_adapter: pandas 3 upgrade of the adapter (from 2010)
  - fars.clean_env_main [T2b/benign] clean: pandas 2.2 upgrade of the cleaning step (from 2010)
  - fars.clean_env_p30 [T2/defect] clean: pandas 3 upgrade: chained-assignment unknown-code handling becomes a no-op (from 2010)
  - fars.clean_modernised [B/benign] clean: chained assignment -> .loc (from 2010)
  - fars.weekend_off_by_one [T3/defect] features: weekend from a 0-based weekday convention (FARS uses 1 = Sunday) (from 2010)
  - fars.features_env_p30 [T2b/benign] features: pandas 3 upgrade of the feature step (from 2010)
  - fars.encoder_refit [T3/defect] encode: categorical codes re-fitted at serving time (training/serving skew) (from 2010)
  - fars.zero_pad_state [T3/defect] encode: state key zero-padded while the encoder artifact holds unpadded codes (from 2010)
  - fars.unknown_as_reference [T3r/defect] encode: unseen categories encoded as the reference category (from 2010)
  - fars.func_layout_stale [T1/defect] crash_adapter: rural/urban and road class still read from the removed ROAD_FNC field (from 2015)
  - fars.func_alias [T1/defect] crash_adapter: FUNC_SYS codes mapped with the old ROAD_FNC table (rename without recode) (from 2015)
  - fars.weather_stale [T1/defect] crash_adapter: weather still read from the removed WEATHER1 field (from 2020)
  - fars.bom_stale [T1/defect] crash_adapter: state read from 'STATE' while the header carries a byte-order mark (from 2021)
  - fars.route_codes_stale [T1/defect] crash_adapter: route-signing codes read with the pre-2023 code list (no crosswalk) (from 2023)
- cases: 240 {'test|benign|none': 23, 'test|clean|none': 23, 'test|defect|T1': 56, 'test|defect|T2': 23, 'test|defect|T3': 69, 'test|defect|T3r': 23, 'test|two|T1+T2': 3, 'test|two|T1+T3': 9, 'test|two|T1+T3r': 2, 'test|two|T2+T3': 6, 'test|two|T2+T3r': 1, 'test|two|T3': 1, 'test|two|T3+T3r': 1}

## landreg (round 3)
- periods: 18 (2008..2025); task binary; 8 model inputs; 5 components; 2,700,000 bronze rows in 18 files
- events: 2013 category B transactions (non-standard sales) and property type 'Other' published
- catalog:
  - landreg.adapter_env_p30 [T2b/benign] sale_adapter: pandas 3 upgrade of the adapter (from 2008)
  - landreg.time_env_main [T2b/benign] time_features: pandas 2.2 upgrade of the time step (string dates still parse to nanoseconds) (from 2008)
  - landreg.time_env_p30 [T2/defect] time_features: pandas 3 upgrade: day of year via astype(int64) changes resolution (from 2008)
  - landreg.dow_one_based [T3/defect] time_features: day of week shifted to a 1-based convention (from 2008)
  - landreg.clean_env_main [T2b/benign] clean: pandas 2.2 upgrade of the cleaning step (from 2008)
  - landreg.clean_env_p30 [T2/defect] clean: pandas 3 upgrade: chained-assignment log price becomes a no-op (from 2008)
  - landreg.clean_modernised [B/benign] clean: chained assignment -> vectorised .where (from 2008)
  - landreg.area_is_outward [T3/defect] geo: postcode district used where the postcode area is expected (from 2008)
  - landreg.geo_env_p30 [T2b/benign] geo: pandas 3 upgrade of the geo step (from 2008)
  - landreg.encoder_refit [T3/defect] encode: categorical codes re-fitted at serving time (training/serving skew) (from 2008)
  - landreg.unknown_as_reference [T3r/defect] encode: unseen categories encoded as the reference category (from 2008)
  - landreg.category_scope_stale [T1/defect] clean: category B (non-standard) sales not excluded after the 2013 coverage change (from 2013)
- cases: 257 {'test|benign|none': 26, 'test|clean|none': 26, 'test|defect|T1': 23, 'test|defect|T2': 52, 'test|defect|T3': 78, 'test|defect|T3r': 26, 'test|two|T1+T2': 1, 'test|two|T1+T3': 6, 'test|two|T1+T3r': 1, 'test|two|T2': 3, 'test|two|T2+T3': 8, 'test|two|T2+T3r': 2, 'test|two|T3': 3, 'test|two|T3+T3r': 2}
