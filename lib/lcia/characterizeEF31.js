// lib/lcia/characterizeEF31.js
// EF 3.1 (proxy) – použije tvoje existující součty a jen je namapuje do EF kategorií.
// Nepotřebuje loader EF31 (JSONy) – ten využijeme až v ILCD režimu.

export function characterizeEF31(passportCalc, { includeMaterialTransport = false, audit } = {}) {
  // Climate change
  let cc = (passportCalc.cc_materials || 0)
         + (passportCalc.cc_packaging || 0)
         + (passportCalc.cc_customer_distribution || 0);

  if (includeMaterialTransport) {
    cc += (passportCalc.cc_material_transport || 0);
    audit?.add?.("cc.material_transport.included", true);
  } else {
    audit?.add?.("cc.material_transport.included", false);
  }

  // Water use (proxy 1:1 – už pracuješ s m³ agregáty)
  let wu = (passportCalc.wu_materials || 0)
         + (passportCalc.wu_packaging || 0)
         + (passportCalc.wu_use_phase_washing || 0);

  // Audit/metainfo
  audit?.add?.("lcia.method", "EF 3.1");
  audit?.add?.("lcia.mode", "proxy");
  audit?.add?.("lcia.cc.source", "proxy-aggregates");
  audit?.add?.("lcia.wu.source", "proxy-aggregates");

  const impacts = { "Climate change": cc, "Water use": wu };
  const lcia = { method: "EF 3.1", mode: "proxy", version: "3.1", categories: Object.keys(impacts) };

  return { impacts, lcia };
}
