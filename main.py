import pygame
import sys


pygame.init()
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("4:28")

# Colors (Monochrome / Noir Thriller Theme)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (50, 50, 50)
RED = (200, 50, 50)


font = pygame.font.SysFont(None, 24)
title_font = pygame.font.SysFont(None, 48)


game_state = "MENU"  # Can be "MENU", "PLAYING", "CHOICE"
player_hp = 100
current_dialogue = 0


script = [
    {"speaker": "Student 1", "text": "Ilang linggo nang nawawala ‘yan... Sabi, huli daw nakita ‘yan sa labas ng gate ng PLM eh."},
    {"speaker": "Student Reporter (Audio)", "text": "...At exactly 4:28 PM when he was last seen near the vicinity of Intramuros..."},
    {"speaker": "Player", "text": "Kawawa naman... Ano kaya ang talagang nangyari sa kanya?"},
    {"speaker": "Unknown Number (4:28 PM)", "text": "*ting!* Kung hinahanap mo ako, puntahan mo ang silid ng mga tahimik na libro..."}
]


clock = pygame.time.Clock()

while True:
    # --- EVENT HANDLING ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        elif event.type == pygame.KEYDOWN:
            if game_state == "MENU":
                if event.key == pygame.K_RETURN:  # Press ENTER to start
                    game_state = "PLAYING"
                    
            elif game_state == "PLAYING":
                if event.key == pygame.K_SPACE:  # Press SPACE to advance dialogue
                    current_dialogue += 1
                    if current_dialogue >= len(script):
                        # End of current script block, switch to choice or loop
                        game_state = "CHOICE"

    # --- DRAWING / RENDERING ---
    screen.fill(BLACK)

    if game_state == "MENU":
        # Draw Title Screen (Sequence #4 concept)
        title_surf = title_font.render("4:28", True, RED)
        screen.blit(title_surf, (320, 200))
        
        start_surf = font.render("Press [ENTER] to Start", True, WHITE)
        screen.blit(start_surf, (315, 300))

    elif game_state == "PLAYING":
        # Draw Dialogue Box UI
        pygame.draw.rect(screen, GRAY, (50, 400, 700, 150))
        pygame.draw.rect(screen, WHITE, (50, 400, 700, 150), 2) # Border

        # Display HP status (Python variable tracking)
        hp_surf = font.render(f"HP: {player_hp}", True, RED)
        screen.blit(hp_surf, (50, 50))

        # Display Current Speaker and Text
        data = script[current_dialogue]
        speaker_surf = font.render(f"[{data['speaker']}]", True, RED)
        text_surf = font.render(data['text'], True, WHITE)

        screen.blit(speaker_surf, (70, 420))
        screen.blit(text_surf, (70, 460))

        prompt_surf = font.render("[Press SPACE to continue]", True, (150, 150, 150))
        screen.blit(prompt_surf, (500, 515))

    elif game_state == "CHOICE":
        # Placeholder for your Clue-Hunting / Location Choices
        choice_title = font.render("Saan ka pupunta susunod?", True, WHITE)
        c1 = font.render("[1] PLM Library", True, RED)
        c2 = font.render("[2] San Agustin Church", True, RED)
        
        screen.blit(choice_title, (300, 200))
        screen.blit(c1, (350, 260))
        screen.blit(c2, (350, 300))

    pygame.display.flip()
    clock.tick(60)
