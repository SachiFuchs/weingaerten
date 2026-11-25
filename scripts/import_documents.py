"""Take invoices and quotes from catalog/imported_documents into catalog/documents.

Only documents of the object `weingaerten-8`. Per document: id = lower-case file name, type `doc_type`,
supplier as company ref (missing companies are created with role supplier), units normalised
(original in `unit_raw`), `items_gross` when the item prices include VAT, `deductions_net` for
deductions without own field, `related` = other documents named in the description.
Items are linked to catalog materials/components by ITEM_REFS; NEW_MATERIALS creates missing materials.
Every linked item becomes an offer in the element's product (existing offers of the same supplier and
date get the `document` ref). The import folder stays untouched.

Usage: python scripts/import_documents.py            (dry run, prints the review list)
       python scripts/import_documents.py --write    (writes files)
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAT = ROOT / "catalog"
IMPORT = CAT / "imported_documents"
DOCUMENTS = CAT / "documents"
COMPANIES = CAT / "companies"
OBJECT = "weingaerten-8"
TOL = 0.05

TYPE_DE = {"invoice": "Rechnung", "quote": "Angebot", "order_confirmation": "Auftragsbestätigung",
           "credit_note": "Gutschrift", "plan": "Plan"}
UNITS = {"stk": "Stk", "stk.": "Stk", "st": "Stk", "st.": "Stk", "stck": "Stk", "stück": "Stk",
         "std": "Std", "std.": "Std", "psch": "psch", "psch.": "psch", "pausch": "psch", "pauschal": "psch",
         "lfm": "m", "to": "t", "cbm": "m³"}
# supplier name (start) -> existing company id; other suppliers get a new company
SUPPLIER_IDS = {"Schuck Dachdeckungen": "schuck-dach", "Neuffer Fenster": "neuffer",
                "Marquardt Fenster": "marquardt", "Riempp Estriche": "riempp-estriche",
                "Lehmputz Trockenbausysteme": "naturbo", "VELUX Deutschland": "velux",
                # new companies with a shorter id than the slug of the full name
                "Alexander Huber": "huber-sanitaer", "Ringschmiede": "ringschmiede-nieswandt",
                "Maier Sanitärtechnik": "maier-sanitaer", "Gesellschaft für Schornstein": "gsa-schornstein",
                "Energieversorgung Filstal": "evf", "Erich Rau": "rau-gartengeraete",
                "Ihre Energieberatung": "energieberatung-krause", "Sorwat": "sorwat-stuckateur",
                "Aux 1804": "wohnklimaplatte", "Landschaftsgärtner Ramo": "ramo-landschaftsgaertner",
                "Böhringer": "boehringer-heizungsbau", "Johs. Koch": "koch-holzwerke",
                "Wärmesysteme Filstal": "waermesysteme-filstal", "Stefan Eisele": "eisele-kaminfeger"}
LEGAL = re.compile(r"\b(gmbh|ag|se|kg|co|e\.?k\.?|mbh|s\.?r\.?l\.?|& co\.?|inh\.?)\b", re.I)
# short company label used in the document name (default: first word of the name)
LABELS = {"Erich Rau": "Rau", "Landschaftsgärtner Ramo": "Ramo", "Energieversorgung Filstal": "EVF",
          "ECO Water": "ECO Water", "Stadtverwaltung Göppingen": "Stadt Göppingen", "Alexander Huber": "Huber",
          "Dussmann Speidel": "Speidel", "Reiner Blessing": "Blessing", "Stefan Eisele": "Eisele",
          "Helmut Kälberer": "Kälberer", "Achim Hubrig": "Hubrig", "Gottfried Wiedmann": "Wiedmann",
          "Johs. Koch": "Koch", "Holz Metzger": "Metzger", "Ihre Energieberatung": "Krause",
          "Theodor Wölpert": "Wölpert", "Wärmesysteme Filstal": "Kupinic", "Aux 1804": "Wohnklimaplatte",
          "Gesellschaft für Schornstein": "GSA", "Ringschmiede": "Nieswandt", "Lehmputz Trockenbausysteme": "Naturbo",
          "Neuffer": "Fensterversand", "Stuckateur Cetin": "Cetin", "HARSCH": "Harsch", "NEXTERIO": "Nexterio",
          "AGRIEURO": "Agrieuro", "VELUX": "VELUX"}
ABBREVIATIONS = {"kg": "KG", "uv": "UV", "fi": "FI", "ls": "LS", "pkw": "PKW", "zas": "ZAS", "fbh": "FBH",
                 "dg": "DG", "eg": "EG", "bafa": "BAFA", "tpn": "TPN", "as": "AS", "re": "RE", "wkp": "WKP"}

# (regex on the item description, ref) - first match wins; None = deliberately not linked
ITEM_REFS = [
    (r"DKL CK04.*Verdunkelungsrollo", "component:roof-blind-velux-dkl-ck04"),
    (r"Eindeckrahmen EDZ.*55 x 98", "component:roof-flashing-velux-ck04"),
    (r"Eindeckrahmen EDZ.*66 x 118", "component:roof-flashing-velux-fk06"),
    (r"VELUX GGU.*CK ?04", "component:roof-window-velux-ck04"),
    (r"VELUX GGU.*FK ?06", "component:roof-window-velux-fk06"),
    (r"DivoDämm Membran", "material:vapour-membrane-divodaemm"),
    (r"DivoDämm Top PIR", "material:pir-divodaemm-top"),
    (r"Tondachziegel Braas Rubin", "material:clay-tile-rubin"),
    (r"^Ortgangausbildung mit Ortgangziegel", "component:roof-verge-tile"),
    (r"^Firstausbildung", "component:roof-ridge"),
    (r"^Trauflüfterkamm", "component:roof-eaves-vent-comb"),
    (r"^Rinnenhalter kupferummantelt", "component:roof-gutter-bracket"),
    (r"^Einlaufblech Kupfer", "component:roof-eaves-flashing"),
    (r"^Kaminverwahrung Sondergröße Kupfer", "component:chimney-flashing"),
    (r"^Kaminverkleidung Alu braun", "component:chimney-cladding"),
    (r"^Edelstahlabdeckung Kamin", "component:chimney-cap"),
    (r"^Balkenwechsler", "component:roof-trimmer"),
    (r"US Faseprofil Scandia", "component:roof-soffit-cladding"),
    (r"^Vorhandene Rinne", "component:roof-gutter"),
    (r"^Traufausbildung mit Keilbohle", "component:roof-eaves-boards"),
    (r"^Heizestrich d=38", "material:heating-screed"),
    (r"^Trägerplatte Fußbodenheizung.*Bekotec", "material:bekotec-en23f-plate"),
    (r"^Randdämmstreifen Schlüter", "material:pe-edge-strip"),
    (r"PUR/PIR WLG 023, S=30", "material:pur-pir-023"),
    (r"PUR/PIR WLG 023, S=50", "material:pur-pir-023-50"),
    (r"Fenster .*– Balkonkammer", "component:window-balkonkammer"),
    (r"Balkontür .*– Balkontür \(IDEAL", "component:door-balkon-schlafzimmer"),
    (r"Balkontür .*– Tür Treppenzimmer", "component:door-balkon-treppenzimmer"),
    (r"Fenster .*– Schlafzimmer", "component:window-schlafzimmer"),
    (r"Fenster .*– Wohnzimmer grosses", "component:window-wz-gross"),
    (r"Fenster .*– Wohnzimmer Fenster zu Terrasse", "component:window-wz-terrasse"),
    (r"Fenster .*– Wohnzimmer kleines", "component:window-wz-klein"),
    (r"Fenster .*– EG Küche", "component:window-eg-kueche"),
    (r"Fenster .*– EG Bad", "component:window-eg-bad"),
    (r"Fenster .*– EG Flur", "component:window-eg-flur"),
    (r"Fenster .*– EG Kammer", "component:window-eg-kammer"),
    (r"^1-flg\. Aluminium-Haustür", "component:door-d1"),
    (r"Claytec Lehm-Oberputz Uni Fein 06", "material:claytec-lehm-oberputz-fein-06-25-kg"),
    (r"Claytec Lehmklebe- und Armiermörtel", "material:claytec-lehmklebe-armiermoertel"),
    (r"Knauf Armiergewebe 4x4", "material:knauf-armiergewebe-4x4"),
    (r"Steico internal", "material:steico-internal-60"),
    (r"Kalziumsilikatplatte", "material:kalziumsilikatplatte-50"),
    (r"KP-Silikatkleber", "material:kp-silikatkleber"),
    (r"Glätt-/Kalkspachtel", "material:kalkspachtel-kalziumsilikat"),
    (r"Silikatgrundierung", "material:silikatgrundierung-kalziumsilikat"),
    (r"^Nordische Fichte A-Sortierung 21 x 146", "material:nord-fichte-nut-feder-21x146"),
    (r"^Fertigparkett Eiche USED Lava", "material:fertigparkett-eiche-lava"),
    (r"^Fertigparkettkleber BAKIT", "material:bakit-fpk-parkettkleber"),
    (r"Landhausdiele Eiche Primitivo", "material:landhausdiele-eiche-primitivo"),
    (r"Bona R 848", "material:bona-r848-parkettklebstoff"),
    (r"^490-100679[47] Fliesen Uni 20x20", "material:fliese-uni-20x20"),
    (r"Feinsteinzeug rot Dekor", "material:feinsteinzeug-rot-dekor-20x20"),
    (r"Feinsteinzeug braun Dekor", "material:feinsteinzeug-braun-dekor-20x20"),
    (r"Leeds Blue Matt", "material:bodenfliese-leeds-blue-33x33"),
    (r"Leeds Garden Matt", "material:bodenfliese-leeds-garden-33x33"),
    (r"\[1001-14\] Dämmplatte", "material:naturbo-daemmplatte"),
    (r"\[1001-19\] Flankendämmplatte", "material:naturbo-flankendaemmplatte"),
    (r"\[1002-7\d\] Klima-Dämmplatte Typ|\[1002-8\d\] Klima-Dämmplatte Typ", "material:naturbo-klima-daemmplatte"),
    (r"\[9102-22\] Haftfix", "material:naturbo-haftfix"),
    (r"\[9102-00\] Fugenfix", "material:naturbo-fugenfix"),
    (r"\[8103-01\] Lehm-Finishputz", "material:naturbo-lehm-finishputz-weiss"),
    (r"Kermi x-net Trockenbauplatte", "material:kermi-x-net-trockenbauplatte"),
    (r"Aduxa Druckrohr PE100RC 32", "material:pe100rc-druckrohr-32"),
    (r"^95020 Mineralbeton", "material:mineralbeton-0-22"),
    (r"^95322 .*Edelsplitt", "material:granit-edelsplitt-16-32"),
    (r"^95011 Betonkies", "material:betonkies-0-16"),
    (r"^95007 .*Sand 0-4", "material:sand-0-4"),
    (r"^95028 Kalksplitt", "material:kalksplitt-11-22"),
    (r"^95081 Universalerde", "material:universalerde"),
    (r"^95013 Kies 16-32", "material:kies-16-32"),
    # round 2 (Nov 2026): review list of all unlinked items
    (r"^Konterlattung mit Rahmenschenkel 40x60", "material:counter-batten-40x60"),
    (r"^Traglattung 30x50", "material:roof-batten-30x50"),
    (r"^Stützbohle Traufe", "component:roof-eaves-support-board"),
    (r"^Windbrett zur seitlichen Abdeckung", "component:roof-wind-board"),
    (r"^Windbrett-Verkleidung|^Stützbohle und Traufbohle mit Blechen", "component:roof-board-flashing"),
    # Titanzink was only quoted; built were copper / aluminium (other price) -> not linked
    (r"^Kaminverwahrung Titanzink", None),
    (r"^Kaminverkleidung Titanzink", None),
    (r"^Dunstrohrdurchgang Ton", "component:roof-vent-pipe-jacobi-w6v"),
    (r"^Außenrollladen (mit )?Solar", "component:roof-shutter-solar"),
    (r"^Nord Fichte Glattkantbretter", "material:glattkantbrett-nord-fichte"),
    (r"^Fichte KVH gehobelt", "material:kvh-fichte"),
    (r"^Tafel Alu braun", "material:aluminium-brown"),
    (r"^Dachbalken liefern", "material:spruce-wood"),
    (r"SIGA Majrex", "material:siga-majrex"),
    (r"Einblasdämmung Zellulose", "material:zellulose-einblasdaemmung"),
    (r"^Dachausbau: Traglattenrost auf Holzbalken, Gipskarton", "material:gypsum-board-gkb"),
    (r"^Abtrennungsband", "material:trennband-trockenbau"),
    (r"^Alu-Eckschienen", "material:alu-eckschiene-trockenbau"),
    (r"^Putzgrund: Haftvermittelnde Grundierung", "material:haftgrundierung-putzgrund"),
    (r"\[1002-91\] Klima-Dämmplatte Dämmriegel", "material:naturbo-klima-daemmriegel"),
    (r"\[9101-00\] Fugenarmierungsgewebe", "material:naturbo-fugenarmierungsgewebe"),
    (r"\[9101-05\] Kantenkleber", "material:naturbo-kantenkleber"),
    (r"^Holzfassade und Dachgesims streichen", "material:facade-paint-taubenblau"),
    (r"^1-flg\. Balkontür, Dreh-Kipp-Links .*Rehau Synego", "component:door-balkon-rehau-synego"),
    (r"^Spelsberg AK 56", "tga-component:spelsberg-ak-56"),
    (r"^Hager Hauptschalter 63A", "tga-component:hager-hauptschalter-63a"),
    (r"^Siemens (FI/LS|LS FI) B16 30mA", "tga-component:siemens-fi-ls-b16-30ma"),
    (r"^Siemens FI LS 5SU1354-6KK16", "tga-component:siemens-fi-ls-5su1354-6kk16"),
    (r"^Siemens FI 4pol 40A 30mA", "tga-component:siemens-fi-4p-40a-30ma"),
    (r"^Siemens Automat B16A 3pol", "tga-component:siemens-ls-b16-3p"),
    (r"^Siemens Automat B16A$", "tga-component:siemens-ls-b16-1p"),
    (r"^Siemens Brücke für FI/LS", "tga-component:siemens-bruecke-fi-ls"),
    (r"^Siemens Brücke$", "tga-component:siemens-bruecke"),
    (r"^Sicherung NH00 50A", "tga-component:sicherung-nh00-50a"),
    (r"^NYM-J 5x16mm2", "tga-component:cable-nym-j-5x16"),
    (r"^NYM-J 3x2,5mm2", "tga-component:emskabel-feuchtraumleitung-nym-j-3-x-2-5-mm2-50-m"),
    (r"^NYM-J 5x2,5mm2", "tga-component:emskabel-feuchtraumleitung-nym-j-5-x-2-5-mm2-50-m"),
    (r"^Leitung 1x10mm2", "tga-component:cable-1x10"),
    (r"^PVC-Rohr M32", "tga-component:pvc-rohr-m32"),
    (r"^PVC-Schelle M32", "tga-component:pvc-schelle-m32"),
    (r"^Montage/Lieferung Zähleranschlusssäule", None),
    (r"Zähleranschluss-?[Ss]äule", "tga-component:evf-zaehleranschlusssaeule"),
    (r"^(BioTopp OK 4 EW )?Kleinkläranlage( BioTopp OK 4 EW)?", "tga-component:biotopp-ok-4-ew"),
    (r"^Vererdung 4-6 EW", "tga-component:biotopp-vererdung-4-6-ew"),
    (r"^PE Außensäule 400x250x1695", "tga-component:biotopp-pe-aussensaeule"),
    (r"^SL01615005B", "tga-component:gsa-fl150-stuetzfuss"),
    (r"^SL02615005B", "tga-component:gsa-fl150-pruefoeffnung"),
    (r"^SL03715005B", "tga-component:gsa-fl150-feuerungsanschluss-90"),
    (r"^SL05315005B", "tga-component:gsa-fl150-wandfutter-120"),
    (r"^SL00415005B", "tga-component:gsa-fl150-rohrelement-1000"),
    (r"^SL08915005B", "tga-component:gsa-fl150-muendungsabschluss"),
    (r"^S008115006", "tga-component:gsa-z150-regenhaube"),
    (r"^SL08815005B", "tga-component:gsa-fl150-dachdurchfuehrung-26-45"),
    (r"^SL08615005B", "tga-component:gsa-fl150-dachdurchfuehrung-flach"),
    (r"^SL12215005B", "tga-component:gsa-fl150-klemmband"),
    (r"^SL10115005B", "tga-component:gsa-fl150-wandhalter-60"),
    (r"^SL10715005B", "tga-component:gsa-fl150-wandhalter-verl-250"),
    (r"^SL04515005B", "tga-component:gsa-fl150-blende-0"),
    (r"^SL19315005B", "tga-component:gsa-fl150-universalblende"),
    (r"^Kermi Verteilerschrank U-XL-L2", "tga-component:kermi-verteilerschrank-u-xl-l2"),
    (r"^Kermi X-Net Verteiler 1\" Komfort 5", "tga-component:kermi-x-net-verteiler-5"),
    (r"^Kermi Eck-Kugelhahnset", "tga-component:kermi-eck-kugelhahnset"),
    (r"^Kermi Einzel-Klemmringverschraubungen 14x2", "tga-component:kermi-klemmring-14x2"),
    (r"^Kermi X-Net Verbundrohr 14 x 2", "tga-component:kermi-x-net-verbundrohr-14x2"),
    (r"^Wärmeleitblech X-Net", "tga-component:kermi-x-net-waermeleitblech"),
    (r"^Kermi X-Net Stellantrieb", "tga-component:kermi-x-net-stellantrieb"),
    (r"^Kermi X-Net Wandanbauregler", "tga-component:kermi-x-net-wandregler"),
    (r"^Kermi X-Net Klemmleiste 6R", "tga-component:kermi-x-net-klemmleiste-6r"),
    (r"^Zehnder Handtuchheizkörper ZENO", "tga-component:zehnder-zeno-elektrisch-1700x600"),
    # Böhringer Angebot 25-0023, all positions (Nov 2026); labour/service positions stay unlinked
    (r"^Weishaupt Splitblock WSB 8-A-RME-AI$", "material:weishaupt-wsb-8-a-rme-ai"),
    (r"^Außenfühler NTC 2k", "material:weishaupt-aussenfuehler-ntc-2k"),
    (r"^Kältemittelleitungs-Set WSB 8/10", "material:weishaupt-kaeltemittelleitung-wsb-10m"),
    (r"^Steuerleitung abgeschirmt LIYCY 2 x 0,75", "material:cable-liycy-2x0-75"),
    (r"^Bodenkonsole für WSB", "material:weishaupt-bodenkonsole-wsb"),
    (r"^Schutzgitter-Set WSB", "material:weishaupt-schutzgitter-wsb"),
    (r"^Ringraumdichtung HRD 150", "material:ringraumdichtung-hrd-150"),
    (r"^Erweiterungsmodul EM-HK", "material:weishaupt-em-hk"),
    (r"^CAN-Bus-Leitung RJ11", "material:weishaupt-can-bus-rj11-5m"),
    (r"^Pumpengruppe WHI pump 25-6", "material:weishaupt-whi-pump-25-6"),
    (r"^Mischergruppe WHI mix 25-6-2,5", "material:weishaupt-whi-mix-25-6-2-5"),
    (r"^Pumpenabschaltung-Set", "material:weishaupt-pumpenabschaltung-fbh"),
    (r"^Verteiler WHI distri-comp 25-2-3,5", "material:weishaupt-whi-distri-comp-25-2"),
    (r"^Hydraulikübergangs-Set WHÜ-A-O", "material:weishaupt-whue-a-o"),
    (r"^Temperaturfühler NTC5k 5m", "material:weishaupt-temperaturfuehler-ntc5k"),
    (r"^Trinkwasserspeicher WAS 200", "material:weishaupt-was-200-le"),
    (r"^Elektro-Heizeinsatz 3,5 kW WEH", "material:weishaupt-weh-f180-3-5"),
    (r"^Aqua-Anschlussgruppe", "material:weishaupt-aqua-anschlussgruppe"),
    (r"^KFE-Kugelhahn Simplex 1/2", "material:kfe-kugelhahn-1-2"),
    (r"^Schnellentluefter 3/8", "material:schnellentluefter-3-8"),
    (r"^Fuellset m\.Schlauch 5 Meter", "material:fuellset-schlauch-5m"),
    (r"^BESTE\s+easyfil VE", "material:beste-easyfil-ve"),
    (r"^BEKOTEC-Therm Rohr PE-RT 14 x 2,0", "material:schlueter-bekotec-therm-hr-14x2"),
    (r"^Xtra Rohrfuehrungsbogen", "material:xtra-rohrfuehrungsbogen-14-17"),
    (r"^Xtra Schutzhuelse 300 x 5", "material:xtra-schutzhuelse-300x5"),
    (r"^Alternativ zu 3\.4: SKV Heizkreis-Verteilerstation", "material:skv-heizkreisverteiler-5-up"),
    (r"^SKV Heizkreis-Verteilerstation", "material:skv-heizkreisverteiler-5"),
    (r"^Regelverteiler für bis zu 6 Raumthermostate", "material:regelverteiler-6-raeume"),
    (r"^XTRA-Stellantriebe 230V", "material:xtra-stellantrieb-230v"),
    (r"^BEKOTEC-Verschraubung 14 x 3/4", "material:bekotec-verschraubung-14-3-4"),
    (r"^Broetje .*Typ 33 E 900x700", "material:broetje-europrof-33-900x700"),
    (r"^Broetje .*Typ 33 E 900x900", "material:broetje-europrof-33-900x900"),
    (r"^Zweirohr-Hahnblock 3/4", "material:zweirohr-hahnblock-3-4"),
    (r"^Heimeier Thermostatkopf", "material:heimeier-thermostatkopf"),
    (r"^HZ Sockelleiste SLF 2000", "material:hz-sockelleiste-slf-2000"),
    (r"^HZ Schelle SCH", "material:hz-schelle-sch"),
    (r"^HZ Ausgleichs-Winkelabsperrverschraubung AWA", "material:hz-awa-15"),
    (r"^HZ Heizkörperanschluss HKU U 18 VP", "material:hz-hku-u-18-vp"),
    (r"^Ca\. Cu-Rohr 35 x 1,5", "material:cu-rohr-35x1-5"),
    (r"^Ca\. Cu-Rohr 28 x 1,5", "material:cu-rohr-28x1-5"),
    (r"^Ca\. Cu-Rohr 22 x 1,5", "material:cu-rohr-22x1-5"),
    (r"^Ca\. Cu-Rohr 18 x 1,0", "material:cu-rohr-18x1-0"),
    (r"^Rohr 28x1,0, zu 100% gemäß HeizAnlV", "material:rohrdaemmung-pvc-28"),
    (r"^Rohr 18x1,0 zu 100% gemäß HeizAnlV", "material:rohrdaemmung-pvc-18"),
    (r"^Bosch Luftwärmepumpen-Paket BOPA CS804", "tga-component:bosch-cs6800iaw-12-mb-paket"),
    (r"\[9200-10\] Alu-Verbundrohr", "tga-component:naturbo-alu-verbundrohr-11-6"),
    (r"\[9201-10\] Presskupplung", "tga-component:naturbo-presskupplung-11-6"),
    (r"\[9201-15\] Presskupplung", "tga-component:naturbo-presskupplung-11-6-90"),
    (r"\[9201-20\] Presskupplung", "tga-component:naturbo-presskupplung-11-6-16"),
    (r"\[9201-25\] Presskupplung", "tga-component:naturbo-presskupplung-11-6-16-90"),
    (r"\[9201-01\] Pressfenster-Einleger", "tga-component:naturbo-pressfenster-einleger"),
    (r"\[9203-00\] Innenkalibrierer", "tga-component:naturbo-innenkalibrierer"),
]
APPEARANCE = {
    "Dämmung": {"color": "#C9B48A", "roughness": 0.9, "hatch": "insulation"},
    "Platten": {"color": "#E6E2D8", "roughness": 0.8, "hatch": "none"},
    "Putz": {"color": "#C8B79E", "roughness": 0.9, "hatch": "plaster"},
    "Baustoffe": {"color": "#B8B4AC", "roughness": 0.9, "hatch": "plaster"},
    "Belag": {"color": "#9A7650", "roughness": 0.6, "hatch": "wood"},
    "Holz": {"color": "#D8B991", "roughness": 0.7, "hatch": "wood"},
    "Fliesen": {"color": "#B5654A", "roughness": 0.3, "hatch": "none"},
    "Trinkwasser": {"color": "#1F1F1F", "roughness": 0.5, "hatch": "none"},
    "Schüttgut": {"color": "#A8A39A", "roughness": 1.0, "hatch": "concrete"},
    "Heizung": {"color": "#B87333", "roughness": 0.4, "hatch": "none"},
}
# id -> (name, category, description, conductivity, manufacturer company id or None)
NEW_MATERIALS = {
    "pur-pir-023-50": ("PUR/PIR-Dämmung WLG 023, 50 mm", "Dämmung", "Estrichdämmung unter Bekotec, 50 mm", 0.023, None),
    "claytec-lehmklebe-armiermoertel": ("Claytec Lehmklebe- und Armiermörtel 25 kg", "Putz",
                                        "Lehmmörtel zum Kleben und Armieren, 25-kg-Sack", None, "rudolf-laier"),
    "knauf-armiergewebe-4x4": ("Knauf Armiergewebe 4×4 mm, 165 g/m²", "Baustoffe",
                               "Armiergewebe, Rolle 1,1 × 50 m = 55 m²", None, "knauf"),
    "steico-internal-60": ("Steico internal Holzfaser-Innendämmung 60 mm", "Dämmung",
                           "Holzfaserplatte mit Nut und Feder, 1200 × 380 × 60 mm, WLG 038", 0.038, None),
    "kalziumsilikatplatte-50": ("Kalziumsilikatplatte 50 mm", "Dämmung",
                                "Klimaplatte (Kalziumsilikat), 1000 × 1000 bzw. 1000 × 1220 × 50 mm", None, None),
    "kp-silikatkleber": ("Spezial-KP-Silikatkleber", "Baustoffe", "Kleber für Kalziumsilikatplatten", None, None),
    "kalkspachtel-kalziumsilikat": ("Glätt-/Kalkspachtel", "Putz", "Spachtel für Kalziumsilikatplatten", None, None),
    "silikatgrundierung-kalziumsilikat": ("Silikatgrundierung", "Baustoffe", "Grundierung für Kalziumsilikatplatten",
                                          None, None),
    "nord-fichte-nut-feder-21x146": ("Nordische Fichte Nut-Feder 21 × 146 mm", "Holz",
                                     "A-Sortierung, KD 10–12 %, Mini-Fase, Deckbreite 132 mm, Länge 4,50 m", None, None),
    "fertigparkett-eiche-lava": ("Fertigparkett Eiche USED Lava, geölt", "Belag",
                                 "Eiche rustikal natur geölt, angeräuchert, 2200 × 195 × 15 mm", None, None),
    "bakit-fpk-parkettkleber": ("Fertigparkettkleber BAKIT FPK 17 kg", "Baustoffe", "Parkettkleber, Gebinde 17 kg",
                                None, None),
    "landhausdiele-eiche-primitivo": ("Landhausdiele Eiche Primitivo, Naturöl", "Belag",
                                      "1-Stab rustikal, handgehobelt, 14 × 190 × 1900 mm, Woodloc 2G", None, None),
    "bona-r848-parkettklebstoff": ("Bona R 848 Parkettklebstoff 15 kg", "Baustoffe",
                                   "elastischer 1-K-Parkettklebstoff", None, None),
    "fliese-uni-20x20": ("Fliese Uni 20 × 20 cm inkl. Sockel", "Fliesen", "Wandfliese uni (zwei Farben im Angebot)",
                         None, None),
    "feinsteinzeug-rot-dekor-20x20": ("Feinsteinzeug rot Dekor mix 20 × 20 cm", "Fliesen", "R10/B, VE 1,04 m²",
                                      None, None),
    "feinsteinzeug-braun-dekor-20x20": ("Feinsteinzeug braun Dekor mix 20 × 20 cm", "Fliesen", "R10/B, VE 1,04 m²",
                                        None, None),
    "bodenfliese-leeds-blue-33x33": ("Bodenfliese Leeds Blue Matt 33 × 33 cm", "Fliesen", "Realonda, Paket",
                                     None, None),
    "bodenfliese-leeds-garden-33x33": ("Bodenfliese Leeds Garden Matt 33 × 33 cm", "Fliesen", "Realonda, Paket",
                                       None, None),
    "naturbo-daemmplatte": ("Naturbo Dämmplatte 62,5 × 125 cm", "Dämmung", "Holzfaser-Dämmplatte für Lehmputz",
                            None, "naturbo"),
    "naturbo-flankendaemmplatte": ("Naturbo Flankendämmplatte", "Dämmung", "Flankendämmung an Anschlüssen",
                                   None, "naturbo"),
    "naturbo-klima-daemmplatte": ("Naturbo Klima-Dämmplatte (Wandheizung)", "Dämmung",
                                  "Dämmplatte mit Rohrführung für Lehm-Wandheizung, Typen D–L", None, "naturbo"),
    "naturbo-haftfix": ("Naturbo Haftfix", "Putz", "Lehm-Klebe- und Haftmörtel, Sack", None, "naturbo"),
    "naturbo-fugenfix": ("Naturbo Fugenfix", "Putz", "Lehm-Fugenmörtel, Sack", None, "naturbo"),
    "naturbo-lehm-finishputz-weiss": ("Naturbo Lehm-Finishputz weiß, Korn 0,5 mm", "Putz", "Lehm-Oberputz, Sack",
                                      None, "naturbo"),
    "kermi-x-net-trockenbauplatte": ("Kermi x-net Trockenbauplatte C13 NM25", "Platten",
                                     "Wandheizungs-Trockenbauplatte 1000 × 500 mm", None, None),
    "pe100rc-druckrohr-32": ("Druckrohr PE100RC 32 × 3,0 SDR11", "Trinkwasser",
                             "Aduxa Trinkwasser-Druckrohr schwarz mit blauer Außenschicht (Hausanschluss)", None, None),
    "mineralbeton-0-22": ("Mineralbeton 0–22 mm", "Schüttgut", "lose, je Tonne", None, None),
    "granit-edelsplitt-16-32": ("Granit-Edelsplitt 16–32 mm grau/blau", "Schüttgut", "Bayernwald, lose, je Tonne",
                                None, None),
    "betonkies-0-16": ("Betonkies 0–16 mm", "Schüttgut", "lose, je Tonne", None, None),
    "sand-0-4": ("Sand 0–4 mm", "Schüttgut", "Egginger Sand, lose, je Tonne", None, None),
    "kalksplitt-11-22": ("Kalksplitt 11–22 mm", "Schüttgut", "lose, je Tonne", None, None),
    "universalerde": ("Universalerde", "Schüttgut", "1 m³ ≈ 0,85 t, je Tonne", None, None),
    "kies-16-32": ("Kies 16–32 mm, gewaschen", "Schüttgut", "lose, je Tonne", None, None),
    "counter-batten-40x60": ("Konterlatte Fichte 40 × 60 mm", "Holz",
                             "Konterlattung mit Rahmenschenkel (Schuck, je m² Dachfläche)", None, None),
    "roof-batten-30x50": ("Traglatte Fichte 30 × 50 mm", "Holz", "Dachlattung (Schuck, je m² Dachfläche)", None, None),
    "glattkantbrett-nord-fichte": ("Glattkantbrett Nordische Fichte", "Holz",
                                   "Schuck RE 1783 Pos. 06.15, je m; Querschnitt im Beleg nicht genannt", None, None),
    "kvh-fichte": ("KVH Fichte gehobelt, technisch getrocknet", "Holz",
                   "Konstruktionsvollholz Fichte; Querschnitt im Beleg nicht genannt (Fenzl: KVH 4/6)", None, None),
    "siga-majrex": ("SIGA Majrex Dampfbremse", "Baustoffe", "feuchtevariable Dampfbremse (Fenzl, Pauschale mit Zubehör)",
                     None, "siga"),
    "zellulose-einblasdaemmung": ("Zellulose-Einblasdämmung WLG 039", "Dämmung",
                                  "Einblasdämmung Dach (Fenzl, Pauschale); Hersteller im Beleg nicht genannt", 0.039, None),
    "trennband-trockenbau": ("Trennband Trockenbau", "Baustoffe", "Abtrennungsband Decke/Wand (Cetin, je m)", None, None),
    "alu-eckschiene-trockenbau": ("Alu-Eckschiene / GK-Abschlussschiene", "Baustoffe",
                                  "Kantenschutz für Gipskarton (Cetin, je m inkl. Einbau)", None, None),
    "haftgrundierung-putzgrund": ("Haftgrundierung Putzgrund", "Baustoffe",
                                  "haftvermittelnde Grundierung Wand/Decke (Cetin, je m² inkl. Auftrag)", None, None),
    "naturbo-klima-daemmriegel": ("Naturbo Klima-Dämmriegel", "Dämmung", "Dämmriegel zur Klima-Dämmplatte", None, "naturbo"),
    "naturbo-fugenarmierungsgewebe": ("Naturbo Fugenarmierungsgewebe", "Baustoffe", "Fugenarmierung, Rolle", None,
                                      "naturbo"),
    "naturbo-kantenkleber": ("Naturbo Kantenkleber", "Baustoffe", "Kleber für Plattenkanten, Kartusche", None, "naturbo"),
}

# new companies with role manufacturer (names from the documents, not checked online); existing ones that get the role
NEW_MANUFACTURERS = {
    "jacobi-walther": "Jacobi Walther (Dunstrohr-/Lüftungsdurchgänge Ton)", "siga": "SIGA (Dampfbremsen, Klebebänder)",
    "rehau": "REHAU (Kunststofffenster-Profilsystem Synego)", "spelsberg": "Spelsberg (Gehäuse, Verteiler)",
    "hager": "Hager (Elektro-Installationsgeräte)", "siemens": "Siemens (Schutzschalter, Reiheneinbaugeräte)",
    "kermi": "Kermi (Flächenheizung x-net, Heizkörper)", "zehnder": "Zehnder (Heizkörper)",
    "weishaupt": "Weishaupt (Wärmepumpen)", "bosch": "Bosch Home Comfort (Wärmepumpen)",
    "broetje": "Brötje (Flachheizkörper EuroProf)", "heimeier": "Heimeier (Thermostatköpfe, Heizkörperarmaturen)",
    "beste": "BESTE (Nachfüllstationen Heizungswasser)", "schlueter": "Schlüter-Systems (BEKOTEC Fußbodenheizung)",
    "hz-weitzel": "Hans Weitzel GmbH & Co. KG, Marke HZ (Sockelleisten, Heizkörperanschlüsse)"}
MANUFACTURER_ROLE = ["gsa-schornstein"]


def _roof_part(name, description, params, main, manufacturer=None, model=None):
    element = {"name": name, "description": description, "class": "class:roof-part", "opening_capable": False,
               "params": params, "materials": {"main": main}, "product": {"offers": []}}
    if manufacturer:
        element["product"] = {"manufacturer": "company:" + manufacturer, "model": model or name, "offers": []}
    return element


def _box(width, height, depth, quantity, unit):
    return {"width": width, "height": height, "depth": depth, "quantity": quantity, "unit": unit}


NEW_COMPONENTS = {
    "roof-eaves-support-board": _roof_part("Stützbohle Traufe 140 mm", "Schuck 2191/1783 Pos. 03.04, je m",
                                           _box(20.0, 0.14, 0.06, 20, "m"), "material:softwood-battens"),
    "roof-wind-board": _roof_part("Windbrett Aufsparrendämmung", "Schuck 2191/1783 Pos. 03.05: seitliche Abdeckung, je m",
                                  _box(22.0, 0.2, 0.024, 22, "m"), "material:softwood-battens"),
    "roof-board-flashing": _roof_part("Blechverkleidung Windbrett / Traufbohle",
                                      "Schuck Angebot 2191 Pos. 06.02/06.03, Zuschnitt bis 400 mm, je m; Blechart im "
                                      "Angebot nicht genannt", _box(25.0, 0.0007, 0.4, 25, "m"), "material:copper-sheet"),
    "roof-vent-pipe-jacobi-w6v": _roof_part("Dunstrohrdurchgang Ton Jacobi Walther W6V",
                                            "Schuck Angebot 2191 Pos. 05.04", _box(0.3, 0.3, 0.4, 1, "pcs"),
                                            "material:clay-tile-rubin", "jacobi-walther", "W6V"),
    "roof-shutter-solar": _roof_part("Außenrollladen Solar für Dachfenster",
                                     "Schuck Nachtrag 2305 Pos. 01.03/01.07; Hersteller im Beleg nicht genannt",
                                     _box(0.66, 0.05, 1.18, 1, "pcs"), "material:aluminium-brown"),
    "roof-blind-velux-dkl-ck04": _roof_part("VELUX Verdunkelungsrollo DKL CK04 4580SWL",
                                            "hell-taupe, weiß lackierte Aluminium-Führungsschienen, für GGU CK04",
                                            _box(0.55, 0.03, 0.98, 1, "pcs"), "material:aluminium-brown", "velux",
                                            "DKL CK04 4580SWL"),
    "door-balkon-rehau-synego": {
        "name": "Balkontür Rehau Synego AD 80, Dreh-Kipp links",
        "description": "Marquardt RE 2026-072 Pos. 03: Hauber Kunststofffenster-System, weiß, Roto NX RC 2, "
                       "abschließbarer Griff, Ug 0,5 / Uw 0,78",
        "class": "class:window", "opening_capable": True,
        "params": {"width": 1.04, "height": 2.22, "depth": 0.08, "frame_width": 0.07, "sashes": 1,
                   "opening_1": "tilt_turn_left", "glazing_type": "triple", "ug_value": 0.5,
                   "burglary_class": "RC2"},
        "materials": {"frame": "material:pvc-white", "glazing": "material:glass"},
        "product": {"manufacturer": "company:rehau", "model": "Synego AD 80", "offers": []}},
}


def _tga(name, cls, din276, system_type, params, manufacturer=None, model=None, note=None):
    element = {"name": name, "class": "tga-class:" + cls, "din276": din276, "system_type": system_type,
               "params": params, "note": note or "aus Beleg (catalog/documents), Maße/Parameter offen",
               "product": {"offers": []}}
    if manufacturer:
        element["product"] = {"manufacturer": "company:" + manufacturer, "model": model or name, "offers": []}
    return element


def _part(part_type, size=None, unit=None):
    params = {"part_type": part_type}
    if size:
        params["size"] = size
    if unit:
        params["unit"] = unit
    return params


def _terminal(terminal_type, mounting):
    return {"terminal_type": terminal_type, "mounting": mounting}


E, H, G = "Stromkreis", "Wandheizung", "Abgasanlage"
NEW_TGA = {
    "spelsberg-ak-56": _tga("Spelsberg AK 56 Verteilergehäuse", "terminal", "440", E,
                            _terminal("distribution_board", "surface"), "spelsberg", "AK 56"),
    "hager-hauptschalter-63a": _tga("Hager Hauptschalter 63 A", "install-part", "440", E, _part("other", "63 A"), "hager"),
    "siemens-fi-ls-b16-30ma": _tga("Siemens FI/LS B16 30 mA", "install-part", "440", E, _part("fuse", "B16 30 mA"),
                                   "siemens"),
    "siemens-fi-ls-5su1354-6kk16": _tga("Siemens FI/LS 5SU1354-6KK16", "install-part", "440", E,
                                        _part("fuse", "B16 30 mA"), "siemens", "5SU1354-6KK16"),
    "siemens-fi-4p-40a-30ma": _tga("Siemens FI 4-polig 40 A 30 mA", "install-part", "440", E, _part("fuse", "40 A 30 mA"),
                                   "siemens"),
    "siemens-ls-b16-3p": _tga("Siemens LS-Schalter B16 3-polig", "install-part", "440", E, _part("fuse", "B16 3p"),
                              "siemens"),
    "siemens-ls-b16-1p": _tga("Siemens LS-Schalter B16 1-polig", "install-part", "440", E, _part("fuse", "B16"),
                              "siemens"),
    "siemens-bruecke": _tga("Siemens Brücke / Sammelschiene", "install-part", "440", E, _part("other"), "siemens"),
    "siemens-bruecke-fi-ls": _tga("Siemens Brücke für FI/LS", "install-part", "440", E, _part("other"), "siemens"),
    "sicherung-nh00-50a": _tga("Sicherung NH00 50 A", "install-part", "440", E, _part("fuse", "NH00 50 A")),
    "cable-nym-j-5x16": _tga("NYM-J 5 × 16 mm²", "cable", "440", E,
                             {"cable_type": "NYM-J", "cores": 5, "cross_section_mm2": 16}),
    "cable-1x10": _tga("Leitung 1 × 10 mm²", "cable", "440", E, {"cable_type": "Einzelader", "cores": 1,
                                                                   "cross_section_mm2": 10},
                       note="Leitungstyp im Beleg nicht genannt (vermutlich H07V-K)"),
    "pvc-rohr-m32": _tga("PVC-Installationsrohr M32", "install-part", "440", E, _part("conduit", "M32", "m")),
    "pvc-schelle-m32": _tga("PVC-Schelle M32", "install-part", "440", E, _part("cable_fixing", "M32")),
    "evf-zaehleranschlusssaeule": _tga("Zähleranschlusssäule 1 Zählerplatz", "terminal", "440", "Hausanschluss",
                                       _terminal("distribution_board", "free"),
                                       note="EVF; Hersteller im Beleg nicht genannt"),
    "biotopp-ok-4-ew": _tga("Kleinkläranlage BioTopp OK 4 EW", "terminal", "411", "Abwasser",
                            _terminal("sanitary", "free"),
                            note="PE-Klärbehälter mit Membranrohrbelüftern, Lufthebern, Rechen, Gebläse; Hersteller "
                                 "im Beleg nicht genannt"),
    "biotopp-vererdung-4-6-ew": _tga("Vererdung 4–6 EW", "terminal", "411", "Abwasser", _terminal("sanitary", "free"),
                                     note="Vererdungsbecken mit Trennwand, Beschickung, Drainage, Edelstahltauchpumpe"),
    "biotopp-pe-aussensaeule": _tga("PE-Außensäule 400 × 250 × 1695 mm", "install-part", "411", "Abwasser",
                                    _part("box", "400x250x1695"), note="Steuer-/Gebläsesäule mit Lüftungsgitter"),
    "kermi-verteilerschrank-u-xl-l2": _tga("Kermi Verteilerschrank U-XL-L2 UP Komfort XL", "install-part", "420", H,
                                           _part("box", "B 535 mm"), "kermi"),
    "kermi-x-net-verteiler-5": _tga("Kermi x-net Verteiler 1\" Komfort, 5 Heizkreise", "terminal", "420", H,
                                    _terminal("manifold", "flush"), "kermi"),
    "kermi-eck-kugelhahnset": _tga("Kermi Eck-Kugelhahnset 1\" × 3/4\"", "install-part", "420", H,
                                   _part("valve", "1\" x 3/4\""), "kermi"),
    "kermi-klemmring-14x2": _tga("Kermi Klemmringverschraubung 14 × 2 mm", "install-part", "420", H,
                                 _part("thread_fitting", "14x2"), "kermi"),
    "kermi-x-net-verbundrohr-14x2": _tga("Kermi x-net Verbundrohr 14 × 2 mm", "pipe", "420", H,
                                         {"nominal_size_dn": 10, "outer_diameter": 0.014, "medium": "heating_supply"},
                                         "kermi", note="Rolle 200 m"),
    "kermi-x-net-waermeleitblech": _tga("Kermi x-net Wärmeleitblech 990 × 120 mm", "install-part", "420", H,
                                        _part("mounting", "990x120"), "kermi"),
    "kermi-x-net-stellantrieb": _tga("Kermi x-net Stellantrieb 230 V", "install-part", "420", H, _part("other", "230 V"),
                                     "kermi"),
    "kermi-x-net-wandregler": _tga("Kermi x-net Wandanbauregler 230 V", "install-part", "420", H,
                                   _part("other", "230 V"), "kermi"),
    "kermi-x-net-klemmleiste-6r": _tga("Kermi x-net Klemmleiste 6R 230 V", "install-part", "420", H,
                                       _part("other", "6 Räume"), "kermi"),
    "zehnder-zeno-elektrisch-1700x600": _tga("Zehnder ZENO Handtuchheizkörper elektrisch 1700 × 600", "terminal", "420",
                                             "Heizung", _terminal("radiator", "surface"), "zehnder", "ZENO"),
    "weishaupt-wsb-8-a-rme-ai": _tga("Weishaupt Splitblock WSB 8-A-RME-AI (Paket)", "terminal", "420", "Heizung",
                                     _terminal("heat_pump", "free"), "weishaupt", "WSB 8-A-RME-AI",
                                     note="Böhringer Angebot 25-0023 Titel 1: Wärmepumpe mit Zubehör (Paketpreis)"),
    "bosch-cs6800iaw-12-mb-paket": _tga("Bosch Luft-Wärmepumpe CS6800iAW 12 MB (Paket BOPA CS804)", "terminal", "420",
                                        "Heizung", _terminal("heat_pump", "free"), "bosch", "BOPA CS804",
                                        note="Kupinic Angebot A-104 Titel 1: AW 7 OR-S, CS6800iAW 12 MB, WH 290 "
                                             "mit Zubehör (Paketpreis)"),
    "naturbo-alu-verbundrohr-11-6": _tga("Naturbo Alu-Verbundrohr Ø 11,6 mm", "pipe", "420", H,
                                         {"nominal_size_dn": 8, "outer_diameter": 0.0116, "medium": "heating_supply"},
                                         "naturbo"),
}
for _key, _name, _type, _angle, _dn_to in (
        ("", "Presskupplung 11,6 / 11,6 mm", "coupling", None, None),
        ("-90", "Presskupplung 11,6 / 11,6 mm 90°", "bend", 90, None),
        ("-16", "Presskupplung 11,6 / 16 mm", "adapter", None, 16.0),
        ("-16-90", "Presskupplung 11,6 / 16 mm 90°", "adapter", 90, 16.0)):
    _params = {"fitting_type": _type, "system_line": "alu_composite", "connection_method": "press", "dn": 11.6}
    if _angle:
        _params["angle"] = _angle
    if _dn_to:
        _params.update(line_to="alu_composite", dn_to=_dn_to)
    NEW_TGA["naturbo-presskupplung-11-6" + _key] = _tga("Naturbo " + _name, "pipe-fitting", "420", H, _params, "naturbo")
NEW_TGA["naturbo-pressfenster-einleger"] = _tga("Naturbo Pressfenster-Einleger", "install-part", "420", H,
                                               _part("other", None, "pcs"), "naturbo")
NEW_TGA["naturbo-innenkalibrierer"] = _tga("Naturbo Innenkalibrierer 11,6 / 16 mm", "install-part", "420", H,
                                          _part("other", None, "pcs"), "naturbo")
for _key, _name in (("stuetzfuss", "Stützfuß geschlossen"), ("pruefoeffnung", "Prüföffnung mit Kasten"),
                    ("feuerungsanschluss-90", "Feuerungsanschluss 90°"), ("wandfutter-120", "DW/EW inkl. Wandfutter 120 mm"),
                    ("rohrelement-1000", "Rohrelement 1000 mm"), ("muendungsabschluss", "Mündungsabschluss"),
                    ("dachdurchfuehrung-26-45", "Dachdurchführung 26–45°"), ("dachdurchfuehrung-flach", "Dachdurchführung flach"),
                    ("klemmband", "Klemmband"), ("wandhalter-60", "Wandhalter 60 mm"),
                    ("wandhalter-verl-250", "Verlängerung Wandhalter 250 mm"), ("blende-0", "Blende 0°"),
                    ("universalblende", "Universalblende")):
    NEW_TGA["gsa-fl150-" + _key] = _tga("GSA Future_Line150 " + _name, "install-part", "420", G,
                                        _part("other", "DN 150"), "gsa-schornstein", "Future_Line150",
                                        note="Edelstahlschornstein doppelwandig (GSA Angebot 016SH24)")
NEW_TGA["gsa-z150-regenhaube"] = _tga("GSA Z150-06 Regenhaube ohne Funkenschutz", "install-part", "420", G,
                                      _part("other", "DN 150"), "gsa-schornstein", "Z150-06")
# Böhringer Angebot 25-0023 (heat pump plant, see Weishaupt Hydraulikplan): every material position becomes a
# material (category Heizung). Product data from a web search (Nov 2026, dealer pages quoting the manufacturer);
# article numbers only where the dealers agree, otherwise None.
# id -> (name, description, manufacturer id or None, model, article_no or None, url or None)
W = "weishaupt"
HEATING_MATERIALS = {
    "weishaupt-wsb-8-a-rme-ai": (
        "Weishaupt Splitblock WSB 8-A-RME-AI", "Luft/Wasser-Split-Wärmepumpe 2,0–7,7 kW aus Innengerät WSB 8-A-RME-I "
        "und Außengerät WSB 8-A-RME-A, verbunden über Kältemittelleitung (Zubehör); Heizen und Kühlen, "
        "Heizwasser nach VDI 2035", W, "WSB 8-A-RME-AI", None,
        "https://www.weishaupt.de/produkte/waermepumpen-solar/weishaupt-splitwaermepumpe"),
    "weishaupt-aussenfuehler-ntc-2k": (
        "Weishaupt Außenfühler NTC 2k", "Außenfühler mit Befestigungs-Set für WAB, WBB, WSB, WGB, WTC-G 15-150, "
        "WTC-GB 470/620 (B1 im Hydraulikplan)", W, "Außenfühler NTC 2k", "50900000822",
        "https://www.loebbeshop.de/weishaupt/zubehoer/aussenfuehler-ntc-2k-fuer-wwp/wtc-wem-inklusive-befestigungsset-50900000822/"),
    "weishaupt-kaeltemittelleitung-wsb-10m": (
        "Weishaupt Kältemittelleitungs-Set WSB 8/10, 10 m", "isolierte Verbindungsleitung Außen-/Innengerät, "
        "1/4\" Flüssigkeits- und 5/8\" Heißgasleitung, Kupfer nach EN 12735-1, für R32/R410A/R407C", W,
        "Kältemittelleitungs-Set WSB 8/10 10 m", "51150511440",
        "https://www.heizbude.de/waermepumpen/kaeltemittelleitungs-set-wsb-8-10-laenge-10-m-51150511440-von-weishaupt-hb-191408"),
    "cable-liycy-2x0-75": (
        "Steuerleitung LIYCY 2 × 0,75 mm² grau", "abgeschirmte Steuerleitung (PVC, Kupfergeflecht), je m", None,
        "LIYCY 2x0,75", None, None),
    "weishaupt-bodenkonsole-wsb": (
        "Weishaupt Bodenkonsole für WSB-Außengerät", "zum Einbetonieren in Punktfundamente, B × T × H "
        "755 × 500 × 800 mm", W, "Bodenkonsole WSB", "51150511300",
        "https://www.wolf-online-shop.de/Weishaupt-Bodenkonsole-fuer-WSB-Aussengeraet-51150511300::523368.html"),
    "weishaupt-schutzgitter-wsb": (
        "Weishaupt Schutzgitter-Set WSB 6/8/10", "Schutzgitter für den Verdampfer des Außengeräts", W,
        "Schutzgitter-Set WSB 6/8/10", "51150505022",
        "https://www.heizbude.de/waermepumpen/schutzgitter-set-wsb-6-8-10-51150505022-von-weishaupt-hb-191374"),
    "ringraumdichtung-hrd-150": (
        "Ringraumdichtung HRD 150 für Kältemittelleitungen", "geteilte Ringraumdichtung für Kernbohrung/Futterrohr "
        "Ø 150 mm, Pressplatten Polyamid GF, EPDM, Edelstahlschrauben, gas- und wasserdicht (Hersteller-Nr. bei "
        "Händlern 50900103622 bzw. 50900102862, nicht eindeutig)", W, "HRD 150", None,
        "https://www.haustechnik-handrich.de/weishaupt-systemtechnik/weishaupt-ringraumdichtung-hrd-150"),
    "weishaupt-em-hk": (
        "Weishaupt Erweiterungsmodul EM-HK", "Regelung eines weiteren Pumpen- oder Mischerheizkreises inkl. "
        "Vorlauffühler, Wand- oder Hutschienenmontage (WP-EM HK im Hydraulikplan)", W, "EM-HK", "51150401512",
        "https://www.loebbeshop.de/weishaupt/zubehoer/erweiterungsmodul-em-hk-51150401512/"),
    "weishaupt-can-bus-rj11-5m": (
        "Weishaupt CAN-Bus-Leitung RJ11 4-polig geschirmt, 5 m", "Verbindungsleitung Erweiterungsmodul – "
        "Hydraulikeinheit", W, "CAN-Bus-Leitung RJ11 5 m", None, None),
    "weishaupt-whi-pump-25-6": (
        "Weishaupt Pumpengruppe WHI pump 25-6 #5", "Pumpengruppe NW 25 mit Grundfos Alpha2.2 25-60, Kugelhähne, "
        "Thermometer, Schwerkraftbremse, EPP-Dämmung; max. 1,7 m³/h bei 200 mbar (Heizkreis 1, M1)", W,
        "WHI pump 25-6 #5", "40900021522",
        "https://www.loebbeshop.de/weishaupt/zubehoer/pumpengruppe-whi-pump-25-6-5-artikel-40900021522/"),
    "weishaupt-whi-mix-25-6-2-5": (
        "Weishaupt Mischergruppe WHI mix 25-6-2,5 #5", "Mischergruppe NW 25 mit Grundfos Alpha2.2 25-60, "
        "3-Wege-Mischer Kvs 2,5 mit Stellantrieb, Kugelhähne, Thermometer, Schwerkraftbremse (Heizkreis 2, MM2)", W,
        "WHI mix 25-6-2,5 #5", "40900021582",
        "https://www.wolf-online-shop.de/Weishaupt-Mischergruppe-WHI-mix-25-6-2-5-5-mit-Alpha2-2-25-60-Kvs-2-5-40900021582::342268.html"),
    "weishaupt-pumpenabschaltung-fbh": (
        "Weishaupt Pumpenabschaltung-Set Fußbodenheizkreis", "Temperaturwächter zur Pumpenabschaltung "
        "(F51/F52 im Hydraulikplan)", W, "Pumpenabschaltung-Set", None, None),
    "weishaupt-whi-distri-comp-25-2": (
        "Weishaupt Verteiler WHI distri-comp 25-2-3,5 #1", "Verteiler mit integrierter Weiche für 2 Heizkreise "
        "NW 25 bis 3,5 m³/h, Kammer 80 × 50 mm, H × B × T 166 × 560 × 219 mm, mit Wärmedämmung", W,
        "WHI distri-comp 25-2-3,5 #1", "40900012242", "https://www.loebbeshop.de/weichenverteiler-whi-distri-comp-25-2-351/"),
    "weishaupt-whue-a-o": (
        "Weishaupt Hydraulik-Übergangs-Set WHÜ-A-O", "Wandkonsole für distri-comp 25-2/3-3,5", W, "WHÜ-A-O",
        "40900012262",
        "https://www.haustechnik-handrich.de/weishaupt-systemtechnik/weishaupt-hydraulik-uebergangs-set-whue-a-o-wandkonsole-fuer-distri-comp-25-2-3-3-5"),
    "weishaupt-temperaturfuehler-ntc5k": (
        "Weishaupt Temperaturfühler-Set NTC 5k, 5 m", "Tauchfühler für Trinkwasserspeicher sowie Puffer, Weiche, "
        "Systemtrennung, 5 m Kabel mit Kabelhalter (B2/B3 im Hydraulikplan)", W, "Temperaturfühler NTC5k 5 m",
        "47130622032",
        "https://www.loebbeshop.de/weishaupt/zubehoer/temperaturfuehler-ntc-5k-mit-5m-kabel-artikel-47130622032/"),
    "weishaupt-was-200-le": (
        "Weishaupt Trinkwasserspeicher WAS 200 LE / Eco", "Wärmepumpenspeicher 200 l mit vergrößertem "
        "Rohrwendel-Wärmetauscher, emaillierter Stahlbehälter mit Schutzanode, 10 bar, Effizienzklasse A "
        "(Art.-Nr. bei Händlern 47520001 bzw. 47720001, nicht eindeutig)", W, "WAS 200 LE / Eco", None,
        "https://www.haustechnik-handrich.de/weishaupt-systemtechnik/weishaupt-trinkwasserspeicher-was-200-le-eco"),
    "weishaupt-weh-f180-3-5": (
        "Weishaupt Elektro-Heizeinsatz WEH F180 3,5 kW", "Flansch Ø 180 mm, 400 V Sternschaltung, Heizleistung "
        "0,5–3,5 kW wählbar (PV-Nutzung), elektropoliert gegen Kalk (E9 im Hydraulikplan)", W, "WEH F180 3,5 - 0,5/1/2",
        "47330018040",
        "https://www.heizbude.de/heizung/elektro-heizeinsatz-3-5-kw-weh-f180-3-5-0-5-1-2-47330018040-von-weishaupt-hb-185220"),
    "weishaupt-aqua-anschlussgruppe": (
        "Weishaupt Aqua-Anschlussgruppe (Trinkwasser)", "Kugelhähne Vor- und Rücklauf mit Verschraubungen für den "
        "Speicheranschluss", W, "Aqua-Anschlussgruppe (Trinkwasser)", "51150501022",
        "https://www.haustechnik-handrich.de/weishaupt-systemtechnik/weishaupt-aqua-anschlussgruppe-trinkwasser"),
    "kfe-kugelhahn-1-2": (
        "KFE-Kugelhahn Simplex 1/2\" vernickelt", "selbstdichtend, PN 16, mit Schlauchverschraubung", None,
        "KFE-Kugelhahn Simplex 1/2\"", None, None),
    "schnellentluefter-3-8": (
        "Schnellentlüfter 3/8\" Messing", "10 bar, mit automatischem Absperrventil", None, "Schnellentlüfter 3/8\"",
        None, None),
    "fuellset-schlauch-5m": (
        "Füllset mit Schlauch 5 m", "Füllschlauch 5 m mit Wandschlauchhalter", None, "Füllset 5 m", None, None),
    "beste-easyfil-ve": (
        "BESTE Nachfüllkombination easyfil VE", "Nachfüllstation mit Systemtrenner BA für vollentsalztes "
        "Heizungswasser nach VDI 2035, Kapazitätskontrolle durch Farbwechsel der Kartusche", "beste", "easyfil VE",
        None, "https://shop.beste-wasser.de/Produkte-zur-Wasseraufbereitung/Heizungswasser/BESTE-Nachfuellkombination-easyfil-VE.html"),
    "schlueter-bekotec-therm-hr-14x2": (
        "Schlüter-BEKOTEC-THERM-HR Heizrohr 14 × 2 mm", "5-Schicht-Verbundrohr PE-RT mit Sauerstoffdiffusionssperre, "
        "DIN 16833, Rollen 120/600 m (BTHR14RT120 / BTHR14RT600), für die Noppenplatte BEKOTEC EN 23 F", "schlueter",
        "BEKOTEC-THERM-HR 14x2", None, "https://eu.schluter.com/de-DE/wassergefuehrte-heizung-269/e/21804/bekotec-therm-hr"),
    "xtra-rohrfuehrungsbogen-14-17": (
        "Xtra Rohrführungsbogen 14–17 mm", "Kunststoff-Führungsbogen für den Rohraustritt aus dem Estrich", None,
        "Rohrführungsbogen 14-17", None, None),
    "xtra-schutzhuelse-300x5": (
        "Xtra Schutzhülse 300 × 5 mm", "Schutzhülse für Rohre bis 20 mm (Bewegungsfugen)", None, "Schutzhülse 300x5",
        None, None),
    "skv-heizkreisverteiler-5": (
        "Heizkreisverteiler Edelstahl 5 Heizkreise (SKV)", "Verteilerstation mit Befestigungskonsolen, Montage "
        "unter der Decke im UG; Hersteller im Beleg nicht genannt", None, "SKV Heizkreis-Verteilerstation 5 HK", None,
        None),
    "skv-heizkreisverteiler-5-up": (
        "Heizkreisverteiler Edelstahl 5 Heizkreise im UP-Schrank (SKV)", "Alternative 3.4a: im Unterputzschrank mit "
        "weiß lackierter Tür; Hersteller im Beleg nicht genannt", None, "SKV Heizkreis-Verteilerstation 5 HK UP", None,
        None),
    "regelverteiler-6-raeume": (
        "Regelverteiler 6 Räume / 14 Stellantriebe 230 V", "Klemmleiste für bis zu 6 Raumthermostate und 14 "
        "Stellantriebe, 230 V, Absicherung 4 A", None, "Regelverteiler 6R", None, None),
    "xtra-stellantrieb-230v": (
        "Xtra Stellantrieb 230 V", "thermischer Stellantrieb für den Heizkreisverteiler", None, "Stellantrieb 230 V",
        None, None),
    "bekotec-verschraubung-14-3-4": (
        "Schlüter-BEKOTEC-THERM-KV Klemmringverschraubung 14 mm, 3/4\"", "vernickeltes Messing, 3/4\" (DN 20) "
        "Eurokonus, Set mit 2 Stück für Vor- und Rücklauf", "schlueter", "BEKOTEC-THERM-KV 14", "BTZ2KV14",
        "https://www.bau99.de/schlueter-bekotec-therm-kv-klemmringverschraubung-dn-20-3-4-14-mm-btz2kv14/"),
    "broetje-europrof-33-900x700": (
        "Brötje Ventil-Flachheizkörper EuroProfil Excellent Typ 33 E 900 × 700", "Bauhöhe 900, Baulänge 700, "
        "Bautiefe 158 mm, profilierte Front weiß, Ventilgarnitur Zweirohr, 10 bar, max. 120 °C", "broetje",
        "EuroProfil Excellent 33 E 900x700", "092005",
        "https://heizung-billiger.de/587380-brotje-ventil-flachheizkorper-europrof-typ-33-e-900x700mm-lackiert-broetje-092005-4017042092005.html"),
    "broetje-europrof-33-900x900": (
        "Brötje Ventil-Flachheizkörper EuroProfil Excellent Typ 33 E 900 × 900", "Bauhöhe 900, Baulänge 900, "
        "profilierte Front weiß, mit Seitenblenden und Abdeckung", "broetje", "EuroProfil Excellent 33 E 900x900",
        "092043",
        "https://heizung-billiger.de/587343-brotje-ventil-flachheizkorper-europrof-typ-33-e-900x900mm-lackiert-broetje-092043-4017042092043.html"),
    "zweirohr-hahnblock-3-4": (
        "Zweirohr-Hahnblock 3/4\" AG Eurokonus, Eckform", "Rohrabstand 50 mm, Anschluss DN 20 AG, 10 bar", None,
        "Hahnblock 3/4\" Eck", None, None),
    "heimeier-thermostatkopf": (
        "Heimeier Thermostatkopf K weiß", "Flüssigkeitsfühler, M30 × 1,5, 6–28 °C, Merkzahl 1–5, ohne Nullstellung",
        "heimeier", "Thermostatkopf K", "6000-00.500",
        "https://www.unidomo.de/heizung/heizkoerper/heizkoerperzubehoer/heimeier-thermostatkopf-k-6000-00-500-m30-mal-1-5-mm_43253_2873/"),
    "hz-sockelleiste-slf-2000": (
        "HZ Sockelleiste SLF 2000 W weiß", "Kunststoff-Hohlkammerprofil 95 × 39 mm, Länge 4 m, für Rohre bis "
        "22 mm, je m", "hz-weitzel", "SLF 2000 W", "2080",
        "https://shop.ottenbruch.de/de/artikel/heizung,2989,hz-sockelleiste-slf-2000w-nr-2080,HZSLF2000W/"),
    "hz-schelle-sch": (
        "HZ Schelle SCH", "Rohr- und Sockelleistenhalter für SLF, Rohre bis 22 mm", "hz-weitzel", "SCH", None, None),
    "hz-awa-15": (
        "HZ Ausgleichs-Winkelabsperrverschraubung AWA 15 mm", "mit Klemmringverschraubung 15 mm, für HKU", "hz-weitzel",
        "AWA", "1022", None),
    "hz-hku-u-18-vp": (
        "HZ Heizkörperanschluss HKU U 18 VP", "zweiteilig, Messing, Presssystem Kontur V für Cu/C-Stahl 18 mm, "
        "10 bar, 90 °C", "hz-weitzel", "HKU 18 VP", "1448", "https://www.hz-weitzel.de/produkte/hku-3/"),
    "rohrdaemmung-pvc-28": (
        "Rohrdämmung 100 % nach HeizAnlV mit PVC-Mantel, Rohr 28 mm", "Böhringer Titel 6, je m gedämmtes Rohr; "
        "Dämmstoff und -dicke im Beleg nicht genannt", None, "Rohrdämmung 28", None, None),
    "rohrdaemmung-pvc-18": (
        "Rohrdämmung 100 % nach HeizAnlV mit PVC-Mantel, Rohr 18 mm", "Böhringer Titel 6, je m gedämmtes Rohr; "
        "Dämmstoff und -dicke im Beleg nicht genannt", None, "Rohrdämmung 18", None, None),
}
for _d, _s in ((35, "1,5"), (28, "1,5"), (22, "1,5"), (18, "1,0")):
    HEATING_MATERIALS["cu-rohr-%dx%s" % (_d, _s.replace(",", "-"))] = (
        "Kupferrohr %d × %s mm" % (_d, _s), "Heizungsleitung Vor-/Rücklauf, Kupfer nach DIN EN 1057, Stangen 6 m, "
        "je m (Beleg 5.3/5.4 nennt widersprüchlich \"aus unlegiertem Stahl\")", None, "Cu %dx%s" % (_d, _s), None, None)


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def dump(p, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def slug(text):
    t = text.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        t = t.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def short_name(supplier):
    # "Stuckateur Cetin GmbH" -> "Stuckateur Cetin"; text in parentheses is dropped
    return re.sub(r"\s+", " ", LEGAL.sub(" ", supplier.split("(")[0].replace(",", " "))).strip(" -–&+")


def company_for(supplier, companies, new_companies):
    known = next((cid for prefix, cid in SUPPLIER_IDS.items() if supplier.startswith(prefix)), None)
    cid = known or slug(short_name(supplier))
    if cid not in companies and cid not in new_companies:
        new_companies[cid] = {"id": cid, "name": supplier, "roles": ["supplier"],
                              "description": "Lieferant/Handwerker aus den Belegen (catalog/imported_documents)"}
    return cid


def topic(stem, number):
    # file name tail after the document number, e.g. "...-1783-schlussrechnung-dach" -> "Schlussrechnung Dach"
    tail = stem.lower().split(slug(number) + "-", 1)[-1] if number else stem[11:]
    words = []
    for w in tail.split("-"):
        if w in ABBREVIATIONS:
            words.append(ABBREVIATIONS[w])
            continue
        w = re.sub(r"(?<![aeq])ue", "ü", w.replace("ae", "ä").replace("oe", "ö"))
        words.append(w if w.isdigit() else w[:1].upper() + w[1:])
    return " ".join(words)


def label(supplier):
    return next((v for k, v in LABELS.items() if supplier.startswith(k)), short_name(supplier).split(" ")[0])


def item_ref(description):
    for pattern, ref in ITEM_REFS:
        if re.search(pattern, description):
            return ref, pattern
    return None, None


def build_document(stem, raw, supplier_id):
    number = raw.get("invoice_number")
    doc_id = slug(stem)
    items, item_sum = [], 0.0
    for raw_item in raw["items"]:
        item = {k: raw_item.get(k) for k in ("position", "description", "quantity", "unit", "unit_price",
                                             "total_price")}
        unit = item["unit"]
        if isinstance(unit, str) and UNITS.get(unit.lower(), unit) != unit:
            item["unit"], item["unit_raw"] = UNITS[unit.lower()], unit
        ref, _ = item_ref(item["description"])
        if ref:
            item["ref"] = ref
        items.append(item)
        item_sum += float(item["total_price"] or 0)
    vat = float(raw.get("vat_rate") or 0)
    subtotal = float(raw.get("subtotal_net") or 0)
    gross_items = abs(item_sum - subtotal) > TOL and abs(item_sum / (1 + vat / 100) - subtotal) <= TOL
    doc = {"id": doc_id, "name": "%s – %s" % (" ".join(filter(None, (label(raw["supplier"]), number))),
                                               topic(stem, number)),
           "doc_type": raw["type"], "supplier": "company:" + supplier_id, "date": raw["date"], "number": number,
           "customer_number": raw.get("customer_number"), "category": raw.get("category"),
           "object": raw.get("object"), "project": raw.get("project"), "description": raw.get("description"),
           "prices_are_net": raw.get("prices_are_net"), "items": items}
    if gross_items:
        doc["items_gross"] = True
    for key in ("subtotal_net", "discount_net", "shipping_net"):
        doc[key] = raw.get(key)
    deductions = subtotal - float(raw.get("discount_net") or 0) + float(raw.get("shipping_net") or 0) \
        - float(raw.get("total_net") or 0)
    if abs(deductions) > TOL:
        doc["deductions_net"] = round(deductions, 2)
    for key in ("total_net", "vat_rate", "vat_amount", "total_gross", "currency"):
        doc[key] = raw.get(key)
    pdf = (IMPORT / raw["pdf"]).resolve() if raw.get("pdf") else None
    doc["pdf"] = "imported_documents/" + raw["pdf"][2:] if pdf and pdf.is_file() else None
    doc.update({"imported_from": "imported_documents/%s.json" % stem, "source_sha256": raw.get("source_sha256"),
                "original_filename": raw.get("original_filename")})
    return doc


def link_related(docs):
    # a document whose description names the number of another document of the same supplier is related to it
    for doc in docs.values():
        for other in docs.values():
            number = other["number"]
            if other is doc or not number or other["supplier"] != doc["supplier"]:
                continue
            if re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(number), doc.get("description") or ""):
                for a, b in ((doc, other), (other, doc)):
                    a.setdefault("related", [])
                    if "document:" + b["id"] not in a["related"]:
                        a["related"].append("document:" + b["id"])
    for doc in docs.values():
        if "related" in doc:
            doc["related"].sort()


def offer_of(doc, item):
    unit = item.get("unit") or ""
    source = "%s %s, Pos. %s, je %s" % (TYPE_DE[doc["doc_type"]], doc["number"] or "", item.get("position") or "-",
                                         unit)
    return {"supplier": doc["supplier"], "price": item["unit_price"], "currency": doc.get("currency") or "EUR",
            "price_basis": "gross" if doc.get("items_gross") else "net", "date": doc["date"],
            "source": source, "document": "document:" + doc["id"]}


def new_material(mid):
    name, category, description, conductivity, manufacturer = NEW_MATERIALS[mid]
    element = {"id": mid, "name": name, "category": category, "description": description,
               "conductivity": conductivity, "values_source": "aus Beleg; Kennwerte sonst offen",
               "product": {"model": name, "offers": []}, "appearance": dict(APPEARANCE[category])}
    if manufacturer:
        element["product"] = {"manufacturer": "company:" + manufacturer, **element["product"]}
    return element


def heating_material(mid):
    name, description, manufacturer, model, article_no, url = HEATING_MATERIALS[mid]
    product = {"model": model}
    if manufacturer:
        product = {"manufacturer": "company:" + manufacturer, **product}
    if article_no:
        product["article_no"] = article_no
    if url:
        product["url"] = url
    product["offers"] = []
    return {"id": mid, "name": name, "category": "Heizung", "description": description, "conductivity": None,
            "values_source": "aus Beleg; Produktdaten laut Händlerseiten (Websuche Nov 2026), Kennwerte offen",
            "product": product, "appearance": dict(APPEARANCE["Heizung"])}


def add_offers(docs, elements, changed, report):
    for doc in sorted(docs.values(), key=lambda d: d["date"]):
        for item in doc["items"]:
            ref = item.get("ref")
            if not ref or not isinstance(item.get("unit_price"), (int, float)) or item["unit_price"] <= 0:
                continue
            if item.get("unit") == "psch":
                # lump sums (material package with labour) are linked but give no unit price
                continue
            element = elements[ref]
            offers = element.setdefault("product", {}).setdefault("offers", [])
            offer = offer_of(doc, item)
            if any(o.get("document") == offer["document"] and o.get("price") == offer["price"] for o in offers):
                continue
            same = [o for o in offers if o.get("supplier") == offer["supplier"] and o.get("date") == doc["date"]
                    and "document" not in o]
            if same:
                same[0]["document"] = offer["document"]
                report.append("  offer linked  %s <- %s" % (ref, doc["id"]))
            else:
                offers.append(offer)
                report.append("  offer added   %s <- %s %.2f/%s" % (ref, doc["id"], offer["price"], item.get("unit")))
            changed.add(ref)


def main(write):
    companies = {p.stem: load(p) for p in COMPANIES.glob("*.json")}
    new_companies, docs, report = {}, {}, []
    for path in sorted(IMPORT.glob("*.json")):
        raw = load(path)
        if raw.get("object") != OBJECT:
            continue
        supplier_id = company_for(raw["supplier"], companies, new_companies)
        doc = build_document(path.stem, raw, supplier_id)
        docs[doc["id"]] = doc
    link_related(docs)
    folders = {"material": CAT / "materials", "component": CAT / "components",
               "tga-component": CAT / "tga-components"}
    new_elements = {"component": NEW_COMPONENTS, "tga-component": NEW_TGA}
    elements, changed = {}, set()
    for doc in docs.values():
        for item in doc["items"]:
            ref = item.get("ref")
            if not ref or ref in elements:
                continue
            kind, eid = ref.split(":")
            path = folders[kind] / (eid + ".json")
            if path.is_file():
                elements[ref] = load(path)
            elif kind == "material" and eid in NEW_MATERIALS:
                elements[ref] = new_material(eid)
                changed.add(ref)
                report.append("  new material  " + ref)
            elif kind == "material" and eid in HEATING_MATERIALS:
                elements[ref] = heating_material(eid)
                changed.add(ref)
                report.append("  new material  " + ref)
            elif eid in new_elements.get(kind, {}):
                elements[ref] = {"id": eid, **json.loads(json.dumps(new_elements[kind][eid]))}
                changed.add(ref)
                report.append("  new %s  %s" % (kind, ref))
            else:
                sys.exit("unknown ref %s (%s)" % (ref, doc["id"]))
    add_offers(docs, elements, changed, report)
    # suppliers that already exist but lack the role supplier (naturbo, velux)
    role_added = [cid for cid in {d["supplier"][8:] for d in docs.values()}
                  if cid in companies and "supplier" not in companies[cid].get("roles", [])]
    for cid, description in NEW_MANUFACTURERS.items():
        if cid not in companies:
            new_companies[cid] = {"id": cid, "name": description.split(" (")[0], "roles": ["manufacturer"],
                                  "description": "Hersteller laut Beleg: " + description}
    maker_added = [cid for cid in MANUFACTURER_ROLE if "manufacturer" not in companies[cid].get("roles", [])]
    print("documents: %d, new companies: %d, supplier role added: %s, manufacturer role added: %s"
          % (len(docs), len(new_companies), role_added, maker_added))
    for cid, company in sorted(new_companies.items()):
        print("  new company   %s (%s)" % (cid, company["name"]))
    print("item links:")
    for doc in docs.values():
        for item in doc["items"]:
            if item.get("ref"):
                print("  %-55s %-45s %s" % (doc["id"][:55], item["ref"], item["description"][:60]))
    print("\n".join(report))
    for doc in docs.values():
        flags = [k for k in ("items_gross", "deductions_net", "related") if k in doc]
        if flags:
            print("  flags %s: %s" % (doc["id"], ", ".join("%s=%s" % (k, doc[k]) for k in flags)))
    if not write:
        print("dry run - use --write")
        return
    DOCUMENTS.mkdir(exist_ok=True)
    for doc in docs.values():
        dump(DOCUMENTS / (doc["id"] + ".json"), doc)
    for cid, company in new_companies.items():
        dump(COMPANIES / (cid + ".json"), company)
    for cid in role_added:
        companies[cid]["roles"].append("supplier")
        dump(COMPANIES / (cid + ".json"), companies[cid])
    for cid in maker_added:
        companies[cid]["roles"].insert(0, "manufacturer")
        dump(COMPANIES / (cid + ".json"), companies[cid])
    for ref in changed:
        kind, eid = ref.split(":")
        dump(folders[kind] / (eid + ".json"), elements[ref])
    print("written: %d documents, %d companies, %d elements" % (len(docs), len(new_companies) + len(role_added),
                                                                  len(changed)))


if __name__ == "__main__":
    main("--write" in sys.argv)
