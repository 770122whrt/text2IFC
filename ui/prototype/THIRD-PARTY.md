# Third-party resources

The optional browser engine is Plotly.js **3.3.1**, distributed under the MIT license. The downloadable standalone preview embeds the copy supplied with this environment's Plotly package. The repository preview can fetch the same pinned version with `node ui/prototype/prepare.mjs`; it otherwise uses the small schematic-only compatibility view.

Sources:
- https://github.com/plotly/plotly.js
- https://cdn.plot.ly/plotly-3.3.1.min.js
- https://plotly.com/javascript/3d-mesh/
- https://plotly.com/javascript/plotlyjs-events/

The header and license notice in the distributed Plotly bundle are preserved. No system font files are included. All displayed buildings, names and values in this preview are illustrative, not copied IFC samples or repair results.

Formal IFC integration is planned with That Open's official IfcLoader / Highlighter components; they are **not yet installed or used by this prototype**. Their source, version compatibility and license notices will be recorded when integrated. The compatibility renderer is only for reviewing this small schematic scene; it must not grow into a replacement IFC engine.
