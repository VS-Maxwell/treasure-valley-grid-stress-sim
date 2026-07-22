(function(){
  'use strict';
  var model = {
    visibleFeatures: 'Public-data inventory',
    screeningNetwork: '94 buses · 156 usable lines',
    interactiveNetwork: '12 selected buses',
    transformers: 'Idealized; parameters unavailable',
    truth: 'MODELED-SCREENING'
  };
  function el(tag, attrs, html){var n=document.createElement(tag);Object.keys(attrs||{}).forEach(function(k){n.setAttribute(k,attrs[k]);});if(html!=null)n.innerHTML=html;return n;}
  function openDrawer(section){var d=document.getElementById('watchdog-drawer');d.classList.add('open');d.setAttribute('aria-hidden','false');if(section){var target=document.getElementById(section);if(target)target.scrollIntoView({block:'start'});}}
  function closeDrawer(){var d=document.getElementById('watchdog-drawer');d.classList.remove('open');d.setAttribute('aria-hidden','true');}
  var rail=el('nav',{id:'watchdog-rail','aria-label':'Model status and evidence controls'},
    '<span class="wd-brand">Earth-State Watchdog</span>'+
    '<span class="wd-pill screening">'+model.truth+'</span>'+
    '<span class="wd-pill"><b>94 / 156</b> screening graph</span>'+
    '<span class="wd-pill"><b>12</b> interactive buses</span>'+
    '<button class="wd-action" data-open="wd-scope">Model scope</button>'+
    '<button class="wd-action" data-open="wd-risk">RAVEN risk</button>'+
    '<button class="wd-action" data-open="wd-truth">Evidence</button>');
  var drawer=el('aside',{id:'watchdog-drawer','aria-hidden':'true','aria-label':'Model scope, risk, and evidence'},
    '<div class="wd-head"><div><h2>What this model can—and cannot—say</h2><div class="truth screening">MODELED-SCREENING</div></div><button class="wd-close" aria-label="Close">×</button></div>'+
    '<section class="wd-section" id="wd-scope"><h3>Network scope</h3><div class="wd-grid"><div class="wd-card"><b>94 buses</b><span>larger screening representation</span></div><div class="wd-card"><b>156 lines</b><span>usable screening branches</span></div><div class="wd-card"><b>12 buses</b><span>selected interactive solver</span></div><div class="wd-card"><b>Idealized</b><span>transformers lack public impedance/tap data</span></div></div><p class="wd-callout">A line visible on the map is not necessarily represented in the electrical calculation. Derived and collapsed corridors must be read as screening abstractions.</p></section>'+
    '<section class="wd-section" id="wd-truth"><h3>Evidence states</h3><p><span class="truth ingested">INGESTED</span> Public geometry or value loaded from a named source.</p><p><span class="truth screening">MODELED-SCREENING</span> Computed with simplifying assumptions for comparison and research prioritization—not operations.</p><p><span class="truth unknown">BLOCKED-MISSING</span> Required authoritative parameters or validation evidence were not available.</p><p>Every operational-sounding conclusion requires a linked source, transformation record, units, timestamp, uncertainty, and validation receipt.</p></section>'+
    '<section class="wd-section" id="wd-risk"><h3>RAVEN risk spine</h3><p>Risk scenarios connect hazard, exposure, vulnerability, controls, residual risk, early warnings, decision authority, and seven-generation lock-in.</p><p class="wd-callout">The displayed probability, LOLE, and EUE values are unvalidated scenario assumptions until the corresponding RAVEN input deck, seed, version, output, and run receipt are linked.</p><ul><li>Grid: congestion, voltage, transformer, heat, wildfire, common-mode failure.</li><li>Water: drought, recharge loss, pumping feedback, flood and quality.</li><li>Land: imperviousness, channelization, grading, erosion and habitat fragmentation.</li><li>Governance: unequal burdens, opaque subsidy, consultation failure and irreversible lock-in.</li></ul></section>'+
    '<section class="wd-section"><h3>Follow the system</h3><div class="wd-paths"><button data-path="energy">Follow energy</button><button data-path="water">Follow water</button><button data-path="nexus">Follow nexus</button><button data-path="risk">Follow risk</button></div><p>These paths change the visible domain controls; they do not create new measurements or causal proof.</p></section>'+
    '<section class="wd-section"><h3>Public-interest questions</h3><ul><li>Who decides?</li><li>Who benefits or is paid?</li><li>Who bears cost and risk?</li><li>What remains uncertain?</li><li>Which future options become difficult to reverse?</li></ul><p>Missing Tribal representation in a public record is a data or governance gap—not evidence of absent Tribal presence, activity, knowledge, or rights.</p></section>');
  document.body.appendChild(rail);document.body.appendChild(drawer);
  rail.addEventListener('click',function(e){var id=e.target.getAttribute('data-open');if(id)openDrawer(id);});
  drawer.querySelector('.wd-close').addEventListener('click',closeDrawer);
  document.addEventListener('keydown',function(e){if(e.key==='Escape')closeDrawer();});
  drawer.addEventListener('click',function(e){var path=e.target.getAttribute('data-path');if(!path)return;if(path==='risk'){openDrawer('wd-risk');return;}var tab=document.querySelector('[data-domain-tab="'+path+'"]');if(tab){tab.click();closeDrawer();}});
  setTimeout(function(){var splash=document.getElementById('game-entry-screen');if(!splash||splash.style.display==='none')openDrawer('wd-scope');},1800);
})();
