"""4:28 - investigation RPG starter

Install once:  py -m pip install pygame-ce
Run:           py game.py

Controls:
  SPACE / ENTER - advance dialogue or confirm a choice
  1, 2, 3       - choose an option
  J             - open/close the evidence journal
  ESC           - return from a menu / quit

Hart will later replace the coloured scene backgrounds with images in assets/ 
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable
import sys
from pathlib import Path
import math
import json
from array import array
try:
    import cv2
except ImportError:
    cv2 = None
import pygame





@dataclass
class Evidence:
    name: str
    description: str
    source: str = "MISSING FRIEND"


@dataclass
class Player:
    name: str = "Investigator"
    character: str = "Silhouette A"
    # "composure" is the code name for the player's Lakas ng Loob.
    # Keeping the English variable name is normal in code; the player only sees Filipino.
    composure: int = 100
    time_minutes: int = 0  # minutes after 4:28 PM
    evidence: list[Evidence] = field(default_factory=list)

    def change_composure(self, amount: int) -> None:
        self.composure = max(0, min(100, self.composure + amount))

    def spend_time(self, minutes: int) -> None:
        self.time_minutes = min(720, self.time_minutes + minutes)

    def add_evidence(self, name: str, description: str, source: str = "MISSING FRIEND") -> bool:
        if any(item.name == name for item in self.evidence):
            return False
        self.evidence.append(Evidence(name, description, source))
        return True


@dataclass
class Choice:
    label: str
    result: str
    next_state: str
    correct: bool 
    composure_change: int = 0
    time_cost: int = 15
    evidence: Evidence | None = None


@dataclass
class Puzzle:
    """A short investigation challenge shown before the travel decision."""
    title: str
    prompt: str
    options: list[str]
    correct_index: int
    success: str
    evidence: Evidence
    failure: str = "That does not fit the evidence. Look again."


@dataclass
class Location:
    key: str
    title: str
    color: tuple[int, int, int]
    dialogue: list[tuple[str, str]]
    choices: list[Choice]


# ---------------------------------------------------------------------------
# Utility drawing functions.  font.render() cannot wrap paragraphs by itself.


def wrap_text(font: pygame.font.Font, text: str, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        line = ""
        for word in words:
            proposal = f"{line} {word}".strip()
            if font.size(proposal)[0] <= width:
                line = proposal
            else:
                if line:
                    lines.append(line)
                line = word
        lines.append(line or "")
    return lines


def clock_text(minutes: int) -> str:
    total = (16 * 60 + 28 + minutes) % (24 * 60)
    hour, minute = divmod(total, 60)
    suffix = "AM" if hour < 12 else "PM"
    shown_hour = hour % 12 or 12
    return f"{shown_hour}:{minute:02d} {suffix}"


def make_font(names: list[str], size: int, bold: bool = False) -> pygame.font.Font:
    for name in names:
        path = pygame.font.match_font(name, bold=bold)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.SysFont(None, size, bold=bold)


class InvestigationGame:
    WIDTH, HEIGHT = 960, 720
    BLACK = (6, 7, 10)
    INK = (12, 16, 24)
    PANEL = (15, 20, 31)
    PAPER = (242, 244, 247)
    RED = (235, 76, 81)
    GOLD = (244, 199, 103)
    MUTED = (148, 176, 194)


    def __init__(self) -> None:
        
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.init()
        pygame.mixer.set_num_channels(32)
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("4:28 - An Investigation RPG")
        self.clock = pygame.time.Clock()
        self.body_fonts = ["centurygothic", "calibri", "segoeui", "sans-serif"]
        self.ui_fonts = ["trebuchetms", "segoeui", "arial", "sans-serif"]
        self.title_fonts = ["perpetua", "garamond", "georgia", "serif"]
        self.font = make_font(self.body_fonts, 22)
        self.small_font = make_font(self.ui_fonts, 17)
        self.title_font = make_font(self.title_fonts, 50, bold=True)
        self.text_size = 22
        # Sample names/traits only: editing these does not change the story rules.
        self.characters = [
            ('Mateo', 'Loyal, emotional, impulsive', 'MATEO.png'),
            ('Clara', 'Analytical, proud, independent', 'CLARA.png'),
            ('Julian', 'Observant, empathetic, reserved', 'JULIAN.png'),
        ]
        self.character_index = 0
        self.character_info_pinned = False
        asset_root = Path(__file__).resolve().parent / 'assets'
        bg_root = asset_root / 'backgrounds'
        char_root = asset_root / 'characters'

        # ---- characters ----
        self.character_images = [self.load_sprite(char_root / f) for _, _, f in self.characters]
        self.back_characters = [self.load_sprite(char_root / f)
                                for f in ['MATEO_back.png', 'CLARA_back.png', 'JULIAN_back.png']]
        sprite_files = {
            'anino': 'anino.png',
            'caretaker_idle': 'caretaker_idle.png',
            'caretaker_talk': 'caretaker_talk.png',
            'clara_phone': 'clara_phone.png',
            'clara_sulat': 'clara_sulat.png',
            'julian_phone': 'julian_phone.png',
            'julian_sulat': 'julian_sulat.png',
            'lucas': 'LUCAS.png',
            'mateo_bulletin': 'MATEO_bulletin.png',
            'mateo_card': 'mateo_card.png',
            'mateo_phone': 'mateo_phone.png',
            'mateo_sulat': 'mateo_sulat.png',
            'student_one': 'student_one.png',
        }
        self.sprites = {key: self.load_sprite(char_root / name) for key, name in sprite_files.items()}

        #SELF for BACKGORUNDS
        self.character_background = self.load_background(bg_root / 'character_background.png')
        self.menu_background = self.load_background(bg_root / 'menu_background.png')
        self.settings_background = self.load_background(bg_root / 'settings_background.png')
        self.plm_hallway_background = self.load_background(bg_root / 'plm_bulletin.png')
        self.plm_hallway_two_background = self.load_background(bg_root / 'plm_hallway_two.png')
        self.backstory_background = self.load_background(bg_root / 'hallway_speaker.png')
        self.mateo_bulletin_bg = self.load_background(self.find_asset('mateo_bulletin_bg', 'mateo_bulletin'))
        self.mateo_and_lucas_bg = self.load_background(self.find_asset('mateo_and_lucas', 'mateo_and_lucas_bg'))
        self.mateo_teary_bg = self.load_background(self.find_asset('mateo_teary_bg', 'mateo_teary'))
        self.clara_and_lucas_bg = self.load_background(self.find_asset('clara_and_lucas_bg', 'clara_and_lucas'))
        self.julian_and_lucas_bg = self.load_background(self.find_asset('julian_and_lucas_bg', 'julian_and_lucas'))
        self.library_background = self.load_background(bg_root / 'plm_library.png')
        self.library_card_background = self.load_background(bg_root / 'library_card.png')
        self.san_agustin_background = self.load_background(bg_root / 'sanagustin.png')
        self.fort_santiago_background = self.load_background(bg_root / 'fortsantiago.png')
        self.escolta_background = self.load_background(bg_root / 'escolta.png')
        self.escolta_radio_background = self.load_background(bg_root / 'escolta_radio.png')
        self.quiapo_background = self.load_background(bg_root / 'quiapo.png')
        self.stacruz_background = self.load_background(bg_root / 'sta_cruz.png')
        self.warehouse_background = self.load_background(bg_root / 'warehouse.png')
        self.warehouse_on_background = self.load_background(bg_root / 'warehouse_on.png')
        self.warehouse_projector_background = self.load_background(self.find_asset('warehouse_projector_background', 'warehouse_projectoron'))
        self.plm_courtyard_background = self.load_background(bg_root / 'plm_courtyard.png')
        self.courtyard_restrained_background = self.load_background(bg_root / 'courtyard_restrained.png')
        self.courtyard_captured_background = self.load_background(self.find_asset('courtyard_captured'))

        self.text_level = 50
        self.drag_slider = None
        self.focus_slider = 'text'
        self.help_page = 0
        self.volume = 0.7
        self.settings_path = Path(__file__).resolve().parent / 'settings.json'

        #SOUND FX & MUSIC
        sound_root = Path(__file__).resolve().parent / 'assets/sounds'
        def load_sound(filename: str) -> pygame.mixer.Sound | None:
            path = sound_root / filename
            if path.exists():
                try:
                    return pygame.mixer.Sound(str(path))
                except pygame.error as error:
                    print(f"Sound load error: {error}")
            return None
        #Music
        self.menu_music = sound_root / 'menu_music.mp3'
        self.menu_music_sound = load_sound('menu_music.mp3')

        self.investigation_music = sound_root / 'investigation_music.mp3'
        self.tension_music = sound_root / 'tension_music.mp3'
        self.finale_music = sound_root / 'final_choice_music.mp3'
        self.ending_music = sound_root / 'ending_music.mp3'

        #ambient sounds
        self.city_ambient = load_sound('city_ambience.mp3')
        self.library_ambience = load_sound('library_ambience.mp3')
        self.warehouse_ambience = load_sound('warehouse_ambience.mp3')
        self.old_building_ambience = load_sound('old_building_ambience.mp3')
        self.plm_hallway_ambience = load_sound('plm_hallway_ambience.mp3')

        #sound fx
        self.intro_sound = load_sound('intro_sound.wav')
        self.loud_heartbeat = load_sound('heartbeat_fast.mp3')
        self.soft_heartbeat = load_sound('heartbeat.mp3')
        self.projector_sound = load_sound('projector.mp3')
        print("PROJECTOR OBJECT:", self.projector_sound)
        self.clue_found_sound = load_sound('clue_found.mp3')
        self.evidence_discovered_sound = load_sound('evidence_discovered.mp3')
        self.puzzle_correct_sound = load_sound('puzzle_correct.mp3')
        self.puzzle_incorrect_sound = load_sound('puzzle_wrong.mp3')

        self.menu_music_channel = None
        self.ambient_channel = None
        self.current_music = None
        self.current_ambient = None
        self.current_sfx = None
        self.sfx_channel = pygame.mixer.Channel(2)
        self.special_sfx_channel = pygame.mixer.Channel(3)
        self.volume_preview = None
        self.preview_channel = None
        self.menu_music_started = False
        self.last_preview_time = -1000
        self.load_settings()
        self.high_contrast = False
        self.running = True
        self.player = Player()
        self.state = "TEASER"
        self.dialogue_index = 0
        self.journal_open = False
        self.notice = ""
        self.locations = self.make_locations()
        self.puzzles = self.make_puzzles()
        self.solved_puzzles: set[str] = set()
        self.security_alerted = False
        self.video_capture = None
        self.video_frame = None
        self.video_index = -1
        self.start_video_teaser()
        self.backstory = [
            ("SYSTEM", "A missing-person poster trembles on a bulletin board."),
            ("STUDENT 1", "Kahapon pa siya nawawala. Wala pa ring balita..."),
            ("STUDENT REPORTER", "The last confirmed sighting was exactly 4:28 PM yesterday, near Intramuros."),
            ("SYSTEM", "Your phone vibrates. A message from an unknown number appears."),
            ("UNKNOWN NUMBER", "Kung gusto mong makita siyang buhay, huwag kang tumawag sa pulis. Hanapin mo ang tahimik na libro at makapal na alikabok. Bilisan mo."),
        ]

    def load_background(self, path):
        """Load a 4:3 background at the window size."""
        path = Path(path)
        if not path.exists():
            print("MISSING BACKGROUND:", path)
            return None
        img = pygame.image.load(str(path)).convert()
        if img.get_size() != (self.WIDTH, self.HEIGHT):
            img = pygame.transform.smoothscale(img, (self.WIDTH, self.HEIGHT))
        return img

    def find_asset(self, *stems):
        """Find an image under assets/backgrounds or assets/characters by file name,
        ignoring case and extension. Tries each name in order."""
        root = Path(__file__).resolve().parent / 'assets'
        for stem in stems:
            for folder in ('backgrounds', 'characters'):
                directory = root / folder
                if not directory.exists():
                    continue
                for f in directory.iterdir():
                    if f.stem.lower() == stem.lower() and f.suffix.lower() in ('.png', '.jpg', '.jpeg'):
                        return f
        print("MISSING ASSET (tried):", ", ".join(stems))
        return root / 'missing_asset.png'

    def load_sprite(self, path, max_w=300, max_h=340):
        """Load a character PNG, crop to its visible pixels, scale to fit max_w x max_h."""
        path = Path(path)
        if not path.exists():
            print("MISSING SPRITE:", path)
            return None
        source = pygame.image.load(str(path)).convert_alpha()
        bounds = source.get_bounding_rect()
        if not (bounds.width and bounds.height):
            return None
        source = source.subsurface(bounds).copy()
        scale = min(max_w / source.get_width(), max_h / source.get_height())
        return pygame.transform.smoothscale(
            source, (round(source.get_width() * scale), round(source.get_height() * scale)))

    def start_video_teaser(self) -> None:
        """Play the exported video with its matching WAV, relative to this file."""
        assets = Path(__file__).resolve().parent / "assets"
        if cv2 is None:
            print("Teaser unavailable: install opencv-python in your game Python.")
            self.finish_teaser()
            return
        self.video_capture = cv2.VideoCapture(str(assets / "videos/intro.mp4"))
        if not self.video_capture.isOpened():
            print("Teaser unavailable: could not open assets/videos/intro.mp4")
            self.finish_teaser()
            return
        self.video_fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        if not math.isfinite(self.video_fps) or self.video_fps <= 0:
            self.video_fps = 30.0
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.load(str(assets / "sounds/introsounds.wav"))
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play()
            else:
                print("Audio device unavailable; playing silent teaser.")
        except pygame.error as error:
            print(f"Teaser audio unavailable: {error}")
        self.teaser_started = pygame.time.get_ticks()

    def play_music(self, music_path, loop=-1):
        if music_path: 
            self.current_music = str(music_path)
            pygame.mixer.music.load(str(music_path))
            pygame.mixer.music.set_volume(self.volume * 0.25)
            pygame.mixer.music.play(loop)

    def stop_investigation_audio(self):
        print("=== STOPPING INVESTIGATION AUDIO ===")
        pygame.mixer.music.stop()

    def play_ambient(self, ambient_sound):
        pygame.mixer.music.stop()
        print("=== AMBIENT called ===")

        if ambient_sound is None:
            print("ERROR AYAW MAG LOAD")
            return
        
        if self.ambient_channel is None:
            self.ambient_channel = pygame.mixer.Channel(1)
        self.ambient_channel.stop()
        self.ambient_channel.set_volume(self.volume * 0.65)
        self.current_ambient = ambient_sound 
        self.ambient_channel.play(ambient_sound, loops=-1)  

    def stop_ambient(self):
        print ("STOPPING AMBIENT CHANNEL")
        print("CURRENT STATE:", self.state)

        if self.ambient_channel:
            self.ambient_channel.stop()
            self.ambient_channel = None

    def play_menu_music(self):
        print ("MENU MUSIC START")

        if self.menu_music_sound:
            if self.menu_music_channel:
                self.menu_music_channel.stop()

            self.menu_music_channel = pygame.mixer.Channel(0)
            self.menu_music_channel.set_volume(self.volume)
            self.menu_music_channel.play(self.menu_music_sound, loops=-1)

    def play_sfx(self, sound):
        if sound:
            self.sfx_channel.set_volume(self.volume)
            self.sfx_channel.play(sound)
    
    def play_special_sfx(self,sound, loops=0):
        print("SPECIAL SFX PLAY CALLED")
        if sound:  
            self.special_sfx_channel.set_volume(self.volume * 0.9)
            self.current_sfx = str(sound)
            self.special_sfx_channel.play(sound, loops=loops)

    def stop_special_sfx(self):
        if hasattr(self, "special_sfx_channel"):
            self.special_sfx_channel.stop()

    def show_audio_status(self):
        print("========== AUDIO STATUS ==========")
        print("STATE:", self.state)
        print("MUSIC:", self.current_music)
        print("AMBIENT:", self.current_ambient)
        print("SPECIAL SFX:", self.current_sfx)

        print("Music busy:", pygame.mixer.music.get_busy())

        if self.ambient_channel:
            print("Ambient busy:", self.ambient_channel.get_busy())

        if hasattr(self, "special_sfx_channel"):
            print("Special SFX busy:", self.special_sfx_channel.get_busy())

        print("==================================")

    def finish_teaser(self) -> None:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
        self.state = "INTRO"
        self.dialogue_index = 0

        if self.ambient_channel is None:
            self.play_ambient(self.plm_hallway_ambience)

    def update(self) -> None:
        if self.state != "TEASER":
            return
        if self.video_capture is None:
            self.finish_teaser()
            return
        
        target = int((pygame.time.get_ticks() - self.teaser_started) * self.video_fps / 1000)
        frame = None
        while self.video_index < target:
            ok, frame = self.video_capture.read()
            if not ok:
                self.finish_teaser()
                return
            self.video_index += 1
        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            surface = pygame.image.frombuffer(frame.tobytes(), (frame.shape[1], frame.shape[0]), "RGB")
            ratio = min(self.WIDTH / surface.get_width(), self.HEIGHT / surface.get_height())
            size = (max(1, round(surface.get_width() * ratio)), max(1, round(surface.get_height() * ratio)))
            self.video_frame = pygame.transform.smoothscale(surface, size)

    def make_locations(self) -> dict[str, Location]:
        """Each location only needs data.  Add scenes by copying this pattern."""
        return {
            "LIBRARY": Location(
                "LIBRARY", "PLM LIBRARY", (40, 54, 67),
                [
                    ("PLAYER", "The library is empty. Dust rests on the shelves like ash."),
                    ("SYSTEM", "Investigation: Which object deserves a closer look?"),
                ],
                [
                    Choice("Travel to San Agustin Church", "The cross symbol leads you deeper into Intramuros.", "SAN_AGUSTIN",True, 0, 20),
                    Choice("Search the University Activity Center", "You find no matching symbol and return to the library.", "LIBRARY", False, -5, 25),
                    Choice("Go to Justo Alberto Auditorium", "The empty seats offer no clue. You return uneasy.", "LIBRARY", -10, 25),
                ],
            ),
            "SAN_AGUSTIN": Location(
                "SAN_AGUSTIN", "SAN AGUSTIN", (69, 54, 47),
                [("PLAYER", "The old stones carry a symbol matching the library stamp."),
                 ("MATEO", "Dito tayo nagpapalipas ng oras pagkatapos ng klase. May krus sa lumang bato, tulad ng nasa card."),
                 ("SYSTEM", "The clue points to a place connected to prisoners and the northern end of Intramuros.")],
                [
                    Choice("Travel to Fort Santiago", "You follow the historical trail toward the northern end of Intramuros.", "FORT_SANTIAGO", 0, 20),
                    Choice("Head to Manila Cathedral", "The architecture is familiar, but the symbols do not match.", "SAN_AGUSTIN", False, -5, 30),
                    Choice("Follow a stranger's shortcut", "A dead end. The sender knows you are wasting time.", "SAN_AGUSTIN", False, -10, 35),
                ],
            ),
            "FORT_SANTIAGO": Location(
                "FORT_SANTIAGO", "FORT SANTIAGO", (60, 69, 56),
                [("CARETAKER", "Your friend left an envelope for whoever kept looking."),
                 ("MATEO", "Sul sulat niya ito... Luke, kahit noon naghahanda ka na?"),
                 ("PLAYER", "Inside is a clue about old cinemas, art, and trade across the river.")],
                [
                    Choice("Cross the river to Escolta", "As sunset falls, an old radio begins playing by itself.", "ESCOLTA", True, 0, 30),
                    Choice("Search Luneta", "You find nothing except crowds and lost time.", "FORT_SANTIAGO", False, -5, 40),
                    Choice("Return to PLM", "It is too early to return; the trail is still outside the walls.", "FORT_SANTIAGO", False, -5, 35),
                ],
            ),
            "ESCOLTA": Location(
                "ESCOLTA", "ESCOLTA - NIGHT", (42, 44, 73),
                [("SYSTEM", "A radio crackles beneath a flickering streetlight."),
                 ("UNKNOWN NUMBER", "Masyado kang mapagtiwala. Binabantayan ko ang bawat liko mo."),
                 ("PLAYER", "The next message mentions devotees, candles, and alleys beside an estero.")],
                [
                    Choice("Follow the signal to Quiapo", "The signal stops, but its direction is clear.", "QUIAPO", True, 0, 25),
                    Choice("Follow the radio into an alley", "The radio was bait. You return shaken.", "ESCOLTA", False, -10, 30),
                    Choice("Travel to Taft", "The description does not fit. You lose precious time.", "ESCOLTA", False, -5, 45),
                ],
            ),
            "QUIAPO": Location(
                "QUIAPO", "QUIAPO", (74, 45, 43),
                [("PLAYER", "A red mark is painted on a cracked wall beside a note about a bridge."),
                 ("SYSTEM", "Compare it with the ink on your earlier clues before you decide.")],
                [
                    Choice("Follow the genuine mark to Sta. Cruz", "You bypass the bridge trap and move before the sender can react.", "STA_CRUZ", True, 0, 20),
                    Choice("Go to the bridge", "Bitag iyon. Nakatakas ka, ngunit nabawasan ang iyong Lakas ng Loob.", "QUIAPO", False, -20, 50),
                    Choice("Ask random vendors for the sender", "Nobody can identify the sender. The search costs time.", "QUIAPO", False, -5, 30),
                ],
            ),
            "STA_CRUZ": Location(
                "STA_CRUZ", "STA. CRUZ", (54, 59, 68),
                [("PLAYER", "In an old shop, a Polaroid and cassette wait on a wooden chair."),
                 ("SYSTEM", "Moonlight reveals invisible ink: an old warehouse beside the estero.")],
                [
                    Choice("Follow the hidden message to the warehouse", "The cassette's traffic sounds grow louder near the estero.", "WAREHOUSE",True, 0, 25),
                    Choice("Search an abandoned church", "No trace of your friend. The sender's clock keeps moving.", "STA_CRUZ", False, -10, 40),
                    Choice("Return to Escolta", "You only find the dead radio again.", "STA_CRUZ", False, -5, 45),
                ],
            ),
            "WAREHOUSE": Location(
                "WAREHOUSE", "OLD WAREHOUSE", (43, 42, 45),
                [("SYSTEM", "A projector flickers on. Your friend is alive - tied up in the PLM courtyard."),
                 ("UNKNOWN NUMBER", "Bumalik ka sa loob ng pader bago sumapit ang liwanag."),
                 ("PLAYER", "The cassette confirms it. The final location is PLM.")],
                [
                    Choice("Return to PLM with the evidence", "You run toward Intramuros before dawn.", "FINALE", True, 0, 35),
                    Choice("Wait for help", "Waiting feels safe, but the message's deadline does not stop.", "WAREHOUSE", False, -15, 55),
                    Choice("Go back to Quiapo", "The old false trail costs nearly an hour.", "WAREHOUSE", False, -10, 60),
                ],
            ),
        }

    def make_puzzles(self) -> dict[str, Puzzle]:
        """One short puzzle per place. Add a new Puzzle here for new locations."""
        return {
            "LIBRARY": Puzzle(
                "LIBRARY CARD CODE",
                "The card says 'DS 686 .P6'. Which shelf label is the closest match?",
                ["DS 686 .P6 - Philippine history", "QA 76.73 - Python programming", "PN 1997 - Film studies"],
                0,
                "The book opens beneath the old stamp. A library card slips out, bearing a cross symbol.",
                Evidence("Library Card", "A careful blue-black stamp and your friend's handwriting identify this as a genuine clue.", "MISSING FRIEND"),
            ),
            "SAN_AGUSTIN": Puzzle(
                "STONE SYMBOLS",
                "The same cross symbol appears beside three directions. Which clue best matches the next location?",
                ["A fort at the northern end of Intramuros", "A mall outside the walls", "A modern office building"],
                0,
                "You align the symbols. The hidden phrase points to Fort Santiago.",
                Evidence("Stone Rubbing", "The same blue-black stamp marks the genuine route to Fort Santiago.", "MISSING FRIEND"),
            ),
            "FORT_SANTIAGO": Puzzle(
                "THE CARETAKER'S TESTIMONY",
                "Which detail in the envelope identifies the next area?",
                ["Old cinemas, art, and commerce across the river", "A beach facing Manila Bay", "A university library with a red gate"],
                0,
                "The description fits Escolta. You mark it on your map.",
                Evidence("Caretaker's Envelope", "The envelope carries your friend's familiar handwriting and points to Escolta.", "MISSING FRIEND"),
            ),
            "ESCOLTA": Puzzle(
                "RADIO FREQUENCY",
                "Turn the radio dial. Which frequency gives a clear fragment: 'deboto ... estero'?",
                ["88.1 FM", "94.2 FM", "101.7 FM"],
                1,
                "The static clears at 94.2 FM. The message points to Quiapo.",
                Evidence("Radio Frequency", "A voice recording mentions Quiapo; it also proves someone is monitoring the route.", "UNKNOWN SENDER"),
            ),
            "QUIAPO": Puzzle(
                "COMPARE THE MARKS",
                "The bridge note looks suspicious. Which difference proves it is a fake clue?",
                ["Its ink is bright red; the earlier clues use dark blue-black ink", "It is written on paper", "It has more than one word"],
                0,
                "You reject the trap. A smaller, genuine mark directs you to Sta. Cruz.",
                Evidence("Forged Mark", "Bright red ink and rushed handwriting prove the bridge note is an antagonist trap.", "ANTAGONIST TRAP"),
            ),
            "STA_CRUZ": Puzzle(
                "INVISIBLE INK",
                "What reveals the message on the Polaroid?",
                ["Hold it under moonlight", "Tear the photograph", "Drop it into the estero"],
                0,
                "Moonlight reveals an old warehouse beside the estero. The cassette captures sounds near PLM.",
                Evidence("Polaroid and Cassette", "Your friend used invisible ink. The cassette records sounds near PLM and supports the real trail.", "MISSING FRIEND"),
            ),
            "WAREHOUSE": Puzzle(
                "PROJECTOR CABLES",
                "The projector has three loose cables. Which connection restores its image?",
                ["Power -> projector, video -> screen, audio -> speaker", "Power -> screen, video -> speaker, audio -> projector", "Connect every cable to the projector"],
                0,
                "The projector flickers on. The recording confirms that your friend is in the PLM courtyard.",
                Evidence("Projector Recording", "A recording confirms the PLM courtyard and shows enough detail to alert campus security.", "MISSING FRIEND"),
            ),
        }

    def reset(self) -> None:
        self.player = Player()
        self.state = "MENU"
        self.dialogue_index = 0
        self.notice = ""
        self.journal_open = False
        self.solved_puzzles.clear()
        self.security_alerted = False

        pygame.mixer.music.stop()
        self.play_menu_music()

    def current_dialogue(self) -> list[tuple[str, str]]:
        if self.state == "INTRO":
            return [
                ("SYSTEM", " A missing-person poster hangs on the bulletin board. The photograph belongs to Lucas 'Luke' Valderrama, a campus journalist."),
                ("STUDENT 1", "Isang linggo na mula nang iulat na nawawala si Lucas. Wala pa ring malinaw na balita..."),
                ("STUDENT REPORTER", "Lucas was last seen near Intramuros at exactly 4:28 PM. Anyone with information is asked to come forward."),
                ("SYSTEM", "The broadcast fades. Around the poster, whispers give way to silence. Someone is still waiting for Lucas to come home."),
            ]
        if self.state == "BACKSTORY":
            return self.backstory
        if self.state in self.locations:
            return self.locations[self.state].dialogue
        if self.state == "FINALE":
            return self.route_finale + [("SYSTEM", "Security has your recording. Keep the antagonist talking." if self.security_alerted else "No backup is confirmed. Lucas watches you from the chair.")]
        return []

    def advance_dialogue(self) -> None:
        dialogue = self.current_dialogue()
        self.dialogue_index += 1
        if self.dialogue_index < len(dialogue):
            return
        self.dialogue_index = 0
        if self.state == "INTRO":
            self.stop_ambient()
            if self.menu_music_channel:
                self.menu_music_channel.stop()
            self.state = "MENU"
            self.play_menu_music()
            
        elif self.state == "BACKSTORY": 
            self.stop_ambient()
            self.state = "CHOICE_OPENING"
            self.play_music(self.investigation_music)   
           
        elif self.state in self.locations:
            if self.state == "WAREHOUSE":
                print("WAREHOUSE DIALOGUE FINISHED - STOPPING PROJECTOR")
                self.special_sfx_channel.stop()
                pygame.mixer.music.stop()
                self.sfx_channel.stop()
            else: 
                self.play_sfx(self.clue_found_sound)
                    
            if self.state in self.solved_puzzles:
                self.state = f"CHOICE_{self.state}"
            else:
                self.state = f"PUZZLE_{self.state}"
        elif self.state == "FINALE":
            self.special_sfx_channel.stop()
            self.state = "FINAL_CHOICE"
            self.play_music(self.finale_music)

    def solve_puzzle(self, index: int) -> None:
        print("SOLVE PUZZLE CALLED:", index)
        """Check an investigation puzzle, then unlock that location's travel choices."""
        location_key = self.state.removeprefix("PUZZLE_")
        puzzle = self.puzzles[location_key]
        if not 0 <= index < len(puzzle.options):
            return
        if location_key in self.solved_puzzles:
            self.state = f'CHOICE_{location_key}'
            return
        if index == puzzle.correct_index:
            self.play_sfx(self.puzzle_correct_sound)
            self.solved_puzzles.add(location_key)
            self.player.change_composure(5)
            intuitive = self.player.character == 'Julian' and location_key in {'LIBRARY', 'QUIAPO', 'STA_CRUZ'}
            self.player.spend_time(5 if intuitive else 10)
            self.notice = puzzle.success
            if intuitive:
                self.notice += '\nIntuition: saved 5 minutes (5 minutes spent).'
            if self.player.add_evidence(puzzle.evidence.name, puzzle.evidence.description, puzzle.evidence.source):
                self.notice += f"\nEvidence added: {puzzle.evidence.name}\nLakas ng Loob +5"
            if location_key == "WAREHOUSE":
                self.security_alerted = True      
                self.notice += "\nYou secretly send the projector recording and PLM location to campus security."
            self.next_after_notice = f"CHOICE_{location_key}"
            self.state = "NOTICE"
        else:
            print("WRONG ANSWER TRIGGERED")
            self.play_sfx(self.puzzle_incorrect_sound)
            penalty = 3 if self.player.character == 'Clara' else 5
            self.player.change_composure(-penalty)
            self.player.spend_time(10)
            if self.check_lakas_ng_loob():
                return
            self.notice = f"{puzzle.failure}\nLakas ng Loob -{penalty}. 10 minutes spent."
            if self.player.character == 'Clara':
                self.notice += '\nDeductive Precision: lost 2 less Lakas ng Loob.'
            self.next_after_notice = self.state
            self.state = "NOTICE"

    def choose(self, index: int) -> None:
        if self.state == 'CHOICE_OPENING':
            if index not in (0, 1, 2):
                return

            self.stop_ambient()
            if not pygame.mixer.music.get_busy():
                self.play_music(self.investigation_music)
            
            self.player.spend_time(5 if index == 2 else 20)
            if index != 2:
                self.play_sfx(self.puzzle_incorrect_sound)

                self.player.change_composure(-10)
                if self.check_lakas_ng_loob():
                    return
                place = ['Justo Alberto Auditorium', 'University Activity Center'][index]
                self.notice = f'{place}: Wala rito ang tinutukoy ng mensahe. Balikan ko ang clue.\nLakas ng Loob -10 | 20 minutes spent.'
                self.next_after_notice = 'CHOICE_OPENING'
            else:
                self.play_sfx(self.puzzle_correct_sound)
                self.notice = 'Tahimik na libro... sa library!\nYou head to the PLM Library. 5 minutes spent.'
                self.next_after_notice = 'PUZZLE_LIBRARY'

            self.dialogue_index = 0
            self.state = 'NOTICE'
            return
        if self.state == "FINAL_CHOICE":
            self.finish(index)
            return
        source = self.state.removeprefix("CHOICE_")
        location = self.locations[source]
        if not 0 <= index < len(location.choices):
            return
        choice = location.choices[index]
        if source == "WAREHOUSE" and choice.next_state != "WAREHOUSE":
            self.stop_ambient()
            self.stop_special_sfx()
        
        if choice.correct:
            self.play_sfx(self.puzzle_correct_sound)
        else: 
            self.play_sfx(self.puzzle_incorrect_sound)
        self.player.change_composure(choice.composure_change)
        shortcut = (self.player.character == 'Mateo' and
                    (source, choice.next_state) in {
                        ('LIBRARY', 'SAN_AGUSTIN'),
                        ('SAN_AGUSTIN', 'FORT_SANTIAGO'),
                    })
        self.player.spend_time(max(0, choice.time_cost - (5 if shortcut else 0)))
        if self.check_lakas_ng_loob():
            return
        self.notice = choice.result
        if shortcut:
            self.notice += f'\nIntramuros Insight: saved 5 minutes ({choice.time_cost - 5} minutes spent).'
        if choice.evidence and self.player.add_evidence(choice.evidence.name, choice.evidence.description):
            self.play_special_sfx(self.evidence_discovered_sound)
            self.notice += f"\nEvidence added: {choice.evidence.name}"
        self.state = "NOTICE"
        self.next_after_notice = choice.next_state

    def check_lakas_ng_loob(self) -> bool:
        """End the run immediately when fear and exhaustion overwhelm the player."""
        if self.player.composure <= 0:
            self.play_sfx(self.loud_heartbeat)
            self.state = "PANIC_ENDING"
            self.journal_open = False
            return True
        elif self.player.composure <= 30: 
            self.play_sfx(self.soft_heartbeat)
        return False

    def finish(self, index: int) -> None:
        has_key_evidence = len(self.player.evidence) >= 5
        if index == 0 and has_key_evidence and self.security_alerted and self.player.composure >= 25 and self.player.time_minutes < 720:
            self.state = "TRUE_ENDING"
        elif index == 0:
            self.state = "BITTERSWEET_ENDING"
        else:
            self.state = "BAD_ENDING"

        self.play_music(self.ending_music)

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.state == 'CHOICE_OPENING' and not self.journal_open and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index in range(3):
                if pygame.Rect(70, 335 + index * 95, 820, 65).collidepoint(event.pos):
                    self.choose(index)
                    break
            return
        if self.state == 'CHARACTER' and event.type != pygame.QUIT:
            self.character_event(event)
            return
        if self.state in ('SETTINGS', 'HELP') and self.settings_event(event):
            return
        if event.type == pygame.QUIT:
            self.running = False
            return
        if self.state in ('MENU', 'SETTINGS'):
            labels = ['START', 'MENU', 'QUIT'] if self.state == 'MENU' else [
                'TEXT -', 'TEXT +', 'CONTRAST', 'VOLUME -', 'VOLUME +', 'BACK']
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for label, rect in self.ui_buttons().items():
                    if rect.collidepoint(event.pos):
                        self.menu_action(label)
                        break
                return
            if event.type == pygame.KEYDOWN:
                if pygame.K_1 <= event.key < pygame.K_1 + len(labels):
                    self.menu_action(labels[event.key - pygame.K_1])
                elif event.key == pygame.K_ESCAPE:
                    self.menu_action('BACK' if self.state == 'SETTINGS' else 'QUIT')
                return
        if event.type != pygame.KEYDOWN:
            return
        if self.state == "TEASER":
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                self.finish_teaser()
            return
        if event.key == pygame.K_j and self.state not in {"MENU", "CHARACTER"}:
            self.journal_open = not self.journal_open
            return
        if self.journal_open:
            if event.key in (pygame.K_j, pygame.K_ESCAPE):
                self.journal_open = False
            return
        if self.state == "MENU":
            if event.key == pygame.K_1:
                self.state = "CHARACTER"
                self.play_menu_music()
            elif event.key == pygame.K_ESCAPE:
                self.running = False
        elif self.state == "CHARACTER":
            if event.key in (pygame.K_1, pygame.K_2):
                self.player.character = "Silhouette A" if event.key == pygame.K_1 else "Silhouette B"
                # The player has already seen the opening message before the menu.
                # Start the first investigation after selecting a character.
                
                if self.menu_music_channel: #stop the menu music
                    self.menu_music_channel.stop()

                pygame.mixer.music.stop() #stop music
                self.stop_ambient() #stop the ambient music

                self.state = "BACKSTORY"
                self.dialogue_index = 0
                
                self.play_ambient(self.plm_hallway_ambience)  
                
            elif event.key == pygame.K_ESCAPE:
                self.state = "MENU"
        elif self.state in {"INTRO", "BACKSTORY", *self.locations, "FINALE"}:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.advance_dialogue()
                
        elif self.state.startswith("PUZZLE_"):
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                self.solve_puzzle(event.key - pygame.K_1)
        elif self.state.startswith("CHOICE_") or self.state == "FINAL_CHOICE":
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                self.choose(event.key - pygame.K_1)

        elif self.state == "NOTICE":
            self.show_audio_status()
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                next_state = self.next_after_notice
                
                if next_state == "WAREHOUSE":
                    print("WAREHOUSE AUDIO RESET")
                    if self.ambient_channel:
                        self.ambient_channel.stop()
                    self.ambient_channel = None
                    
                    self.play_ambient(self.warehouse_ambience)
                    self.stop_special_sfx()
                    self.play_special_sfx(self.projector_sound)

                elif next_state == "LIBRARY":
                    self.stop_ambient()
                    self.play_ambient(self.library_ambience)

                elif next_state in ["SAN_AGUSTIN", "FORT_SANTIAGO"]:
                    self.stop_ambient()
                    self.play_ambient(self.old_building_ambience)

                elif next_state in ["ESCOLTA", "QUIAPO", "STA_CRUZ"]:
                    self.stop_ambient()
                    self.play_ambient(self.city_ambient)

                self.state = next_state
                self.show_audio_status()
                self.dialogue_index = 0

        elif self.state.endswith("ENDING") and event.key == pygame.K_r:
            self.reset()

    def panel(self, rect: pygame.Rect, border: tuple[int, int, int] | None = None) -> None:
        pygame.draw.rect(self.screen, self.PANEL, rect, border_radius=8)
        pygame.draw.rect(self.screen, border or self.MUTED, rect, 2, border_radius=8)

    def draw_text(self, text: str, font: pygame.font.Font, color: tuple[int, int, int],
                  pos: tuple[int, int], shadow: bool = False) -> pygame.Rect:
        if shadow:
            self.screen.blit(font.render(text, True, (3, 5, 10)), (pos[0] + 2, pos[1] + 2))
        surface = font.render(text, True, color)
        self.screen.blit(surface, pos)
        return surface.get_rect(topleft=pos)

    def draw_lines(self, text: str, x: int, y: int, width: int, color: tuple[int, int, int],
                   font: pygame.font.Font | None = None, shadow: bool = False) -> int:
        used_font = font or self.font
        for line in wrap_text(used_font, text, width):
            self.draw_text(line, used_font, color, (x, y), shadow)
            y += used_font.get_linesize()
        return y

    def draw_hud(self) -> None:
        pygame.draw.rect(self.screen, (5, 7, 12), (0, 0, self.WIDTH, 52))
        left = f"LAKAS NG LOOB: {self.player.composure:03d}"
        center = f"TIME: {clock_text(self.player.time_minutes)}"
        right = f"EVIDENCE: {len(self.player.evidence)}   [J] JOURNAL"
        self.draw_text(left, self.small_font, self.RED if self.player.composure < 35 else self.PAPER, (20, 17))
        self.draw_text(center, self.small_font, self.GOLD, (410, 17))
        self.draw_text(right, self.small_font, self.MUTED, (750, 17))

    def draw_teaser(self) -> None:
        self.screen.fill((0, 0, 0))
        if self.video_frame is not None:
            self.screen.blit(self.video_frame, self.video_frame.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2)))
        prompt = self.small_font.render("[SPACE] skip teaser", True, self.PAPER)
        self.screen.blit(prompt, prompt.get_rect(bottomright=(self.WIDTH - 24, self.HEIGHT - 20)))

    def draw_dialogue(self) -> None:
        dialogue = self.current_dialogue()
        idx = self.dialogue_index
        speaker, text = dialogue[idx]
        spk = speaker.upper()
        char_name = self.characters[self.character_index][0].upper()
        title = " " if self.state in {"INTRO", "BACKSTORY"} else self.locations[self.state].title if self.state in self.locations else "PLM COURTYARD"
        color = self.locations[self.state].color if self.state in self.locations else (47, 35, 42)

        background = None
        cutouts = []  

        # INTRO
        if self.state == "INTRO":
            background = self.plm_hallway_background
            if idx == 1 and self.sprites.get("student_one"):
                cutouts.append((self.sprites["student_one"], 600))
            elif idx == 2:
                background = self.backstory_background or self.plm_hallway_background  

        # BACKSTORY per-route storyboard by line index
        elif self.state == "BACKSTORY":
            background = self.plm_hallway_background
            back = self.back_characters[self.character_index]
            cutout = None
            cutout_x = 70
            phone_start = next((i for i, (_, line) in enumerate(dialogue)
                                if "phone vibrates" in line.lower()), len(dialogue))
            phone_line = idx >= phone_start
            if char_name == "MATEO":
                if idx == 0:
                    background = self.mateo_bulletin_bg or background
                elif idx == 4:
                    background = self.mateo_and_lucas_bg or background
                elif idx == 2:
                    cutout, cutout_x = self.sprites.get("student_one"), 600
                elif idx == 3:
                    background = self.mateo_teary_bg or background
                elif phone_line:
                    cutout = self.sprites.get("mateo_phone") or back
                else:
                    cutout = back
            elif char_name == "CLARA":
                if idx == 2:
                    background = self.clara_and_lucas_bg or background
                elif phone_line:
                    cutout = self.sprites.get("clara_phone") or self.sprites.get("clara_sulat") or back
                else:
                    cutout = back
            elif char_name == "JULIAN":
                if idx == 2:
                    background = self.julian_and_lucas_bg or background
                elif phone_line:
                    cutout = self.sprites.get("julian_phone") or self.sprites.get("julian_sulat") or back
                else:
                    cutout = back
            if cutout:
                cutouts.append((cutout, cutout_x))

        # LOCATIONS + FINALE
        else:
            if self.state == "LIBRARY":
                card = self.library_card_background if "library stamp" in text.lower() else None
                background = card or self.library_background
            elif self.state == "SAN_AGUSTIN":
                background = self.san_agustin_background
            elif self.state == "FORT_SANTIAGO":
                background = self.fort_santiago_background
            elif self.state == "ESCOLTA":
                background = (self.escolta_radio_background if idx == 0 else self.escolta_background) or self.escolta_background
            elif self.state == "QUIAPO":
                background = self.quiapo_background
            elif self.state == "STA_CRUZ":
                background = self.stacruz_background
            elif self.state == "WAREHOUSE":
                if idx >= 2:
                    background = self.warehouse_projector_background    
                elif idx == 1:
                    background = self.warehouse_on_background           
                background = background or self.warehouse_background
            elif self.state == "FINALE":
                if idx == 0:
                    background = self.plm_courtyard_background
                background = background or self.courtyard_restrained_background
            sprite = None
            sprite_x = 600
            if spk == "UNKNOWN NUMBER" and self.state == "ESCOLTA":
                sprite = self.sprites.get("anino")
                sprite_x = 640
            elif spk in ("MATEO", "CLARA", "JULIAN"):
                if spk == "MATEO" and self.state == "SAN_AGUSTIN":
                    sprite = self.sprites.get("mateo_card")
                elif self.state == "FORT_SANTIAGO":
                    sprite = self.sprites.get(f"{spk.lower()}_sulat")
                sprite = sprite or self.character_images[{"MATEO": 0, "CLARA": 1, "JULIAN": 2}[spk]]
            elif spk == "CARETAKER":
                sprite = self.sprites.get("caretaker_idle") or self.sprites.get("caretaker_talk")
                sprite_x = 550
            elif spk == "STUDENT 1":
                sprite = self.sprites.get("student_one")
            elif spk == "LUCAS":
                sprite = self.sprites.get("lucas")

            if sprite:
                cutouts.append((sprite, sprite_x))

        # DRAW
        if background:
            self.screen.blit(background, (0, 0))
        else:
            self.screen.fill(color)

        for surface, x in cutouts:
            self.screen.blit(surface, (x, 460 - surface.get_height()))   # base sits on the panel's top edge

        self.draw_hud()
        self.draw_text(title, self.title_font, self.PAPER, (40, 78), shadow=True)
        self.panel(pygame.Rect(45, 460, 870, 225), self.GOLD)
        self.draw_text(speaker, self.font, self.GOLD, (70, 480))
        self.draw_lines(text, 70, 515, 820, self.PAPER)
        self.draw_text("[SPACE] continue", self.small_font, self.MUTED, (745, 655))


    def draw_choice(self) -> None:
        if self.state == "FINAL_CHOICE":
            source = "FINALE"
        else:
            source = self.state.removeprefix("CHOICE_")

        if self.state == "CHOICE_LIBRARY" and self.library_background:
            self.screen.blit(self.library_background, (0, 0))
        elif self.state == "CHOICE_SAN_AGUSTIN" and self.san_agustin_background:
            self.screen.blit(self.san_agustin_background, (0, 0))
        elif self.state == "CHOICE_FORT_SANTIAGO" and self.fort_santiago_background:
            self.screen.blit(self.fort_santiago_background, (0, 0))
        elif self.state == "CHOICE_ESCOLTA" and self.escolta_background:
            self.screen.blit(self.escolta_background, (0, 0))
        elif self.state == "CHOICE_QUIAPO" and self.quiapo_background:
            self.screen.blit(self.quiapo_background, (0, 0))
        elif self.state == "CHOICE_STA_CRUZ" and self.stacruz_background:
            self.screen.blit(self.stacruz_background, (0, 0))
        elif self.state == "CHOICE_WAREHOUSE" and self.warehouse_background:
            self.screen.blit(self.warehouse_background, (0, 0))
        else:
            self.screen.fill(self.INK)

        self.draw_hud()
        if source == "FINALE":
            title = "FINAL DECISION"
            choices = self.final_choices
        else:
            title = self.locations[source].title
            choices = [choice.label for choice in self.locations[source].choices]
        self.draw_text(title, self.title_font, self.PAPER, (45, 100), shadow=True)
        self.draw_lines("Choose carefully. Choices cost time and affect your Lakas ng Loob; they are not forced retries.",
                        48, 180, 840, self.MUTED, shadow=True)
        for index, label in enumerate(choices):
            rect = pygame.Rect(70, 275 + index * 95, 820, 65)
            # Every route must look equally possible.  Never highlight option 1,
            # because that would accidentally reveal the intended route.
            self.panel(rect, self.MUTED)
            self.draw_lines(f"[{index + 1}] {label}", 95, rect.y + 18, 790, self.PAPER)

    def draw_puzzle(self) -> None:
        """Draw a dedicated puzzle screen instead of treating it as ordinary dialogue."""
        location_key = self.state.removeprefix("PUZZLE_")
        puzzle = self.puzzles[location_key]
        color = self.locations[location_key].color
        if location_key == "LIBRARY" and self.library_card_background:
            self.screen.blit(self.library_card_background, (0, 0))
        elif location_key == "SAN_AGUSTIN" and self.san_agustin_background:
            self.screen.blit(self.san_agustin_background, (0, 0))
        elif location_key == "FORT_SANTIAGO" and self.fort_santiago_background:
            self.screen.blit(self.fort_santiago_background, (0, 0))
        elif location_key == "ESCOLTA" and self.escolta_background:
            self.screen.blit(self.escolta_background, (0, 0))
        elif location_key == "QUIAPO" and self.quiapo_background:
            self.screen.blit(self.quiapo_background, (0, 0))
        elif location_key == "STA_CRUZ" and self.stacruz_background:
            self.screen.blit(self.stacruz_background, (0, 0))
        elif location_key == "WAREHOUSE" and self.warehouse_background:
            self.screen.blit(self.warehouse_background, (0, 0))
        
        else:
            self.screen.fill(color)
        self.draw_hud()
        self.panel(pygame.Rect(45, 128, 870, 130), self.GOLD)
        self.draw_text(puzzle.title, self.font, self.GOLD, (70, 150))
        self.draw_lines(puzzle.prompt, 70, 188, 820, self.PAPER)
        for index, option in enumerate(puzzle.options):
            rect = pygame.Rect(70, 335 + index * 95, 820, 65)
            self.panel(rect, self.MUTED)
            self.draw_lines(f"[{index + 1}] {option}", 95, rect.y + 18, 790, self.PAPER)
        penalty = 3 if self.player.character == 'Clara' else 5
        hint = f'Wrong answer: 10 minutes and {penalty} Lakas ng Loob.'
        text_w = self.small_font.size(hint)[0]
        text_x = (self.WIDTH - text_w) // 2
        self.draw_text(hint, self.small_font, self.MUTED, (text_x, 665), shadow=True)

    def draw_journal(self) -> None:
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))
        rect = pygame.Rect(105, 60, 750, 530)
        pygame.draw.rect(self.screen, self.PAPER, rect, border_radius=8)
        pygame.draw.rect(self.screen, self.GOLD, rect, 4, border_radius=8)
        self.screen.blit(self.title_font.render("EVIDENCE JOURNAL", True, self.INK), (145, 90))
        y = 165
        if not self.player.evidence:
            self.screen.blit(self.font.render("No evidence collected yet.", True, self.INK), (145, y))
        for item in self.player.evidence:
            self.screen.blit(self.font.render(f"- {item.name} [{item.source}]", True, self.RED), (145, y))
            y = self.draw_lines(item.description, 170, y + 26, 630, self.INK, self.small_font) + 14
        self.screen.blit(self.small_font.render("[J] or [ESC] close journal", True, self.INK), (630, 535))

    def draw_ending(self) -> None:
        endings = {
            "TRUE_ENDING": ("TRUE ENDING", "Your evidence exposes the planted clues. Because you sent the projector recording, campus security reaches the courtyard in time and rescues your friend."),
            "BITTERSWEET_ENDING": ("BITTERSWEET ENDING", "You reach your friend, but missing evidence leaves gaps in the case. The antagonist disappears before the full truth can be proven."),
            "BAD_ENDING": ("TRAGIC ENDING", "The wrong final move gives the antagonist control. The screen fades just before dawn."),
            "PANIC_ENDING": ("GAME OVER - LOST IN THE DARK", "Your Lakas ng Loob reaches zero. Fear and exhaustion overwhelm you; you lose your direction, stop trusting the clues, and the trail goes cold before you can reach your friend."),
        }
        title, _ = endings[self.state]
        description = self.route_endings[self.state]
        self.screen.fill((32, 15, 21))
        if self.state == "TRUE_ENDING" and self.courtyard_captured_background:
            self.screen.blit(self.courtyard_captured_background, (0, 0))
            shade = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 150))
            self.screen.blit(shade, (0, 0))
        title_surface = self.title_font.render(title, True, self.RED)
        title_rect = title_surface.get_rect(center=(self.WIDTH // 2, 205))
        self.draw_text(title, self.title_font, self.RED, title_rect.topleft, shadow=True)
        self.panel(pygame.Rect(145, 265, 670, 205), self.GOLD)
        self.draw_lines(description, 170, 295, 620, self.PAPER)
        self.draw_text("[R] Restart", self.font, self.GOLD, (400, 580), shadow=True)

    def ui_buttons(self) -> dict:
        if self.state == 'MENU':
            return {label: pygame.Rect(340, 340 + index * 68, 280, 52)
                    for index, label in enumerate(['START', 'MENU', 'QUIT'])}
        return {'HELP / TUTORIAL': pygame.Rect(300, 440, 360, 54),
                'BACK': pygame.Rect(360, 520, 240, 52)}

    def load_settings(self):
        try:
            data = json.loads(self.settings_path.read_text(encoding='utf-8'))
            self.slider_value('text', float(data.get('text', 63)))
            self.slider_value('volume', float(data.get('volume', 70)))
        except (OSError, ValueError, TypeError, AttributeError, OverflowError):
            self.slider_value('text', 63)
            self.slider_value('volume', 70)

    def save_settings(self):
        try:
            self.settings_path.write_text(json.dumps({
                'text': self.text_level, 'volume': round(self.volume * 100)
            }, indent=2), encoding='utf-8')
        except OSError as error:
            print(f'Could not save settings: {error}')

    def preview_volume(self):
        mixer = pygame.mixer.get_init()
        if not mixer:
            return
        now = pygame.time.get_ticks()
        if now - self.last_preview_time < 150:
            return
        self.last_preview_time = now
        if self.volume_preview is None:
            rate, sample_format, channels = mixer
            if sample_format != -16:
                return
            count = int(rate * 0.12)
            samples = array('h')
            for i in range(count):
                envelope = min(1.0, i / (rate * .01), (count - i) / (rate * .03))
                sample = round(6500 * envelope * math.sin(2 * math.pi * 440 * i / rate))
                samples.extend([sample] * channels)
            self.volume_preview = pygame.mixer.Sound(buffer=samples.tobytes())
        self.volume_preview.set_volume(self.volume)
        self.preview_channel = self.volume_preview.play()
        if self.preview_channel:
            self.preview_channel.set_volume(1.0)

    def slider_value(self, name, value):
        value = max(1, min(100, round(value)))
        if name == 'text':
            # Snap to real pixel sizes: each selectable step looks different.
            self.text_size = round(18 + (value - 1) * 8 / 99)
            self.text_level = round(1 + (self.text_size - 18) * 99 / 8)
            self.font = make_font(self.body_fonts, self.text_size)
        else:
            self.volume = value / 100
            if pygame.mixer.get_init():
                pygame.mixer.music.set_volume(self.volume)
                for i in range(pygame.mixer.get_num_channels()):
                    pygame.mixer.Channel(i).set_volume(self.volume)
                if self.volume_preview:
                    # The preview sound owns its gain; avoid applying it twice.
                    self.volume_preview.set_volume(self.volume)
                    if self.preview_channel:
                        self.preview_channel.set_volume(1.0)

    def settings_event(self, event):
        if event.type == pygame.QUIT:
            self.save_settings()
            return False
        if self.state == 'HELP':
            if ((event.type == pygame.KEYDOWN and event.key in
                 (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN))
                    or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)):
                self.state = 'SETTINGS'
                self.drag_slider = None
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.drag_slider:
                self.save_settings()
            self.drag_slider = None
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for name, y in [('text', 260), ('volume', 375)]:
                if pygame.Rect(265, y - 20, 430, 40).collidepoint(event.pos):
                    self.drag_slider = self.focus_slider = name
                    self.slider_value(name, 1 + (event.pos[0] - 280) / 400 * 99)
                    if name == 'volume':
                        self.preview_volume()
                    return True
            for name, rect in self.ui_buttons().items():
                if rect.collidepoint(event.pos):
                    self.save_settings()
                    self.drag_slider = None
                    self.state = 'HELP' if name == 'HELP / TUTORIAL' else 'MENU'
                    self.help_page = 0
        elif event.type == pygame.MOUSEMOTION and self.drag_slider:
            self.slider_value(self.drag_slider, 1 + (event.pos[0] - 280) / 400 * 99)
            if self.drag_slider == 'volume':
                self.preview_volume()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.save_settings()
                self.drag_slider = None
                self.state = 'MENU'
            elif event.key == pygame.K_h:
                self.state = 'HELP'
                self.help_page = 0
            elif event.key == pygame.K_TAB:
                self.focus_slider = 'volume' if self.focus_slider == 'text' else 'text'
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                value = self.text_level if self.focus_slider == 'text' else round(self.volume * 100)
                step = 99 / 8 if self.focus_slider == 'text' else 1
                self.slider_value(self.focus_slider, value + (step if event.key == pygame.K_RIGHT else -step))
                if self.focus_slider == 'volume':
                    self.preview_volume()
                self.save_settings()
        return True

    def settings_button(self, label, rect):
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(self.screen, (29, 35, 49), rect, border_radius=12)
        pygame.draw.rect(self.screen, self.GOLD if hovered or 'HELP' in label else self.MUTED, rect, 2, border_radius=12)
        text = self.font.render(label, True, self.PAPER)
        self.screen.blit(text, text.get_rect(center=rect.center))

    def draw_settings_ui(self):
        self.screen.fill(self.BLACK)
        if self.settings_background:
            self.screen.blit(self.settings_background, (0, 0))
        if self.state == 'HELP':
            # One centered modal, matching the supplied reference.
            if self.menu_background:
                self.screen.blit(self.menu_background, (0, 0))
            shade = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 185))
            self.screen.blit(shade, (0, 0))
            box = pygame.Rect(90, 40, 780, 560)
            pygame.draw.rect(self.screen, (29, 35, 49), box, border_radius=12)
            pygame.draw.rect(self.screen, self.GOLD, box, 3, border_radius=12)
            title = self.title_font.render('HOW TO PLAY', True, self.GOLD)
            self.screen.blit(title, title.get_rect(center=(480, 92)))
            tutorial_font = make_font(self.ui_fonts, 20)
            body = (
                "OBJECTIVE:\n"
                "Investigate your friend's disappearance before time runs out.\n\n"
                "GAME MECHANICS:\n"
                "- Lakas ng Loob: Wrong choices and traps lower your courage.\n"
                "  Reaching 0 results in a Panic Game Over!\n"
                "- Time: Puzzle attempts and travel take time. Reading does not.\n"
                "- Evidence Journal [J]: Review collected clues to choose wisely.\n\n"
                "CONTROLS:\n"
                "- [SPACE / ENTER]: Advance text dialogue\n"
                "- [1, 2, 3]: Answer puzzles and choose investigation routes\n"
                "- [J]: Open or close your Evidence Journal\n"
                "- [R]: Restart after an ending"
            )
            self.draw_lines(body, 130, 150, 700, self.PAPER, tutorial_font)
            hint = tutorial_font.render(
                'Click anywhere or press [ESC] / [SPACE] to close',
                True, self.GOLD)
            self.screen.blit(hint, hint.get_rect(center=(480, 565)))
            return
        if not self.settings_background:
            self.draw_lines('GAME SETTINGS', 300, 90, 500, self.RED)
        for name, y in [('text', 260), ('volume', 375)]:
            value = self.text_level if name == 'text' else round(self.volume * 100)
            label = f'Text: {value}%' if name == 'text' else f'Volume: {value}%'
            surface = self.font.render(label, True, self.PAPER)
            self.screen.blit(surface, surface.get_rect(center=(480, y - 42)))
            pygame.draw.line(self.screen, (58, 51, 48), (280, y), (680, y), 12)
            x = round(280 + (value - 1) / 99 * 400)
            pygame.draw.line(self.screen, self.GOLD, (280, y), (x, y), 12)
            pygame.draw.rect(self.screen, self.GOLD, (x - 10, y - 14, 20, 28), border_radius=4)
            pygame.draw.rect(self.screen, self.INK, (x - 10, y - 14, 20, 28), 2, border_radius=4)
            for number, position in [('1', 280), ('100', 680)]:
                text = self.small_font.render(number, True, self.PAPER)
                self.screen.blit(text, text.get_rect(center=(position, y + 28)))
        for label, rect in self.ui_buttons().items():
            self.settings_button(label, rect)

    def menu_action(self, action: str) -> None:
        if action == 'START':
            self.state = 'CHARACTER'
        elif action == 'MENU':
            self.state = 'SETTINGS'
        elif action == 'QUIT':
            self.running = False
        elif action == 'BACK':
            self.state = 'MENU'
        elif action.startswith('TEXT'):
            self.text_size = max(18, min(26, self.text_size + (1 if action.endswith('+') else -1)))
            self.font = make_font(self.body_fonts, self.text_size)
        elif action == 'CONTRAST':
            self.high_contrast = not self.high_contrast
            self.PAPER = (255, 255, 255) if self.high_contrast else (248, 241, 222)
            self.MUTED = (225, 225, 225) if self.high_contrast else (184, 194, 208)
            self.PANEL = (0, 0, 0) if self.high_contrast else (18, 23, 35)
        elif action.startswith('VOLUME'):
            self.volume = round(max(0, min(1, self.volume + (0.1 if action.endswith('+') else -0.1))), 1)
            if pygame.mixer.get_init():
                pygame.mixer.music.set_volume(self.volume)

    def draw_menu_ui(self) -> None:
        self.screen.fill(self.BLACK)
        if self.state == 'MENU' and self.menu_background:
            self.screen.blit(self.menu_background, (0, 0))
        elif self.state == 'MENU':
            title = self.title_font.render('4:28', True, self.RED)
            self.screen.blit(title, title.get_rect(center=(480, 210)))
        else:
            title = self.title_font.render('GAME SETTINGS', True, self.PAPER)
            self.draw_text('GAME SETTINGS', self.title_font, self.PAPER, title.get_rect(center=(480, 110)).topleft,
                           shadow=True)
            for text, y in [(f'Text size: {self.text_size}', 190),
                            ('Contrast: ' + ('High' if self.high_contrast else 'Normal'), 280),
                            (f'Volume: {round(self.volume * 100)}%', 390)]:
                surface = self.font.render(text, True, self.PAPER)
                self.draw_text(text, self.font, self.PAPER, surface.get_rect(center=(480, y)).topleft, shadow=True)
        for label, rect in self.ui_buttons().items():
            hovered = rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(self.screen, (95, 15, 20) if hovered else (20, 16, 17), rect, border_radius=5)
            pygame.draw.rect(self.screen, self.RED if hovered else self.PAPER, rect, 2, border_radius=5)
            surface = self.font.render(label, True, self.PAPER)
            self.screen.blit(surface, surface.get_rect(center=rect.center))
        hint = 'Click or use [1] [2] [3]' if self.state == 'MENU' else 'Click or use [1]-[6] | ESC: back'
        surface = self.small_font.render(hint, True, self.PAPER)
        self.draw_text(hint, self.small_font, self.PAPER, surface.get_rect(center=(480, 570)).topleft, shadow=True)

    def configure_route(self):
        name = self.characters[self.character_index][0]
        self.player = Player(name=name, character=name)
        self.solved_puzzles.clear()
        self.security_alerted = False
        self.journal_open = False
        self.notice = ''
        self.locations = self.make_locations()
        self.puzzles = self.make_puzzles()
        # The locations and puzzle rules are shared; the perspective is not.
        routes = {
            'Mateo': {
                'opening': [
                    ('SYSTEM', 'Mateo Delos Reyes stops at the missing poster. Lucas, his childhood best friend, stares back from the photograph.'),
                    ('MATEO', 'Hindi... Nagtalo pa kami sa labas ng gate bago siya umalis. Bakit hindi ko siya pinigilan?'),
                    ('STUDENT 1', 'Kalma lang, Mateo. Sobrang bigat na rin ng loob namin para kay Lucas.'),
                    ('SYSTEM', 'Mateo braces a shaking hand against the wall.'),
                    ('MATEO', 'Kasalanan ko ito. Kung sinamahan ko lang sana siya pabalik... nasaan ka na ba, Luke?'),
                ],
                'reaction': 'Alam niya kung saan kami madalas tumambay. Magpakita ka! Hindi ko iiwan si Lucas.',
                'scenes': {
                    'LIBRARY': [('MATEO', 'Dito kami madalas magpuyat para sa exams. Nangako kaming sabay ga-graduate. Nasaan ang iniwan mo, Luke?'), ('SYSTEM', 'Dust covers the empty shelves. An old textbook carries a library stamp.')],
                    'SAN_AGUSTIN': [('MATEO', 'Dito tayo nagpapalipas ng oras pagkatapos ng klase. May krus sa lumang bato, tulad ng nasa card.'), ('SYSTEM', 'The stone trail refers to prisoners and the northern end of Intramuros.')],
                    'FORT_SANTIAGO': [('CARETAKER', 'Ilang linggo na mula nang pumunta rito ang lagi mong kasama, iho. May iniwan siyang sobre para sa magpapatuloy.'), ('MATEO', 'Sul sulat niya ito... Luke, kahit noon naghahanda ka na?')],
                    'ESCOLTA': [('SYSTEM', 'A radio crackles beneath a flickering streetlight.'), ('UNKNOWN NUMBER', 'Masyado kang mapagtiwala, Mateo. Binabantayan ko ang bawat liko mo.'), ('MATEO', 'Galit lang ang gusto mong makuha sa akin. Kailangan kong makinig sa signal, hindi sa iyo.')],
                    'QUIAPO': [('SYSTEM', 'A bright red mark and a bridge note stand out on a cracked wall.'), ('MATEO', 'Gusto kong tumakbo agad kay Lucas. Pero paano kung bitag? Ihahambing ko muna sa mga nauna.')],
                    'STA_CRUZ': [('SYSTEM', 'A Polaroid and cassette wait on a wooden chair in an abandoned shop.'), ('MATEO', 'Hindi pa tapos ang pangako natin, Luke. May tinatago ang litratong ito; kailangan kong makita.')],
                    'WAREHOUSE': [('SYSTEM', 'Inside the damp warehouse, loose cables surround a flickering projector.'), ('MATEO', 'May tao sa malabong larawan. Lucas? Kailangan kong linawin ito bago ako sumugod.'), ('UNKNOWN NUMBER', 'Bumalik ka sa loob ng pader bago sumapit ang liwanag.')],
                },
                'success': [
                    'Sulat ni Lucas at ang blue-black stamp. Totoong bakas ito. Ang krus at lumang bato ay patungo sa San Agustin.',
                    'Fort Santiago. Susundan ko ang ebidensya, hindi ang takot ko.',
                    'Escolta, sa kabilang ilog. Kilala ko ang daan; hawak ko ang sobre ni Lucas.',
                    '94.2 FM: deboto at estero. Quiapo ang susunod, kahit may nagmamanman.',
                    'Pulang tinta at padalos-dalos na sulat. Hindi ito kay Lucas. Sa Sta. Cruz ang tunay na marka.',
                    'Sa liwanag ng buwan, lumitaw ang bodega sa tabi ng estero. Ang cassette ay may tunog malapit sa PLM.',
                    'Buhay si Lucas, nakatali sa PLM courtyard. Ipapadala ko ang recording; hindi ko siya maililigtas sa galit lang.',
                ],
                'failure': 'Huminga ka, Mateo. Hindi mo maitatama ang away ninyo sa padalos-dalos na sagot.',
                'travel': 'Para kay Lucas. Kailangan kong manatiling kalmado.',
                'finale': [('ANTAGONIST', 'You and Lucas found the recordings. You were going to expose me, so I made this into a game.'), ('MATEO', 'Alam ko kung alin ang totoong clue at alin ang itinanim mo. Bitawan mo na siya!')],
                'choices': ['Present the evidence and keep the antagonist talking', 'Surrender the evidence to bargain for Lucas', 'Leave Lucas to search for help outside'],
                'endings': [
                    'Mateo holds back his anger and presents the evidence. Security intervenes and rescues Lucas. Their argument is no longer their last conversation. Mateo finally has the chance to apologize and rebuild their promise.',
                    'Mateo gets Lucas to safety, but the case remains incomplete and the antagonist escapes. His best friend is alive; their relief is shadowed by unanswered questions. An apology is only the beginning of healing.',
                    'Mateo lets desperation replace the evidence-led plan. The antagonist regains control, cutting off his chance to reach Lucas. As the scene fades, Mateo calls his best friend\'s name without an answer.',
                    'At zero Lakas ng Loob, guilt and exhaustion overwhelm Mateo. Every turn recalls their last argument. He can no longer follow the trail, and the search ends before he reaches Lucas.',
                ],
            },
            'Clara': {
                'opening': [
                    ('SYSTEM', 'Clara Gonzales stares at Lucas Valderrama\'s missing poster. Students whisper about their academic rivalry.'),
                    ('CLARA', 'Hindi ko ginawa. Bakit ganyan makatingin ang lahat sa akin?'),
                    ('STUDENT 1', 'Magkalaban kayo sa pinakamataas na parangal. Ikaw raw ang huling kausap niya, Clara?'),
                    ('SYSTEM', 'Clara backs away from the crowd, trying to steady her breathing.'),
                    ('CLARA', 'Kailangan kong mahanap si Lucas. Kung hindi, ako ang pagbibintangan. Walang maniniwala sa akin.'),
                ],
                'reaction': 'May nagtatanim ng ebidensya laban sa akin. Kailangan kong sundan ang trail at patunayan kung sino ang may gawa.',
                'scenes': {
                    'LIBRARY': [('CLARA', 'Dito magsisimula ang laro niya. Hindi sapat ang hinala; kailangan ko ng mapapatunayang ebidensya.'), ('SYSTEM', 'An old textbook and its shelf code interrupt the rows of dusty books.')],
                    'SAN_AGUSTIN': [('SYSTEM', 'Clara examines the stone markings, repeatedly looking over her shoulder.'), ('CLARA', 'Baka may sumusunod. Pero ang simbolo ang susuriin ko, hindi ang bawat anino.')],
                    'FORT_SANTIAGO': [('CARETAKER', 'May sobre para sa taong pinagbintangan ng lahat. Ilang linggo na mula nang pumunta rito ang karibal mo.'), ('CLARA', 'Kahit dito, alam nila ang tsismis. Ano ang tunay na sinasabi ng sobre?')],
                    'ESCOLTA': [('SYSTEM', 'A radio crackles beneath the streetlight.'), ('UNKNOWN NUMBER', 'Akala mo malinis ang pangalan mo, Clara? Konti na lang, sa kulungan ka matatapos.'), ('CLARA', 'Sino ka ba? Hindi ako susuko sa pagbabanta. May malinaw na signal sa ingay na ito.')],
                    'QUIAPO': [('SYSTEM', 'A red note directs Clara toward a bridge.'), ('CLARA', 'Kung may nag-aabang na awtoridad doon, magmumukha akong tumatakas. Susuriin ko ang marka bago sumunod.')],
                    'STA_CRUZ': [('SYSTEM', 'A wooden chair holds a Polaroid and cassette in a deserted shop.'), ('CLARA', 'May kulang sa nakikita ko. Kapag nahanap ko ang nakatagong mensahe, mas malapit ako sa gumawa nito.')],
                    'WAREHOUSE': [('SYSTEM', 'A projector struggles to display an image through loose connections.'), ('CLARA', 'Kailangan ko ng malinaw na recording, hindi isa pang paratang. Ito ang puwedeng sumira sa setup niya.'), ('UNKNOWN NUMBER', 'Bumalik ka sa PLM. Tingnan natin kung sino ang paniniwalaan nila.')],
                },
                'success': [
                    'DS 686 .P6: Philippine history. Nakuha ko ang card at krus. Susuriin ko ang pinagmulan habang sinusundan ang San Agustin clue.',
                    'Ang bilangguan at hilagang lokasyon ay tumuturo sa Fort Santiago. May lohika ang trail.',
                    'Lumang sinehan at kalakalan sa kabilang ilog: Escolta. Mas matibay ito kaysa tsismis.',
                    '94.2 FM. Ang deboto at estero ay tumuturo sa Quiapo. Itatala ko ang recording.',
                    'Pula at minadaling sulat, hindi blue-black. Tinangka akong ilagay sa bridge trap. Sa Sta. Cruz ang tunay na trail.',
                    'Ipinakita ng moonlight ang warehouse location. Itatabi ko rin ang cassette bilang corroborating evidence.',
                    'Nasa PLM courtyard si Lucas. Ipapadala ko ang recording para maimbestigahan ang totoong salarin at ang pag-frame sa akin.',
                ],
                'failure': 'Takot ang humahadlang, Clara. Balikan ang detalye; hindi patunay ang unang hinala.',
                'travel': 'Bawat hakbang ay kailangang may batayan, hindi tsismis.',
                'finale': [('ANTAGONIST', 'Ginamit ko ang rivalry ninyo. Madaling paniwalain silang gusto mong mawala si Lucas.'), ('CLARA', 'Maling tao ang pinagbintangan mo. Hawak ko ang trail ng panlilinlang mo at ang ebidensya kung nasaan si Lucas.')],
                'choices': ['Expose the planted clues and hold the antagonist\'s attention', 'Hand over the evidence for a promise to clear your name', 'Leave the courtyard to defend yourself elsewhere'],
                'endings': [
                    'Clara exposes the frame-up and security rescues Lucas. The evidence identifies the mastermind and clears her name. She faces her academic rival as an ally, no longer letting campus rumors define her.',
                    'Clara helps Lucas escape, but gaps in the evidence allow the mastermind to disappear. Lucas can speak for her, yet the full setup remains unproven. She has saved him, but rebuilding trust will take time.',
                    'Clara abandons the evidence-led confrontation. The antagonist exploits her fear for her reputation and regains control of the scene. Lucas remains beyond her reach, and her account of the truth goes unheard.',
                    'At zero Lakas ng Loob, fear of accusation overwhelms Clara. She stops trusting witnesses and her own deductions. Unable to continue the investigation, she loses the trail before she can rescue Lucas or expose the setup.',
                ],
            },
            'Julian': {
                'opening': [
                    ('SYSTEM', 'Julian Mendoza stands near Lucas Valderrama\'s missing poster, gripping a sketchbook filled with portraits he never showed him.'),
                    ('JULIAN', 'Lagi kitang pinagmamasdan mula sa malayo. Bakit hindi ko sinabi kung gaano ka kahalaga sa akin?'),
                    ('STUDENT 1', 'Madalas silang magkatabi sa library, pero halos hindi nag-uusap.'),
                    ('SYSTEM', 'Julian closes his eyes and grips his bag as a tear falls.'),
                    ('JULIAN', 'Hindi na ako mananahimik. Hahanapin kita, Lucas.'),
                ],
                'reaction': 'Ang linyang iyan ay mula sa librong pinagsasaluhan namin. Sino ka? Bakit mo ginagamit ang alaala namin?',
                'scenes': {
                    'LIBRARY': [('JULIAN', 'Dalawang taon sa parehong mesa. Kabisado ko ang tahimik mong gawi, Lucas. May bakas ka bang iniwan?'), ('SYSTEM', 'Julian searches the dusty shelves near their familiar table.')],
                    'SAN_AGUSTIN': [('JULIAN', 'Naalala ko ang hapong nag-sketch tayo rito. Pamilyar ang mga batong ito.'), ('SYSTEM', 'The cross symbol leads Julian to a historical trail toward a northern fort.')],
                    'FORT_SANTIAGO': [('CARETAKER', 'May iniwang sobre para sa taong nakakakilala sa kanya nang lubusan. Tahimik din siyang dumadaan dito.'), ('JULIAN', 'Alam ng nagpadala ang mga lugar na pinuntahan namin. Pero sino ang nagmamasid?')],
                    'ESCOLTA': [('SYSTEM', 'Static interrupts the silence around an old radio.'), ('UNKNOWN NUMBER', 'Tahimik ka, Julian. Pero hindi siya maililigtas ng pagmamahal na itinatago mo sa mga pahina.'), ('JULIAN', 'Alam niya ang nararamdaman ko? Hindi iyon dahilan para tumigil. Pakikinggan ko ang signal.')],
                    'QUIAPO': [('SYSTEM', 'A red mark points toward a bridge; a smaller mark is almost hidden nearby.'), ('JULIAN', 'Hindi lang kulay ang titingnan ko. May sariling galaw ang sulat ni Lucas.')],
                    'STA_CRUZ': [('SYSTEM', 'Moonlight falls through the old shop window beside a Polaroid and cassette.'), ('JULIAN', 'Konting tiis na lang. May detalye rito na hindi pa lumilitaw sa dilim.')],
                    'WAREHOUSE': [('SYSTEM', 'A faint figure flickers across the warehouse projector screen.'), ('JULIAN', 'Lucas? Hindi sapat na makita lang kita. Aayusin ko ito at hihingi ako ng tulong.'), ('UNKNOWN NUMBER', 'Bumalik ka sa PLM bago ka muling maubusan ng lakas ng loob.')],
                },
                'success': [
                    'Kilala ko ang sulat ni Lucas. May dagdag na selyo na kailangan pang unawain. Ang krus ay humahantong sa San Agustin.',
                    'Fort Santiago ang tinutukoy. Ang alaala ng pag-sketch namin ay tumutulong basahin ang trail.',
                    'Escolta. Alam ng sulat ang mga lugar na pamilyar sa amin; itatabi ko ang sobre.',
                    'Sa 94.2 FM, malinaw ang deboto at estero. Sa Quiapo ang susunod na bakas.',
                    'Wala sa pulang marka ang pamilyar niyang stroke. Peke ito. Ang maliit na genuine mark ay patungo sa Sta. Cruz.',
                    'Lumitaw sa moonlight ang warehouse location. Ang cassette ay may tunog malapit sa PLM. Malapit na, Lucas.',
                    'Buhay si Lucas sa PLM courtyard. Ipapadala ko ang malinaw na recording. Tapos na ang pananahimik ko.',
                ],
                'failure': 'Julian, huwag hayaang takot sa pagkawala niya ang tumakip sa maliliit na detalye.',
                'travel': 'Susundan ko ang mga detalye. Hindi pa huli para kumilos.',
                'finale': [('ANTAGONIST', 'Nakarating ka rin, quiet boy. Lahat ito para sa taong hindi mo masabihang mahal mo?'), ('JULIAN', 'Hindi mo magagamit ang pananahimik ko laban kay Lucas. Hawak ko na ang ebidensya. Hindi ako uurong.')],
                'choices': ['Speak up with the evidence and distract the antagonist', 'Give up the evidence in exchange for Lucas\'s safety', 'Retreat to look for someone who can speak for you'],
                'endings': [
                    'Julian speaks firmly and uses the evidence while security rescues Lucas. He finally steps out of the background and chooses an honest conversation. What Lucas feels in return is his to express; tonight, he is safe.',
                    'Julian reaches Lucas and helps him escape, but incomplete proof leaves the antagonist free. He finally makes himself heard, although fear and unanswered questions linger. Their next conversation must wait until Lucas is ready.',
                    'Julian lets the antagonist take control instead of holding to the evidence. The chance to reach Lucas slips away. His sketchbook remains in his hands as the courtyard fades and the words he prepared go unspoken.',
                    'At zero Lakas ng Loob, Julian is overwhelmed by the thought of losing Lucas. Familiar details become impossible to interpret. He stops following the trail, unable to reach the person he hoped to speak to at last.',
                ],
            },
        }
        route = routes[name]
        self.opening_message = ('Kung gusto mong makita siyang buhay, huwag kang tumawag sa pulis. '
                                'Hanapin mo ang tahimik na libro at makapal na alikabok. Bilisan mo.')
        if name == 'Clara':
            self.opening_message += ' Bago nila madiskubre ang ebidensya sa silid mo.'
        self.backstory = route['opening'] + [
            ('SYSTEM', 'Your phone vibrates. An unknown number sends a message at 4:28 PM.'),
            ('UNKNOWN NUMBER', self.opening_message),
            (name.upper(), route['reaction']),
        ]
        for key, thought in zip(self.locations, route['success']):
            self.locations[key].dialogue = route['scenes'][key]
            self.puzzles[key].success = thought
            self.puzzles[key].failure = route['failure']
            self.puzzles[key].evidence.description = self.puzzles[key].evidence.description.replace("your friend's", "Lucas's").replace('Your friend', 'Lucas')
            if self.puzzles[key].evidence.source == 'MISSING FRIEND':
                self.puzzles[key].evidence.source = 'LUCAS'
            for choice in self.locations[key].choices:
                choice.result += '\n' + name + ': ' + route['travel']
        self.route_finale = [('SYSTEM', 'PLM COURTYARD - Lucas sits restrained as you face the person behind the trail.')] + route['finale']
        self.final_choices = route['choices']
        self.route_endings = dict(zip(('TRUE_ENDING', 'BITTERSWEET_ENDING', 'BAD_ENDING', 'PANIC_ENDING'), route['endings']))

    def character_rect(self):
        sprite = self.character_images[self.character_index]
        return sprite.get_rect(midbottom=(480, 565)) if sprite else pygame.Rect(400, 260, 160, 305)


    def character_buttons(self):
        return {'<': pygame.Rect(260, 350, 60, 60),
                '>': pygame.Rect(640, 350, 60, 60),
                'BACK': pygame.Rect(260, 650, 170, 42),
                'SELECT': pygame.Rect(530, 650, 170, 42)}

    def character_action(self, action):
        if action in ('<', '>'):
            self.character_index = (self.character_index + (1 if action == '>' else -1)) % len(self.characters)
            self.character_info_pinned = False
        elif action == 'BACK':
            self.state = 'MENU'
        elif action == 'SELECT':
            self.configure_route()
            pygame.mixer.music.stop()
            self.stop_ambient()
            self.state = 'BACKSTORY'
            self.dialogue_index = 0
            print("ENTERED BACKSTORY")
            self.play_ambient(self.plm_hallway_ambience)

    def character_event(self, event):
        if event.type == pygame.KEYDOWN:
            actions = {pygame.K_LEFT: '<', pygame.K_RIGHT: '>', pygame.K_ESCAPE: 'BACK', pygame.K_RETURN: 'SELECT'}
            if event.key in actions:
                self.character_action(actions[event.key])
            elif event.key in (pygame.K_SPACE, pygame.K_i):
                self.character_info_pinned = not self.character_info_pinned
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for action, rect in self.character_buttons().items():
                if rect.collidepoint(event.pos):
                    self.character_action(action)
                    return
            self.character_info_pinned = (not self.character_info_pinned) if self.character_rect().collidepoint(event.pos) else False

    def draw_character_selection(self):
        self.screen.fill(self.INK)
        if self.character_background:
            self.screen.blit(self.character_background, (0, 0))
        else:
            self.draw_lines('CHOOSE A CHARACTER', 200, 65, 600, self.RED)
        sprite = self.character_images[self.character_index]
        rect = self.character_rect()
        if sprite:
            self.screen.blit(sprite, rect)
        else:
            pygame.draw.ellipse(self.screen, self.MUTED, rect)
        for label, button in self.character_buttons().items():
            self.settings_button(label, button)
        counter = self.small_font.render(f'{self.character_index + 1} / 3   |   Hover or click for traits', True, self.PAPER)
        pygame.draw.rect(self.screen, self.INK, (270, 615, 420, 26), border_radius=6)
        self.screen.blit(counter, counter.get_rect(center=(480, 628)))

        if self.character_info_pinned or rect.collidepoint(pygame.mouse.get_pos()):
            self.draw_character_profile()

    def draw_character_profile(self):
        profiles = {
            'Mateo': ('Mateo Delos Reyes', 'The Loyal Best Friend',
                      'Lucas is his childhood best friend. They promised to graduate together.'),
            'Clara': ('Clara Gonzales', 'The Academic Rival',
                      'Lucas is her academic rival. His disappearance puts her under suspicion.'),
            'Julian': ('Julian Mendoza', 'The Secret Admirer',
                       'Lucas is his library companion and secret crush. His feelings remain unspoken.'),
        }
        name, traits, _ = self.characters[self.character_index]
        full_name, role, connection = profiles[name]
        abilities = {
            'Mateo': 'Street Familiarity: His familiarity with Intramuros helps him navigate its winding streets.',
            'Clara': 'Analytical Mind: She can regain her focus and reassess the evidence when a deduction goes wrong.',
            'Julian': 'Keen Observation: He notices subtle details that others often overlook.',
        }
        width = 205
        sections = [
            (full_name, self.font, self.GOLD, 8),
            (role, self.small_font, self.MUTED, 4),
            ('TRAITS', self.small_font, self.GOLD, 4),
            (traits, self.small_font, self.PAPER, 4),
            ('CONNECTION TO LUCAS', self.small_font, self.GOLD, 4),
            (connection, self.small_font, self.PAPER, 4),
            ('STRENGTH', self.small_font, self.GOLD, 4),
            (abilities[name], self.small_font, self.PAPER, 0),
        ]
        height = 30 + sum(len(wrap_text(font, text, width)) * font.get_linesize() + gap
                          for text, font, _, gap in sections)
        card = pygame.Rect(710, min(175, 625 - height), 235, height)
        self.panel(card, self.GOLD)
        y = card.y + 15
        for text, font, color, gap in sections:
            y = self.draw_lines(text, card.x + 15, y, width, color, font) + gap
        return card

    def draw(self) -> None:
        if self.state == 'CHOICE_OPENING':
            if self.plm_hallway_two_background:
                self.screen.blit(self.plm_hallway_two_background, (0, 0))
            else:
                self.screen.fill(self.INK)  

            self.draw_hud()
            self.draw_text('THE FIRST CLUE', self.title_font, self.PAPER, (50, 65), shadow=True)
            
            self.panel(pygame.Rect(50, 140, 860, 160), self.GOLD)
            self.draw_lines('UNKNOWN NUMBER - 4:28 PM', 70, 150, 820, self.GOLD, self.small_font)
            self.draw_lines(self.opening_message, 70, 185, 810, self.PAPER)
            
            for index, label in enumerate(['Justo Alberto Auditorium', 'University Activity Center', 'PLM Library']):
                rect = pygame.Rect(70, 335 + index * 95, 820, 65)
                self.panel(rect, self.MUTED)
                self.draw_lines(f'[{index + 1}] {label}', 95, rect.y + 18, 760, self.PAPER)
            self.draw_lines('Saan kaya ito? Click a location or press 1, 2, or 3.',
                            70, 650, 820, self.MUTED, self.small_font, shadow=True)
            if self.journal_open:
                self.draw_journal()
            pygame.display.flip()
            return
        if self.state == 'CHARACTER':
            self.draw_character_selection()
            pygame.display.flip()
            return
        if self.state in ('SETTINGS', 'HELP'):
            self.draw_settings_ui()
            pygame.display.flip()
            return
        if self.state in ('MENU', 'SETTINGS'):
            self.draw_menu_ui()
            pygame.display.flip()
            return
        if self.state == "TEASER":
            self.draw_teaser()
        elif self.state == "MENU":
            if not self.menu_music_started:
                self.play_menu_music()
                self.menu_music_started = True
            self.screen.fill(self.BLACK)
            self.draw_text("4:28", self.title_font, self.RED, (380, 150), shadow=True)
            self.draw_lines("A fictional investigation RPG set around PLM and Intramuros. All characters and events are fictional.",
                            230, 235, 550, self.MUTED, shadow=True)
            self.draw_text("[1] START INVESTIGATION", self.font, self.PAPER, (345, 330), shadow=True)
            self.draw_text("[ESC] quit", self.small_font, self.MUTED, (420, 380), shadow=True)
        elif self.state == "CHARACTER":
            self.screen.fill(self.INK)
            self.draw_text("CHOOSE YOUR CHARACTER", self.title_font, self.PAPER, (150, 130), shadow=True)
            self.draw_text("[1] Silhouette A", self.font, self.GOLD, (350, 280))
            self.draw_text("[2] Silhouette B", self.font, self.GOLD, (350, 330))
        elif self.state in {"INTRO", "BACKSTORY", *self.locations, "FINALE"}:
            self.draw_dialogue()
        elif self.state.startswith("PUZZLE_"):
            self.draw_puzzle()
        elif self.state.startswith("CHOICE_") or self.state == "FINAL_CHOICE":
            self.draw_choice()
        elif self.state == "NOTICE":
            # show the next location bg
            if self.next_after_notice in {"CHOICE_OPENING", "INTRAMUROS"} and self.plm_hallway_two_background:
                self.screen.blit(self.plm_hallway_two_background, (0, 0))
            elif self.next_after_notice in {"LIBRARY", "CHOICE_LIBRARY", "PUZZLE_LIBRARY"} and self.library_background:
                self.screen.blit(self.library_background, (0, 0))
            elif self.next_after_notice in {"SAN_AGUSTIN", "CHOICE_SAN_AGUSTIN", "PUZZLE_SAN_AGUSTIN"} and self.san_agustin_background:
                self.screen.blit(self.san_agustin_background, (0, 0))
            elif self.next_after_notice in {"FORT_SANTIAGO", "CHOICE_FORT_SANTIAGO", "PUZZLE_FORT_SANTIAGO"} and self.fort_santiago_background:
                self.screen.blit(self.fort_santiago_background, (0, 0))
            elif self.next_after_notice in {"ESCOLTA", "CHOICE_ESCOLTA", "PUZZLE_ESCOLTA"} and self.escolta_background:
                print("NEXT LOCATION:", self.next_after_notice)
                self.screen.blit(self.escolta_background, (0, 0))
            elif self.next_after_notice in {"QUIAPO", "CHOICE_QUIAPO", "PUZZLE_QUIAPO"} and self.quiapo_background:
                self.screen.blit(self.quiapo_background, (0, 0))
            elif self.next_after_notice in {"STA_CRUZ", "CHOICE_STA_CRUZ", "PUZZLE_STA_CRUZ"} and self.stacruz_background:
                self.screen.blit(self.stacruz_background, (0, 0))
            elif self.next_after_notice in {"WAREHOUSE", "CHOICE_WAREHOUSE", "PUZZLE_WAREHOUSE"} and self.warehouse_background:
                self.screen.blit(self.warehouse_background, (0, 0))
            elif self.next_after_notice in {"FINALE", "CHOICE_FINALE"} and self.plm_courtyard_background:
                self.screen.blit(self.plm_courtyard_background, (0, 0))
            else:
                self.screen.fill(self.INK)
            self.draw_hud()
            self.panel(pygame.Rect(90, 115, 780, 540), self.GOLD)
        
            title_surface = self.title_font.render("RESULT", True, self.GOLD)
            title_x = (self.WIDTH - title_surface.get_width()) // 2
            self.screen.blit(title_surface, (title_x, 135))
            
            self.draw_lines(self.notice, 120, 220, 720, self.PAPER)
            continue_surface = self.small_font.render("[SPACE] continue", True, self.MUTED)
            continue_x = 865 - continue_surface.get_width()
            self.screen.blit(continue_surface, (continue_x, 620))
        else:
            self.draw_ending()
        if self.journal_open:
            self.draw_journal()
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            self.update()
            self.draw()
            self.clock.tick(60)
        self.finish_teaser()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    InvestigationGame().run()
