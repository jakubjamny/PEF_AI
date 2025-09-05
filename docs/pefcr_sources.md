# PEFCR A&F – zdrojové tabulky a parametry (profil A&F_EU_2025)

## Use-phase (CC + WU)
- **Frekvence praní / počet použití mezi praními:** zdroj = PEFCR, sekce Use stage (tabulky „washing types / number of uses between washes / drying / ironing“) – doplníme přesné číslo tabulky a stranu.
- **Teplota praní (°C):** zdroj = PEFCR Use stage – doplníme tab./stranu.
- **Voda na praní (L / cyklus):** zdroj = PEFCR Use stage – doplníme tab./stranu.
- **Energie na praní (kWh / cyklus):** zdroj = PEFCR Use stage – doplníme tab./stranu.
- **Metoda sušení (line/tumble) – podíly/spotřeby:** zdroj = PEFCR Use stage – doplníme tab./stranu.
- **Podíl žehlení/steam (IRON share):** zdroj = PEFCR Use stage – doplníme tab./stranu.
- **Pozn.:** při auditu uvedeme i grid mix „EF_GRID_ELECTRICITY_GWP_KGCO2_PER_KWH“ (zdroj EF/PEF).

## Transport (agregované tkm)
- **EF faktory pro road/sea/rail/air:** zdroj = PEF/EF dataset / PEFCR default transport parameters – doplníme tab./stranu.
- **TKM výpočet (sanity test):** definice tkm ≈ km × product.weight_kg/1000 (tolerance 1e-3).

## End of Life (EoL/CFF – minimum pro CC + WU)
- **R2 (recycling share), R3 (energy recovery), landfill share:** zdroj = PEFCR EoL – doplníme tab./stranu.
- **Recycling yield a ztráty:** zdroj = PEFCR EoL – doplníme tab./stranu.
- **Energy recovery credit (kgCO₂/kWh):** zdroj = EF/PEF – doplníme.
- **Pozn.:** zatím používáme agregovaný koeficient v env; substituční CF rozpracujeme později.

## ILCD pokrytí (materiály + balení)
- **knowledge/lci_map.csv** – mapuje interní kódy na ILCD flow + FU (1 kg).
- **Balení (karton/LDPE) – volitelně:** přidáme ILCD položky ke snížení proxy podílu.

## Evidenční poznámky
- Verze dokumentů (PEFCR v3.1), cesty v repu, commit hash, datum.
- Při doplnění tabulky vždy uveď: **dokument → sekce/tabulka → strana**.


# PEFCR A&F v3.1 — Use phase defaults (Tables 39–42)

Tento soubor popisuje, z jakých tabulek PEFCR A&F v3.1 čerpáme defaulty pro use-phase a jak se mapují na env proměnné.

## Zdroje (PEFCR v3.1)
- **Washing types & temperatures** – Table 39 “Default washing types and specific instructions” (kap. 6.4.1, str. ~165–166). Používáme teplotu z řádku **All materials** dle podkategorie (např. T-shirts: 40 °C; Sweaters: 30 °C; Underwear: 60 °C). :contentReference[oaicite:0]{index=0}
- **Uses between washes** – Table 40 “Number of uses between washes” (kap. 6.4.1, str. ~167). Hodnota „Average uses prior to washing“. Převádíme na `PEF_USE_WASH_FREQ_PER_MONTH` vztahem  
  `freq = PEF_USE_AVG_MONTHLY_USES / uses_between_washes`. :contentReference[oaicite:1]{index=1}
- **Drying shares** – Table 41 “Data for drying per product sub-category” (kap. 6.4.2, str. ~168). Bereme podíl **Tumble drying** (např. T-shirts 30 %, Underwear 35 %). :contentReference[oaicite:2]{index=2}
- **Ironing / steaming** – Table 42 “Data for ironing and steaming” (kap. 6.4.3, str. ~169). Bereme `% garments ironed per use` a `time per garment (min)`. V PEFCR je žehlení **po každém praní** s danou pravděpodobností. :contentReference[oaicite:3]{index=3}
- **Default datasets pro use phase** – odkaz na **Annex VII** (samostatný XLSX): „Default datasets & DQR“ tabs. (Použitelné, pokud místo parametrického výpočtu použijeme přímo EF dataset.) :contentReference[oaicite:4]{index=4}

## Mapování → env proměnné
- `PEFCR_USE_PHASE_APPLY` (bool): zap/vyp PEFCR profil v R3.
- `PEF_USE_AVG_MONTHLY_USES` (č./měsíc): průměr použití za měsíc (default 20).  
  → `PEF_USE_WASH_FREQ_PER_MONTH = AVG_MONTHLY_USES / (Tab. 40)`.
- `PEF_USE_WASH_TEMP_C`: přepisujeme podle Tab. 39 (All materials) dle podkategorie.
- `PEF_USE_WATER_L_PER_WASH`: (L/cyklus) – zůstává parametrizované; EF dataset viz Annex VII. :contentReference[oaicite:5]{index=5}
- `PEF_USE_ENERGY_KWH_PER_WASH`: (kWh/cyklus) – parametrizované; případně nahraditelné EF datasetem.
- `PEF_USE_ENERGY_KWH_PER_TUMBLE_DRY`: (kWh/cyklus) – pro výpočet sušení; podíl sušičky z Tab. 41.
- `PEF_USE_IRON_KWH_PER_MIN`: (kWh/min) – pro výpočet žehlení; pravděpodobnost a min/oděv z Tab. 42.
- `use_phase.tumble_dry_share` / `use_phase.air_dry_share`: ukládáme do JSON podle Tab. 41.

## Poznámky
- Při **blendech** PEFCR doporučuje řídit se materiálem s nejvyšším podílem; pokud není zřejmý, použít „All materials“. :contentReference[oaicite:6]{index=6}
- U **footwear** má PEFCR odlišné zacházení (my defaultně nepřepisujeme — zůstává stávající env logika). :contentReference[oaicite:7]{index=7}

# PEFCR A&F v3.1 — Use phase defaults (Tables 39–42)

Tento dokument popisuje, z jakých tabulek PEFCR A&F v3.1 čerpáme defaulty pro use-phase a jak se mapují na proměnné v pipeline.

## Zdroje (PEFCR v3.1)
- **Table 39** – Default washing types & temperatures (kap. 6.4.1, p. 165–166).
- **Table 40** – Number of uses between washes (kap. 6.4.1, p. 167).
- **Table 41** – Drying shares per sub-category (kap. 6.4.2, p. 168).
- **Table 42** – Ironing & steaming data (kap. 6.4.3, p. 168).
- **Annex VII (XLSX)** – Default datasets (energy/water per wash by temperature, tumble kWh/cycle, iron kWh/min).

## Mapování → proměnné a dataset
- `PEF_USE_MODE = dataset|parametric` — přepíná, zda se berou hodnoty z datasetu (JSON) nebo z env.
- `USE_PHASE_DATASET_JSON` — JSON s defaulty (viz `data/ef31/use_phase_datasets_v31.json`).
- Pokud dataset chybí pro danou subkategorii/teplotu, skript padá na **env fallback**:
  - `PEF_USE_ENERGY_KWH_PER_WASH`, `PEF_USE_WATER_L_PER_WASH`,
  - `PEF_USE_ENERGY_KWH_PER_TUMBLE_DRY`, `PEF_USE_IRON_KWH_PER_MIN`.
