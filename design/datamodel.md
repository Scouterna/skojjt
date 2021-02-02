# DataModellen i Skojjt

Använder Google Appengine ndb.
KeyProperty används för att binda ihop datatyperna genom keys.
En del KeyProperties är redundanta, så de är inte med i sammanställningen nedan

De huvudsakliga klasserna är

* ScoutGroup = Kår. Har inga KeyProperties
* Person = person i Scoutnet för viss kår. KeyProperty: ScoutGroup
* Troop = Avdelning för en viss termin och kår, KeyProperties: Semester (termin) och ScoutGroup (kår)
* TroopPerson - person som tillhör en avdelning (en viss termin), KeyProperties: Troop, Person
* Meeting - möte/lägerdag för en avdelning och en lista med personer, KeyProperties: Troop, lista av personer

Till detta kommer nya klasser för Märken (Badges).
Specas i data_badge.py

* Badge = Märke. Kårspecifikt märke/certifikat.
  KeyProperty: ScoutGroup.
  Andra: namn, description, parts_scout_short, parts_scout_long, parts_admin_short, parts_admin_long
  De semare är för olika delar och är korta och långa beskrivningar.
* BadgePartDone - detaljer av godkänd del.
  KeyProperties: Person, Badge
  Andra properties: idx, date, examiner
  idx som ger BadgePart, date och examiner ger
  detaljer om när och vem som godkände. idx >= ADMIN_OFFSET är admin-delar.
* TroopBadges = Lista av märken för avdelning(och termin):
  KeyProperties: Troop, Badge.
  Andra properties: idx för att sortera samma hela tiden (onödig)
* BadgeCompleted - egentligen redundant, men gör det lättare
  att lista hur många och vilka som är klara
  KeyProperties: badge_key, person_key
  Other: date, examiner


Hur göra tabeller av relevanta data:

1. Kårnivå lista:
    Sök alla Badge med keyProperty=Scoutgroup
    Lista namn
2. Detaljer av märke
   1. Slå upp en badge
3. På avdelningsnivå per termin
    Sök på TroopBadges med troop som nyckel
4. För listning av progress för avdelning och märke
   För märke och märkesdelar, hämta detta från Badge
   För personrad, sök på BadgePartDone med nycklar badge och person
5. För listning av alla scouters som klarat ett märke.
   Sök BadgeCompleted(scout_group, badge)

## Ta bort (ej ännu implementerat)

### Ta bort märke:

   1. BadgePartDone, BadgeCompleted, TroopBadge
      har alla badge_key som KeyProperty och kan lätt hittas
      Ta bort dessa
   2. Ta bort Badge

### Ta bort del av märke:

    1. Sök på BadgePartDone med märke och index och ta bort all
    2. Skriv över listan med delar av märket

### Ta bort person:
   * Sök alla BadgePartDone på person och ta bort
   * Sök all BadgeCompleted på personen och ta bort