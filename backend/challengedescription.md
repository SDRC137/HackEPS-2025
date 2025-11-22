# Repte: restb.ai - El Joc de Barris

## 1. Benvinguda i Visió General

Benvinguts, participants! Avui us proposem un repte universal: trobar el lloc perfecte per viure. Per aconseguir-ho, haureu de combinar ciència de dades, integració d'APIs i un bon disseny. La vostra missió és crear una eina que recomani el barri ideal per a un grup de clients molt especials. No són clients normals: són versions modernes dels personatges de Joc de Trons, cadascun amb les seves pròpies necessitats. Per guanyar, no n'hi haurà prou amb posar dades en un mapa. Haureu d'entendre a fons cada client, trobar les mètriques clau i construir una justificació sòlida basada en dades.

## 2. La Missió

Heu de crear una aplicació o un prototip funcional. Aquesta eina ha de fer possible la visualització de dades personalitzades basades en els requeriments del client, on es pugui veure quina és la zona idònia per cada un. La part més important del projecte és el "motor de justificació": que l'aplicació mostri per què un barri és perfecte per a aquell client, basant-se en les dades que heu integrat.

## 3. Els Clients del Món Modern

Per a desenvolupar la vostra aplicació i saber quines necessitats tenen els clients, aquí teniu una mica més d’informació sobre qui són. Llegiu entre línies: la seva personalitat és la clau!

- **Daenerys Targaryen: L'Emprenedora Ètica**  
    Fundadora d'una startup sostenible, és nova a la ciutat amb els seus tres "dracs" (així li agrada referir-se als seus gossos). Busca un barri amb ànima, ple de negocis locals i amb un fort sentit de comunitat.

- **Cersei Lannister: La Reina Corporativa**  
    Una executiva d'alt nivell que viu pel poder, el prestigi i la privacitat. Per a ella i els seus fills, vol viure aïllada en una bombolla de màxima seguretat, escoles d'elit i botigues de luxe.

- **Bran Stark: L'Analista Total**  
    Un científic de dades que treballa 100% des de casa. Es mou en cadira de rodes, així que necessita zero barreres arquitectòniques. Busca un lloc tranquil, silenciós i amb la millor fibra òptica per poder treballar sense límits.

- **Jon Snow: El Guardià de la Comunitat**  
    Treballa als serveis d'emergència i té un sou públic. Busca un barri autèntic, on els veïns es coneguin. Valora allò pràctic, no el luxe, i necessita tenir la natura a prop per desconnectar.

- **Arya Stark: La Nòmada Urbana**  
    Una freelance independent que valora l'anonimat i la llibertat per sobre de tot. Necessita una "base" en una zona densa i moguda, on pugui barrejar-se amb la gent. Transport públic 24/7 per a qualsevol aventura.

- **Tyrion Lannister: L'Estratega Urbà**  
    Un consultor brillant i molt social. El seu hàbitat és l'epicentre cultural i gastronòmic de la ciutat. Ho vol tot a peu: de la reunió al millor restaurant, i d'allà a un bar sense agafar cap taxi.

## 4. Àmbit Geogràfic: Los Angeles

El repte se situa en un lloc concret: Los Angeles, Califòrnia. Tota la vostra cerca s'ha de centrar exclusivament en aquesta metròpolis. L.A. és una ciutat de contrastos, amb centenars de barris únics. És el llenç perfecte per trobar una llar per a clients tan diferents com la Cersei o en Jon.

## 5. Fonts de Dades i Punt de Partida

Part del repte és que actueu com a "detectius de dades". Teniu llibertat per triar les APIs que vulgueu, però us recomanem que us plantegeu aquestes 5 àrees:

1. **Demografia i Economia**: Quina gent hi viu? (ingressos, edat, densitat, activitat econòmica).
2. **Estil de Vida i Serveis**: Què s'hi pot fer? (restaurants, parcs, cultura, gimnasos, botigues).
3. **Mobilitat i Transport**: Com es mou la gent? (accessibilitat a peu, transport públic, carrils bici, autopistes).
4. **Seguretat**: Com és de segur el barri? (estadístiques de criminalitat o similars).
5. **Habitatge**: Com és viure-hi? (preus de lloguer o compra, tipus d'habitatges).

A continuació us deixem un llistat de recursos per començar:

### APIs Públiques (Per a dades en temps real i consultes)

1. **Overpass API (OpenStreetMap)** - Molt Recomanada  
     - Permet fer consultes complexes a OpenStreetMap.  
     - Ús: Trobar botigues, parcs, parades de bus, accessibilitat (voreres) i molt més.

2. **Los Angeles Open Data Portal**  
     - Portal oficial de dades de la ciutat.  
     - Web: data.lacity.org  
     - Ús: Aquí trobareu dades oficials de crims (LAPD), permisos de construcció, llicències de negocis, etc.

3. **US Census Bureau API**  
     - Dades demogràfiques oficials dels EUA.  
     - Web: census.gov/data/developers/data-sets.html  
     - Ús: Per saber la renda mitjana per codi postal, edat mitjana, densitat de població, etc.

### Datasets Avançats (Arxius per descarregar)

Si voleu anar més enllà i processar dades massives, us recomanem aquests datasets tècnics:

1. **Contaminació Acústica (Noise)**  
     Ideal per a clients com en Bran Stark (que necessita silenci) o la Cersei (que vol aïllament).  
     - Font: US Department of Transportation (National Transportation Noise Map).  
     - Què inclou: Dades de soroll d'aviació, ferrocarril i carretera.  
     - Enllaç: bts.gov/geospatial/national-transportation-noise-map  
     - Nota tècnica: Descarregueu els arxius "Continental U.S." de 2020. És possible que les dades vinguin en format .tiff (raster/imatge). Per treballar-hi millor, us recomanem convertir-les a format .geojson o similar.

2. **Xarxa Viària i Transport (Roads)**  
     Per a anàlisis de mobilitat molt detallades.  
     - Font: Overture Maps Foundation.  
     - Enllaç: docs.overturemaps.org  
     - Nota: És un dataset molt complet i potent, ideal si voleu analitzar connectivitat a gran escala.

### Nota Important sobre l'Estratègia

Volem que gaudiu del repte, així que tingueu en compte aquests punts:

- **Llibertat Total**: Com ja hem mencionat, teniu total llibertat d’utilitzar les APIs i datasets que vulgueu. Les llistes anteriors són només recomanacions per si no sabeu per on començar.
- **Pels més novells**: Si veieu que gestionar múltiples fonts és massa complex, us recomanem centrar-vos en només una API que tingui prou dades integrades, com podria ser l'Overpass API.
- **Qualitat > Quantitat**: La solució no té com a requeriment obligatori cobrir totes les àrees que proposem. A vegades val més la pena centrar-se en una única àrea i fer-la molt bé (amb una justificació excel·lent), que intentar cobrir-ho tot de manera superficial.

## 6. La Prova Final: El Client Secret (Bonus)

Durant les presentacions finals, us revelarem un setè client secret sorpresa perquè proveu la vostra eina en directe.

- **L'Objectiu**: Volem veure com el vostre prototip reacciona davant d'un input nou i inesperat.
- **Punts Extra**: Aquesta demostració servirà per guanyar punts extra, però no és un requisit obligatori per guanyar la competició.
- **Gestió de dades**: Som conscients que potser la vostra eina s'ha especialitzat en una àrea concreta (ex: soroll) i el client secret demana una altra cosa (ex: parcs). No us preocupeu! Els jutges valoraran la robustesa de l'eina i com gestioneu la situació, encara que no tingueu totes les dades per satisfer-lo al 100%.

## 7. Què heu d'entregar?

Al final de la hackathon, cada equip ha de presentar:

1. Un repositori de codi públic (p. ex., GitHub, GitLab).
2. Un prototip o aplicació funcional accessible per als jutges.
3. Una presentació final (màx. 5 minuts) on demostrareu la solució i com funciona amb el "Client Secret".

Bona sort, i que el millor equip guanyi el tron!
