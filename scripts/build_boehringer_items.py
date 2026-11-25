"""Writes all positions of Böhringer Angebot 25-0023 (HZ_Tausch PDF) into its raw import JSON and adds the
Weishaupt Hydraulikplan as raw import JSON (doc_type plan). Run once, then scripts/import_documents.py --write."""
import hashlib
import json
import pathlib

IMPORT = pathlib.Path(__file__).resolve().parent.parent / "catalog" / "imported_documents"
OFFER = IMPORT / "2025-04-14-boehringer-25-0023-angebot-waermepumpe.json"
PLAN = IMPORT / "2025-05-26-weishaupt-hydraulikplan-waermepumpe.json"
PLAN_PDF = "HZ_Tausch/2025-05-26 Hydraulikplan CCE26052025_0003.pdf"

# position, quantity, unit, description, unit price, total (None = alternative position)
ITEMS = [
    ("1.1", 1, "St", "Weishaupt Splitblock WSB 8-A-RME-AI", 9701.47, 9701.47),
    ("1.2", 1, "St", "Außenfühler NTC 2k für WAB, WBB, WSB, WGB, WTC-G 15-150, WTC-GB 470/620", 41.18, 41.18),
    ("1.3", 1, "St", "Kältemittelleitungs-Set WSB 8/10 Länge 10 m", 523.78, 523.78),
    ("1.4", 12, "m", "Steuerleitung abgeschirmt LIYCY 2 x 0,75 grau (pro lfm)", 2.74, 32.88),
    ("1.5", 1, "St", "Bodenkonsole für WSB Außengerät", 567.07, 567.07),
    ("1.6", 1, "St", "Schutzgitter-Set WSB 6/8/10", 227.04, 227.04),
    ("1.7", 1, "St", "Ringraumdichtung HRD 150", 223.87, 223.87),
    ("1.8", 1, "St", "Erweiterungsmodul EM-HK für weiteren Mischerkreis WAB, WBB, WSB, WGB, GB 620", 699.07, 699.07),
    ("1.9", 1, "St", "CAN-Bus-Leitung RJ11 5 m lang 4-polig, geschirmt", 17.67, 17.67),
    ("1.10", 1, "St", "Pumpengruppe WHI pump 25-6 #5 mit Alpha2.2 25-60", 731.61, 731.61),
    ("1.11", 1, "St", "Mischergruppe WHI mix 25-6-2,5 #5 mit Alpha2.2 25-60, Kvs 2,5", 990.00, 990.00),
    ("1.12", 1, "St", "Pumpenabschaltung-Set für Fußbodenheizkreis (für alle Heizsysteme)", 102.96, 102.96),
    ("1.13", 1, "St", "Verteiler WHI distri-comp 25-2-3,5 #1 integr. Weiche, 2 Heizkreise, bis 3,5 m3/h", 454.41, 454.41),
    ("1.14", 1, "St", "Hydraulikübergangs-Set WHÜ-A-O Wandkonsole für distri-comp 25-2/3-3,5", 69.79, 69.79),
    ("1.15", 2, "St", "Temperaturfühler NTC5k 5m Puffer, Weiche, Warmwasser (WTC-G 15-150, 470/620, WWP)", 33.16, 66.32),
    ("1.16", 1, "St", "Trinkwasserspeicher WAS 200 LE / Eco", 2264.06, 2264.06),
    ("1.17", 1, "St", "Elektro-Heizeinsatz 3,5 kW WEH F180 3,5 - 0,5/1/2", 524.70, 524.70),
    ("1.18", 1, "St", "Aqua-Anschlussgruppe (Trinkwasser) empty", 104.54, 104.54),
    ("1.19", 1, "St", "Kältetechnische Inbetriebnahme Split", 1551.00, 1551.00),
    ("2.1", 4, "St", "KFE-Kugelhahn Simplex 1/2\" vernickelt selbstdicht. PN 16 m.Schlauchverschr.", 16.50, 66.00),
    ("2.2", 4, "St", "Schnellentluefter 3/8\" 10 bar messing m.automatischem Absperrventil", 10.50, 42.00),
    ("2.3", 1, "St", "Fuellset m.Schlauch 5 Meter u.Wandschlauchhalter", 42.00, 42.00),
    ("2.4", 1, "St", "BESTE easyfil VE Nachfüllstation für die Heizungsanlage zur automatischen Befüllung mit "
                     "vollentsalztem Wasser, Kapazitätskontrolle durch Farbwechsel der Kartusche", 480.00, 480.00),
    ("2.5", 1, "St", "Befüllung der Heizungsanlage mit aufbereitetem Wasser nach VDI 2035", 450.00, 450.00),
    ("3.1", 500, "m", "BEKOTEC-Therm Rohr PE-RT 14 x 2,0 mm in Rollen", 2.55, 1275.00),
    ("3.2", 10, "St", "Xtra Rohrfuehrungsbogen f.Rohr 14-17mm Kunststoff", 2.04, 20.40),
    ("3.3", 10, "St", "Xtra Schutzhuelse 300 x 5 mm, fuer Rohre bis 20mm", 1.11, 11.10),
    ("3.4", 1, "St", "SKV Heizkreis-Verteilerstation aus Edelstahl, einschl. Befestigungskonsolen. für 5 Heizkreise "
                     "zur Montage unter der Decke im UG", 612.00, 612.00),
    ("3.4a", 1, "St", "Alternativ zu 3.4: SKV Heizkreis-Verteilerstation aus Edelstahl, einschl. Befestigungskonsolen. "
                      "für 5 Heizkreise, im UP-Schrank, mit weiss lackierter Tür", 714.00, None),
    ("3.5", 1, "St", "Regelverteiler für bis zu 6 Raumthermostate, und bis zu 14 Stellantriebe, 230V, Absicherung 4A",
     98.60, 98.60),
    ("3.6", 5, "St", "XTRA-Stellantriebe 230V", 23.80, 119.00),
    ("3.7", 10, "St", "BEKOTEC-Verschraubung 14 x 3/4\" IG, Eurokonus, aus Messing", 6.63, 66.30),
    ("4.1", 2, "St", "Broetje Ventil-Flachheizkoerper EuroProf Typ 33 E 900x700 mm lackiert", 580.00, 1160.00),
    ("4.2", 1, "St", "Broetje Ventil-Flachheizkoerper EuroProf Typ 33 E 900x900 mm lackiert", 704.00, 704.00),
    ("4.3", 3, "St", "Zweirohr-Hahnblock 3/4\" AG Konus lose m.AG DN 20 Rohrabstand 50mm Eck 10 bar", 25.60, 76.80),
    ("4.4", 3, "St", "Heimeier Thermostatkopf weiss, Merkzahl 1 bis 5", 24.00, 72.00),
    ("4.5", 12, "m", "HZ Sockelleiste SLF 2000 W, Weiss, Länge 4 Meter", 9.60, 115.20),
    ("4.6", 24, "St", "HZ Schelle SCH, zur Befestigung über den Rohren bis 22 mm", 1.93, 46.32),
    ("4.7", 3, "St", "HZ Ausgleichs-Winkelabsperrverschraubung AWA, mit Klemmringverschraubung 15 mm", 44.16, 132.48),
    ("4.8", 3, "St", "HZ Heizkörperanschluss HKU U 18 VP, zweiteilig, Presssystem Kontur V", 63.50, 190.50),
    ("5.1", 1, "m", "Ca. Cu-Rohr 35 x 1,5 mm", 34.00, 34.00),
    ("5.2", 20, "m", "Ca. Cu-Rohr 28 x 1,5 mm", 22.10, 442.00),
    ("5.3", 10, "m", "Ca. Cu-Rohr 22 x 1,5 mm, aus unlegiertem Stahl, in Stangen a 6m", 18.70, 187.00),
    ("5.4", 26, "m", "Ca. Cu-Rohr 18 x 1,0 mm, aus unlegiertem Stahl, in Stangen a 6m", 15.30, 397.80),
    ("5.5", 1, "psch", "Zuschlag für Form- und Verbindungsstücke Rohrschellen, etc. (wird nach tatsächlichem Aufwand "
                       "abgerechnet.)", 1360.00, 1360.00),
    ("6.1", 20, "m", "Rohr 28x1,0, zu 100% gemäß HeizAnlV isoliert mit PVC Mantel.", 24.65, 493.00),
    ("6.2", 10, "m", "Rohr 28x1,0, zu 100% gemäß HeizAnlV isoliert mit PVC Mantel.", 23.80, 238.00),
    ("6.3", 12, "m", "Rohr 18x1,0 zu 100% gemäß HeizAnlV isoliert mit PVC Mantel.", 22.10, 265.20),
    ("7.1", 70, "Std.", "Ca. Obermonteurstunden für die Montagearbeiten der Heizungsanlage", 69.50, 4865.00),
    ("7.2", 70, "Std.", "Ca. Monteurstunden für die Montagearbeiten der Heizungsanlage", 69.50, 4865.00),
]

OFFER_DESCRIPTION = (
    "Angebot der Böhringer Bauplanung und Heizungsbau GmbH für die neue Heizungsanlage in Weingärten 8 mit "
    "Weishaupt-Split-Luft-Wasser-Wärmepumpe, Trinkwasserspeicher, Fußbodenheizung, Flachheizkörpern, Rohrleitungen, "
    "Dämmung und Montage, mit allen Einzelpositionen. Titelsummen: 1. Wärmepumpe und Zubehör 18.893,42 €, "
    "2. Armaturen und Zubehör 1.080,00 €, 3. Fußbodenheizung und Zubehör 2.202,40 € (untere Ausgleichschicht und "
    "Systemplatte bauseits durch das Gewerk Estrich; Raumthermostate bauseits durch das Gewerk Elektro), "
    "4. Heizflächen und Zubehör 2.497,30 € (Heizkörpergrößen nach Heizlastberechnung), 5. Rohrleitungen 2.420,80 €, "
    "6. Wärmedämmung 996,20 €, 7. Montagekosten 9.730,00 € (nach tatsächlichem Aufwand). Position 3.4a ist eine "
    "Alternative zu 3.4 ohne Gesamtpreis. In 5.3/5.4 steht beim Cu-Rohr \"aus unlegiertem Stahl\" (Widerspruch im "
    "Beleg); 6.1 und 6.2 nennen beide Rohr 28x1,0 zu verschiedenen Preisen. Diese Fassung enthält die aufschiebende "
    "und auflösende Bedingung zur BEG-Förderung durch BAFA beziehungsweise KfW mit leeren Unterschriftsfeldern "
    "(inhaltsgleiche Fassung ohne Förderklausel: \"2025Boehringer-Heizungstausch.pdf\"); Preisbindung 30 Tage. "
    "Der Auftrag wurde offenbar erteilt, da Böhringer am 07.04.2026 die erste Abschlagsrechnung 26-0150 für die "
    "Heizungsanlage stellte; eine Schlussrechnung liegt noch nicht vor. Anlagenschema: Weishaupt Hydraulikplan "
    "15 00 0 4 01 03 0 0 0.")

PLAN_DESCRIPTION = (
    "Weishaupt Muster-Anlagenschema (Hydraulikplan) Plan 15 00 0 4 01 03 0 0 0 für die Split-Luft-Wasser-Wärmepumpe "
    "zum Angebot 25-0023, Scan vom 26.05.2025 (Plan VW 01.10.17, H und EL geprüft 19.02.18). Komponenten: "
    "1 Außengerät Split WWP, 2 Hydraulikeinheit Split WWP-HE, 3 Trinkwasserspeicher WAS (Glattrohr-Wärmetauscher, "
    "Flanschheizung E9), 4 Verteilerbalken mit integrierter Weiche, 5 Mischermodul WHM (Heizkreis 2, Mischer MM2, "
    "Pumpe M2.2, Vorlauffühler B6.2, Temperaturwächter F52), 6 Pumpengruppe WHP (Heizkreis 1, Pumpe M1, "
    "Temperaturwächter F51). Heizkreis 1 und 2 sind Fußbodenheizkreise. Fühler und Elektrik: B1 Außenfühler, "
    "B2 Weichenfühler, B3 Trinkwasserfühler, B6.2 Vorlauffühler HK 2, EV Elektroverteiler, E9 Flanschheizung "
    "Trinkwasser, F51/F52 Temperaturwächter Fußbodenheizung HK 1/HK 2, M1/M2.2 Heizungsumwälzpumpen HK 1/HK 2, "
    "MM2 Mischer HK 2, WP-EM HK Wärmepumpen-Erweiterungsmodul. Außengerät und Hydraulikeinheit sind über die "
    "Kältemittelleitungen verbunden; die Hydraulikeinheit speist den Verteilerbalken (Vor-/Rücklauf) und die "
    "Speicherladung des Trinkwasserspeichers (Kaltwasser unten, Warmwasser oben). Laut Plan unverbindliches "
    "Anlagenbeispiel ohne Anspruch auf Vollständigkeit; keine Preise. Übergeben vermutlich von Böhringer "
    "(Lieferant angenommen).")


def main():
    offer = json.loads(OFFER.read_text(encoding="utf-8"))
    offer["items"] = [{"position": p, "description": d, "quantity": q, "unit": u, "unit_price": ep, "total_price": gp}
                      for p, q, u, d, ep, gp in ITEMS]
    total = round(sum(gp or 0 for *_, gp in ITEMS), 2)
    assert abs(total - offer["subtotal_net"]) < 0.01, total
    offer["description"] = OFFER_DESCRIPTION
    offer["pdf"] = "./HZ_Tausch/2025-09-11-Boehringer-Angebot-25-0023.pdf"
    OFFER.write_text(json.dumps(offer, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pdf = IMPORT / PLAN_PDF
    plan = {"type": "plan", "supplier": offer["supplier"], "date": "2025-05-26",
            "invoice_number": None, "customer_number": None, "category": "heizung-kamin",
            "object": "weingaerten-8", "project": offer["project"], "items": [], "prices_are_net": True,
            "subtotal_net": None, "discount_net": None, "shipping_net": None, "total_net": None, "vat_rate": None,
            "vat_amount": None, "total_gross": None, "currency": "EUR", "description": PLAN_DESCRIPTION,
            "pdf": "./" + PLAN_PDF, "source_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
            "original_filename": pdf.name}
    PLAN.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("items: %d, sum %.2f; plan written" % (len(ITEMS), total))


if __name__ == "__main__":
    main()
