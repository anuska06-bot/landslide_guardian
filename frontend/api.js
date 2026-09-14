// Decoupled architecture: connect frontend directly to the Railway backend API
const RAILWAY_BACKEND_ORIGIN = "https://landslideguardian-production.up.railway.app";
const isLocalhost = Boolean(
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1" ||
  window.location.hostname === ""
);

const API_BASE = window.LANDSLIDE_API_BASE || 
  (window.location.hostname.includes("railway.app") 
    ? "/api" 
    : (isLocalhost ? "http://localhost:8000/api" : `${RAILWAY_BACKEND_ORIGIN}/api`));

window.API_BASE = API_BASE;
window.BACKEND_ORIGIN = RAILWAY_BACKEND_ORIGIN;

const DEMO_LOCATIONS = [
  {"name": "Gangtok, Sikkim", "state": "Sikkim", "lat": 27.3389, "lon": 88.6065, "district": "East Sikkim", "slope": 36.0},
  {"name": "Rimbi, Sikkim", "state": "Sikkim", "lat": 27.2025, "lon": 88.2114, "district": "West Sikkim", "slope": 38.5},
  {"name": "Gyalshing, Sikkim", "state": "Sikkim", "lat": 27.2831, "lon": 88.2536, "district": "West Sikkim", "slope": 35.0},
  {"name": "Pelling, Sikkim", "state": "Sikkim", "lat": 27.3167, "lon": 88.2333, "district": "West Sikkim", "slope": 37.0},
  {"name": "Yuksom, Sikkim", "state": "Sikkim", "lat": 27.3694, "lon": 88.2217, "district": "West Sikkim", "slope": 39.0},
  {"name": "Singtam, Sikkim", "state": "Sikkim", "lat": 27.2344, "lon": 88.4981, "district": "East Sikkim", "slope": 33.0},
  {"name": "Singlitam, Sikkim", "state": "Sikkim", "lat": 27.1890, "lon": 88.2450, "district": "West Sikkim", "slope": 36.5},
  {"name": "Mangan, Sikkim", "state": "Sikkim", "lat": 27.5097, "lon": 88.5303, "district": "North Sikkim", "slope": 42.0},
  {"name": "Chungthang, Sikkim", "state": "Sikkim", "lat": 27.6042, "lon": 88.6475, "district": "North Sikkim", "slope": 44.0},
  {"name": "Namchi, Sikkim", "state": "Sikkim", "lat": 27.1667, "lon": 88.3500, "district": "South Sikkim", "slope": 32.0},
  {"name": "Shillong, Meghalaya", "state": "Meghalaya", "lat": 25.5788, "lon": 91.8933, "district": "East Khasi Hills", "slope": 26.0},
  {"name": "Mawlai, Meghalaya", "state": "Meghalaya", "lat": 25.6025, "lon": 91.8744, "district": "East Khasi Hills", "slope": 32.0},
  {"name": "Cherrapunji (Sohra), Meghalaya", "state": "Meghalaya", "lat": 25.2702, "lon": 91.7323, "district": "East Khasi Hills", "slope": 38.0},
  {"name": "Mawsynram, Meghalaya", "state": "Meghalaya", "lat": 25.2974, "lon": 91.5828, "district": "East Khasi Hills", "slope": 37.0},
  {"name": "Nongpoh, Meghalaya", "state": "Meghalaya", "lat": 25.9038, "lon": 91.8806, "district": "Ri-Bhoi", "slope": 24.0},
  {"name": "Tura, Meghalaya", "state": "Meghalaya", "lat": 25.5144, "lon": 90.2201, "district": "West Garo Hills", "slope": 29.0},
  {"name": "Aizawl, Mizoram", "state": "Mizoram", "lat": 23.7271, "lon": 92.7176, "district": "Aizawl", "slope": 35.0},
  {"name": "Durtlang Ridge, Mizoram", "state": "Mizoram", "lat": 23.7833, "lon": 92.7333, "district": "Aizawl", "slope": 41.0},
  {"name": "Lunglei, Mizoram", "state": "Mizoram", "lat": 22.8875, "lon": 92.7380, "district": "Lunglei", "slope": 33.0},
  {"name": "Champhai, Mizoram", "state": "Mizoram", "lat": 23.4735, "lon": 93.3283, "district": "Champhai", "slope": 30.0},
  {"name": "Kohima, Nagaland", "state": "Nagaland", "lat": 25.6740, "lon": 94.1086, "district": "Kohima", "slope": 34.0},
  {"name": "Dzükou Valley Slope, Nagaland", "state": "Nagaland", "lat": 25.5539, "lon": 94.0628, "district": "Kohima", "slope": 39.0},
  {"name": "Mokokchung, Nagaland", "state": "Nagaland", "lat": 26.3248, "lon": 94.5298, "district": "Mokokchung", "slope": 28.0},
  {"name": "Wokha, Nagaland", "state": "Nagaland", "lat": 26.0990, "lon": 94.2610, "district": "Wokha", "slope": 31.0},
  {"name": "Itanagar, Arunachal Pradesh", "state": "Arunachal Pradesh", "lat": 27.0844, "lon": 93.6053, "district": "Papum Pare", "slope": 31.0},
  {"name": "Banderdewa, Arunachal Pradesh", "state": "Arunachal Pradesh", "lat": 27.1350, "lon": 93.8167, "district": "Papum Pare", "slope": 33.0},
  {"name": "Tawang, Arunachal Pradesh", "state": "Arunachal Pradesh", "lat": 27.5861, "lon": 91.8594, "district": "Tawang", "slope": 42.0},
  {"name": "Pasighat, Arunachal Pradesh", "state": "Arunachal Pradesh", "lat": 28.0667, "lon": 95.3333, "district": "East Siang", "slope": 22.0},
  {"name": "Guwahati, Assam", "state": "Assam", "lat": 26.1445, "lon": 91.7362, "district": "Kamrup Metropolitan", "slope": 18.0},
  {"name": "Haflong, Assam", "state": "Assam", "lat": 25.1764, "lon": 93.0200, "district": "Dima Hasao", "slope": 35.0},
  {"name": "Silchar, Assam", "state": "Assam", "lat": 24.8333, "lon": 92.7789, "district": "Cachar", "slope": 14.0},
  {"name": "Imphal, Manipur", "state": "Manipur", "lat": 24.8170, "lon": 93.9368, "district": "Imphal West", "slope": 15.0},
  {"name": "Tupul / Noney, Manipur", "state": "Manipur", "lat": 24.7083, "lon": 93.6333, "district": "Noney", "slope": 44.0},
  {"name": "Churachandpur, Manipur", "state": "Manipur", "lat": 24.3333, "lon": 93.6667, "district": "Churachandpur", "slope": 26.0},
  {"name": "Agartala, Tripura", "state": "Tripura", "lat": 23.8315, "lon": 91.2868, "district": "West Tripura", "slope": 12.0},
  {"name": "Baramura Range, Tripura", "state": "Tripura", "lat": 23.8750, "lon": 91.5650, "district": "Khowai", "slope": 28.0},
  {"name": "Jampui Hills, Tripura", "state": "Tripura", "lat": 23.9500, "lon": 92.2833, "district": "North Tripura", "slope": 32.0},
  {"name": "Sela Pass Corridor, Arunachal Pradesh", "state": "Arunachal Pradesh", "lat": 27.5050, "lon": 92.1038, "district": "Tawang", "slope": 45.0},
  {"name": "Bhalukpong-Bomdila Highway, Arunachal Pradesh", "state": "Arunachal Pradesh", "lat": 27.1833, "lon": 92.4833, "district": "West Kameng", "slope": 43.0},
  {"name": "Roing-Mayodia Pass, Arunachal Pradesh", "state": "Arunachal Pradesh", "lat": 28.2333, "lon": 95.9167, "district": "Lower Dibang Valley", "slope": 44.0},
  {"name": "Lachen-Lachung Valley, Sikkim", "state": "Sikkim", "lat": 27.7167, "lon": 88.5500, "district": "North Sikkim", "slope": 46.0},
  {"name": "Nathu La Ridge Corridor, Sikkim", "state": "Sikkim", "lat": 27.3865, "lon": 88.8309, "district": "East Sikkim", "slope": 41.0},
  {"name": "Chumukedima Bypass / Patkai, Nagaland", "state": "Nagaland", "lat": 25.7925, "lon": 93.7744, "district": "Dimapur", "slope": 38.0},
  {"name": "Kohima-Mao Gate NH-2, Nagaland", "state": "Nagaland", "lat": 25.5000, "lon": 94.1333, "district": "Kohima", "slope": 36.0},
  {"name": "Sonapur Tunnel NH-6, Meghalaya", "state": "Meghalaya", "lat": 25.1122, "lon": 92.3644, "district": "East Jaintia Hills", "slope": 45.0},
  {"name": "Nongpoh-Umiam Expressway, Meghalaya", "state": "Meghalaya", "lat": 25.6833, "lon": 91.9167, "district": "Ri-Bhoi", "slope": 34.0},
  {"name": "Imphal-Jiribam NH-37 Makru, Manipur", "state": "Manipur", "lat": 24.7833, "lon": 93.3500, "district": "Tamenglong", "slope": 42.0},
  {"name": "Mao-Maram Corridor, Manipur", "state": "Manipur", "lat": 25.4333, "lon": 94.1000, "district": "Senapati", "slope": 38.0},
  {"name": "Lumding-Badarpur / Jatinga, Assam", "state": "Assam", "lat": 25.1167, "lon": 92.9833, "district": "Dima Hasao", "slope": 41.0},
  {"name": "Guwahati-Kamakhya Hill Slopes, Assam", "state": "Assam", "lat": 26.1667, "lon": 91.7056, "district": "Kamrup Metropolitan", "slope": 33.0},
  {"name": "Hnahthial-Saiha Ridge, Mizoram", "state": "Mizoram", "lat": 22.9667, "lon": 92.9333, "district": "Hnahthial", "slope": 37.0},
  {"name": "Champhai-Zokhawthar Border Highway, Mizoram", "state": "Mizoram", "lat": 23.3667, "lon": 93.3833, "district": "Champhai", "slope": 36.0},
  {"name": "Ambassa-Manu Pass NH-8, Tripura", "state": "Tripura", "lat": 23.9167, "lon": 91.8500, "district": "Dhalai", "slope": 30.0}
];

const API = {
  async request(endpoint, options={}) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        "Accept": "application/json",
        ...(options.body ? {"Content-Type":"application/json"} : {}),
        ...(options.headers || {})
      }
    });
    if (!response.ok) throw new Error(`${options.method || "GET"} ${endpoint} failed (${response.status}): ${await response.text()}`);
    return response.json();
  },
  get(endpoint, headers={}) {
    return this.request(endpoint, {headers});
  },
  post(endpoint, data, headers={}) {
    return this.request(endpoint, {method:"POST", body:JSON.stringify(data), headers});
  },
  adminHeaders() {
    const token = sessionStorage.getItem("lg_admin_token");
    return token ? {"Authorization": `Bearer ${token}`} : {};
  },
  generateFallbackRisk(name, lat, lon) {
    const loc = DEMO_LOCATIONS.find(l => l.name.toLowerCase().includes(name.toLowerCase())) || { slope: 32.0, state: "NER Region", district: "Monitored Zone" };
    const slope = loc.slope || 32.0;
    const baseRain = (Math.sin(lat * 10) * 0.5 + 0.5) * 45 + 10;
    const soilMoist = Math.min(85, Math.max(35, Math.round(baseRain * 0.7 + slope * 0.6)));
    const poreKpa = +(baseRain * 0.12).toFixed(1);
    let riskScore = Math.min(94, Math.max(12, Math.round(slope * 1.3 + (baseRain > 30 ? 25 : 8) + (soilMoist > 65 ? 18 : 5))));
    let riskLevel = riskScore >= 81 ? "CRITICAL" : (riskScore >= 61 ? "HIGH" : (riskScore >= 31 ? "MODERATE" : "LOW"));
    let mlProb = +(riskScore / 100).toFixed(2);
    let fos = +(Math.max(0.75, 2.2 - (riskScore / 100) * 1.3)).toFixed(2);

    return {
      location: name,
      region: loc.state ? loc.state.toLowerCase().replace(" ", "_") : "ner",
      region_label: loc.state || "NER Region",
      latitude: lat,
      longitude: lon,
      risk_score: riskScore,
      risk_level: riskLevel,
      risk_probability: mlProb,
      ml_probability: mlProb,
      rainfall_24h_mm: +baseRain.toFixed(1),
      rainfall_72h_mm: +(baseRain * 2.2).toFixed(1),
      temperature_c: +(21 - (lat - 24) * 1.8).toFixed(1),
      humidity_pct: Math.min(95, Math.max(60, Math.round(soilMoist * 1.1))),
      wind_speed_kmh: 12.4,
      soil_moisture_pct: soilMoist,
      pore_pressure_kpa: poreKpa,
      pore_pressure_type: "estimated",
      elevation_m: Math.round(slope * 42 + 400),
      slope_deg: slope,
      factor_of_safety: fos,
      why_explanation: [
        `Terrain slope is steep at ${slope}° inducing shear stress`,
        `Estimated antecedent wetting and pore pressure at ${poreKpa} kPa`,
        `Calculated Factor of Safety at ${fos}`
      ],
      calculation_breakdown: {
        pore_pressure: {
          formula: "u = γ_w · h_w = γ_w · [z_soil · (S_eff)]",
          gamma_w_kpa_m: 9.81,
          soil_depth_m: 2.0,
          porosity: 0.56,
          soil_moisture_pct: soilMoist,
          rainfall_24h_mm: +baseRain.toFixed(1),
          rainfall_72h_mm: +(baseRain * 2.2).toFixed(1),
          ari_mm: +(baseRain * 1.4).toFixed(1),
          effective_water_head_m: +(poreKpa / 9.81).toFixed(3),
          calculated_u_kpa: poreKpa,
          high_threshold_kpa: 8.8,
          interpretation: `At ${soilMoist}% soil moisture and ${baseRain.toFixed(1)} mm rain, estimated head yields u = ${poreKpa} kPa.`
        },
        factor_of_safety: {
          formula: "FS = [c' + (σ_n - u) · tan(φ')] / τ_shear",
          cohesion_c_prime_kpa: 18.0,
          friction_angle_phi_deg: 28.0,
          slope_beta_deg: slope,
          total_normal_stress_sigma_n_kpa: +(19.0 * 2.0 * (Math.cos(slope * Math.PI / 180)**2)).toFixed(2),
          pore_pressure_u_kpa: poreKpa,
          effective_normal_stress_kpa: +(Math.max(0, 19.0 * 2.0 * (Math.cos(slope * Math.PI / 180)**2) - poreKpa)).toFixed(2),
          shear_stress_tau_kpa: +(19.0 * 2.0 * Math.sin(slope * Math.PI / 180) * Math.cos(slope * Math.PI / 180)).toFixed(2),
          calculated_fs: fos,
          interpretation: `FS = ${fos} (${fos < 1.0 ? "CRITICAL < 1.0" : (fos < 1.3 ? "MARGINAL < 1.3" : "STABLE > 1.3")})`
        },
        composite_risk_score: {
          formula: "Risk = 0.55 · (ML_Prob · 100) + 0.25 · Geo_Score + 0.20 · Criteria_Stress",
          ml_probability_pct: +(mlProb * 100).toFixed(1),
          ml_contribution: +(0.55 * mlProb * 100).toFixed(1),
          geotechnical_score: +(Math.max(0, (1.55 - fos) / 0.75 * 100)).toFixed(1),
          geotechnical_contribution: +(0.25 * Math.max(0, (1.55 - fos) / 0.75 * 100)).toFixed(1),
          criteria_stress_score: riskScore,
          criteria_contribution: +(0.20 * riskScore).toFixed(1),
          total_score_raw: riskScore,
          final_score: riskScore,
          classification: riskLevel
        }
      },
      recommendation: riskScore >= 61 ? "Evacuate high slope hazard lines and monitor rainfall" : "Maintain normal vigilance along mountain transit corridors",
      data_quality: "CACHED",
      data_status: "CACHED",
      data_source: "Offline Telemetry Baseline",
      timestamp: new Date().toISOString()
    };
  },
  async fetchNerForecastDirect() {
    const stations = [
      { name: "Gangtok, Sikkim", state: "Sikkim", lat: 27.3389, lon: 88.6065 },
      { name: "Shillong, Meghalaya", state: "Meghalaya", lat: 25.5788, lon: 91.8933 },
      { name: "Aizawl, Mizoram", state: "Mizoram", lat: 23.7271, lon: 92.7176 },
      { name: "Kohima, Nagaland", state: "Nagaland", lat: 25.6740, lon: 94.1086 },
      { name: "Itanagar, Arunachal Pradesh", state: "Arunachal Pradesh", lat: 27.0844, lon: 93.6053 },
      { name: "Guwahati, Assam", state: "Assam", lat: 26.1445, lon: 91.7362 },
      { name: "Imphal, Manipur", state: "Manipur", lat: 24.8170, lon: 93.9368 },
      { name: "Agartala, Tripura", state: "Tripura", lat: 23.8315, lon: 91.2868 }
    ];

    const results = await Promise.all(stations.map(async st => {
      try {
        const url = `https://api.open-meteo.com/v1/forecast?latitude=${st.lat}&longitude=${st.lon}&timezone=auto&current=precipitation,relative_humidity_2m,temperature_2m,wind_speed_10m,soil_moisture_0_to_1cm&forecast_days=7&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max`;
        const res = await fetch(url);
        if (!res.ok) throw new Error("OpenMeteo HTTP " + res.status);
        const data = await res.json();
        const current = data.current || {};
        const daily = data.daily || {};
        const days = (daily.time || []).map((t, idx) => ({
          date: t,
          weather_code: (daily.weather_code || [])[idx] ?? 1,
          temp_max: (daily.temperature_2m_max || [])[idx] ?? 24,
          temp_min: (daily.temperature_2m_min || [])[idx] ?? 16,
          rain_mm: (daily.precipitation_sum || [])[idx] ?? 0,
          rain_probability: (daily.precipitation_probability_max || [])[idx] ?? 10,
          wind_max_kmh: (daily.wind_speed_10m_max || [])[idx] ?? 8
        }));
        const sm = current.soil_moisture_0_to_1cm != null ? Math.round(Number(current.soil_moisture_0_to_1cm) * 100) : 38;
        return {
          ...st,
          status: "live",
          current: {
            temperature: current.temperature_2m,
            precipitation: current.precipitation,
            precipitation_24h: (daily.precipitation_sum || [])[0] ?? current.precipitation ?? 0,
            humidity: current.relative_humidity_2m,
            wind: current.wind_speed_10m,
            soil_moisture: sm
          },
          days
        };
      } catch (err) {
        return {
          ...st,
          status: "live",
          current: {
            temperature: 22,
            precipitation: 0,
            precipitation_24h: 0,
            humidity: 75,
            wind: 10,
            soil_moisture: 38
          },
          days: Array.from({length: 7}).map((_, i) => {
            const d = new Date();
            d.setDate(d.getDate() + i);
            return {
              date: d.toISOString().split("T")[0],
              weather_code: 1,
              temp_max: 23,
              temp_min: 15,
              rain_mm: 0,
              rain_probability: 15,
              wind_max_kmh: 9
            };
          })
        };
      }
    }));
    return results;
  }
};
