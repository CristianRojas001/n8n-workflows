✅ Table — Missing Fields vs What CAN Be Extracted From the PDF


🧱 Identification, purpose & scope
CSV_field_name	Extracted now?	Present in PDFs?	Status	General how-to extract from PDF
objeto	null	Yes (often)	Missing but in PDF	Look for heading/paragraph with OBJETO or phrase tiene por objeto. Extract the sentence(s) describing the purpose of the subsidy/convenio.
tipo_administracion	null	Yes (implicit)	Missing but in PDF	Infer from the granting body: Ayuntamiento → Local; Diputación → Local Provincial; Junta/Comunidad Autónoma → Autonómica; Ministerio/Estado → Estatal.
nivel_administracion	null	Yes (implicit)	Missing but in PDF	Map organism type to a more specific level: municipal, provincial, autonómico, estatal.
finalidad	null	Yes (implicit)	Missing but in PDF	Search for phrases like finalidad, tiene como finalidad, proyecto de promoción y difusión…. Convert to a short thematic label (e.g. Cultura, Deporte, Empleo).
finalidad_descripcion	null	Yes	Missing but in PDF	From same purpose paragraphs, keep 1–3 sentences explaining what is promoted/financed (festival, research, social inclusion, etc.).
ambito	null	Yes (implicit)	Missing but in PDF	Detect phrases like ámbito provincial, en la provincia de, en el término municipal de, ámbito estatal. Normalize to local, provincial, autonómico, estatal, internacional.
👥 Beneficiaries
CSV_field_name	Extracted now?	Present in PDFs?	Status	General how-to extract from PDF
tipos_beneficiario	[]	Yes (often)	Missing but in PDF	Look for sections titled Personas beneficiarias, Beneficiarios, Entidades beneficiarias. Map phrases (personas físicas, PYME, fundaciones, corporaciones locales, etc.) to your standard categories.
beneficiarios_descripcion	null	Yes (often)	Missing but in PDF	Take the full descriptive paragraph under the Beneficiarios section: who can receive the aid, with what characteristics.
requisitos_beneficiarios	null	Yes (often)	Missing but in PDF	Under headings like Requisitos, Condiciones de los beneficiarios, extract bullet lists/paragraphs describing legal, fiscal, and other conditions.
tipos_beneficiario_raw	null	Yes (in text)	Missing but in PDF	Same Beneficiarios section: store the raw sentences before normalizing (useful for later mapping).
tipos_beneficiario_normalized	null	Yes (via mapping)	Missing but in PDF	Apply your mapping from tipos_beneficiario_raw to normalized labels (PERSONA_FISICA, PYME, etc.).
📅 Dates (execution & justification)
CSV_field_name	Extracted now?	Present in PDFs?	Status	General how-to extract from PDF
plazo_justificacion	null	Yes (often)	Missing but in PDF	Find phrases with justificación + plazo, fecha límite, antes del. Extract the limit date and short phrase (e.g. “hasta el 15 de octubre de 2025”).
plazo_resolucion	null	Sometimes	Missing but in PDF	In bases/convocatorias, search for plazo máximo para resolver, resolver y notificar en el plazo de. Extract the number of months/days.
💶 Amounts & compatibility
CSV_field_name	Extracted now?	Present in PDFs?	Status	General how-to extract from PDF
importe_total	null	Yes (often)	Missing but in PDF	Look for importe total, presupuesto total, or similar. When not explicit but clearly derivable (sum of line items), you can compute from per-project amounts.
importe_maximo	null	Often	Missing but in PDF	In Cuantía section, locate importe máximo, no podrá superar, hasta. Take the maximum amount a beneficiary can receive.
porcentaje_financiacion	null	Sometimes	Missing but in PDF	Search text for % near financiación, coste subvencionable. Example pattern: hasta el 50% del coste.
cuantia_min	null	Sometimes	Missing but in PDF	Look for importe mínimo, no inferior a. Extract the smallest grant amount per beneficiary.
intensidad_ayuda	null	Sometimes	Missing but in PDF	When the doc states coverage like “hasta el X% del coste elegible”, store X as intensity of aid.
compatibilidad_otras_ayudas	null	Yes (often)	Missing but in PDF	Search for compatible con otras ayudas, incompatible con. Extract whole clause describing compatibility conditions.
es_compatible_otras_ayudas	null	Yes (often)	Missing but in PDF	From previous clause, set boolean: true if explicitly compatible (usually with limit “sin superar el 100% del coste”), false if explicitly incompatible.
forma_pago	null	Sometimes	Missing but in PDF	Look for forma de pago, se abonará. Extract if it’s single payment, split payments (e.g. 70% + 30%), on justification, etc.
pago_anticipado	null	Sometimes	Missing but in PDF	Detect mentions of anticipo, pago anticipado. Set boolean + small description (anticipo del 50% tras firma, etc.).
garantias	null	Sometimes	Missing but in PDF	Search garantía, aval, fianza. Store full description of guarantee requirements.
exige_aval	null	Sometimes	Missing but in PDF	If there is an obligation to present aval/fianza for anticipos, set this boolean accordingly.
📩 Application / submission / justification
CSV_field_name	Extracted now?	Present in PDFs?	Status	General how-to extract from PDF
forma_solicitud	null	Often (in convocatorias)	Missing but in PDF	In section Presentación de solicitudes, extract how to submit: presencial, electrónica, both; and if there is a standard form (modelo de solicitud).
lugar_presentacion	null	Often	Missing but in PDF	Same section: capture postal addresses (Registro General, Oficina de asistencia) and/or the mention of electronic office.
url_tramite	null	Sometimes	Missing but in PDF	Extract any https:// URL that appears in the application section (sede electrónica, form URL).
forma_justificacion	null	Yes (often)	Missing but in PDF	Look for headings Justificación or Forma de justificación. Summarise the process: required reports, invoices, deadlines.
documentacion_requerida	null	Yes (often)	Missing but in PDF	Under Documentación a presentar or similar, collect bullet/numbered lists of required documents (for request and/or justification).
sistema_evaluacion	null	Sometimes	Missing but in PDF	In competitivas, search Criterios de valoración, procedimiento de concesión. Extract description of whether it’s competitive, first-come, etc.
criterios_valoracion	null	Sometimes	Missing but in PDF	From Criterios de valoración section, extract the list of criteria and, if present, their weights/scores.
obligaciones_beneficiario	null	Yes (often)	Missing but in PDF	Use Obligaciones del beneficiario or equivalent heading. Extract numbered/bullet list of obligations (publicity, justification, conservation of docs…).
publicidad_requerida	null	Yes (often)	Missing but in PDF	Find references to logos and mentions like deberá hacer constar que la actividad está subvencionada por…. Save entire clause; can be normalized later.
subcontratacion	null	Sometimes	Missing but in PDF	Search subcontratación (or subcontratar). Capture conditions and limits (e.g. “hasta el 50% del coste subvencionable”).
modificaciones_permitidas	null	Sometimes	Missing but in PDF	Look for sections about Modificación de la resolución or alteración de las condiciones. Summarise when and how modifications are allowed.
requisitos_tecnicos	null	Sometimes	Missing but in PDF	In more technical calls, extract from Requisitos técnicos / Características técnicas any mandatory technical specs.
memoria_obligatoria	null	Yes (often)	Missing but in PDF	If justificación docs explicitly include memoria técnica and/or memoria económica, set boolean true (and optionally point to which type).
📜 Normativa, bases, raw text
CSV_field_name	Extracted now?	Present in PDFs?	Status	General how-to extract from PDF
bases_reguladoras	null	Sometimes	Missing but in PDF	Look for references like Bases reguladoras aprobadas por... or publicadas en el BOE/BOP nº ... de fecha .... Capture citation and/or link.
normativa	[]	Yes (often)	Missing but in PDF	Collect all law references: Ley, Real Decreto, Orden, plus number/year (e.g. Ley 38/2003, General de Subvenciones). Store as array.
compatibilidades	null	Yes (often)	Missing but in PDF	Full paragraph(s) about compatibility/incompatibility with other grants (can be longer text than es_compatible_otras_ayudas).
raw_gastos_subvencionables	null	Yes	Missing but in PDF	Entire original text under Gastos subvencionables or equivalent, before summarizing into gastos_subvencionables.
raw_forma_justificacion	null	Yes	Missing but in PDF	Full Justificación section text: step-by-step, docs, etc.
raw_plazo_ejecucion	null	Yes	Missing but in PDF	Original textual phrase describing execution period (del 1 de enero al 31 de agosto de 2025).
raw_plazo_justificacion	null	Yes	Missing but in PDF	Original phrase where the justification deadline appears.
raw_forma_pago	null	Sometimes	Missing but in PDF	Unprocessed paragraphs about payment schedule and conditions.
raw_compatibilidad	null	Yes	Missing but in PDF	Raw paragraph describing compatibility; can feed multiple normalized fields later.
raw_publicidad	null	Yes	Missing but in PDF	Full text describing logos, mention of funding body, design rules.
raw_garantias	null	Sometimes	Missing but in PDF	Complete paragraph on guarantees/aval requirements.
raw_subcontratacion	null	Sometimes	Missing but in PDF	Raw paragraphs where subcontratation is regulated.
🌍 Regions & instruments
CSV_field_name	Extracted now?	Present in PDFs?	Status	General how-to extract from PDF
region_mencionada	null	Yes (implicit)	Missing but in PDF	Extract all place names: municipalities, provinces, autonomous communities (Jerez de la Frontera, Cádiz, etc.) from title, purpose, and scope sections.
region_nuts	null	Yes (via mapping)	Missing but in PDF	Map region_mencionada to NUTS codes using your own geography table (ES612 for Cádiz, etc.).
sectores_raw	null	Yes (implicit)	Missing but in PDF	From title + finalidad + objeto, classify free text sectors (cultura, deporte, I+D, empleo, etc.) before any CNAE mapping.
sectores_inferidos	null	Yes (via logic)	Missing but in PDF	Map sectores_raw to your controlled sector vocabulary.
instrumentos_raw	null	Yes (often)	Missing but in PDF	Look for phrases in normative part: subvención, entrega dineraria sin contraprestación, préstamo, bonificación de cuotas, etc.
instrumento_normalizado	null	Yes (via mapping)	Missing but in PDF	Normalize instrumentos_raw to a small set (e.g. SUBVENCION, PRESTAMO, BONIFICACION_FISCAL).
procedimiento	null	Sometimes	Missing but in PDF	Detect phrases concurrencia competitiva, concesión directa, régimen de concurrencia no competitiva, etc.; map to a small controlled set.