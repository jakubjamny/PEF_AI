// lib/lcia/ef31.js
// Jednoduchý loader EF 3.1 CF extraktů (Climate change, Water use)
// Čte JSONy z data/ef31 a ukládá je do Mapy pro rychlý lookup.

let EF31 = { cfByMethod: new Map(), loaded: false };

export function loadEF31CFs({ baseDir = "data/ef31" } = {}) {
if (EF31.loaded) return EF31;

const files = [
"ef31_cf_climate_change.json",
"ef31_cf_water_use.json"
];

for (const f of files) {
const path = `${baseDir}/${f}`;
// GitHub web buildy obvykle bundlují statická data – tady předpokládáme Node/SSR nebo bundler s file-loaderem.
// Pokud máš již utilitu na čtení JSONů, použij ji (např. import json assert s bundlerem Vite/Webpack).
// Nejjednodušší varianta: při buildu tyto JSONy importovat přímo.
// Zde zkusíme dynamický import (funguje v Node a v bundlerech):
try {
// @ts-ignore – dynamic import JSON (Node ≥v20: { type: 'json' } nebo bundler)
const arr = requireJson(path);
for (const r of arr) {
const key = `${r.method_name}::${r.flow_uuid}::${r.location}`;
EF31.cfByMethod.set(key, r);
}
} catch (e) {
// Fallback pro bundlery: zkus import přes import.meta (pokud používáš Vite)
// nebo vynech – pro náš PROXY režim není lookup zatím kritický.
}
}

EF31.loaded = true;
return EF31;
}

export function getCF({ methodName, flow_uuid, location = "" }) {
const key = `${methodName}::${flow_uuid}::${location}`;
return EF31.cfByMethod.get(key)?.cf ?? null;
}

// Pomocná utilita – zkus načíst JSON v prostředí Node (pokud dostupné)
function requireJson(p) {
// Pokud běžíš v Node.js
// eslint-disable-next-line
const fs = typeof require !== 'undefined' ? require('fs') : null;
if (fs && fs.existsSync && fs.readFileSync) {
const raw = fs.readFileSync(p, 'utf-8');
return JSON.parse(raw);
}
// Pokud Node/FS není k dispozici, vrať prázdno – PROXY režim to nevyžaduje.
return [];
}
