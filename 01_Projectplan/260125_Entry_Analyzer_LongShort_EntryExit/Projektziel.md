› In der Anwendung gibt es den 'Entry Analyzer' und wiederrum gibt es da die ersten vier Tabs die dazu da sind, die
  Regimes im aktuellen chart zu bestimmen. Ablauf Tab regime:
  0. 'json V2' laden in der die indikatoren... angegeben sind, siehe z.b.
  "03_JSON\Entry_Analyzer\Regime\260125075545_regime_optimization_results_BTCUSDT_5m_#1.json" mitteld des Buttons:
  'Load Regime Config' (wird in eine Tabelle geladen)
  0.1 Analyse starten durch den Button 'Analyse Visible Range' -> Funktion verwendet 200bars zum warmup, ohne regimes
  ein zu zeichnen und ab da werden regimes detektiert und letzendlich als vertikale linien, mit der beschriftung
  welches regime es ist, in den chart gezeichnet. Damit wären die nötigen dinge schon getan.
  Wenn ich aber nun das geladene Indikatoren settin optimieren und backtesten möchte, dann gehe ich auf:
  1. Regime Setup
  1.1 Button 'Import Config (JSON)' und lade die Datei die ich schon im Tab Regime geladen habe
  1.2 Die Daten werden dann in drei Bereiche und drei Tabellen geladen a. Current Regime Indicators (zur Info welche
  Indikatoren verwendet werden) b. Indicator Parameter Optimization Ranges in der ich für jeden Parameter der
  Indikatoren aus a, einen min und max wert, sowie einen step wert angeben kann (fürs Variantentesting)
  c. Regime Treshold Optimization Range - das gleiche wie in tabelle b, sondern nur für Regimes, wie BULL, Bear,
  Sideways...
  1.3. Angabe der Backtesting schleifen z.b. 150
  1.4 Button 'Apply Continue to Optimization':
  2. Tab Regime Optimization
  2.1 Button 'Start optimization' -> Nun wird das Indikatorensetup am geöffneten chart im chartmodul gestestet und zu
  schluß werden alle isse mit einem score über 50 in einer tabelle eingestellt.
  2.2 Ich wähle einen Einztrag aus, den ich mir ansehen und speichern möcht, markiere die Zeile und:
  2.3 Button 'Save & load in Regime' -> dieser button speichert das gewählte setup im 'json V2' Format ab und lässt
  dieses im Tab 0 Regime laden, wo ich dann wieder die Simulation durchspielen kann um zu sehen wie gut die Regimes
  jetzt gesetzt sind.. ENDE regime ermittelung
  
  Warum ich das alles schreibe, es gibt drei weitere Tabs im 'Entry Analyser' die überarbeitet und deren funktionen neu geschrieben werden müssen (die alten, falls vorhanden, müssen gelöscht werden, ohne Backup!).
  Die Tabs heissen 4. Indicator Setup, 5. Indicator Optimization und 6. Indicator result
  Nun ist das ziel ähnlich wie bei den Regime Tabs und der Ablauf auch, es soll im tab 4 eine json eingelesen werden können (in Select Indicators to Test), die aber nur eine Liste von Indikatoren hat .
  In dem Tab entfallen Select Indicators to test und Parameter Ranges, dafür muss eine Tabelle wie im Tab 'Regime Setup' eingefügt werden, mit der selben spaltenlogik (bis zu 10 Indikatoren Parameter einstellbar mit Range und step). Tabelle 'Indicator Parameter Optimization Ranges. Die Groupbox 'Regime Selection' muss gelöscht werden, wieder auch mit deren funktionen. 
  In der Goupbox 'Signal Types to Optimize' alle checkboxen als checked, als vorauswahl.
  Dann ins Tab 5 wechseln (Da gehört noch ein editfeld rein, mit der angabe der durchläufe)
  Dann Button 'Start optimization' und dann als Vorschlag für den Code, Ziel ist es die besten parametersets für Entry long, Entry short, Exit Long und Exit short zu finden: "\260125_Entry_Analyzer_LongShort_EntryExit\Indikatorensets" Darin ist auch ein riskmanagment system beschrieben um tp und sl zu bestimmen, das bitte auch mit einbinden evt in einem neuen tab inkl Backtesting dann mit den ermittelten Indikator sets um P&L€ zu ermitteln.
  
  
  
  Bitte erstelle einen detaillierten und umfassenden Umsetzungsplan zu diesem Projekt:
  "\01_Projectplan\260125_Entry_Analyzer_LongShort_EntryExit\Projektziel.md"
  Ändere keinen code und speichere den umsetzungsplan unter
  \01_Projectplan\260125_Entry_Analyzer_LongShort_EntryExit\Umsetzungsplan_Indikatorensets_Trading.md
  