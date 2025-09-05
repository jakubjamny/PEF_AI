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
