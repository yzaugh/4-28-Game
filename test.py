import pygame
import sys
import os

# 1. Initialize Pygame-ce
pygame.init()
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("4:28")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (40, 40, 40)
RED = (200, 50, 50)

# Fonts
font = pygame.font.SysFont(None, 24)
title_font = pygame.font.SysFont(None, 48)

# Game State & Variables
game_state = "BACKSTORY"  # Starts with Sequence #1 backstory before the Menu
player_hp = 100
backstory_dialogue = 0
current_dialogue = 0
library_dialogue = 0
san_agustin_dialogue = 0
fort_santiago_dialogue = 0
escolta_dialogue = 0
quiapo_dialogue = 0
sta_cruz_dialogue = 0
bodega_dialogue = 0
climax_dialogue = 0

# Character Selection Tracking
selected_character = "Black Figure A"

# Sequence #1 Backstory Script (Before Menu)
backstory_script = [
    {"speaker": "Scene", "text": "INT. PLM (PAMANTASAN NG LUNGSOD NG MAYNILA) - HALLWAY"},
    {"speaker": "System", "text": "(Close-up shot of a missing poster pinned to a bulletin board inside PLM, bearing the face of a student.)"},
    {"speaker": "Student 1", "text": "“Ilang linggo nang nawawala ‘yan...”"},
    {"speaker": "Student 2", "text": "“Sabi, huli daw nakita ‘yan sa labas ng gate ng PLM eh...”"},
    {"speaker": "Student 3", "text": "“Grabe, hanggang ngayon ba wala pa ring balita? Nakakatakot na pumasok nang gabi rito.”"},
    {"speaker": "Student Reporter (Audio)", "text": "“...Isang linggo na ang lumipas mula nang ianunsyo ang pagkawala ng ating kapwa-estudyante... at exactly 4:28 when he was last seen near the vicinity of Intramuros before completely vanishing into thin air...”"},
    {"speaker": "System", "text": "(The radio audio fades out slowly, leaving an eerie silence in the hallway.)"}
]

# Story Script (Sequence #2 to #3)
script = [
    {"speaker": "Player", "text": "“Kawawa naman, ano kaya nangyari..”"},
    {"speaker": "System", "text": "*ting!* (Isang mensahe ang pumasok mula sa unknown number...)"},
    {"speaker": "Unknown Number (4:28)", "text": "“Kung hinahanap mo ako, puntahan mo ang silid ng mga tahimik na libro at makapal na alikabok, sa ilalim ng lumang selyo. Bilisan mo.”"},
    {"speaker": "Player", "text": "?!?!?!?!? \nAno to??!?!?"}
]

# Library Scene Script (Sequence #6)
library_script = [
    {"speaker": "Player", "text": "“Tahimik na libro? Saan kaya to”"},
    {"speaker": "System", "text": "Binabati kita! Nahanap mo ang unang clue. (+5 HP)"},
    {"speaker": "Notebook", "text": "“Sundan mo ang mga piyesa ng lumang bato na may krus— doon sa simbahan kung saan nagsimula ang kasaysayan sa loob ng pader.”"}
]

# San Agustin Scene Script (Sequence #7)
san_agustin_script = [
    {"speaker": "Player", "text": "“San kaya dito?”"},
    {"speaker": "System", "text": "Binabati kita! Nahanap mo ang pangalawang clue. Ngayon, pumili ka na... (+5 HP)"},
    {"speaker": "Pamphlet", "text": "“Hindi lang ito basta lumang bato. Dito dumaan ang mga binihag noon bago dalhin sa dulo ng hilaga kung saan nakakulong ang pangarap ng ating bayani.”"}
]

# Fort Santiago Scene Script (Sequence #8)
fort_santiago_script = [
    {"speaker": "NPC", "text": "“Ilang linggo na ang lumipas simula nang huling pumunta rito ang batang hinahanap mo.”"},
    {"speaker": "Player", "text": "“May iniwan ba siyang mensahe?”"},
    {"speaker": "NPC", "text": "“Meron. Sabi niya, ibigay ko raw ito sa maghahanap sa kanya... Heto oh. Ingat ka, bata.”"},
    {"speaker": "System", "text": "Binabati kita! Nahanap mo ang pangatlong clue. (+5 HP)"},
    {"speaker": "Envelope", "text": "“Nalampasan mo ang loob ng pader, pero malayo pa ang tatahakin mo. Tumawid ka sa ilog kung saan nakatayo ang mga lumang gusali ng sining, sinehan, at kalakalan noong nakaraan.”"}
]

# Escolta Scene Script (Sequence #9)
escolta_script = [
    {"speaker": "Player", "text": "“Escolta… sarado na ang lahat. Nasaan na naman kaya ang susunod na iniwan nya?”"},
    {"speaker": "Player", "text": "“Huh??” \n“Ano yun”"},
    {"speaker": "Unknown Number", "text": "“Masyado kang mapagtiwala... Binabantayan ko ang bawat liko mo. Ingat, isang maling liko maaaring buhay ang kapalit..”"},
    {"speaker": "Player", "text": "“Sino ka ba?!?!? Magpakita ka!”"},
    {"speaker": "System", "text": "Binabati kita! Nahanap mo ang ikaapat na clue. Ngunit mag-ingat ka... (+5 HP)"}
]

# Quiapo Scene Script (Sequence #10)
quiapo_script = [
    {"speaker": "Player", "text": "“Quiapo… Ang sikip. Ang dilim. Kung nasaan ang mga deboto, malamang nandito rin ang sumusunod sa akin.”"},
    {"speaker": "Player", "text": "“Teka... Parang iba ang kulay at sulat nito. Hindi ito katulad ng mga naunang clue.”"},
    {"speaker": "Unknown Number", "text": "“Magaling kang sumunod. Pero tingnan mo kung saan ka dinadala ng mga pekeng bakas... Subukan mong lumakad sa bitag ko.”"},
    {"speaker": "Player", "text": "“Alam niyang sinusuri ko ang marka... Pinaglalaruan niya lang ako!”"},
    {"speaker": "System", "text": "Babala: Ang markang ito ay isang patibong mula sa taong nagmamanman sa iyo! Huwag itong sundin. (+0 HP)"}
]

# Sta. Cruz Scene Script (Sequence #11)
sta_cruz_script = [
    {"speaker": "Player", "text": "“Sta. Cruz… Ang tahimik. Mas nakakapanibago kaysa sa ingay ng Quiapo. Kailangan ko nang matapos ito.”"},
    {"speaker": "Player", "text": "“Isang polaroid at cassette tape... Para saan naman to?”"},
    {"speaker": "Unknown Number", "text": "“Magaling kang umabot dito. Pero may isa pang silid bago mo ako abutan. Huwag kang maliligaw.”"},
    {"speaker": "System", "text": "Binabati kita! Nahanap mo ang clue sa Sta. Cruz. Magpatuloy ka sa susunod na lokasyon. (+10 HP)"}
]

# Bodega Scene Script (Sequence #12)
bodega_script = [
    {"speaker": "Player", "text": "“Anong klaseng lugar ito... Amoy kalawang at sirang papel. Nasaan na naman kaya ang sunod niyang naiwan?”"},
    {"speaker": "Player", "text": "(Live feed ng kaibigan sa PLM courtyard) \n“Hayop ka... Pabalik na ako. Hintayin mo ako.”"},
    {"speaker": "System", "text": "Binabati kita! Nahanap mo ang huling pahiwatig at nakumpirma ang totoong lokasyon ng bihag. (+10 HP)"}
]

# Climax Scene Script (Sequence #13)
climax_script = [
    {"speaker": "Player", "text": "\"Nandito na ako... Binitawan mo na siya!\""},
    {"speaker": "Antagonist", "text": "\"Nakabalik ka nga.. Tamang-tama sa 4:28. Enjoyed the game, honor student?\""},
    {"speaker": "Friend", "text": "“...Tumakas ka na! Umalis ka na rito!”"},
    {"speaker": "Player", "text": "\"Wala kang kwenta! Kung may gusto ka, sa akin mo gawin—huwag sa kanya!\""},
    {"speaker": "Antagonist", "text": "\"Matapang. Pero huli na ang lahat para sa mga patakaran ng laro.\""}
]

# --- LOAD ASSETS (Images) ---
def load_image(filename, size=None):
    path = os.path.join("assets", filename)
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.scale(img, size)
        return img
    return None

# Load background and character 
bg_image = load_image("bg_plm.png", (800, 600))
silhouette_image = load_image("silhouette.png", (200, 400))

# Main Game Loop
clock = pygame.time.Clock()

while True:
    # --- EVENT HANDLING ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        elif event.type == pygame.KEYDOWN:
            if game_state == "BACKSTORY":
                if event.key == pygame.K_SPACE:  # Press SPACE to advance backstory
                    backstory_dialogue += 1
                    if backstory_dialogue >= len(backstory_script):
                        game_state = "MENU"  # Transitions to Game Menu after backstory

            elif game_state == "MENU":
                if event.key == pygame.K_1:  # START
                    game_state = "CHARACTER_SELECT"
                elif event.key == pygame.K_2:  # SETTINGS
                    game_state = "SETTINGS"
                    
            elif game_state == "SETTINGS":
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE:
                    game_state = "MENU"

            elif game_state == "CHARACTER_SELECT":
                if event.key == pygame.K_1:
                    selected_character = "Black Figure A"
                    game_state = "PLAYING"
                elif event.key == pygame.K_2:
                    selected_character = "Black Figure B"
                    game_state = "PLAYING"

            elif game_state == "PLAYING":
                if event.key == pygame.K_SPACE:  # Press SPACE to advance dialogue
                    current_dialogue += 1
                    if current_dialogue >= len(script):
                        game_state = "CHOICE_1"
                        
            elif game_state == "CHOICE_1":
                if event.key == pygame.K_3:  # PLM Library (Correct)
                    player_hp = min(100, player_hp + 5)
                    game_state = "LIBRARY_SCENE"
                    library_dialogue = 0
                elif event.key == pygame.K_1 or event.key == pygame.K_2:  # Wrong choices
                    player_hp -= 15
                    game_state = "WRONG_CHOICE_1"

            elif game_state == "WRONG_CHOICE_1":
                if event.key == pygame.K_RETURN:
                    game_state = "CHOICE_1"

            elif game_state == "LIBRARY_SCENE":
                if event.key == pygame.K_SPACE:
                    library_dialogue += 1
                    if library_dialogue >= len(library_script):
                        game_state = "CHOICE_2"

            elif game_state == "CHOICE_2":
                if event.key == pygame.K_2:  # San Agustin Church (Correct)
                    player_hp = min(100, player_hp + 5)
                    game_state = "SAN_AGUSTIN_SCENE"
                    san_agustin_dialogue = 0
                elif event.key == pygame.K_1 or event.key == pygame.K_3:
                    player_hp -= 15
                    game_state = "WRONG_CHOICE_2"

            elif game_state == "WRONG_CHOICE_2":
                if event.key == pygame.K_RETURN:
                    game_state = "CHOICE_2"

            elif game_state == "SAN_AGUSTIN_SCENE":
                if event.key == pygame.K_SPACE:
                    san_agustin_dialogue += 1
                    if san_agustin_dialogue >= len(san_agustin_script):
                        game_state = "CHOICE_3"

            elif game_state == "CHOICE_3":
                if event.key == pygame.K_1:  # Fort Santiago (Correct)
                    player_hp = min(100, player_hp + 5)
                    game_state = "FORT_SANTIAGO_SCENE"
                    fort_santiago_dialogue = 0
                elif event.key == pygame.K_2 or event.key == pygame.K_3:
                    player_hp -= 15
                    game_state = "WRONG_CHOICE_3"

            elif game_state == "WRONG_CHOICE_3":
                if event.key == pygame.K_RETURN:
                    game_state = "CHOICE_3"

            elif game_state == "FORT_SANTIAGO_SCENE":
                if event.key == pygame.K_SPACE:
                    fort_santiago_dialogue += 1
                    if fort_santiago_dialogue >= len(fort_santiago_script):
                        game_state = "CHOICE_4"

            elif game_state == "CHOICE_4":
                if event.key == pygame.K_1:  # Escolta (Correct)
                    player_hp = min(100, player_hp + 5)
                    game_state = "ESCOLTA_SCENE"
                    escolta_dialogue = 0
                elif event.key == pygame.K_2 or event.key == pygame.K_3:
                    player_hp -= 15
                    game_state = "WRONG_CHOICE_4"

            elif game_state == "WRONG_CHOICE_4":
                if event.key == pygame.K_RETURN:
                    game_state = "CHOICE_4"

            elif game_state == "ESCOLTA_SCENE":
                if event.key == pygame.K_SPACE:
                    escolta_dialogue += 1
                    if escolta_dialogue >= len(escolta_script):
                        game_state = "CHOICE_5"

            elif game_state == "CHOICE_5":
                if event.key == pygame.K_1:  # Quiapo (Correct)
                    player_hp = min(100, player_hp + 5)
                    game_state = "QUIAPO_SCENE"
                    quiapo_dialogue = 0
                elif event.key == pygame.K_2 or event.key == pygame.K_3:
                    player_hp -= 15
                    game_state = "WRONG_CHOICE_5"

            elif game_state == "WRONG_CHOICE_5":
                if event.key == pygame.K_RETURN:
                    game_state = "CHOICE_5"

            elif game_state == "QUIAPO_SCENE":
                if event.key == pygame.K_SPACE:
                    quiapo_dialogue += 1
                    if quiapo_dialogue >= len(quiapo_script):
                        game_state = "CHOICE_6"

            elif game_state == "CHOICE_6":
                if event.key == pygame.K_1:  # Sta. Cruz (Correct)
                    game_state = "STA_CRUZ_SCENE"
                    sta_cruz_dialogue = 0
                elif event.key == pygame.K_2 or event.key == pygame.K_3:
                    player_hp -= 25
                    game_state = "WRONG_CHOICE_6"

            elif game_state == "WRONG_CHOICE_6":
                if event.key == pygame.K_RETURN:
                    game_state = "CHOICE_6"

            elif game_state == "STA_CRUZ_SCENE":
                if event.key == pygame.K_SPACE:
                    sta_cruz_dialogue += 1
                    if sta_cruz_dialogue >= len(sta_cruz_script):
                        game_state = "CHOICE_7"

            elif game_state == "CHOICE_7":
                if event.key == pygame.K_1:  # Lumang Bodega (Correct)
                    player_hp = min(100, player_hp + 10)
                    game_state = "BODEGA_SCENE"
                    bodega_dialogue = 0
                elif event.key == pygame.K_2 or event.key == pygame.K_3:
                    player_hp -= 20
                    game_state = "WRONG_CHOICE_7"

            elif game_state == "WRONG_CHOICE_7":
                if event.key == pygame.K_RETURN:
                    game_state = "CHOICE_7"

            elif game_state == "BODEGA_SCENE":
                if event.key == pygame.K_SPACE:
                    bodega_dialogue += 1
                    if bodega_dialogue >= len(bodega_script):
                        game_state = "CHOICE_8"

            elif game_state == "CHOICE_8":
                if event.key == pygame.K_1:  # PLM (Correct)
                    player_hp = min(100, player_hp + 10)
                    game_state = "CLIMAX_SCENE"
                    climax_dialogue = 0
                elif event.key == pygame.K_2 or event.key == pygame.K_3:
                    player_hp -= 25
                    game_state = "WRONG_CHOICE_8"

            elif game_state == "WRONG_CHOICE_8":
                if event.key == pygame.K_RETURN:
                    game_state = "CHOICE_8"

            elif game_state == "CLIMAX_SCENE":
                if event.key == pygame.K_SPACE:
                    climax_dialogue += 1
                    if climax_dialogue >= len(climax_script):
                        game_state = "FINAL_CHOICE"

            elif game_state == "FINAL_CHOICE":
                if event.key == pygame.K_1:  # Correct choice: Tackle antagonist
                    game_state = "TRUE_ENDING"
                elif event.key == pygame.K_2 or event.key == pygame.K_3:  # Wrong choices
                    game_state = "BAD_ENDING"

            elif game_state in ["TRUE_ENDING", "BAD_ENDING"]:
                if event.key == pygame.K_R:  # Restart game option
                    game_state = "BACKSTORY"
                    player_hp = 100
                    backstory_dialogue = 0
                    current_dialogue = 0

    # --- DRAWING / RENDERING ---
    screen.fill(BLACK)

    if game_state == "BACKSTORY":
        if bg_image:
            screen.blit(bg_image, (0, 0))
        else:
            screen.fill((20, 20, 20))

        pygame.draw.rect(screen, GRAY, (50, 420, 700, 140))
        pygame.draw.rect(screen, WHITE, (50, 420, 700, 140), 2)

        bs_data = backstory_script[backstory_dialogue]
        speaker_surf = font.render(f"[{bs_data['speaker']}]", True, RED)
        text_surf = font.render(bs_data['text'], True, WHITE)

        screen.blit(speaker_surf, (70, 440))
        screen.blit(text_surf, (70, 480))
        prompt_surf = font.render("[Press SPACE to continue]", True, (150, 150, 150))
        screen.blit(prompt_surf, (500, 525))

    elif game_state == "MENU":
        title_surf = title_font.render("4:28", True, RED)
        c1 = font.render("[1] START", True, WHITE)
        c2 = font.render("[2] SETTINGS", True, WHITE)
        screen.blit(title_surf, (360, 180))
        screen.blit(c1, (350, 260))
        screen.blit(c2, (340, 300))

    elif game_state == "SETTINGS":
        set_title = title_font.render("SETTINGS", True, WHITE)
        desc1 = font.render("Audio: On / Volume: 100%", True, GRAY)
        desc2 = font.render("Press [BACKSPACE] or [ESC] to return", True, RED)
        screen.blit(set_title, (310, 180))
        screen.blit(desc1, (290, 250))
        screen.blit(desc2, (230, 320))

    elif game_state == "CHARACTER_SELECT":
        sel_title = title_font.render("PILIIN ANG IYONG CHARACTER", True, WHITE)
        c1 = font.render("[1] Black Figure A (Standard Silhouette)", True, RED)
        c2 = font.render("[2] Black Figure B (Alternate Silhouette)", True, RED)
        screen.blit(sel_title, (170, 180))
        screen.blit(c1, (220, 250))
        screen.blit(c2, (220, 290))

    elif game_state == "PLAYING":
        if bg_image:
            screen.blit(bg_image, (0, 0))
        else:
            screen.fill((20, 20, 20))

        if silhouette_image:
            screen.blit(silhouette_image, (150, 80))

        pygame.draw.rect(screen, GRAY, (50, 420, 700, 140))
        pygame.draw.rect(screen, WHITE, (50, 420, 700, 140), 2)

        hp_surf = font.render(f"HP: {player_hp} | Char: {selected_character}", True, RED)
        screen.blit(hp_surf, (50, 30))

        data = script[current_dialogue]
        speaker_surf = font.render(f"[{data['speaker']}]", True, RED)
        text_surf = font.render(data['text'], True, WHITE)

        screen.blit(speaker_surf, (70, 440))
        screen.blit(text_surf, (70, 480))
        prompt_surf = font.render("[Press SPACE to continue]", True, (150, 150, 150))
        screen.blit(prompt_surf, (500, 525))

    elif game_state == "CHOICE_1":
        choice_title = font.render("Saan ka pupunta susunod?", True, WHITE)
        c1 = font.render("[1] Justo Alberto Auditorium", True, RED)
        c2 = font.render("[2] University Activity Center", True, RED)
        c3 = font.render("[3] PLM Library", True, WHITE)
        screen.blit(choice_title, (280, 180))
        screen.blit(c1, (260, 240))
        screen.blit(c2, (260, 280))
        screen.blit(c3, (260, 320))

    elif game_state == "WRONG_CHOICE_1":
        desc = font.render("Sayang lang oras ko, wala siya dito. (-15 HP)", True, RED)
        retry = font.render("Press [ENTER] to try again", True, WHITE)
        screen.blit(desc, (230, 250))
        screen.blit(retry, (290, 310))

    elif game_state == "LIBRARY_SCENE":
        if bg_image: screen.blit(bg_image, (0, 0))
        pygame.draw.rect(screen, GRAY, (50, 420, 700, 140))
        pygame.draw.rect(screen, WHITE, (50, 420, 700, 140), 2)
        hp_surf = font.render(f"HP: {player_hp}", True, RED)
        screen.blit(hp_surf, (50, 30))
        lib_data = library_script[library_dialogue]
        screen.blit(font.render(f"[{lib_data['speaker']}]", True, RED), (70, 440))
        screen.blit(font.render(lib_data['text'], True, WHITE), (70, 480))
        screen.blit(font.render("[Press SPACE to continue]", True, (150, 150, 150)), (500, 525))

    elif game_state == "CHOICE_2":
        choice_title = font.render("Sundan ang mga piyesa ng lumang bato:", True, WHITE)
        c1 = font.render("[1] Manila Cathedral", True, RED)
        c2 = font.render("[2] San Agustin Church", True, WHITE)
        c3 = font.render("[3] San Ignacio Church", True, RED)
        screen.blit(choice_title, (250, 180))
        screen.blit(c1, (280, 240))
        screen.blit(c2, (280, 280))
        screen.blit(c3, (280, 320))

    elif game_state == "WRONG_CHOICE_2":
        desc = font.render("Wala rito... Sabi sa clue, yung pinakamatandang bato. (-15 HP)", True, RED)
        retry = font.render("Press [ENTER] to try again", True, WHITE)
        screen.blit(desc, (180, 250))
        screen.blit(retry, (290, 310))

    elif game_state == "SAN_AGUSTIN_SCENE":
        if bg_image: screen.blit(bg_image, (0, 0))
        pygame.draw.rect(screen, GRAY, (50, 420, 700, 140))
        pygame.draw.rect(screen, WHITE, (50, 420, 700, 140), 2)
        hp_surf = font.render(f"HP: {player_hp}", True, RED)
        screen.blit(hp_surf, (50, 30))
        sa_data = san_agustin_script[san_agustin_dialogue]
        screen.blit(font.render(f"[{sa_data['speaker']}]", True, RED), (70, 440))
        screen.blit(font.render(sa_data['text'], True, WHITE), (70, 480))
        screen.blit(font.render("[Press SPACE to continue]", True, (150, 150, 150)), (500, 525))

    elif game_state == "CHOICE_3":
        choice_title = font.render("Saan dumaan ang mga binihag noon?", True, WHITE)
        c1 = font.render("[1] Fort Santiago", True, WHITE)
        c2 = font.render("[2] Luneta Park", True, RED)
        c3 = font.render("[3] Binondo", True, RED)
        screen.blit(choice_title, (250, 180))
        screen.blit(c1, (300, 240))
        screen.blit(c2, (300, 280))
        screen.blit(c3, (300, 320))

    elif game_state == "WRONG_CHOICE_3":
        desc = font.render("Mali.. Hindi rito ang tinutukoy. (-15 HP)", True, RED)
        retry = font.render("Press [ENTER] to try again", True, WHITE)
        screen.blit(desc, (260, 250))
        screen.blit(retry, (290, 310))

    elif game_state == "FORT_SANTIAGO_SCENE":
        if bg_image: screen.blit(bg_image, (0, 0))
        pygame.draw.rect(screen, GRAY, (50, 420, 700, 140))
        pygame.draw.rect(screen, WHITE, (50, 420, 700, 140), 2)
        hp_surf = font.render(f"HP: {player_hp}", True, RED)
        screen.blit(hp_surf, (50, 30))
        fs_data = fort_santiago_script[fort_santiago_dialogue]
        screen.blit(font.render(f"[{fs_data['speaker']}]", True, RED), (70, 440))
        screen.blit(font.render(fs_data['text'], True, WHITE), (70, 480))
        screen.blit(font.render("[Press SPACE to continue]", True, (150, 150, 150)), (500, 525))

    elif game_state == "CHOICE_4":
        choice_title = font.render("Tumawid ka sa ilog kung saan may mga lumang sinehan:", True, WHITE)
        c1 = font.render("[1] Escolta", True, WHITE)
        c2 = font.render("[2] Luneta Park", True, RED)
        c3 = font.render("[3] Quiapo", True, RED)
        screen.blit(choice_title, (200, 180))
        screen.blit(c1, (320, 240))
        screen.blit(c2, (320, 280))
        screen.blit(c3, (320, 320))

    elif game_state == "WRONG_CHOICE_4":
        desc = font.render("Mali... Hindi rito ang lumang sinehan. Nasayang oras mo. (-15 HP)", True, RED)
        retry = font.render("Press [ENTER] to try again", True, WHITE)
        screen.blit(desc, (170, 250))
        screen.blit(retry, (290, 310))

    elif game_state == "ESCOLTA_SCENE":
        if bg_image: screen.blit(bg_image, (0, 0))
        pygame.draw.rect(screen, GRAY, (50, 420, 700, 140))
        pygame.draw.rect(screen, WHITE, (50, 420, 700, 140), 2)
        hp_surf = font.render(f"HP: {player_hp}", True, RED)
        screen.blit(hp_surf, (50, 30))
        es_data = escolta_script[escolta_dialogue]
        screen.blit(font.render(f"[{es_data['speaker']}]", True, RED), (70, 440))
        screen.blit(font.render(es_data['text'], True, WHITE), (70, 480))
        screen.blit(font.render("[Press SPACE to continue]", True, (150, 150, 150)), (500, 525))

    elif game_state == "CHOICE_5":
        choice_title = font.render("Saan nagtatagpo ang mga deboto at estero?", True, WHITE)
        c1 = font.render("[1] Quiapo", True, WHITE)
        c2 = font.render("[2] Binondo", True, RED)
        c3 = font.render("[3] Taft", True, RED)
        screen.blit(choice_title, (220, 180))
        screen.blit(c1, (320, 240))
        screen.blit(c2, (320, 280))
        screen.blit(c3, (320, 320))

    elif game_state == "WRONG_CHOICE_5":
        desc = font.render("Mali... Hindi rito ang tinutukoy ng mensahe. (-15 HP)", True, RED)
        retry = font.render("Press [ENTER] to try again", True, WHITE)
        screen.blit(desc, (210, 250))
        screen.blit(retry, (290, 310))

    elif game_state == "QUIAPO_SCENE":
        if bg_image: screen.blit(bg_image, (0, 0))
        pygame.draw.rect(screen, GRAY, (50, 420, 700, 140))
        pygame.draw.rect(screen, WHITE, (50, 420, 700, 140), 2)
        hp_surf = font.render(f"HP: {player_hp}", True, RED)
        screen.blit(hp_surf, (50, 30))
        qu_data = quiapo_script[quiapo_dialogue]
        screen.blit(font.render(f"[{qu_data['speaker']}]", True, RED), (70, 440))
        screen.blit(font.render(qu_data['text'], True, WHITE), (70, 480))
        screen.blit(font.render("[Press SPACE to continue]", True, (150, 150, 150)), (500, 525))

    elif game_state == "CHOICE_6":
        choice_title = font.render("Alin ang tamang landas mula sa marka?", True, WHITE)
        c1 = font.render("[1] Sta. Cruz", True, WHITE)
        c2 = font.render("[2] Pumunta sa Tulay (Bitag)", True, RED)
        c3 = font.render("[3] Binondo", True, RED)
        screen.blit(choice_title, (250, 180))
        screen.blit(c1, (290, 240))
        screen.blit(c2, (290, 280))
        screen.blit(c3, (290, 320))

    elif game_state == "WRONG_CHOICE_6":
        desc = font.render("Mali... Nahuli ka sa bitag ng taong nagmamanman! (-25 HP)", True, RED)
        retry = font.render("Press [ENTER] to try again", True, WHITE)
        screen.blit(desc, (180, 250))
        screen.blit(retry, (290, 310))

    elif game_state == "STA_CRUZ_SCENE":
        if bg_image: screen.blit(bg_image, (0, 0))
        pygame.draw.rect(screen, GRAY, (50, 420, 700, 140))
        pygame.draw.rect(screen, WHITE, (50, 420, 700, 140), 2)
        hp_surf = font.render(f"HP: {player_hp}", True, RED)
        screen.blit(hp_surf, (50, 30))
        sc_data = sta_cruz_script[sta_cruz_dialogue]
        screen.blit(font.render(f"[{sc_data['speaker']}]", True, RED), (70, 440))
        screen.blit(font.render(sc_data['text'], True, WHITE), (70, 480))
        screen.blit(font.render("[Press SPACE to continue]", True, (150, 150, 150)), (500, 525))

    elif game_state == "CHOICE_7":
        choice_title = font.render("Saan ang susunod na lokasyon sa Sta. Cruz?", True, WHITE)
        c1 = font.render("[1] Lumang Bodega sa Gilid ng Estero", True, WHITE)
        c2 = font.render("[2] Abandonadong Simbahan", True, RED)
        c3 = font.render("[3] Tumawid pabalik sa Escolta", True, RED)
        screen.blit(choice_title, (230, 180))
        screen.blit(c1, (250, 240))
        screen.blit(c2, (250, 280))
        screen.blit(c3, (250, 320))

    elif game_state == "WRONG_CHOICE_7":
        desc = font.render("Mali... Walang tao rito. Nasayang oras at lakas mo. (-20 HP)", True, RED)
        retry = font.render("Press [ENTER] to try again", True, WHITE)
        screen.blit(desc, (180, 250))
        screen.blit(retry, (290, 310))

    elif game_state == "BODEGA_SCENE":
        if bg_image: screen.blit(bg_image, (0, 0))
        pygame.draw.rect(screen, GRAY, (50, 420, 700, 140))
        pygame.draw.rect(screen, WHITE, (50, 420, 700, 140), 2)
        hp_surf = font.render(f"HP: {player_hp}", True, RED)
        screen.blit(hp_surf, (50, 30))
        bo_data = bodega_script[bodega_dialogue]
        screen.blit(font.render(f"[{bo_data['speaker']}]", True, RED), (70, 440))
        screen.blit(font.render(bo_data['text'], True, WHITE), (70, 480))
        screen.blit(font.render("[Press SPACE to continue]", True, (150, 150, 150)), (500, 525))

    elif game_state == "CHOICE_8":
        choice_title = font.render("Saan dadalhin ang pagtatapos?", True, WHITE)
        c1 = font.render("[1] PLM", True, WHITE)
        c2 = font.render("[2] Manatili sa Bodega", True, RED)
        c3 = font.render("[3] Estasyon ng Quiapo", True, RED)
        screen.blit(choice_title, (270, 180))
        screen.blit(c1, (300, 240))
        screen.blit(c2, (300, 280))
        screen.blit(c3, (300, 320))

    elif game_state == "WRONG_CHOICE_8":
        desc = font.render("Mali... Naubusan ka ng oras sa paghihintay. (-25 HP)", True, RED)
        retry = font.render("Press [ENTER] to try again", True, WHITE)
        screen.blit(desc, (210, 250))
        screen.blit(retry, (290, 310))

    elif game_state == "CLIMAX_SCENE":
        if bg_image: screen.blit(bg_image, (0, 0))
        pygame.draw.rect(screen, GRAY, (50, 420, 700, 140))
        pygame.draw.rect(screen, WHITE, (50, 420, 700, 140), 2)
        hp_surf = font.render(f"HP: {player_hp}", True, RED)
        screen.blit(hp_surf, (50, 30))
        cl_data = climax_script[climax_dialogue]
        screen.blit(font.render(f"[{cl_data['speaker']}]", True, RED), (70, 440))
        screen.blit(font.render(cl_data['text'], True, WHITE), (70, 480))
        screen.blit(font.render("[Press SPACE to continue]", True, (150, 150, 150)), (500, 525))

    elif game_state == "FINAL_CHOICE":
        choice_title = font.render("Huling Pagsubok: Piliin ang iyong huling hakbang", True, WHITE)
        c1 = font.render("[1] Lumaban at sugurin ang antagonist", True, WHITE)
        c2 = font.render("[2] Magmakaawa at sumuko", True, RED)
        c3 = font.render("[3] Subukang tumakas", True, RED)
        screen.blit(choice_title, (200, 180))
        screen.blit(c1, (220, 240))
        screen.blit(c2, (220, 280))
        screen.blit(c3, (220, 320))

    elif game_state == "TRUE_ENDING":
        t1 = title_font.render("TRUE SURVIVAL ENDING", True, WHITE)
        t2 = font.render("Dumating ang mga pulis at nailigtas mo ang iyong kaibigan!", True, WHITE)
        t3 = font.render("Press [R] to Restart Game", True, RED)
        screen.blit(t1, (200, 200))
        screen.blit(t2, (180, 270))
        screen.blit(t3, (300, 340))

    elif game_state == "BAD_ENDING":
        t1 = title_font.render("TRAGIC ENDING", True, RED)
        t2 = font.render("Huli na ang lahat. Nagdilim ang paligid sa 4:28.", True, WHITE)
        t3 = font.render("Press [R] to Restart Game", True, WHITE)
        screen.blit(t1, (280, 200))
        screen.blit(t2, (210, 270))
        screen.blit(t3, (300, 340))

    pygame.display.flip()
    clock.tick(60)
