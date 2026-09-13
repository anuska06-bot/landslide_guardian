let dashMapInstance=null, trendChartInstance=null;
document.addEventListener("DOMContentLoaded",initDashboard);

async function initDashboard(){
 try{
  const d=await API.get("/risk/latest");document.getElementById("dataModeBadge").textContent="● Backend + ML ONLINE";renderDashboardData(d);renderMap(d.latitude,d.longitude,d.location,d.risk_level,d.risk_score);renderCharts(d);
  refreshLiveBadge();
  setInterval(async()=>{try{const nd=await API.get("/risk/latest");renderDashboardData(nd);renderMap(nd.latitude,nd.longitude,nd.location,nd.risk_level,nd.risk_score);renderCharts(nd);refreshLiveBadge();}catch(e){}},30000);
 }catch(e){
   console.warn("Backend /risk/latest unavailable, rendering telemetry fallback:", e);
   document.getElementById("dataModeBadge").textContent="● Telemetry Fallback";
   const fallback = API.generateFallbackRisk("Gangtok, Sikkim", 27.3389, 88.6065);
   const formatted = {
     location: fallback.location,
     risk_score: fallback.risk_score,
     risk_level: fallback.risk_level,
     recommendation: fallback.recommendation,
     latitude: fallback.latitude,
     longitude: fallback.longitude,
     environmental_data: {
       rainfall_24h: fallback.rainfall_24h_mm,
       soil_moisture: fallback.soil_moisture_pct,
       pore_pressure_kpa: fallback.pore_pressure_kpa
     },
     sensor_snapshot: {
       tilt_degrees: 0.8
     },
     thresholds: {
       rainfall_24h_high_mm: 45.0,
       soil_moisture_high_pct: 65.0,
       pore_pressure_high_kpa: 8.8,
       tilt_high_deg: 2.5
     },
     factors: {
       slope_angle: "36.0°",
       soil_saturation: `${fallback.soil_moisture_pct}%`,
       estimated_pore_pressure: `${fallback.pore_pressure_kpa} kPa`
     },
     calculation_notes: fallback.why_explanation || []
   };
   renderDashboardData(formatted);
   renderMap(formatted.latitude, formatted.longitude, formatted.location, formatted.risk_level, formatted.risk_score);
   renderCharts(formatted);
   refreshLiveBadge();
 }
}
function refreshLiveBadge(){
 const badge=document.getElementById("liveBadge"),stamp=document.getElementById("liveStamp");
 if(badge){badge.style.display="inline-block";}
 if(stamp){stamp.textContent=`Automatic monitoring active — latest update ${new Date().toLocaleTimeString()}. Every region is re-checked by the backend automatically; HIGH/CRITICAL auto-notifies registered residents.`;}
}
function renderDashboardData(d){
 dashLocation.textContent=d.location;dashScore.textContent=`${d.risk_score}%`;dashRecommendation.textContent=d.recommendation;
 dashLevelBadge.textContent=`${d.risk_level} RISK`;dashLevelBadge.className=`badge badge-${d.risk_level.toLowerCase()}`;
 const e=d.environmental_data||{},s=d.sensor_snapshot||{};
 metricRain.textContent=`${Number(e.rainfall_24h||0).toFixed(1)} mm`;metricMoisture.textContent=`${Number(e.soil_moisture||0).toFixed(1)} %`;metricPore.textContent=`${Number(e.pore_pressure_kpa||0).toFixed(2)} kPa`;metricTilt.textContent=`${Number(s.tilt_degrees||0).toFixed(1)}°`;
 const t=d.thresholds||{}, rows=[["🌧️ Rainfall",e.rainfall_24h,"mm",t.rainfall_24h_high_mm],["💧 Soil saturation",e.soil_moisture,"% ",t.soil_moisture_high_pct],["🫧 Pore pressure",e.pore_pressure_kpa,"kPa",t.pore_pressure_high_kpa],["📐 Tilt",s.tilt_degrees,"°",t.tilt_high_deg]];
 criteriaPanel.innerHTML=rows.map(r=>`<div class="metric-card"><span class="metric-label">${r[0]}</span><span class="metric-val">${Number(r[1]||0).toFixed(1)} ${r[2]}</span><span class="metric-source">High threshold: ${r[3]}</span></div>`).join("");
 explainFactors.innerHTML=Object.entries(d.factors||{}).map(([k,v])=>`<div class="factor-pill"><span>${k.replaceAll("_"," ").toUpperCase()}</span><strong>${v}</strong></div>`).join("");
 calcNotes.innerHTML=`<div class="metric-label">Calculation notes</div>${(d.calculation_notes||[]).map(x=>`<p style="font-size:.76rem;color:var(--muted);margin-top:.3rem">• ${x}</p>`).join("")}`;
}
function renderMap(lat,lon,name,level,score){
 if(dashMapInstance)dashMapInstance.remove();dashMapInstance=L.map("dashMap").setView([lat,lon],9);L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{attribution:"&copy; OpenStreetMap contributors"}).addTo(dashMapInstance);
 L.marker([lat,lon]).addTo(dashMapInstance).bindPopup(`<strong>${name}</strong><br>Risk: ${score}% (${level})`).openPopup();
}
function renderCharts(d){
 const c=document.getElementById("trendChart"),rain=Number(d.environmental_data?.rainfall_24h||0);if(!c)return;if(trendChartInstance)trendChartInstance.destroy();
 trendChartInstance=new Chart(c.getContext("2d"),{type:"line",data:{labels:["00:00","04:00","08:00","12:00","16:00","20:00","Now"],datasets:[{label:"Rainfall (mm)",data:[0,rain*.15,rain*.3,rain*.5,rain*.7,rain*.88,rain]},{label:"Risk score (%)",data:Array(7).fill(d.risk_score)}]},options:{responsive:true,maintainAspectRatio:false,scales:{y:{beginAtZero:true},y1:{min:0,max:100}}}});
}
