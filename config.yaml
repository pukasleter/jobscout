# ============================================================
# Job-Agent – Konfiguration (Stand: Profil vom 03.10.2026)
# Das inhaltliche Profil steckt NICHT hier, sondern im Prompt der
# Claude-Aufgabe. Hier nur: wonach gesucht und was hart aussortiert wird.
# ============================================================

# Wie weit zurück gesucht wird (Tage). Erster Lauf: 14, danach 2.
days_back: 2

# ------------------------------------------------------------
# Suchbegriffe = Berufs-/Themenfelder (nicht "Soziologie", nicht "HR")
# Reihenfolge ~ Priorität aus dem Profil
# ------------------------------------------------------------
queries:
  de:
    - "Projektkoordination"
    - "Bildungsplanung"
    - "Bildungskoordination"
    - "Bildungsmanagement"
    - "Sozialplanung"
    - "Stadtentwicklung"
    - "Quartiersmanagement"
    - "Gleichstellung"
    - "Chancengleichheit"
    - "Diversity"
    - "Wissenschaftsmanagement"
    - "Wissenschaftskommunikation"
    - "Netzwerkkoordination"
    - "Evaluation"
    - "Sozialwissenschaften"
    - "Kulturmanagement"
    - "Integrationsmanagement"
    - "Familienförderung"
    - "Promotionsstelle Soziologie"
    - "Wissenschaftliche Mitarbeiterin Soziologie"
  ch:
    - "Projektleiterin Bildung"
    - "Fachspezialistin Gesellschaft"
    - "Fachstelle Gleichstellung"
    - "Chancengleichheit"
    - "Kinder Jugend Familie"
    - "Sozialplanung"
    - "Stadtentwicklung"
    - "Bildungsplanung"
    - "Wissenschaftliche Mitarbeiterin Sozialwissenschaften"
    - "Wissenschaftskommunikation"
    - "Projektkoordination"
    - "Evaluation"
    - "Doktorandin Soziologie"

# ------------------------------------------------------------
# Regionen – kein Auto, nur ÖV. Zürich bewusst NICHT im Standard-Radius.
# Pendelzeiten prüft Claude im Detail; hier nur grobe Vorauswahl.
# ------------------------------------------------------------
locations:
  # Bundesagentur (nur DE). umkreis = Luftlinie km; deckt Singen, Radolfzell,
  # Überlingen, Friedrichshafen (Katamaran) ab.
  ba:
    - { wo: "Konstanz", umkreis: 40 }

  # Google Jobs via SerpApi
  serpapi:
    - { location: "Konstanz, Baden-Wurttemberg, Germany", gl: "de", hl: "de", lrad: 40 }
    - { location: "Kreuzlingen, Thurgau, Switzerland",     gl: "ch", hl: "de", lrad: 30 }
    - { location: "St. Gallen, Switzerland",               gl: "ch", hl: "de", lrad: 15 }
    - { location: "Winterthur, Switzerland",               gl: "ch", hl: "de", lrad: 15 }
    - { location: "Schaffhausen, Switzerland",             gl: "ch", hl: "de", lrad: 15 }

  # LinkedIn via Apify
  linkedin:
    - "Konstanz, Baden-Württemberg, Germany"
    - "Friedrichshafen, Baden-Württemberg, Germany"
    - "Thurgau, Switzerland"
    - "St. Gallen, Switzerland"
    - "Winterthur, Switzerland"
    - "Schaffhausen, Switzerland"

# ------------------------------------------------------------
# Quellen
# ------------------------------------------------------------
sources:
  ba:
    enabled: true
    page_size: 50
    angebotsart: 1          # 1 = Arbeit
    fetch_details: true

  serpapi:
    enabled: true
    # 66 Kombinationen (Begriff x Ort); 8 pro Tag -> alle ~8 Tage einmal durch.
    # Google Jobs listet Anzeigen meist mehrere Wochen, daher reicht das.
    max_requests_per_run: 8

  linkedin:
    enabled: true
    actor: "jmlp~linkedin-jobs-scraper"
    date_posted: "day"            # erlaubt: any | month | week | day
    max_items: 100
    scrape_details: true
    timeout_s: 280

# ------------------------------------------------------------
# Harte Ausschlüsse (No-Gos aus dem Profil) – Regex auf den TITEL.
# Bewusst eng gehalten: Grenzfälle soll Claude anhand der Beschreibung
# beurteilen, nicht der Filter.
# ------------------------------------------------------------
exclude:
  title_patterns:
    # Einstieg/Ausbildung/zu niedrig dotiert
    - "praktik|werkstudent|ausbildung|azubi|minijob|aushilfe|volontär|volontariat|trainee|duales studium|fsj|bfd|bundesfreiwillig"
    # Vertrieb/Akquise
    - "vertrieb|sales|verkäuf|verkauf|außendienst|aussendienst|key account|account manag|akquise|call ?center|telefonist|kundenberater|kundenservice"
    # Buchhaltung/Kasse/Abrechnung
    - "buchhalt|kassier|finanzbuchh|lohnbuchh|entgeltabrechn|payroll|controller|steuerfach|bilanz"
    # klassische HR-Administration / Sachbearbeitung
    - "personalsachbearb|personalreferent|hr[- ]?referent|hr[- ]?generalist|hr[- ]?business|hr[- ]?administrat|personaladministr|personalverwaltung|verwaltungsfachang|bürokauf|kaufm.*angestellte|assistenz der geschäftsführung|sekretär|empfang"
    # Technik/Ingenieurwesen/IT
    - "ingenieur|engineer|techniker|informatik|software|entwickler|developer|devops|elektro|mechatron|konstrukt"
    # Führung (aktuell nicht gesucht)
    - "teamleit|abteilungsleit|bereichsleit|amtsleit|fachbereichsleit|geschäftsführ|direktor|head of"
    # Schicht/Pflege/Erziehung (andere Berufsausbildung)
    - "schicht|pflegefach|pflegekraft|pflegedienst|erzieher|kinderpfleg|heilerzieh|sozialpädagog.*(wohngruppe|schicht)|pädagogische fachkraft|ergänzungskraft|fachkraft.*(kita|krippe|kindergarten)|schulbegleit"
    # Medizin/Gesundheit
    - "arzt|ärzt|oberarzt|facharzt|klinik.*leit|therapeut|physio|sanitäter|zahnmedizin|medizinische fachangestellte|\\bmfa\\b|apothek|optiker|optometr|psycholog"
    # Handwerk/Gastro/Logistik/Handel
    - "koch|köch|küche|patissier|reinigung|hausmeister|gärtner|garten- und landschaft|lager|logistik|fahrer|disponent|mechani|schlosser|schweiß|monteur|maler|elektrik|netzelektr|werkzeug|fertigung|kunststoff|bauleiter|architekt|bauhof|straßenunterhalt|detailhandel|store manager|filialleit|boutique|lehrstelle|\\befz\\b|\\beba\\b|soldat|wehrdienst"
    # Finanzen/IT/Recht ohne Bezug
    - "treasur|einkäufer|einkauf|beschaffung|audit|compliance|underwrit|private equity|relationship manager|cyber|security|\\bsap\\b|cloud|\\bit[- ]|rechtsanwaltsfach|gerichtsschreiber|versicherungs|vorsorge.*berat|finanzberat"
  companies:
    - "randstad"
    - "adecco"
    - "manpower"
    - "hays"
    - "orizon"
    - "persona service"
    - "dis ag"
    - "amadeus fire"
  zeitarbeit: false

# Ortsfilter – gilt NUR für LinkedIn (Arbeitsagentur und Google Jobs suchen
# schon per Umkreis um Konstanz bzw. die Schweizer Orte).
# Fliegt raus, wenn der Ort keinen dieser Begriffe enthält. Stellen ohne Ort
# oder mit "Remote" bleiben drin. Zürich bewusst nicht enthalten (Ausnahme-
# regel, findet Claude bei Bedarf direkt).
location_filter_sources: ["linkedin"]
location_allow:
  # Kreis Konstanz / Hegau
  - "konstanz|constance|allensbach|reichenau|radolfzell|singen|steißlingen|stockach|engen|hilzingen|rielasingen|gottmadingen|gailingen|öhningen|moos|bodman|ludwigshafen"
  # Bodenseekreis / Überlingen / Friedrichshafen
  - "überlingen|ueberlingen|sipplingen|owingen|meersburg|uhldingen|hagnau|immenstaad|markdorf|salem|friedrichshafen|meckenbeuren|tettnang|langenargen|eriskirch|kressbronn|bodensee"
  # Schweiz: ganze Kantone Thurgau, St. Gallen, Schaffhausen + Winterthur
  - "thurgau|kreuzlingen|tägerwilen|ermatingen|bottighofen|münsterlingen|frauenfeld|weinfelden|amriswil|romanshorn|arbon"
  - "st\\.? ?gallen|schaffhausen|winterthur|herisau|rorschach|wil\\b|stein am rhein|diessenhofen"
  - "remote|homeoffice|home office|beliebig|^(deutschland|germany|schweiz|switzerland)$"
