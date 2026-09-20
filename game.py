"""4:28 - investigation RPG starter

Install once:  py -m pip install pygame-ce
Run:           py game.py

Controls:
  SPACE / ENTER - advance dialogue or confirm a choice
  1, 2, 3       - choose an option
  J             - open/close the evidence journal
  ESC           - return from a menu / quit

This file deliberately uses simple Pygame drawing first.  Your group can later
replace the coloured scene backgrounds with images in assets/ without changing
the game logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable
import sys
from pathlib import Path
import math
try:
    import cv2
except ImportError:
    cv2 = None
import pygame


# ---------------------------------------------------------------------------
# Data classes: these are the "objects" your OOP subject wants to see.


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


class InvestigationGame:
    WIDTH, HEIGHT = 960, 640
    BLACK = (11, 13, 20)
    INK = (20, 24, 35)
    PANEL = (28, 34, 49)
    PAPER = (234, 229, 212)
    RED = (213, 70, 74)
    GOLD = (235, 186, 78)
    MUTED = (157, 169, 188)

    def __init__(self) -> None:
        # Ask Pygame for a predictable sound format before it starts.
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("4:28 - An Investigation RPG")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 21)
        self.small_font = pygame.font.SysFont("consolas", 16)
        self.title_font = pygame.font.SysFont("georgia", 52, bold=True)
        self.text_size = 21
        self.volume = 0.7
        self.high_contrast = False
        self.menu_background = None
        background_path = Path(__file__).resolve().parent / 'assets/backgrounds/menu_background.png'
        if background_path.exists():
            self.menu_background = pygame.transform.smoothscale(
                pygame.image.load(str(background_path)).convert(), (self.WIDTH, self.HEIGHT))
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
            ("SYSTEM", "PLM HALLWAY - A missing-person poster trembles on a bulletin board."),
            ("STUDENT 1", "Kahapon pa siya nawawala. Wala pa ring balita..."),
            ("STUDENT REPORTER", "The last confirmed sighting was exactly 4:28 PM yesterday, near Intramuros."),
            ("SYSTEM", "Your phone vibrates. A message from an unknown number appears."),
            ("UNKNOWN NUMBER", "Kung gusto mong makita siyang buhay, huwag kang tumawag sa pulis. Hanapin mo ang tahimik na libro at makapal na alikabok. Bilisan mo."),
        ]

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

    def finish_teaser(self) -> None:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
        self.state = "BACKSTORY"
        self.dialogue_index = 0

    def update(self) -> None:
        if self.state != "TEASER":
            return
        if self.video_capture is None:
            self.finish_teaser()
            return
        # Use elapsed time, not frame-by-frame delays, to prevent audio drift.
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
                    Choice("Travel to San Agustin Church", "The cross symbol leads you deeper into Intramuros.", "SAN_AGUSTIN", 0, 20),
                    Choice("Search the University Activity Center", "You find no matching symbol and return to the library.", "LIBRARY", -5, 25),
                    Choice("Go to Justo Alberto Auditorium", "The empty seats offer no clue. You return uneasy.", "LIBRARY", -10, 25),
                ],
            ),
            "SAN_AGUSTIN": Location(
                "SAN_AGUSTIN", "SAN AGUSTIN", (69, 54, 47),
                [("PLAYER", "The old stones carry a symbol matching the library stamp."),
                 ("SYSTEM", "The clue points to a place connected to prisoners and the northern end of Intramuros.")],
                [
                    Choice("Travel to Fort Santiago", "You follow the historical trail toward the northern end of Intramuros.", "FORT_SANTIAGO", 0, 20),
                    Choice("Head to Manila Cathedral", "The architecture is familiar, but the symbols do not match.", "SAN_AGUSTIN", -5, 30),
                    Choice("Follow a stranger's shortcut", "A dead end. The sender knows you are wasting time.", "SAN_AGUSTIN", -10, 35),
                ],
            ),
            "FORT_SANTIAGO": Location(
                "FORT_SANTIAGO", "FORT SANTIAGO", (60, 69, 56),
                [("CARETAKER", "Your friend left an envelope for whoever kept looking."),
                 ("PLAYER", "Inside is a clue about old cinemas, art, and trade across the river.")],
                [
                    Choice("Cross the river to Escolta", "As sunset falls, an old radio begins playing by itself.", "ESCOLTA", 0, 30),
                    Choice("Search Luneta", "You find nothing except crowds and lost time.", "FORT_SANTIAGO", -5, 40),
                    Choice("Return to PLM", "It is too early to return; the trail is still outside the walls.", "FORT_SANTIAGO", -5, 35),
                ],
            ),
            "ESCOLTA": Location(
                "ESCOLTA", "ESCOLTA - NIGHT", (42, 44, 73),
                [("SYSTEM", "A radio crackles beneath a flickering streetlight."),
                 ("UNKNOWN NUMBER", "Masyado kang mapagtiwala. Binabantayan ko ang bawat liko mo."),
                 ("PLAYER", "The next message mentions devotees, candles, and alleys beside an estero.")],
                [
                    Choice("Follow the signal to Quiapo", "The signal stops, but its direction is clear.", "QUIAPO", 0, 25),
                    Choice("Follow the radio into an alley", "The radio was bait. You return shaken.", "ESCOLTA", -10, 30),
                    Choice("Travel to Taft", "The description does not fit. You lose precious time.", "ESCOLTA", -5, 45),
                ],
            ),
            "QUIAPO": Location(
                "QUIAPO", "QUIAPO", (74, 45, 43),
                [("PLAYER", "A red mark is painted on a cracked wall beside a note about a bridge."),
                 ("SYSTEM", "Compare it with the ink on your earlier clues before you decide.")],
                [
                    Choice("Follow the genuine mark to Sta. Cruz", "You bypass the bridge trap and move before the sender can react.", "STA_CRUZ", 0, 20),
                    Choice("Go to the bridge", "Bitag iyon. Nakatakas ka, ngunit nabawasan ang iyong Lakas ng Loob.", "QUIAPO", -20, 50),
                    Choice("Ask random vendors for the sender", "Nobody can identify the sender. The search costs time.", "QUIAPO", -5, 30),
                ],
            ),
            "STA_CRUZ": Location(
                "STA_CRUZ", "STA. CRUZ", (54, 59, 68),
                [("PLAYER", "In an old shop, a Polaroid and cassette wait on a wooden chair."),
                 ("SYSTEM", "Moonlight reveals invisible ink: an old warehouse beside the estero.")],
                [
                    Choice("Follow the hidden message to the warehouse", "The cassette's traffic sounds grow louder near the estero.", "WAREHOUSE", 0, 25),
                    Choice("Search an abandoned church", "No trace of your friend. The sender's clock keeps moving.", "STA_CRUZ", -10, 40),
                    Choice("Return to Escolta", "You only find the dead radio again.", "STA_CRUZ", -5, 45),
                ],
            ),
            "WAREHOUSE": Location(
                "WAREHOUSE", "OLD WAREHOUSE", (43, 42, 45),
                [("SYSTEM", "A projector flickers on. Your friend is alive - tied up in the PLM courtyard."),
                 ("UNKNOWN NUMBER", "Bumalik ka sa loob ng pader bago sumapit ang liwanag."),
                 ("PLAYER", "The cassette confirms it. The final location is PLM.")],
                [
                    Choice("Return to PLM with the evidence", "You run toward Intramuros before dawn.", "FINALE", 0, 35),
                    Choice("Wait for help", "Waiting feels safe, but the message's deadline does not stop.", "WAREHOUSE", -15, 55),
                    Choice("Go back to Quiapo", "The old false trail costs nearly an hour.", "WAREHOUSE", -10, 60),
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
        self.state = "BACKSTORY"
        self.dialogue_index = 0
        self.notice = ""
        self.journal_open = False
        self.solved_puzzles.clear()
        self.security_alerted = False

    def current_dialogue(self) -> list[tuple[str, str]]:
        if self.state == "BACKSTORY":
            return self.backstory
        if self.state in self.locations:
            return self.locations[self.state].dialogue
        if self.state == "FINALE":
            return [
                ("SYSTEM", "PLM COURTYARD - 4:28 AM. Your hidden alert has reached campus security. You have one last chance."),
                ("ANTAGONIST", "You and your friend found the recordings. You were going to expose me, so I made this into a game."),
                ("PLAYER", "I know which clues were yours, which were planted, and where you were watching from."),
                ("SYSTEM", "The security team has your location and the projector recording. Keep the antagonist talking."),
            ]
        return []

    def advance_dialogue(self) -> None:
        dialogue = self.current_dialogue()
        self.dialogue_index += 1
        if self.dialogue_index < len(dialogue):
            return
        self.dialogue_index = 0
        if self.state == "BACKSTORY":
            self.state = "MENU"
        elif self.state in self.locations:
            # A solved puzzle stays solved if the player returns after a wrong route.
            if self.state in self.solved_puzzles:
                self.state = f"CHOICE_{self.state}"
            else:
                self.state = f"PUZZLE_{self.state}"
        elif self.state == "FINALE":
            self.state = "FINAL_CHOICE"

    def solve_puzzle(self, index: int) -> None:
        """Check an investigation puzzle, then unlock that location's travel choices."""
        location_key = self.state.removeprefix("PUZZLE_")
        puzzle = self.puzzles[location_key]
        if index == puzzle.correct_index:
            self.solved_puzzles.add(location_key)
            self.player.change_composure(5)
            self.player.spend_time(10)
            self.notice = puzzle.success
            if self.player.add_evidence(puzzle.evidence.name, puzzle.evidence.description, puzzle.evidence.source):
                self.notice += f"\nEvidence added: {puzzle.evidence.name}\nLakas ng Loob +5"
            if location_key == "WAREHOUSE":
                self.security_alerted = True
                self.notice += "\nYou secretly send the projector recording and PLM location to campus security."
            self.next_after_notice = f"CHOICE_{location_key}"
            self.state = "NOTICE"
        else:
            self.player.change_composure(-5)
            self.player.spend_time(10)
            if self.check_lakas_ng_loob():
                return
            self.notice = f"{puzzle.failure}\nLakas ng Loob -5. Time passes."
            self.next_after_notice = self.state
            self.state = "NOTICE"

    def choose(self, index: int) -> None:
        if self.state == "FINAL_CHOICE":
            self.finish(index)
            return
        source = self.state.removeprefix("CHOICE_")
        location = self.locations[source]
        if index >= len(location.choices):
            return
        choice = location.choices[index]
        self.player.change_composure(choice.composure_change)
        self.player.spend_time(choice.time_cost)
        if self.check_lakas_ng_loob():
            return
        self.notice = choice.result
        if choice.evidence and self.player.add_evidence(choice.evidence.name, choice.evidence.description):
            self.notice += f"\nEvidence added: {choice.evidence.name}"
        self.state = "NOTICE"
        self.next_after_notice = choice.next_state

    def check_lakas_ng_loob(self) -> bool:
        """End the run immediately when fear and exhaustion overwhelm the player."""
        if self.player.composure <= 0:
            self.state = "PANIC_ENDING"
            self.journal_open = False
            return True
        return False

    def finish(self, index: int) -> None:
        has_key_evidence = len(self.player.evidence) >= 5
        if index == 0 and has_key_evidence and self.security_alerted and self.player.composure >= 25 and self.player.time_minutes < 720:
            self.state = "TRUE_ENDING"
        elif index == 0:
            self.state = "BITTERSWEET_ENDING"
        else:
            self.state = "BAD_ENDING"

    def handle_event(self, event: pygame.event.Event) -> None:
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
            elif event.key == pygame.K_ESCAPE:
                self.running = False
        elif self.state == "CHARACTER":
            if event.key in (pygame.K_1, pygame.K_2):
                self.player.character = "Silhouette A" if event.key == pygame.K_1 else "Silhouette B"
                # The player has already seen the opening message before the menu.
                # Start the first investigation after selecting a character.
                self.state = "LIBRARY"
                self.dialogue_index = 0
            elif event.key == pygame.K_ESCAPE:
                self.state = "MENU"
        elif self.state in {"BACKSTORY", *self.locations, "FINALE"}:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.advance_dialogue()
        elif self.state.startswith("PUZZLE_"):
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                self.solve_puzzle(event.key - pygame.K_1)
        elif self.state.startswith("CHOICE_") or self.state == "FINAL_CHOICE":
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                self.choose(event.key - pygame.K_1)
        elif self.state == "NOTICE":
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.state = self.next_after_notice
                self.dialogue_index = 0
        elif self.state.endswith("ENDING") and event.key == pygame.K_r:
            self.reset()

    def panel(self, rect: pygame.Rect, border: tuple[int, int, int] | None = None) -> None:
        pygame.draw.rect(self.screen, self.PANEL, rect, border_radius=10)
        pygame.draw.rect(self.screen, border or self.MUTED, rect, 2, border_radius=10)

    def draw_lines(self, text: str, x: int, y: int, width: int, color: tuple[int, int, int], font: pygame.font.Font | None = None) -> int:
        used_font = font or self.font
        for line in wrap_text(used_font, text, width):
            self.screen.blit(used_font.render(line, True, color), (x, y))
            y += used_font.get_linesize()
        return y

    def draw_hud(self) -> None:
        pygame.draw.rect(self.screen, (8, 10, 16), (0, 0, self.WIDTH, 52))
        left = f"LAKAS NG LOOB: {self.player.composure:03d}"
        center = f"TIME: {clock_text(self.player.time_minutes)}"
        right = f"EVIDENCE: {len(self.player.evidence)}   [J] JOURNAL"
        self.screen.blit(self.small_font.render(left, True, self.RED if self.player.composure < 35 else self.PAPER), (20, 18))
        self.screen.blit(self.small_font.render(center, True, self.GOLD), (410, 18))
        self.screen.blit(self.small_font.render(right, True, self.MUTED), (670, 18))

    def draw_teaser(self) -> None:
        self.screen.fill((0, 0, 0))
        if self.video_frame is not None:
            self.screen.blit(self.video_frame, self.video_frame.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2)))
        prompt = self.small_font.render("[SPACE] skip teaser", True, self.PAPER)
        self.screen.blit(prompt, prompt.get_rect(bottomright=(self.WIDTH - 24, self.HEIGHT - 20)))

    def draw_dialogue(self) -> None:
        dialogue = self.current_dialogue()
        title = "PLM HALLWAY" if self.state == "BACKSTORY" else self.locations[self.state].title if self.state in self.locations else "PLM COURTYARD"
        color = self.locations[self.state].color if self.state in self.locations else (47, 35, 42)
        self.screen.fill(color)
        # A simple silhouette. Replace later with sprite images if desired.
        pygame.draw.ellipse(self.screen, self.INK, (115, 150, 150, 180))
        pygame.draw.rect(self.screen, self.INK, (145, 285, 90, 180), border_radius=30)
        self.draw_hud()
        self.screen.blit(self.title_font.render(title, True, self.PAPER), (40, 78))
        self.panel(pygame.Rect(45, 445, 870, 160), self.GOLD)
        speaker, text = dialogue[self.dialogue_index]
        self.screen.blit(self.font.render(speaker, True, self.GOLD), (70, 470))
        self.draw_lines(text, 70, 505, 820, self.PAPER)
        self.screen.blit(self.small_font.render("[SPACE] continue", True, self.MUTED), (745, 575))

    def draw_choice(self) -> None:
        if self.state == "FINAL_CHOICE":
            source = "FINALE"
        else:
            source = self.state.removeprefix("CHOICE_")
        self.screen.fill(self.INK)
        self.draw_hud()
        if source == "FINALE":
            title = "FINAL DECISION"
            choices = [
                "Use the evidence and distract the antagonist",
                "Plead and surrender",
                "Run away to find help",
            ]
        else:
            title = self.locations[source].title
            choices = [choice.label for choice in self.locations[source].choices]
        self.screen.blit(self.title_font.render(title, True, self.PAPER), (45, 100))
        self.draw_lines("Choose carefully. Choices cost time and affect your Lakas ng Loob; they are not forced retries.", 48, 180, 840, self.MUTED)
        for index, label in enumerate(choices):
            rect = pygame.Rect(70, 255 + index * 100, 820, 75)
            # Every route must look equally possible.  Never highlight option 1,
            # because that would accidentally reveal the intended route.
            self.panel(rect, self.MUTED)
            self.draw_lines(f"[{index + 1}] {label}", 95, rect.y + 16, 760, self.PAPER)

    def draw_puzzle(self) -> None:
        """Draw a dedicated puzzle screen instead of treating it as ordinary dialogue."""
        location_key = self.state.removeprefix("PUZZLE_")
        puzzle = self.puzzles[location_key]
        color = self.locations[location_key].color
        self.screen.fill(color)
        self.draw_hud()
        self.screen.blit(self.title_font.render("INVESTIGATION", True, self.PAPER), (45, 78))
        self.screen.blit(self.font.render(puzzle.title, True, self.GOLD), (50, 155))
        self.draw_lines(puzzle.prompt, 50, 190, 840, self.PAPER)
        for index, option in enumerate(puzzle.options):
            rect = pygame.Rect(70, 285 + index * 95, 820, 70)
            self.panel(rect, self.MUTED)
            self.draw_lines(f"[{index + 1}] {option}", 95, rect.y + 14, 760, self.PAPER)
        self.screen.blit(self.small_font.render("Solve the clue. A wrong answer costs 10 minutes and 5 Lakas ng Loob.", True, self.MUTED), (185, 590))

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
        self.screen.blit(self.small_font.render("[J] or [ESC] close journal", True, self.INK), (570, 550))

    def draw_ending(self) -> None:
        endings = {
            "TRUE_ENDING": ("TRUE ENDING", "Your evidence exposes the planted clues. Because you sent the projector recording, campus security reaches the courtyard in time and rescues your friend."),
            "BITTERSWEET_ENDING": ("BITTERSWEET ENDING", "You reach your friend, but missing evidence leaves gaps in the case. The antagonist disappears before the full truth can be proven."),
            "BAD_ENDING": ("TRAGIC ENDING", "The wrong final move gives the antagonist control. The screen fades just before dawn."),
            "PANIC_ENDING": ("GAME OVER - LOST IN THE DARK", "Your Lakas ng Loob reaches zero. Fear and exhaustion overwhelm you; you lose your direction, stop trusting the clues, and the trail goes cold before you can reach your friend."),
        }
        title, description = endings[self.state]
        self.screen.fill((32, 15, 21))
        title_surface = self.title_font.render(title, True, self.RED)
        self.screen.blit(title_surface, title_surface.get_rect(center=(self.WIDTH // 2, 205)))
        self.draw_lines(description, 170, 285, 620, self.PAPER)
        self.screen.blit(self.font.render("[R] Restart", True, self.GOLD), (400, 450))

    def ui_buttons(self) -> dict:
        if self.state == 'MENU':
            return {label: pygame.Rect(340, 340 + index * 68, 280, 52)
                    for index, label in enumerate(['START', 'MENU', 'QUIT'])}
        return {
            'TEXT -': pygame.Rect(260, 220, 180, 48),
            'TEXT +': pygame.Rect(520, 220, 180, 48),
            'CONTRAST': pygame.Rect(340, 300, 280, 48),
            'VOLUME -': pygame.Rect(260, 420, 180, 48),
            'VOLUME +': pygame.Rect(520, 420, 180, 48),
            'BACK': pygame.Rect(380, 510, 200, 48),
        }

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
            self.text_size = max(18, min(23, self.text_size + (1 if action.endswith('+') else -1)))
            self.font = pygame.font.SysFont('consolas', self.text_size)
        elif action == 'CONTRAST':
            self.high_contrast = not self.high_contrast
            self.PAPER = (255, 255, 255) if self.high_contrast else (234, 229, 212)
            self.MUTED = (225, 225, 225) if self.high_contrast else (157, 169, 188)
            self.PANEL = (0, 0, 0) if self.high_contrast else (28, 34, 49)
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
            self.screen.blit(title, title.get_rect(center=(480, 110)))
            for text, y in [(f'Text size: {self.text_size}', 190),
                            ('Contrast: ' + ('High' if self.high_contrast else 'Normal'), 280),
                            (f'Volume: {round(self.volume * 100)}%', 390)]:
                surface = self.font.render(text, True, self.PAPER)
                self.screen.blit(surface, surface.get_rect(center=(480, y)))
        for label, rect in self.ui_buttons().items():
            hovered = rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(self.screen, (95, 15, 20) if hovered else (20, 16, 17), rect, border_radius=5)
            pygame.draw.rect(self.screen, self.RED if hovered else self.PAPER, rect, 2, border_radius=5)
            surface = self.font.render(label, True, self.PAPER)
            self.screen.blit(surface, surface.get_rect(center=rect.center))
        hint = 'Click or use [1] [2] [3]' if self.state == 'MENU' else 'Click or use [1]-[6] | ESC: back'
        surface = self.small_font.render(hint, True, self.PAPER)
        self.screen.blit(surface, surface.get_rect(center=(480, 570)))

    def draw(self) -> None:
        if self.state in ('MENU', 'SETTINGS'):
            self.draw_menu_ui()
            pygame.display.flip()
            return
        if self.state == "TEASER":
            self.draw_teaser()
        elif self.state == "MENU":
            self.screen.fill(self.BLACK)
            self.screen.blit(self.title_font.render("4:28", True, self.RED), (380, 150))
            self.draw_lines("A fictional investigation RPG set around PLM and Intramuros. All characters and events are fictional.", 230, 235, 550, self.MUTED)
            self.screen.blit(self.font.render("[1] START INVESTIGATION", True, self.PAPER), (345, 330))
            self.screen.blit(self.small_font.render("[ESC] quit", True, self.MUTED), (420, 380))
        elif self.state == "CHARACTER":
            self.screen.fill(self.INK)
            self.screen.blit(self.title_font.render("CHOOSE YOUR CHARACTER", True, self.PAPER), (150, 130))
            self.screen.blit(self.font.render("[1] Silhouette A", True, self.GOLD), (350, 280))
            self.screen.blit(self.font.render("[2] Silhouette B", True, self.GOLD), (350, 330))
        elif self.state in {"BACKSTORY", *self.locations, "FINALE"}:
            self.draw_dialogue()
        elif self.state.startswith("PUZZLE_"):
            self.draw_puzzle()
        elif self.state.startswith("CHOICE_") or self.state == "FINAL_CHOICE":
            self.draw_choice()
        elif self.state == "NOTICE":
            self.screen.fill(self.INK)
            self.draw_hud()
            self.panel(pygame.Rect(110, 190, 740, 250), self.GOLD)
            self.screen.blit(self.title_font.render("RESULT", True, self.GOLD), (355, 225))
            self.draw_lines(self.notice, 155, 310, 650, self.PAPER)
            self.screen.blit(self.small_font.render("[SPACE] continue", True, self.MUTED), (625, 400))
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
