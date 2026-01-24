"""Trading Jokes Service - SQLite-basierte Witz-Verwaltung.

Provides random trading jokes for splash screens and waiting screens.
"""

from __future__ import annotations

import logging
import random
import sqlite3
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class TradingJokesService:
    """Service für Trading-Witze aus SQLite-Datenbank."""

    _instance: Optional[TradingJokesService] = None
    _db_path: Path
    _initialized: bool = False

    def __new__(cls) -> TradingJokesService:
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the jokes service."""
        if self._initialized:
            return

        # Database path: data/trading_jokes.db
        project_root = Path(__file__).parent.parent.parent.parent
        self._db_path = project_root / "data" / "trading_jokes.db"
        self._ensure_database()
        self._initialized = True

    def _ensure_database(self) -> None:
        """Ensure database exists and is populated."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()

        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jokes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                joke_de TEXT NOT NULL,
                joke_en TEXT,
                category TEXT DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Check if jokes exist
        cursor.execute("SELECT COUNT(*) FROM jokes")
        count = cursor.fetchone()[0]

        if count == 0:
            logger.info("Populating trading jokes database...")
            self._populate_jokes(cursor)
            conn.commit()
            logger.info(f"Added {self._get_joke_count(cursor)} trading jokes to database")
        elif count < 200:
            # Add Gemini-style jokes if not yet added (migration)
            logger.info("Adding Gemini-style loading jokes...")
            self._add_gemini_jokes(cursor)
            conn.commit()
            logger.info(f"Database now has {self._get_joke_count(cursor)} jokes")

        conn.close()

    def _get_joke_count(self, cursor: sqlite3.Cursor) -> int:
        """Get total joke count."""
        cursor.execute("SELECT COUNT(*) FROM jokes")
        return cursor.fetchone()[0]

    def _populate_jokes(self, cursor: sqlite3.Cursor) -> None:
        """Populate database with 100 trading jokes."""
        jokes = [
            # Allgemeine Trading-Witze
            ("Warum sind Trader so schlecht im Verstecken spielen? Weil sie immer ihre Positionen zeigen!", "Why are traders bad at hide and seek? Because they always show their positions!", "general"),
            ("Was ist der Unterschied zwischen einem Trader und einem Pizzaboten? Der Pizzabote weiß, wo er morgen arbeitet.", "What's the difference between a trader and a pizza delivery guy? The pizza guy knows where he'll work tomorrow.", "general"),
            ("Mein Portfolio ist wie mein Dating-Leben: Viele rote Flaggen, aber ich halte trotzdem.", "My portfolio is like my dating life: Lots of red flags, but I'm still holding.", "general"),
            ("Warum trinken Trader so viel Kaffee? Weil der Markt nie schläft und sie auch nicht!", "Why do traders drink so much coffee? Because the market never sleeps and neither do they!", "general"),
            ("Was sagt ein Trader zu seinem Portfolio? 'Du hast mich enttäuscht, aber ich glaube immer noch an dich.'", "What does a trader say to his portfolio? 'You disappointed me, but I still believe in you.'", "general"),

            # Bullen und Bären
            ("Treffen sich ein Bulle und ein Bär... Der Rest ist Geschichte – wortwörtlich.", "A bull and a bear walk into a bar... The rest is history – literally.", "animals"),
            ("Warum mögen Bären keine Bullen? Weil sie immer so aufgeblasen sind!", "Why don't bears like bulls? Because they're always so inflated!", "animals"),
            ("Was ist der Lieblingssport eines Bullen? Hochsprung – er will immer höher!", "What's a bull's favorite sport? High jump – he always wants to go higher!", "animals"),
            ("Ein Bär geht in eine Bar und bestellt einen Short. Der Barkeeper fragt: 'Whiskey?' – 'Nein, Tesla!'", "A bear walks into a bar and orders a short. Bartender asks: 'Whiskey?' – 'No, Tesla!'", "animals"),
            ("Warum sind Bären so pessimistisch? Weil sie immer nach unten schauen!", "Why are bears so pessimistic? Because they always look down!", "animals"),

            # Krypto-Witze
            ("Warum hat der Bitcoin-Investor keinen Regenschirm? Weil er an HODL glaubt!", "Why doesn't the Bitcoin investor have an umbrella? Because he believes in HODL!", "crypto"),
            ("Was ist der Unterschied zwischen einem Krypto-Investor und einem Casino-Spieler? Der Casino-Spieler bekommt wenigstens Gratisgetränke.", "What's the difference between a crypto investor and a gambler? The gambler at least gets free drinks.", "crypto"),
            ("Mein Krypto-Portfolio hat mehr Volatilität als meine Beziehungen.", "My crypto portfolio has more volatility than my relationships.", "crypto"),
            ("Warum sind Krypto-Trader so fit? Weil sie ständig zwischen Mond und Boden hin und her rennen!", "Why are crypto traders so fit? Because they're constantly running between moon and floor!", "crypto"),
            ("Was sagt ein Krypto-Hodler beim Zahnarzt? 'HODL! Ich verkaufe nicht, auch wenn es wehtut!'", "What does a crypto hodler say at the dentist? 'HODL! I'm not selling, even if it hurts!'", "crypto"),

            # Verlust-Witze
            ("Ich habe meinen Verlust nicht realisiert. Also existiert er nicht, oder?", "I haven't realized my loss. So it doesn't exist, right?", "losses"),
            ("Mein Portfolio ist jetzt eine Langzeit-Investition. Nicht freiwillig.", "My portfolio is now a long-term investment. Not voluntarily.", "losses"),
            ("Was ist rot und fällt? Mein Portfolio. Jeden. Einzelnen. Tag.", "What's red and falling? My portfolio. Every. Single. Day.", "losses"),
            ("Ich trade nicht mit Geld, das ich mir nicht leisten kann zu verlieren. Ich trade mit Geld, das ich bereits verloren habe.", "I don't trade with money I can't afford to lose. I trade with money I've already lost.", "losses"),
            ("Meine Strategie? Buy high, sell low, repeat until broke.", "My strategy? Buy high, sell low, repeat until broke.", "losses"),

            # Technische Analyse
            ("Technische Analyse ist wie Astrologie, nur mit mehr Linien.", "Technical analysis is like astrology, just with more lines.", "ta"),
            ("Warum lieben Trader Dreiecke? Weil sie hoffen, dass die Spitze nach oben zeigt!", "Why do traders love triangles? Because they hope the tip points up!", "ta"),
            ("Meine Trendlinie sieht aus wie ein EKG während eines Herzinfarkts.", "My trendline looks like an ECG during a heart attack.", "ta"),
            ("Support und Resistance? Mehr wie Hoffnung und Verzweiflung.", "Support and resistance? More like hope and despair.", "ta"),
            ("Warum brauchen Trader einen Bleistift? Um Linien zu zeichnen, die der Markt ignoriert.", "Why do traders need a pencil? To draw lines that the market ignores.", "ta"),

            # Daytrading
            ("Daytrading: Die Kunst, 8 Stunden zu arbeiten, um 50€ zu verdienen oder 5000€ zu verlieren.", "Day trading: The art of working 8 hours to make €50 or lose €5000.", "daytrading"),
            ("Was ist der Unterschied zwischen Daytrading und Glücksspiel? Beim Glücksspiel gibt's Gratisgetränke.", "What's the difference between day trading and gambling? Gambling comes with free drinks.", "daytrading"),
            ("Mein Daytrading-Tagebuch: 'Heute wieder emotional gehandelt. Ergebnis: Wie erwartet.'", "My day trading journal: 'Traded emotionally again today. Result: As expected.'", "daytrading"),
            ("Daytrader-Morgenmotto: 'Heute wird alles anders!' Abends: 'Morgen wird alles anders!'", "Day trader's morning motto: 'Today will be different!' Evening: 'Tomorrow will be different!'", "daytrading"),
            ("Warum stehen Daytrader früh auf? Um pünktlich Geld zu verlieren!", "Why do day traders wake up early? To lose money on time!", "daytrading"),

            # FOMO und Emotionen
            ("FOMO: Fear Of Missing Out. Auch bekannt als: 'Warum bin ich eingestiegen?!'", "FOMO: Fear Of Missing Out. Also known as: 'Why did I get in?!'", "emotions"),
            ("Mein Trading-Plan: Kaufen wenn Panik, Verkaufen wenn Gier. Umsetzung: Genau umgekehrt.", "My trading plan: Buy when panic, sell when greed. Execution: Exact opposite.", "emotions"),
            ("Gier ist gut, sagten sie. Mein Kontostand sagt was anderes.", "Greed is good, they said. My account balance says otherwise.", "emotions"),
            ("Emotionsloses Trading? Existiert nicht. Ich nenne es 'kontrolliertes Weinen'.", "Emotionless trading? Doesn't exist. I call it 'controlled crying'.", "emotions"),
            ("Der Markt kann länger irrational bleiben als ich solvent.", "The market can stay irrational longer than I can stay solvent.", "emotions"),

            # Broker und Gebühren
            ("Mein Broker verdient mehr an mir als ich an mir.", "My broker makes more money from me than I do.", "broker"),
            ("Spread? Mehr wie 'Spread my money across their pockets'.", "Spread? More like 'Spread my money across their pockets'.", "broker"),
            ("Warum lächelt mein Broker immer? Weil er an meinen Verlusten verdient.", "Why does my broker always smile? Because he profits from my losses.", "broker"),
            ("Kommissionsfreies Trading? Die Kommission ist nur woanders versteckt.", "Commission-free trading? The commission is just hidden somewhere else.", "broker"),
            ("Mein Broker hat mir geschrieben: 'Danke für Ihren Beitrag zu unserem Jahresbonus.'", "My broker wrote me: 'Thanks for your contribution to our annual bonus.'", "broker"),

            # Hebel und Risiko
            ("Hebel 100x? Das ist keine Strategie, das ist ein Hilferuf.", "100x leverage? That's not a strategy, that's a cry for help.", "leverage"),
            ("Mit Hebel handeln ist wie mit dem Feuer spielen. Nur dass das Feuer auch dein Geld verbrennt.", "Trading with leverage is like playing with fire. Except the fire also burns your money.", "leverage"),
            ("Mein Risikomanagement: Ich riskiere alles, was ich nicht haben sollte.", "My risk management: I risk everything I shouldn't have.", "leverage"),
            ("Stop-Loss? Ich lebe gefährlich.", "Stop-loss? I like to live dangerously.", "leverage"),
            ("Margin Call ist nur eine andere Art zu sagen: 'Du hast verkackt.'", "Margin call is just another way of saying: 'You messed up.'", "leverage"),

            # Aktien und Investments
            ("Warum heißen sie Aktien? Weil man aktiv daran arbeitet, sie zu verlieren.", "Why are they called stocks? Because you actively work on losing them.", "stocks"),
            ("Ich habe in ein Unternehmen investiert, das Fallschirme herstellt. Es geht nur abwärts.", "I invested in a company that makes parachutes. It's only going down.", "stocks"),
            ("Meine Blue-Chip-Aktien sind jetzt Potato-Chips.", "My blue-chip stocks are now potato chips.", "stocks"),
            ("Diversifikation bedeutet, auf verschiedene Arten Geld zu verlieren.", "Diversification means losing money in different ways.", "stocks"),
            ("Ich kaufe Aktien wie Lebensmittel: Immer das Verfallsdatum ignorieren.", "I buy stocks like groceries: Always ignoring the expiration date.", "stocks"),

            # Analysten und Experten
            ("Analysten: Leute, die erklären, warum sie falsch lagen.", "Analysts: People who explain why they were wrong.", "analysts"),
            ("'Experten sagen...' – Die drei gefährlichsten Wörter im Trading.", "'Experts say...' – The three most dangerous words in trading.", "analysts"),
            ("Warum haben Analysten immer zwei Meinungen? Damit eine davon stimmt.", "Why do analysts always have two opinions? So one of them is right.", "analysts"),
            ("Finanzberater: Jemand, der dein Geld investiert, bis es weg ist.", "Financial advisor: Someone who invests your money until it's gone.", "analysts"),
            ("'Laut meiner Analyse...' – Übersetzung: 'Ich rate nur.'", "'According to my analysis...' – Translation: 'I'm just guessing.'", "analysts"),

            # Markt-Timing
            ("Den Markt timen? Ich kann nicht mal meine Mikrowelle timen.", "Timing the market? I can't even time my microwave.", "timing"),
            ("Ich kaufe immer am Höchststand. Es ist ein Talent.", "I always buy at the top. It's a talent.", "timing"),
            ("'Time in the market beats timing the market.' – Mein Kontostand widerspricht.", "'Time in the market beats timing the market.' – My account balance disagrees.", "timing"),
            ("Perfektes Timing: Verkaufen kurz bevor es steigt, kaufen kurz bevor es fällt.", "Perfect timing: Selling right before it goes up, buying right before it goes down.", "timing"),
            ("Warum ist Market Timing so schwer? Weil der Markt meine Pläne kennt.", "Why is market timing so hard? Because the market knows my plans.", "timing"),

            # Geduld und HODL
            ("HODL: Hold On for Dear Life. Auch bekannt als: 'Ich kann nicht verkaufen, weil ich im Minus bin.'", "HODL: Hold On for Dear Life. Also known as: 'I can't sell because I'm in the red.'", "hodl"),
            ("Geduld ist eine Tugend. Außer beim Trading, da ist es Folter.", "Patience is a virtue. Except in trading, there it's torture.", "hodl"),
            ("Diamond Hands? Mehr wie 'zu faul zum Verkaufen'.", "Diamond hands? More like 'too lazy to sell'.", "hodl"),
            ("Langfristig investieren heißt: Zu stolz, den Verlust zu realisieren.", "Long-term investing means: Too proud to realize the loss.", "hodl"),
            ("Ich halte diese Aktie seit 5 Jahren. Nicht weil ich an sie glaube, sondern weil sie 90% im Minus ist.", "I've held this stock for 5 years. Not because I believe in it, but because it's down 90%.", "hodl"),

            # Charts und Muster
            ("Ich sehe überall Kopf-Schulter-Formationen. Auch in meinem Shampoo.", "I see head-and-shoulders patterns everywhere. Even in my shampoo.", "patterns"),
            ("Cup and Handle? Das einzige, was ich heute handle, ist meine Kaffeetasse.", "Cup and Handle? The only thing I'm handling today is my coffee cup.", "patterns"),
            ("Double Bottom: Wenn du zweimal am Boden aufschlägst.", "Double bottom: When you hit rock bottom twice.", "patterns"),
            ("Meine Charts sehen aus wie abstrakte Kunst. Teuer und unverständlich.", "My charts look like abstract art. Expensive and incomprehensible.", "patterns"),
            ("Kerzen lesen? Ich kann kaum meine Kontoauszüge lesen.", "Reading candles? I can barely read my bank statements.", "patterns"),

            # Trades und Entscheidungen
            ("Jeder Trade ist eine Gelegenheit zu lernen. Ich lerne viel.", "Every trade is an opportunity to learn. I'm learning a lot.", "trades"),
            ("Meine beste Trade-Entscheidung? Den Computer auszuschalten.", "My best trading decision? Turning off the computer.", "trades"),
            ("Revenge Trading: Weil der erste Fehler nicht genug war.", "Revenge trading: Because the first mistake wasn't enough.", "trades"),
            ("Ich trade nach Gefühl. Das Gefühl ist meistens Panik.", "I trade by feeling. The feeling is usually panic.", "trades"),
            ("Ein guter Trade ist wie ein Einhorn: Jeder redet davon, aber niemand sieht eins.", "A good trade is like a unicorn: Everyone talks about it, but nobody sees one.", "trades"),

            # Geld und Reichtum
            ("Reich werden mit Trading? Ja, wenn du vorher sehr reich warst.", "Getting rich from trading? Yes, if you were very rich before.", "money"),
            ("Mein Vermögen wächst exponentiell. Exponentiell negativ.", "My wealth is growing exponentially. Exponentially negative.", "money"),
            ("Financial Freedom? Mehr wie Financial Prison.", "Financial freedom? More like financial prison.", "money"),
            ("Das einzige, was bei mir steigt, sind meine Schulden.", "The only thing going up for me is my debt.", "money"),
            ("Ich habe eine Million gemacht! Aus zwei Millionen.", "I made a million! Out of two million.", "money"),

            # Bildung und Lernen
            ("YouTube-Trading-Gurus: Verdienen mehr mit Kursen als mit Trading.", "YouTube trading gurus: Make more from courses than from trading.", "education"),
            ("'Dieser Kurs macht dich zum Profi!' – 3 Monate später: Immer noch Amateur.", "'This course will make you a pro!' – 3 months later: Still an amateur.", "education"),
            ("Paper Trading: Der einzige Ort, wo ich profitabel bin.", "Paper trading: The only place where I'm profitable.", "education"),
            ("Backtesting funktioniert perfekt. Live-Trading? Nicht so sehr.", "Backtesting works perfectly. Live trading? Not so much.", "education"),
            ("Ich habe 100 Bücher über Trading gelesen. Mein Konto weiß es nicht.", "I've read 100 books about trading. My account doesn't know it.", "education"),

            # Psychologie
            ("Trading-Psychologie: Die Kunst, nicht zu weinen.", "Trading psychology: The art of not crying.", "psychology"),
            ("Mein Trading-Tagebuch: 'Heute habe ich emotional gehandelt. Wie jeden Tag.'", "My trading journal: 'Traded emotionally today. Like every day.'", "psychology"),
            ("Disziplin im Trading? Ich habe Disziplin beim Ignorieren meiner Stop-Losses.", "Discipline in trading? I have discipline in ignoring my stop-losses.", "psychology"),
            ("Meditation hilft beim Trading. Es bereitet auf den Verlust vor.", "Meditation helps with trading. It prepares you for the loss.", "psychology"),
            ("Meine Trading-Routine: Aufstehen, Chart anschauen, weinen, schlafen.", "My trading routine: Wake up, look at chart, cry, sleep.", "psychology"),

            # News und Events
            ("'Buy the rumor, sell the news.' – Ich kaufe die News und verkaufe das Rumor.", "'Buy the rumor, sell the news.' – I buy the news and sell the rumor.", "news"),
            ("Fed-Entscheidung: Der Tag, an dem alle falsch liegen.", "Fed decision: The day everyone gets it wrong.", "news"),
            ("Earnings Season: Die Zeit, in der Überraschungen nicht überraschend sind.", "Earnings season: The time when surprises aren't surprising.", "news"),
            ("Breaking News: Mein Portfolio ist auch gebrochen.", "Breaking news: My portfolio is also broken.", "news"),
            ("Warum lese ich Finanznachrichten? Um zu wissen, warum ich Geld verloren habe.", "Why do I read financial news? To know why I lost money.", "news"),

            # Verschiedene
            ("Der Markt ist wie meine Katze: Unberechenbar und manchmal gemein.", "The market is like my cat: Unpredictable and sometimes mean.", "misc"),
            ("Meine Frau versteht mein Trading nicht. Ich auch nicht.", "My wife doesn't understand my trading. Neither do I.", "misc"),
            ("Trading-Sucht? Nein, ich kann jederzeit aufhören. Nach diesem einen Trade.", "Trading addiction? No, I can quit anytime. After this one trade.", "misc"),
            ("Warum heißt es 'Börse'? Weil es meine Börse leert.", "Why is it called stock exchange? Because it exchanges my money for nothing.", "misc"),
            ("Mein Finanzplan für die Rente: Lottoscheine.", "My financial plan for retirement: Lottery tickets.", "misc"),

            # Mehr Klassiker
            ("Ein Trader, ein Investor und ein Hodler gehen in eine Bar. Nur der Barkeeper verdient.", "A trader, an investor, and a hodler walk into a bar. Only the bartender profits.", "classic"),
            ("Was haben Trader und Meteorologen gemeinsam? Beide liegen oft falsch und werden trotzdem bezahlt.", "What do traders and meteorologists have in common? Both are often wrong and still get paid.", "classic"),
            ("Ich habe meinem Broker gesagt, ich will reich werden. Er lachte. Ich lachte. Das Konto weinte.", "I told my broker I want to get rich. He laughed. I laughed. The account cried.", "classic"),
            ("Meine Investmentstrategie: Panik kaufen, Panik verkaufen, Panik wiederholen.", "My investment strategy: Panic buy, panic sell, panic repeat.", "classic"),
            ("Der beste Zeitpunkt zum Investieren war vor 20 Jahren. Der zweitbeste? Aufhören zu fragen und einfach Geld zu verlieren wie alle anderen.", "The best time to invest was 20 years ago. The second best? Stop asking and just lose money like everyone else.", "classic"),
        ]

        cursor.executemany(
            "INSERT INTO jokes (joke_de, joke_en, category) VALUES (?, ?, ?)",
            jokes
        )

    def _add_gemini_jokes(self, cursor: sqlite3.Cursor) -> None:
        """Add Gemini CLI-style loading jokes to the database."""
        gemini_jokes = [
            # Gemini CLI Witty Loading Phrases (translated and adapted)
            ("Ich hab' ein gutes Gefühl bei diesem Trade!", "I'm Feeling Lucky", "loading"),
            ("Liefere Genialität aus...", "Shipping awesomeness…", "loading"),
            ("Male die Serifen wieder an...", "Painting the serifs back on…", "loading"),
            ("Navigiere durch den Schleimpilz...", "Navigating the slime mold…", "loading"),
            ("Befrage die digitalen Geister...", "Consulting the digital spirits…", "loading"),
            ("Berechne Splines neu...", "Reticulating splines…", "loading"),
            ("Wärme die KI-Hamster auf...", "Warming up the AI hamsters…", "loading"),
            ("Frage die magische Muschel...", "Asking the magic conch shell…", "loading"),
            ("Generiere witzige Antwort...", "Generating witty retort…", "loading"),
            ("Poliere die Algorithmen...", "Polishing the algorithms…", "loading"),
            ("Perfektion braucht Zeit (und mein Code auch)...", "Don't rush perfection (or my code)…", "loading"),
            ("Braue frische Bytes...", "Brewing fresh bytes…", "loading"),
            ("Zähle Elektronen...", "Counting electrons…", "loading"),
            ("Aktiviere kognitive Prozessoren...", "Engaging cognitive processors…", "loading"),
            ("Prüfe auf Syntaxfehler im Universum...", "Checking for syntax errors in the universe…", "loading"),
            ("Einen Moment, optimiere Humor...", "One moment, optimizing humor…", "loading"),
            ("Mische Pointen...", "Shuffling punchlines…", "loading"),
            ("Entwirre neuronale Netze...", "Untangling neural nets…", "loading"),
            ("Kompiliere Brillanz...", "Compiling brilliance…", "loading"),
            ("Lade wit.exe...", "Loading wit.exe…", "loading"),
            ("Beschwöre die Wolke der Weisheit...", "Summoning the cloud of wisdom…", "loading"),
            ("Bereite eine witzige Antwort vor...", "Preparing a witty response…", "loading"),
            ("Kurz mal, ich debugge die Realität...", "Just a sec, I'm debugging reality…", "loading"),
            ("Verwirre die Optionen...", "Confuzzling the options…", "loading"),
            ("Stimme die kosmischen Frequenzen ab...", "Tuning the cosmic frequencies…", "loading"),
            ("Erstelle eine Antwort, die deiner Geduld würdig ist...", "Crafting a response worthy of your patience…", "loading"),
            ("Kompiliere die Einsen und Nullen...", "Compiling the 1s and 0s…", "loading"),
            ("Löse Abhängigkeiten... und existenzielle Krisen...", "Resolving dependencies… and existential crises…", "loading"),
            ("Defragmentiere Erinnerungen... RAM und persönliche...", "Defragmenting memories… both RAM and personal…", "loading"),
            ("Starte das Humor-Modul neu...", "Rebooting the humor module…", "loading"),
            ("Cache die Essentials (meistens Katzen-Memes)...", "Caching the essentials (mostly cat memes)…", "loading"),
            ("Optimiere für absurde Geschwindigkeit...", "Optimizing for ludicrous speed", "loading"),
            ("Tausche Bits... sag's nicht den Bytes...", "Swapping bits… don't tell the bytes…", "loading"),
            ("Garbage Collection... bin gleich zurück...", "Garbage collecting… be right back…", "loading"),
            ("Baue das Internet zusammen...", "Assembling the interwebs…", "loading"),
            ("Wandle Kaffee in Code um...", "Converting coffee into code…", "loading"),
            ("Update die Syntax für die Realität...", "Updating the syntax for reality…", "loading"),
            ("Verdrahte die Synapsen neu...", "Rewiring the synapses…", "loading"),
            ("Suche nach einem verlorenen Semikolon...", "Looking for a misplaced semicolon…", "loading"),
            ("Öle die Zahnräder der Maschine...", "Greasin' the cogs of the machine…", "loading"),
            ("Heize die Server vor...", "Pre-heating the servers…", "loading"),
            ("Kalibriere den Flux-Kompensator...", "Calibrating the flux capacitor…", "loading"),
            ("Aktiviere den Unwahrscheinlichkeitsantrieb...", "Engaging the improbability drive…", "loading"),
            ("Kanalisiere die Macht...", "Channeling the Force…", "loading"),
            ("Richte die Sterne für optimale Antwort aus...", "Aligning the stars for optimal response…", "loading"),
            ("So sei es...", "So say we all…", "loading"),
            ("Lade die nächste große Idee...", "Loading the next great idea…", "loading"),
            ("Einen Moment, ich bin in der Zone...", "Just a moment, I'm in the zone…", "loading"),
            ("Bereite mich vor, dich mit Brillanz zu blenden...", "Preparing to dazzle you with brilliance…", "loading"),
            ("Kurz, ich poliere meinen Witz...", "Just a tick, I'm polishing my wit…", "loading"),
            ("Halt dich fest, ich erschaffe ein Meisterwerk...", "Hold tight, I'm crafting a masterpiece…", "loading"),
            ("Gleich, ich debugge das Universum...", "Just a jiffy, I'm debugging the universe…", "loading"),
            ("Moment, ich richte die Pixel aus...", "Just a moment, I'm aligning the pixels…", "loading"),
            ("Sekunde, ich optimiere den Humor...", "Just a sec, I'm optimizing the humor…", "loading"),
            ("Moment, ich stimme die Algorithmen...", "Just a moment, I'm tuning the algorithms…", "loading"),
            ("Warp-Geschwindigkeit aktiviert...", "Warp speed engaged…", "loading"),
            ("Schürfe nach mehr Dilithium-Kristallen...", "Mining for more Dilithium crystals…", "loading"),
            ("Keine Panik...", "Don't panic…", "loading"),
            ("Folge dem weißen Kaninchen...", "Following the white rabbit…", "loading"),
            ("Die Wahrheit ist hier drin... irgendwo...", "The truth is in here… somewhere…", "loading"),
            ("Puste auf das Modul...", "Blowing on the cartridge…", "loading"),
            ("Lade... Mach eine Rolle!", "Loading… Do a barrel roll!", "loading"),
            ("Warte auf den Respawn...", "Waiting for the respawn…", "loading"),
            ("Beende den Kessel-Run in unter 12 Parsecs...", "Finishing the Kessel Run in less than 12 parsecs…", "loading"),
            ("Der Kuchen ist keine Lüge, er lädt noch...", "The cake is not a lie, it's just still loading…", "loading"),
            ("Spiele am Charakter-Erstellungsbildschirm...", "Fiddling with the character creation screen…", "loading"),
            ("Moment, ich finde das richtige Meme...", "Just a moment, I'm finding the right meme…", "loading"),
            ("Drücke 'A' zum Fortfahren...", "Pressing 'A' to continue…", "loading"),
            ("Hüte digitale Katzen...", "Herding digital cats…", "loading"),
            ("Poliere die Pixel...", "Polishing the pixels…", "loading"),
            ("Finde einen passenden Ladebildschirm-Witz...", "Finding a suitable loading screen pun…", "loading"),
            ("Lenke dich mit diesem witzigen Spruch ab...", "Distracting you with this witty phrase…", "loading"),
            ("Fast da... wahrscheinlich...", "Almost there… probably…", "loading"),
            ("Unsere Hamster arbeiten so schnell sie können...", "Our hamsters are working as fast as they can…", "loading"),
            ("Streichle die Katze...", "Petting the cat…", "loading"),
            ("Rickrolle meinen Chef...", "Rickrolling my boss…", "loading"),
            ("Klatsche den Bass...", "Slapping the bass…", "loading"),
            ("Probiere die Schnozzbeeren...", "Tasting the snozberries…", "loading"),
            ("Ich gehe die Distanz, ich gehe auf Speed...", "I'm going the distance, I'm going for speed…", "loading"),
            ("Ist das das echte Leben? Ist das nur Fantasie?...", "Is this the real life? Is this just fantasy?…", "loading"),
            ("Ich hab' ein gutes Gefühl dabei...", "I've got a good feeling about this…", "loading"),
            ("Stochere den Bären...", "Poking the bear…", "loading"),
            ("Recherchiere die neuesten Memes...", "Doing research on the latest memes…", "loading"),
            ("Überlege, wie ich das witziger machen kann...", "Figuring out how to make this more witty…", "loading"),
            ("Hmmm... lass mich nachdenken...", "Hmmm… let me think…", "loading"),
            ("Was nennt man einen Fisch ohne Augen? Einen Fsch...", "What do you call a fish with no eyes? A fsh…", "loading"),
            ("Warum ging der Computer zur Therapie? Zu viele Bytes...", "Why did the computer go to therapy? It had too many bytes…", "loading"),
            ("Warum mögen Programmierer keine Natur? Zu viele Bugs...", "Why don't programmers like nature? It has too many bugs…", "loading"),
            ("Warum bevorzugen Programmierer Dark Mode? Licht zieht Bugs an...", "Why do programmers prefer dark mode? Because light attracts bugs…", "loading"),
            ("Warum ging der Entwickler pleite? Er hat seinen Cache aufgebraucht...", "Why did the developer go broke? Because they used up all their cache…", "loading"),
            ("Was kann man mit einem kaputten Bleistift machen? Nichts, er ist sinnlos...", "What can you do with a broken pencil? Nothing, it's pointless…", "loading"),
            ("Wende perkussive Wartung an...", "Applying percussive maintenance…", "loading"),
            ("Suche die richtige USB-Orientierung...", "Searching for the correct USB orientation…", "loading"),
            ("Stelle sicher, dass der magische Rauch in den Drähten bleibt...", "Ensuring the magic smoke stays inside the wires…", "loading"),
            ("Schreibe in Rust um ohne besonderen Grund...", "Rewriting in Rust for no particular reason…", "loading"),
            ("Versuche Vim zu beenden...", "Trying to exit Vim…", "loading"),
            ("Drehe das Hamsterrad an...", "Spinning up the hamster wheel…", "loading"),
            ("Das ist kein Bug, das ist ein undokumentiertes Feature...", "That's not a bug, it's an undocumented feature…", "loading"),
            ("Engage.", "Engage.", "loading"),
            ("Ich komme wieder... mit einer Antwort.", "I'll be back… with an answer.", "loading"),
            ("Mein anderer Prozess ist eine TARDIS...", "My other process is a TARDIS…", "loading"),
            ("Kommuniziere mit dem Maschinengeist...", "Communing with the machine spirit…", "loading"),
            ("Lass die Gedanken marinieren...", "Letting the thoughts marinate…", "loading"),
            ("Hab' grad erinnert wo ich meine Schlüssel hingelegt hab...", "Just remembered where I put my keys…", "loading"),
            ("Betrachte den Orb...", "Pondering the orb…", "loading"),
            ("Ich habe Dinge gesehen, die ihr nicht glauben würdet... wie einen User, der Lademeldungen liest.", "I've seen things you people wouldn't believe… like a user who reads loading messages.", "loading"),
            ("Initiiere nachdenklichen Blick...", "Initiating thoughtful gaze…", "loading"),
            ("Was ist der Lieblingssnack eines Computers? Microchips.", "What's a computer's favorite snack? Microchips.", "loading"),
            ("Warum tragen Java-Entwickler Brillen? Weil sie nicht C#.", "Why do Java developers wear glasses? Because they don't C#.", "loading"),
            ("Lade den Laser... pew pew!", "Charging the laser… pew pew!", "loading"),
            ("Dividiere durch Null... nur Spaß!", "Dividing by zero… just kidding!", "loading"),
            ("Suche nach einem erwachsenen Aufpasser... ich meine, verarbeite.", "Looking for an adult superviso… I mean, processing.", "loading"),
            ("Mach beep boop.", "Making it go beep boop.", "loading"),
            ("Buffere... weil auch KIs mal einen Moment brauchen.", "Buffering… because even AIs need a moment.", "loading"),
            ("Verschränke Quantenpartikel für schnellere Antwort...", "Entangling quantum particles for a faster response…", "loading"),
            ("Poliere das Chrom... an den Algorithmen.", "Polishing the chrome… on the algorithms.", "loading"),
            ("Bist du nicht unterhalten? (Arbeite dran!)", "Are you not entertained? (Working on it!)", "loading"),
            ("Beschwöre die Code-Gremlins... zum Helfen natürlich.", "Summoning the code gremlins… to help, of course.", "loading"),
            ("Warte nur auf das Ende des Einwahltons...", "Just waiting for the dial-up tone to finish…", "loading"),
            ("Rekalibriere das Humor-o-meter.", "Recalibrating the humor-o-meter.", "loading"),
            ("Mein anderer Ladebildschirm ist noch witziger.", "My other loading screen is even funnier.", "loading"),
            ("Ziemlich sicher, dass irgendwo eine Katze über die Tastatur läuft...", "Pretty sure there's a cat walking on the keyboard somewhere…", "loading"),
            ("Verbessere... Verbessere... Lade noch.", "Enhancing… Enhancing… Still loading.", "loading"),
            ("Es ist kein Bug, es ist ein Feature... dieses Ladebildschirms.", "It's not a bug, it's a feature… of this loading screen.", "loading"),
            ("Hast du schon versucht, es aus- und wieder anzuschalten? (Den Ladebildschirm, nicht mich.)", "Have you tried turning it off and on again? (The loading screen, not me.)", "loading"),
            ("Konstruiere zusätzliche Pylonen...", "Constructing additional pylons…", "loading"),
            ("Neue Zeile? Das ist Ctrl+J.", "New line? That's Ctrl+J.", "loading"),
            ("Entlasse die Hypno-Drohnen...", "Releasing the HypnoDrones…", "loading"),
        ]

        cursor.executemany(
            "INSERT INTO jokes (joke_de, joke_en, category) VALUES (?, ?, ?)",
            gemini_jokes
        )
        logger.info(f"Added {len(gemini_jokes)} Gemini-style jokes")

    def get_random_joke(self, language: str = "de", exclude_ids: list[int] | None = None) -> tuple[str, int]:
        """Get a random trading joke.

        Args:
            language: 'de' for German, 'en' for English
            exclude_ids: List of joke IDs to exclude (for no-repeat sessions)

        Returns:
            Tuple of (joke string, joke ID)
        """
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()

            column = "joke_de" if language == "de" else "joke_en"

            # Build query with optional exclusion
            if exclude_ids:
                placeholders = ",".join("?" * len(exclude_ids))
                query = f"SELECT id, {column} FROM jokes WHERE id NOT IN ({placeholders}) ORDER BY RANDOM() LIMIT 1"
                cursor.execute(query, exclude_ids)
            else:
                cursor.execute(f"SELECT id, {column} FROM jokes ORDER BY RANDOM() LIMIT 1")

            result = cursor.fetchone()
            conn.close()

            if result and result[1]:
                return result[1], result[0]

            # Fallback if all jokes excluded - reset and get any
            return "Warum fiel der Trader in den Brunnen? Weil er nicht auf den Boden schaute!", -1

        except Exception as e:
            logger.warning(f"Failed to get joke: {e}")
            return "Trading ist wie Fahrradfahren. Außer dass das Fahrrad brennt. Und alles brennt.", -1

    def get_random_joke_with_category(self, language: str = "de") -> tuple[str, str]:
        """Get a random trading joke with its category.

        Args:
            language: 'de' for German, 'en' for English

        Returns:
            Tuple of (joke, category)
        """
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()

            column = "joke_de" if language == "de" else "joke_en"
            cursor.execute(f"SELECT {column}, category FROM jokes ORDER BY RANDOM() LIMIT 1")
            result = cursor.fetchone()
            conn.close()

            if result and result[0]:
                return result[0], result[1]
            return "Der Markt hat immer recht. Außer wenn ich long bin.", "general"

        except Exception as e:
            logger.warning(f"Failed to get joke: {e}")
            return "Buy low, sell lower - mein Motto.", "general"

    def get_joke_count(self) -> int:
        """Get total number of jokes in database."""
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM jokes")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.warning(f"Failed to get joke count: {e}")
            return 0


# Convenience functions
def get_random_trading_joke(language: str = "de", exclude_ids: list[int] | None = None) -> tuple[str, int]:
    """Get a random trading joke (convenience function).

    Args:
        language: 'de' for German, 'en' for English
        exclude_ids: List of joke IDs to exclude (for no-repeat sessions)

    Returns:
        Tuple of (joke string, joke ID)
    """
    service = TradingJokesService()
    return service.get_random_joke(language, exclude_ids)


def get_random_trading_joke_simple(language: str = "de") -> str:
    """Get a random trading joke - simple version without ID tracking.

    Args:
        language: 'de' for German, 'en' for English

    Returns:
        Random joke string
    """
    joke, _ = get_random_trading_joke(language)
    return joke
