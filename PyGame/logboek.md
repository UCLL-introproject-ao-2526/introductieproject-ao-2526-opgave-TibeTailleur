## 29 september 2025 (6-7 uur)

Vandaag ben ik begonnen met de blackjack game, startend met de tutorial. Bij elk complexer stukje code heb ik meteen een klein stukje uitleg toegevoegd, zodat ik later nog weet waarvoor het dient.

Daarna ben ik gaan nadenken over hoe ik de game wilde uitbreiden. Ik wilde een simpel spelletje maken dat toch een beetje uitdaging geeft. Daar kwam de volgende structuur uit:

- Menu toevoegen (voor het spel begint)
- UI verbeteren (kaarten met afbeeldingen, achtergrond, knoppen vervangen door keybinds etc.)
- Bettingsysteem (startbedrag krijgen en bet kunnen bepalen, makkelijk aanpasbaar)
- Extra spelregels (split & double down toevoegen voor extra spanning)
- Kaartanimaties (kaarten omdraaien en uit een stapel trekken met animatie)

Dat leek me voldoende om 20 uur bezig te zijn, zeker met relatief weinig Python-ervaring. Ik heb gepland om dit in deze volgorde te doen, omdat de moeilijkheidsgraad telkens iets hoger wordt.

Ik ben gestart met het menu. Hiervoor heb ik een variabele toegevoegd die de status van het spel bijhoudt (`game_state`). Ik maakte het scherm voor zowel het menu als de regels, vrij simpel. Het was even zoeken waar overal moest worden gecheckt wat de status was, maar na veel proberen met `if` en `elif` leek het te werken (ik stond zelf ook versteld 😆).

Daarna ben ik de UI gaan upgraden, stukje per stukje. Eerst fullscreen geprobeerd, maar dat voelde niet helemaal goed voor zo'n spelletje, dus heb ik het venster groter gemaakt op basis van de schermgrootte. Dat gaf wel wat uitlijnproblemen, maar met wat googlen en proberen lukte dat. Het menu gaf ik een achtergrond, logo en mooiere knoppen. De lay-out aanpassen zoals bijvoorbeeld het centreren van de tekst was lastig en kostte wat zoekwerk. Het ‘Rules’-tabje was daarna makkelijker omdat het grotendeels copy-paste was.

Ook heb ik de kaarten vervangen door afbeeldingen. Dit was niet zo complex maar wel wat werk: Google heeft gelukkig een kaarten deck dat je simpel kunt downloaden. Het was wat zoeken het ik het het beste ging toevoegen omdat de tutorial niet 52 kaarten had. Het was vooral een saai werkje, maar uiteindelijk wel een hele verbetering voor het spel.

Dat waren al heel wat uren proberen en aanpassen. Nu begint het echte aanpassen van het spel pas. Ik wil eerst het bettingsysteem maken, maar mijn kennis van Python is nog niet zo sterk. Daarom ga ik eerst Programming 1 door te nemen, zodat ik de basisprincipes goed snapte, voordat ik de logica van het spel echt ging aanpassen.

<br>

## 27 oktober 2025 (3-4 uur)

Na Programming 1 te hebben doorlopen, was ik eindelijk klaar om een poging te wagen om het bettingsysteem te implementeren. Eerst moest ik het bestand opnieuw bekijken om alles te begrijpen, daarvoor heb ik even de hulp ingeroepen van chatGPT. Ik heb simpelweg gevraagd om het document op te ruimen en overzichtelijker te maken, dat hielp al veel.

Ik ben begonnen met de basisvariabelen zoals `balance`, `current_bet` en `show_bet_popup`. Het lastigste was het menu voor de bet bouwen en checks invoegen om te bepalen wanneer het moest verschijnen en verdwijnen. Dat kostte veel tijd, en vooral veel `Run Python file in terminal`. Uiteindelijk werkte het wel, eerst nog met een standaard bet van 100 euro. Het aanpassen van de bet was daarna relatief makkelijk, want de logica stond al.

Een probleem waar ik echt tegenaan liep: als je won, werd de bet bij elke frame opnieuw bij de balance opgeteld, waardoor het geld veel te snel opliep. Dat snapte ik niet helemaal dus heb ik daar de hulp van AI ingeroepe. Het probleem bleek redelijk makkelijk op te lossen met een nieuwe variabele `payout_done` die checkt of de uitbetaling al is uitgevoerd.

Uiteindelijk werkt het bettingsysteem (of toch voorlopig 😅): je kunt een bet inzetten, de kaarten worden gedeeld, je kunt hit of stand gebruiken, en de balance wordt correct bijgewerkt na een ronde.

<br>

## 28 oktober 2025 (6-7 uur)

Ik heb een tijdje in een startup gewerkt met een eigen platform en als ze daar iets maakten, wachtte men altijd een dag om het op productie te zetten. De volgende dag werd het dan nog eens getest met een fris hoofd. Dat deed ik nu ook en al snel stuitte ik op enkele foutjes: de `rules` werkte plots niet meer en als je meer dan 3 kaarten had, liep het over de scores heen. Het eerste werkje van de dag was dus die twee dingen oplossen.

Vandaag was het doel om vooral double down en splitten te maken. Ik begon met double down, wat uiteindelijk makkelijker bleek dan gedacht. Het is eigenlijk een hit, maar daarna stopt de game en qua bet moest het dan verhoogd worden. Splitten was van een ander kaliber.

Ik begon eerst met nadenken hoe ik dat kon implementeren. Het klinkt redelijk makkelijk: je maakt een tweede list (hand) en toont ze beide. Maar daarvoor moest er gigantisch veel veranderd worden in de logica. Als je namelijk de eerste hand speelt, moet je naar de tweede gaan en mag de dealer nog niet getoond worden. Heel complex dus. Heel eerlijk: voor dit stuk heb ik veel gebruik gemaakt van AI. Het was een stuk complexer en nam vooral veel meer tijd in beslag dan gehoopt. Toch vond ik het leerrijk, vooral om te zien hoe AI kan helpen; het denkt mee en kent de blackjackregels beter dan ik. Maar volledig zelf het maken of mij vervangen zat er niet in, het maakte nog veel fouten 😅.

Alles werkte redelijk, en daarna ging ik nog eens goed testen. Ik stootte vooral op irritante foutjes:

- Als je eenmaal double downed, kon je bet op €2000 komen terwijl de max normaal €1000 is. Hiervoor maakte ik een variabele `original_bet` aan.
- Als je bij het dealen al 21 had (een aas en kaart met waarde 10), moest je volgens de game nog iets doen, terwijl je eigenlijk al gewonnen had. Omgekeerd geldt hetzelfde als de dealer 21 heeft.
- Als je dan wint dan ineens springt alles over elkaar, hiervoor heb ik een kleine delay toegevoegd.
- Nog veel meer...

Het werd uiteindelijk een productieve dag, al voelde het soms alsof ik meer tijd stak in debugging dan in nieuwe features.

<br>

## 29 oktober 2025 (2–3 uur)

Vandaag was het de bedoeling om de game zo ver mogelijk af te werken en ook animaties toe te voegen. Daarna kan ik het dan insturen voor feedback.

Ik begon met wat finetuning aan de pop-ups en vooral mijn code eens grondig op te ruimen. Hiervoor had ik de hulp gevraagd van v0, een AI die heel goed is met code, en eerlijk gezegd ook een pak slimmer dan ChatGPT 😅. Na een minuut of vijf had die mijn code beter ingedeeld en vooral chronologischer/logischer gemaakt. Dat was echt een opluchting. In het vervolg ga ik toch wat ordelijker moeten werken, vooral bij mijn beginvariabelen… die stonden zowat overal verspreid.

Daarna heb ik op bepaalde stukken wat extra commentaar toegevoegd. Soms vergeet ik namelijk waarom ik iets op een bepaalde manier gedaan heb, en een simpel zinnetje erbij kan later veel tijd besparen als ik weer aan het staren ben 😅.

Als allerlaatste begon ik aan de animaties. Daar kende ik eerlijk gezegd niets van, dus heb ik hier opnieuw AI voor ingeschakeld. Er moest blijkbaar een class gemaakt worden (daar zou ik zelf niet meteen op gekomen zijn). Dat stuk heb ik deels laten genereren, want het was wat te complex op dat moment. Maar ik moest zelf nog heel wat bijsturen en aanpassen om het goed te krijgen. Uiteindelijk kreeg ik de kaartanimaties overal werkend of toch zover ik kon zien. Want ik verloor al snel overzicht omdat de animaties niet door mij gemaakt waren.

Belangrijkste les vandaag: AI kan helpen, maar als ik niet begrijp wat er gebeurt, maakt het het alleen moeilijker.

<br>

## 30 oktober 2025 (1–2 uur)

Vandaag wou ik de game goed testen, nog wat bugs fixen en daarna feedback vragen.  
Ik kwam eigenlijk al vrij snel achter een paar bugs, zoals dat de split plots niet meer werkte. Bleek uiteindelijk gewoon een stomme fout te zijn met een foute variabele waardoor de code stopte.

Ook waren er nog wat dingen die ik eerder gestart was maar nooit had afgewerkt, zoals het blut/broke scherm. Dat heb ik vandaag ook eindelijk aangepakt.

Uiteindelijk lijkt alles nu goed te werken. Er zitten vast nog wat kleine schoonheidsfoutjes in (zoals dat je je winst al ziet adhv je balance voor je de pop-up ziet), of dingen waar ik over gekeken heb, maar al bij al ben ik wel tevreden.  
Na al die uren vind ik dat het een leuk spelletje geworden is. Al ben ik eerlijk gezegd wel wat beu van games maken, maar het was wél superleerrijk, vooral omdat je constant moet opzoeken en proberen tot het eindelijk werkt zoals in je hoofd.
