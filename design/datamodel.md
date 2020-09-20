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

* Badge = Märke. Kårspecifikt märke/certifikat. KeyProperty: ScoutGroup. Andra: namn
* BadgePart = Märkesdel. KeyProperties: Badge. Har ett index idx som använts för att ordna
  och klassificera. idx < ADMIN_OFFSET är delar som scouten gör själv. Andra properties: short_desc och long_desc
* BadgePartDone - detaljer av godkänd del. KeyProperties: Person
  Badge. Har sen idx som ger BadgePart och date och examiner med
  detaljer om när och vem som godkände
* TroopBadges = Lista av märken för avdelning(och termin):
  KeyProperties: Troop, Badge. Har också ett idx för att
  sortera samma hela tiden
* BadgeProgress = Märkesprogress för en person. KeyProperties: Badge, Person, List of BadgePartDone
* BadgeCompleted - egentligen redundant, men gör det lättare
  att lista hur många och vilka som är klara
  KeyProperties: badge_key, person_key
  Other: date, examiner


Hur göra tabeller av relevanta data:

1. Kårnivå lista:
    Sök alla Badge med keyProperty=Scoutgroup
    Lista namn
2. Lista på märkesdelar på kårnivå
    För ett visst märke, sök efter alla BadgePart med nyckel Badge och sortera efter idx
3. På avdelningsnivå per termin
    Sök på TroopBadges med troop som nyckel
4. För listning av progress för avdelning och märke
   För rubriker, sök på märkesdelar för märke
   För personrad, sök på BadgePartDone med nycklar badge och person
5. För listning av alla scouters som klarat ett märke.
   Sök BadgeCompleted(scout_group, badge)

## Ta bort (ej ännu implementerat)

### Ta bort märke:

   1. BadgePart, BadgePartDone, BadgeCompleted, TroopBadge
      har alla badge_key som KeyProperty och kan lätt hittas
      Ta bort dessa
   2. Ta bort Badge

### Ta bort person:
   * Sök alla BadgePartDone på person och ta bort
   * Sök all BadgeCompleted på personen och ta bort
