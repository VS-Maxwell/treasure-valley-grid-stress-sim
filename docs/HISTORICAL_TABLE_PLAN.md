# Historical and offline table plan

Updated: 2026-09-14

## Runtime rule

The shipped simulator must open its historical record from immutable local packs. Public APIs may be used by explicit acquisition jobs, but a successful website or API response is not a runtime dependency and is not proof that data were preserved. Each acquisition keeps original bytes, provider identifiers, retrieval time, byte count, full SHA-256, format validation and a transformation receipt. Keyed provider services are optional online overlays; credentials are never bundled in browser JavaScript or committed to Git.

## Shared columns

Every scientific or infrastructure fact must resolve through stable identifiers rather than labels alone. Tables use these common fields where applicable:

- `record_id`, `source_id`, `source_record_id`, `receipt_id`;
- `valid_time_start`, `valid_time_end`, `observed_at`, `retrieved_at`;
- `longitude`, `latitude`, `geometry_id`, `crs`, `horizontal_datum`, `vertical_datum`;
- `value`, `unit`, `parameter_code`, `quality_code`, `missing_reason`;
- `truth_state`: observed, ingested, reconstructed, modeled-screening, modeled-validated, projected, synthetic;
- `review_state`, `authority_scope`, `redistribution_state`, `limitations`.

No null measurement is converted to zero. Source values and display transforms remain separate.

## Foundation and lineage

| Table | Grain | Purpose |
|---|---|---|
| `source` | one row per provider dataset/version | Provider, source URL/DOI, terms, publication date and scope |
| `source_object` | one row per original file/API page | Provider ID, local original path, bytes, SHA-256, media type and validation result |
| `transform_receipt` | one row per derived artifact | Tool/version, inputs, parameters, output hash, row counts and exclusions |
| `time_index` | one row per simulation time step | Deep time, historical dates and future scenario time in one ordered axis |
| `geometry` | one row per stable spatial object | Point/line/polygon identity, CRS and geometry-pack offset |
| `geography_crosswalk` | one row per object-to-region relation | Model cell, watershed, county, Tribal territory and grid region links with method/confidence |
| `unit_definition` | one row per unit | Canonical unit, dimensions and exact conversion rule |

## Terrain, geology and aquifers

| Table | Grain | Required content |
|---|---|---|
| `terrain_sample` | one row/packed value per terrain vertex | Longitude, latitude, elevation meters NAVD88, source tile and sample method |
| `terrain_tile` | one row per original DEM tile/version | Bounds, resolution, datum, source hash and acquisition receipt |
| `geologic_unit` | one row per named unit | Unit name/code, age, lithology, porosity/permeability evidence and source |
| `borehole` | one row per well/core hole | Location, collar elevation, total depth, drilling method and authority |
| `borehole_interval` | one row per logged depth interval | Top/bottom depth, lithology, formation, screen/open interval and quality code |
| `aquifer_model_cell` | one row per model/layer/row/column | Active state, top and bottom elevations, thickness, hydraulic properties and model identity |
| `aquifer_layer_surface` | packed surface per model layer | Top/bottom geometry for rendering the six TVGWFM layers and later separate ESPAM layers |
| `model_domain_link` | one row per domain seam | TVGWFM-to-ESPAM boundary/coupling method, variables, cadence, validation and limitations |

The published TVGWFM `DIS` file already contains six explicit bottom arrays. Those are the authoritative first geometry for that model; core and borehole logs are independent evidence used to interpret or test the hydrogeologic framework. Gaps are interpolated only under an explicit method and remain labeled reconstructed.

## Groundwater and surface water

| Table | Grain | Required content |
|---|---|---|
| `groundwater_measurement` | one row per field measurement | Site, time, parameter, value/unit, approval/qualifier, land-surface datum and missingness |
| `monitoring_site` | one row per well/site version | Coordinates, altitude/datum, construction depth, aquifer code and source |
| `well_screen_interval` | one row per screen/open interval | Well, top/bottom depth, unit and evidence; required before layer assignment |
| `modeled_head` | packed values by run/time/layer/cell | Head in source units, inactive sentinel, model run and quantization receipt |
| `groundwater_budget` | model run/time/component | Recharge, pumping, storage, river exchange and other inflow/outflow terms |
| `stream_reach` | one row per directed reach | From-node, to-node, waterbody, watershed and flow direction |
| `stream_observation` | site/time/parameter | Discharge, stage, temperature or quality with approval and unit |
| `canal_diversion` | diversion/time | Withdrawal, delivery, return flow, destination service area and source |
| `water_right_or_allocation` | right/version | Legal allocation facts kept distinct from measured use and model assumptions |

## Dams and reservoirs

| Table | Grain | Required content |
|---|---|---|
| `dam` | one row per NID structure/version | NID ID, name, point, river, owner class, type, completion year, height and status |
| `reservoir` | one row per impoundment/version | Storage levels, surface area, purposes and linked dam IDs |
| `dam_watershed_path` | dam-to-receiving-system path | Directed reach/catchment path and class: upstream supply, in-valley, downstream, unrelated or unresolved |
| `reservoir_observation` | reservoir/time/parameter | Storage, elevation, inflow, release and spill with units and quality |
| `dam_operation` | dam/time interval | Release rule or historical operation; observed operations stay separate from scenario rules |
| `dam_hydropower_link` | dam-to-generator relation | EIA plant/generator IDs, name and distance evidence, capacity, match status and review |

All dams that feed the region are selected by watershed connectivity, not a bounding box. Non-powered dams remain water nodes; hydropower dams become both water and energy nodes.

## Energy and electrical grid

| Table | Grain | Required content |
|---|---|---|
| `energy_plant` | one row per plant/version | EIA plant ID, name, coordinates, operator, balancing authority and status |
| `energy_generator` | one row per generator/version | Fuel/technology, nameplate and seasonal capacity, operating/planned/retired dates |
| `energy_generation` | generator or plant/month | Net generation, fuel consumption where applicable, unit and reporting status |
| `renewable_resource` | cell/time or summary period | Solar irradiance, wind speed/power class, hydro resource and source model |
| `storage_asset` | one row per battery/pumped-storage unit | Power MW, energy MWh, duration, efficiency, status and connection evidence |
| `substation` | one row per substation/version | Stable ID, location, voltage levels, operator and source provenance |
| `bus` | one row per model bus/version | Bus type, nominal kV, source substation/generator/load links and model scope |
| `branch` | one row per directed/undirected electrical branch | From/to bus, circuit, voltage, impedance/rating evidence and status |
| `transmission_corridor` | one row per visible line geometry/version | Geometry, voltage, operator and relation to one or more modeled branches |
| `electric_load` | zone or bus/time | MW/MWh, sector, weather basis and observed/estimated status |
| `grid_project` | one row per project/version | Wind, solar, hydro, storage, transmission or substation project; proposed/queued/active/retired/canceled kept distinct |
| `power_flow_result` | run/time/bus-or-branch | Voltage angle/magnitude, MW/Mvar flow, loading and solver receipt |

The visible map may show all receipted projects, but the solver uses only buses and branches with adequate topology and electrical parameters. The current 94-bus/156-branch screening graph is the next interactive target; proximity alone cannot create a new electrical connection.

## Climate, atmosphere, land and pollutants

| Table | Grain | Required content |
|---|---|---|
| `weather_observation` | station/time/parameter | Temperature, precipitation, humidity, wind and quality flags |
| `climate_projection` | model/member/scenario/cell/time | Downscaled variable, ensemble member, bias correction and source experiment |
| `snowpack` | basin/time | SWE, snow depth, melt and observation/model source |
| `land_cover` | geometry/version | Land-cover class, imperviousness, crop/irrigation class and source year |
| `soil_property` | soil unit/depth interval | Texture, hydraulic property, erodibility and source |
| `pollutant_site` | one row per source/legacy pile/version | Material, geometry, containment state, authority and evidence confidence |
| `pollutant_observation` | site/time/analyte | Concentration, medium, sample method, detection limit, unit and qualifier |
| `pollutant_process_parameter` | material/scenario | Phase change, dissolution, transport parameter and evidence range |

## Risk, scenarios and coupled runs

| Table | Grain | Required content |
|---|---|---|
| `scenario` | one row per immutable scenario version | Assumptions, forcing set, authority, parent and status |
| `scenario_parameter` | scenario/model/parameter | Value/distribution, unit, source or elicitation method |
| `model_run` | one row per execution | Code commit, environment, inputs, seed, runtime, completion and receipt |
| `coupling_exchange` | run/time/from-model/to-model/variable | Water-energy-atmosphere transfer value, unit and conservation check |
| `raven_sample` | risk run/sample/parameter | Distribution draw, seed and dependency/correlation identity |
| `risk_result` | run/asset/hazard/metric | Probability, consequence, uncertainty interval and screening/validated state |
| `validation_metric` | run/dataset/metric | Residual/bias/RMSE/coverage with acceptance threshold and reviewer |

## Archives, education and local AI

| Table | Grain | Required content |
|---|---|---|
| `archive_object` | one row per original archival object | Custody, original hash/bytes, access class, community authority and derivative links |
| `archive_segment` | page/time segment | OCR/transcript text, language, speaker where approved, time/page offsets and QC state |
| `archive_entity_event` | evidence-backed mention | Entity/event/time/place plus segment citations and reviewer state |
| `embedding_index` | approved segment/vector-model version | Local retrieval pointer; never substitutes for the original or acceptance review |
| `lesson` | lesson/version | Audience, objectives, approved sources, activities and educator-review state |
| `ai_output_receipt` | one row per retained AI result | Model/version, prompt policy, cited inputs, output hash and human decision boundary |

Protected or sovereignty-sensitive records are not automatically included merely because the game shell can hold them. Storage, access gates, citation, and community authority remain separate from software licensing.

## Browser packaging

Large normalized tables should live in Parquet/GeoParquet in the data lake and be compiled into scene-specific browser packs:

- JSON manifests for schema, counts, bounds, source hashes and limitations;
- little-endian typed binaries for dense numeric arrays;
- compact GeoJSON or binary geometry for small vector layers;
- precomputed chart series and map tiles for historical playback;
- immutable filenames whenever a schema or artifact set changes.

The browser verifies structure and dimensions. Build/release validation performs full hashes. The original provider objects remain outside the web bundle on the T drive and preservation storage.
