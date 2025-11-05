import copy
import random
import pygame

pygame.init()

# DECK SETUP
cards = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
suits = ['C','D','H','S']  # C=Clubs(Klaveren), D=Diamonds(Ruiten), H=Hearts(Harten), S=Spades(Schoppen)
one_deck = [f"{c}{s}" for c in cards for s in suits] # Maak één compleet deck door elke kaart met elke suit te combineren
decks = 4

# SCHERM
info = pygame.display.Info()

WIDTH = int(info.current_w * 0.8)
HEIGHT = int(info.current_h * 0.85)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Blackjack!')

fps = 60
timer = pygame.time.Clock()
font = pygame.font.Font('Poppins-Medium.ttf', 44)
smaller_font = pygame.font.Font('Poppins-Medium.ttf', 28)

# GAME STATE VARIABELEN
game_state = "menu"
active = False

initial_deal = False # True betekent dat we de eerste kaarten moeten delen
hand_active = False
reveal_dealer = False
outcome = 0
player_score = 0
dealer_score = 0
my_hand = []
dealer_hand = []

# SPLIT & DOUBLE DOWN VARIABELEN
split_mode = False
split_hands = [] # Bijvoorbeeld: [["AH", "5C"], ["AD", "KC"]]
current_hand_index = 0 #geeft aan welke hand nu actief is (0 of 1)
double_down_used = False # voorkomt dat je meerdere keren double down doet

# BET SYSTEEM
balance = 5000
current_bet = 100
max_bet = 1000
min_bet = 1
original_bet = current_bet
hand_bets = []  # Lijst met inzetten per hand

# AFBEELDINGEN
background_img = pygame.image.load("background_menu.jpg")
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))
logo_img = pygame.image.load("logo.png")
logo_img = pygame.transform.scale(logo_img, (int(WIDTH*0.2), int((WIDTH*0.2)*768/1500)))
logo_play_img = pygame.transform.scale(logo_img, (int(WIDTH*0.1), int((WIDTH*0.1)*768/1500)))
card_back_img = pygame.image.load("cards/back.png")
CARD_WIDTH, CARD_HEIGHT = 150, 220

# RESULTAAT POPUP VARIABELEN
result_delay_ms = 1000  # Wachttijd in milliseconden voordat resultaat popup verschijnt
result_time = None  # Tijdstip waarop de hand eindigde

bankrupt_popup = False

# Teksten voor de resultaat popup
result_title = ""
result_lines = []
result_net = 0

animations = [] # Elke animatie wordt opgeslagen als een dictionary met de nodige gegevens

dealing = False  # zijn we nu kaarten aan het delen?
flip_anim = None  # animatie voor het omdraaien van de dealer's verborgen kaart

DECK_POS = (WIDTH // 2 - CARD_WIDTH // 2, -CARD_HEIGHT - 50) # Positie van het deck (buiten het scherm bovenaan)

dealer_has_drawn = False


# HELPER/CHECK FUNCTIES
def can_split(hand):
    if len(hand) != 2:
        return False

    # Haal de waarde van beide kaarten op ("AH" wordt "A", "10C" wordt "10")
    v1 = hand[0][:-1]  # eerste kaart
    v2 = hand[1][:-1]  # tweede kaart

    # Lijst met alle 10's
    tens = ['10','J','Q','K']

    if v1 == v2 or (v1 in tens and v2 in tens):
        return True

    return False

def deal_cards(hand, deck):
    card = random.choice(deck)

    hand.append(card)

    # Verwijder de kaart uit het deck (kan niet twee keer gedeeld worden)
    deck.remove(card)

    return hand, deck

def calculate_score(hand):
    score = 0  # Start met score 0
    aces = 0  # Houd bij hoeveel Azen we hebben

    # Tel alle kaarten op
    for card in hand:
        v = card[:-1]# Haal de waarde van de kaart op ("AH" wordt "A", "10C" wordt "10")

        if v in ['J','Q','K']:             # Plaatjes tellen als 10
            score += 10
        elif v == 'A':
            score += 11
            aces += 1  # tel aas bij
        else:
            score += int(v) # Nummers

    # Pas Azen aan als we bust zijn
    while score > 21 and aces > 0:
        score -= 10  # Verander een Aas van 11 naar 1
        aces -= 1  # We hebben nu één Aas minder die we kunnen aanpassen

    return score

def draw_centered_lines(surface, rect, lines, title_font, line_font, title_offset=-40, line_spacing=40):
    # Bereken de Y positie voor de titel
    y = rect.centery + title_offset

    # Teken de titel (eerste regel)
    title_surf = title_font.render(lines[0], True, (0,0,0))  # Zwarte tekst
    title_rect = title_surf.get_rect(center=(rect.centerx, y))  # Centreer horizontaal
    surface.blit(title_surf, title_rect)

    # Teken de rest van de regels
    for i, ln in enumerate(lines[1:]):
        # Bereken Y positie voor deze regel
        sy = y + (i+1)*line_spacing

        # Render de tekst
        ls = line_font.render(ln, True, (0,0,0))  # Zwarte tekst
        lrect = ls.get_rect(center=(rect.centerx, sy))  # Centreer horizontaal
        surface.blit(ls, lrect)

def create_deal_animation(card, end_pos, is_back=False, delay=0):
    global animations, dealing

    # Zet dealing flag op True (anders kan je doorspelen)
    dealing = True
    card_name = "BACK" if is_back else card # Bepaal welke kaart afbeelding we gebruiken

    # deal animatie
    anim = {
        'card': card_name,
        'start_pos': DECK_POS,
        'end_pos': end_pos,
        'start_time': pygame.time.get_ticks() + delay,
        'duration': 800,
        'flip': False,
        'active': True
    }

    animations.append(anim)

def create_flip_animation(card, pos):
    global flip_anim

    # flip animatie
    flip_anim = {
        'card': card,
        'start_pos': pos,
        'end_pos': pos,
        'start_time': pygame.time.get_ticks(),
        'duration': 600,
        'flip': True,
        'active': True,
        'flip_prog': 0
    }

def get_animation_position(anim):
    now = pygame.time.get_ticks() # Bereken de huidige positie van een animatie

    # Als we nog in de delay periode zitten, return start positie
    if now < anim['start_time']:
        return anim['start_pos']

    elapsed = now - anim['start_time'] # Bereken hoeveel tijd er verstreken is sinds de start
    progress = min(elapsed / anim['duration'], 1.0) # Bereken de voortgang: 0.0 = net gestart, 1.0 = klaar
    eased = 1 - pow(1 - progress, 2) # vloeiende beweging

    # Bereken de huidige positie tussen start en eind
    pos = (
        anim['start_pos'][0] + (anim['end_pos'][0] - anim['start_pos'][0]) * eased,
        anim['start_pos'][1] + (anim['end_pos'][1] - anim['start_pos'][1]) * eased
    )

    return pos

def get_total_bet_display():
    if split_mode and len(hand_bets) >= 2:
        return hand_bets[0] + hand_bets[1] # Split
    elif len(hand_bets) > 0:
        return hand_bets[0] # double down
    else:
        return original_bet # Normaal


# DRAW FUNCTIES
def draw_menu():
    screen.blit(background_img, (0, 0))
    screen.blit(logo_img, ((WIDTH // 2 - logo_img.get_width() // 2), 50))

    # KNOPPEN
    spacing = 120

    start_btn = pygame.Rect((WIDTH - 300)//2, 350, 300, 80)
    rules_btn = pygame.Rect((WIDTH - 300)//2, 350 + spacing, 300, 80)
    quit_btn = pygame.Rect((WIDTH - 300)//2, 350 + spacing * 2, 300, 80)

    mouse_pos = pygame.mouse.get_pos()  # Muispositie voor hover

    # knoppen in menu
    # Start
    color = (200, 200, 200) if start_btn.collidepoint(mouse_pos) else (255, 255, 255)
    pygame.draw.rect(screen, color, start_btn, border_radius=10)
    pygame.draw.rect(screen, (0, 0, 0), start_btn, 3, border_radius=10)
    text_start = smaller_font.render("Start", True, (0, 0, 0))
    screen.blit(text_start, text_start.get_rect(center=start_btn.center))

    # Rules
    color = (200, 200, 200) if rules_btn.collidepoint(mouse_pos) else (255, 255, 255)
    pygame.draw.rect(screen, color, rules_btn, border_radius=10)
    pygame.draw.rect(screen, (0, 0, 0), rules_btn, 3, border_radius=10)
    text_rules = smaller_font.render("Rules", True, (0, 0, 0))
    screen.blit(text_rules, text_rules.get_rect(center=rules_btn.center))

    # Quit
    color = (200, 200, 200) if quit_btn.collidepoint(mouse_pos) else (255, 255, 255)
    pygame.draw.rect(screen, color, quit_btn, border_radius=10)
    pygame.draw.rect(screen, (0, 0, 0), quit_btn, 3, border_radius=10)
    text_quit = smaller_font.render("Quit", True, (0, 0, 0))
    screen.blit(text_quit, text_quit.get_rect(center=quit_btn.center))

    # BANKRUPT POPUP
    if bankrupt_popup:
        # transparante overlay
        overlay_full = pygame.Surface((WIDTH, HEIGHT))
        overlay_full.set_alpha(200)  # 200/255
        overlay_full.fill((0, 0, 0))  # Zwart
        screen.blit(overlay_full, (0, 0))

        # popup box
        w, h = WIDTH//2, HEIGHT//3
        popup = pygame.Surface((w, h))
        popup.fill("white")  # Witte achtergrond
        pygame.draw.rect(popup, "black", (0,0,w,h), 3, border_radius=15)  # Zwarte rand
        rect = popup.get_rect(center=(WIDTH//2, HEIGHT//2))  # Centreer op scherm

        # Bereken verticale centrering voor de tekst
        total_content_height = 60 + 40 + 60  # title + message + button
        start_y = (h - total_content_height) // 2

        # titel
        t = font.render("You're broke!", True, "black")
        popup.blit(t, (w//2 - t.get_width()//2, start_y))

        # bericht
        msg = smaller_font.render("You lost all your money.", True, "black")
        popup.blit(msg, (w//2 - msg.get_width()//2, start_y + 60))

        # quit knop
        quit_btn2 = pygame.Rect(w//2 - 60, start_y + 120, 120, 50)
        pygame.draw.rect(popup, (230,230,230), quit_btn2, border_radius=8)
        pygame.draw.rect(popup, (0,0,0), quit_btn2, 2, border_radius=8)
        qtxt = smaller_font.render("Quit", True, "black")
        popup.blit(qtxt, qtxt.get_rect(center=quit_btn2.center))

        # popup op het scherm
        screen.blit(popup, rect.topleft)

        # popup-knop omztten zodat hij klikbaar is
        quit_btn2_screen = pygame.Rect(rect.left + quit_btn2.left, rect.top + quit_btn2.top, quit_btn2.width, quit_btn2.height)
        return [start_btn, rules_btn, quit_btn, quit_btn2_screen]

    return [start_btn, rules_btn, quit_btn]

def draw_rules():
    #  achtergrond
    screen.blit(background_img, (0, 0))

    title = font.render("Rules", True, "white")
    screen.blit(title, (50, 60))

    rules_texts = [
        "Blackjack Rules:",
        "- Get as close to 21 as possible.",
        "- Face cards = 10, A = 1 or 11.",
        "- Dealer must stand on 17.",
        "- ENTER = Hit | SPACE = Stand",
        "- TAB = Double Down | E = Split (if allowed)"
    ]

    # elke regel met 50 pixels verticale ruimte
    for i, line in enumerate(rules_texts):
        screen.blit(smaller_font.render(line, True, "white"), (50, 150 + i*50))

    # TERUG KNOP
    back_btn = pygame.Rect((WIDTH-300)//2, HEIGHT-150, 300, 80)
    mouse_pos = pygame.mouse.get_pos()

    # Hover effect
    color = (200,200,200) if back_btn.collidepoint(mouse_pos) else (255,255,255)
    pygame.draw.rect(screen, color, back_btn, border_radius=10)
    pygame.draw.rect(screen, (0,0,0), back_btn, 3, border_radius=10)

    bt = smaller_font.render("BACK", True, (0,0,0))
    screen.blit(bt, bt.get_rect(center=back_btn.center))

    return [back_btn]

def draw_bet_popup():
    # popup achtergrond
    w, h = WIDTH // 2, HEIGHT // 3
    overlay = pygame.Surface((w, h))
    overlay.fill("white")
    pygame.draw.rect(overlay, "black", (0, 0, w, h), 3, border_radius=15)
    rect = overlay.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(overlay, rect.topleft)

    # titel
    title = font.render("Place your bet", True, "black")
    screen.blit(title, (rect.centerx - title.get_width() // 2, rect.top + 40))

    # saldo en inzet
    bal_text = smaller_font.render(f"Balance: €{balance}", True, "black")
    bet_text = smaller_font.render(f"Bet: €{current_bet}", True, "black")
    screen.blit(bal_text, (rect.centerx - bal_text.get_width() // 2, rect.top + 110))
    screen.blit(bet_text, (rect.centerx - bet_text.get_width() // 2, rect.top + 150))

    # knoppenposities
    bet_y = rect.top + 150
    text_height = bet_text.get_height()

    plus_btn = pygame.Rect(rect.centerx + 80, bet_y + text_height // 2 - 15, 40, 30)
    minus_btn = pygame.Rect(rect.centerx - 130, bet_y + text_height // 2 - 15, 40, 30)
    deal_btn = pygame.Rect(rect.centerx - 100, bet_y + 80, 200, 60)

    # plus-knop
    pygame.draw.rect(screen, (230, 230, 230), plus_btn, border_radius=8)
    pygame.draw.rect(screen, (0, 0, 0), plus_btn, 2, border_radius=8)
    plus_text = smaller_font.render("+", True, "black")
    screen.blit(plus_text, plus_text.get_rect(center=plus_btn.center))

    # min-knop
    pygame.draw.rect(screen, (230, 230, 230), minus_btn, border_radius=8)
    pygame.draw.rect(screen, (0, 0, 0), minus_btn, 2, border_radius=8)
    minus_text = smaller_font.render("-", True, "black")
    screen.blit(minus_text, minus_text.get_rect(center=minus_btn.center))

    # deal-knop
    pygame.draw.rect(screen, (230, 230, 230), deal_btn, border_radius=8)
    pygame.draw.rect(screen, (0, 0, 0), deal_btn, 2, border_radius=8)
    deal_text = smaller_font.render("DEAL", True, "black")
    screen.blit(deal_text, deal_text.get_rect(center=deal_btn.center))

    # return knoppen zodat ze klikbaar zijn
    return [plus_btn, minus_btn, deal_btn]

def popup_result():
    # POPUP HOOGTE OP BASIS VAN CONTENT
    title_height = 80  # Ruimte voor titel
    line_height = 35  # Hoogte per tekst regel
    button_area = 80  # Ruimte voor knoppen
    padding = 40

    # Bereken totale hoogte
    content_height = title_height + (len(result_lines) * line_height) + button_area + padding

    # Beperk hoogte tussen minimum en maximum
    min_height = 250
    max_height = HEIGHT * 0.6
    h = max(min_height, min(content_height, max_height))

    # POPUP BOX
    w = WIDTH//2
    overlay = pygame.Surface((w, h))
    overlay.fill("white")
    pygame.draw.rect(overlay, "black", (0,0,w,h), 3, border_radius=15)
    rect = overlay.get_rect(center=(WIDTH//2, HEIGHT//2))
    screen.blit(overlay, rect.topleft)

    # titel
    title = font.render(result_title, True, "black")
    screen.blit(title, (rect.centerx - title.get_width()//2, rect.top + 30))

    # ALLE RESULTAAT REGELS
    line_y = rect.top + 90
    for line in result_lines:
        txt = smaller_font.render(line, True, "black")
        screen.blit(txt, (rect.centerx - txt.get_width() // 2, line_y))
        line_y += line_height

    # KNOPPEN
    button_y = rect.top + h - 80

    # New-knop (start nieuwe ronde)
    again_btn = pygame.Rect(rect.centerx - 120, button_y, 100, 50)
    pygame.draw.rect(screen, (230, 230, 230), again_btn, border_radius=8)
    pygame.draw.rect(screen, (0, 0, 0), again_btn, 2, border_radius=8)
    again_text = smaller_font.render("New", True, "black")
    screen.blit(again_text, again_text.get_rect(center=again_btn.center))

    # Menu-knop (terug naar hoofdmenu)
    menu_btn = pygame.Rect(rect.centerx + 20, button_y, 100, 50)
    pygame.draw.rect(screen, (230, 230, 230), menu_btn, border_radius=8)
    pygame.draw.rect(screen, (0, 0, 0), menu_btn, 2, border_radius=8)
    menu_text = smaller_font.render("Menu", True, "black")
    screen.blit(menu_text, menu_text.get_rect(center=menu_btn.center))

    return [again_btn, menu_btn]

def draw_card_animated(surface, anim):
    now = pygame.time.get_ticks()

    # Als we nog in de delay periode zitten, teken niets
    if now < anim['start_time']:
        return

    # Bereken voortgang van animatie
    elapsed = now - anim['start_time']
    progress = min(elapsed / anim['duration'], 1.0)

    # Krijg de huidige positie
    pos = get_animation_position(anim)

    try:
        # FLIP ANIMATIE
        if anim['flip']:
            # Update flip voortgang
            anim['flip_prog'] = progress

            if progress < 0.5:
                # Eerste helft: achterkant zien
                img = card_back_img
                scale = 1 - (progress * 2)
            else:
                # Tweede helft: voorkant zien
                img = pygame.image.load(f"cards/{anim['card']}.png")
                scale = (progress - 0.5) * 2

            # Schaal de kaart naar standaard grootte
            img = pygame.transform.scale(img, (CARD_WIDTH, CARD_HEIGHT))

            # Bereken de geschaalde breedte
            scaled_w = int(CARD_WIDTH * scale)

            # Alleen tonen als breedte > 0
            if scaled_w > 0:
                img = pygame.transform.scale(img, (scaled_w, CARD_HEIGHT))
                x_offset = (CARD_WIDTH - scaled_w) // 2
                surface.blit(img, (pos[0] + x_offset, pos[1]))
        else:
            # NORMALE ANIMATIE (geen flip)
            if anim['card'] == "BACK":
                img = card_back_img
            else:
                img = pygame.image.load(f"cards/{anim['card']}.png")

            img = pygame.transform.scale(img, (CARD_WIDTH, CARD_HEIGHT))
            surface.blit(img, pos)
    except:
        # Fallback: achterkant
        img = card_back_img
        img = pygame.transform.scale(img, (CARD_WIDTH, CARD_HEIGHT))
        surface.blit(img, pos)

def draw_playing():
    global flip_anim

    # achtergrond
    screen.blit(background_img, (0, 0))
    # klein logo rechtsboven
    screen.blit(logo_play_img, (WIDTH - logo_play_img.get_width() - 20, 20))

    # DEALER KAARTEN
    # dealer kaarten gecentreerd
    dealer_start = (WIDTH - len(dealer_hand)*CARD_WIDTH)//2

    # hole card verbergen tijdens split mode als we de eerste hand spelen
    hide_hole = False
    if split_mode and current_hand_index == 0 and hand_active:
        hide_hole = True

    # Teken elke dealer kaart
    for i, c in enumerate(dealer_hand):
        card_x = dealer_start + i*CARD_WIDTH
        card_y = 50

        # Check of deze kaart momenteel geanimeerd wordt
        is_anim = False
        for anim in animations:
            if anim['active'] and anim['card'] == c:
                draw_card_animated(screen, anim)  # Teken de animatie
                is_anim = True
                break

        # Check voor flip animatie op de hole card (tweede kaart)
        if i == 1 and flip_anim and flip_anim['active']:
            draw_card_animated(screen, flip_anim)  # Teken flip animatie
            is_anim = True

        # Als de kaart niet geanimeerd wordt, teken hem normaal
        if not is_anim:
            if i == 1 and not reveal_dealer:
                # Tweede kaart (hole card) is verborgen tot reveal
                img = card_back_img
            else:
                if i == 1 and hide_hole:
                    # Verberg hole card tijdens split eerste hand
                    img = card_back_img
                else:
                    # Laat de echte kaart zien
                    try:
                        img = pygame.image.load(f"cards/{c}.png")
                    except:
                        img = card_back_img

            # Schaal kaart
            img = pygame.transform.scale(img, (CARD_WIDTH, CARD_HEIGHT))
            screen.blit(img, (card_x, card_y))

    # Laat dealer score zien (alleen als we niet in bet popup zijn)
    if not show_bet_popup:
        # Toon "?" als dealer nog niet revealed is, anders de echte score
        dealer_display = dealer_score if reveal_dealer else "?"
        screen.blit(smaller_font.render(f"Dealer: {dealer_display}", True, "white"),
                   (dealer_start, 50 + CARD_HEIGHT + 10))


    # SPELER KAARTEN
    # Bepaal welke handen we moeten tekenen (split of normale hand)
    all_hands = split_hands if split_mode else [my_hand]
    hand_y = HEIGHT//2 + 50  # Y positie voor speler kaarten

    if split_mode:
        # SPLIT MODE: Teken twee handen naast elkaar
        spacing_between_hands = 80  # Ruimte tussen de twee handen

        # Bereken totale breedte van beide handen
        total_width = len(all_hands[0])*CARD_WIDTH + spacing_between_hands + len(all_hands[1])*CARD_WIDTH

        # Bereken start X zodat beide handen gecentreerd zijn
        start_x = (WIDTH - total_width)//2

        # Teken elke hand
        for idx, hand in enumerate(all_hands):
            # Bereken X positie voor deze hand
            if idx == 0:
                # Linker hand
                hand_x = start_x
            else:
                # Rechter hand (na spacing)
                hand_x = start_x + len(all_hands[0])*CARD_WIDTH + spacing_between_hands

            # Teken elke kaart in deze hand
            for i, c in enumerate(hand):
                card_x = hand_x + i*CARD_WIDTH

                # Check of deze kaart geanimeerd wordt
                is_anim = False
                for anim in animations:
                    if anim['active'] and anim['card'] == c:
                        draw_card_animated(screen, anim)
                        is_anim = True
                        break

                # Teken kaart normaal als niet geanimeerd
                if not is_anim:
                    try:
                        img = pygame.image.load(f"cards/{c}.png")
                    except:
                        img = card_back_img
                    img = pygame.transform.scale(img, (CARD_WIDTH, CARD_HEIGHT))
                    screen.blit(img, (card_x, hand_y))

            # Laat score zien voor deze hand
            if not show_bet_popup:
                score = calculate_score(hand)
                label = f"Left hand: {score}" if idx == 0 else f"Right hand: {score}"
                screen.blit(smaller_font.render(label, True, "white"),
                            (hand_x, hand_y + CARD_HEIGHT + 10))

            # Teken pijltje bij actieve hand
            if idx == current_hand_index and hand_active:
                arrow = font.render("`´", True, "white")
                arrow_x = hand_x + len(hand)*CARD_WIDTH//2 - arrow.get_width()//2
                arrow_y = hand_y - 40
                screen.blit(arrow, (arrow_x, arrow_y))
    else:
        # NORMALE HAND: één hand gecentreerd
        hand_x = (WIDTH - len(my_hand)*CARD_WIDTH)//2

        # elke kaart
        for i, c in enumerate(my_hand):
            card_x = hand_x + i*CARD_WIDTH

            # Check of deze kaart geanimeerd wordt
            is_anim = False
            for anim in animations:
                if anim['active'] and anim['card'] == c:
                    draw_card_animated(screen, anim)
                    is_anim = True
                    break

            # Teken kaart normaal als niet geanimeerd
            if not is_anim:
                try:
                    img = pygame.image.load(f"cards/{c}.png")
                except:
                    img = card_back_img
                img = pygame.transform.scale(img, (CARD_WIDTH, CARD_HEIGHT))
                screen.blit(img, (card_x, hand_y))

        # Laat score zien
        if not show_bet_popup:
            score = calculate_score(my_hand)
            screen.blit(smaller_font.render(f"Your hand: {score}", True, "white"),
                        (hand_x, hand_y + CARD_HEIGHT + 10))

    # CONTROLS
    key_lines = ["ENTER=Hit", "SPACE=Stand"] # Basis controls (altijd beschikbaar)

    # Check of split beschikbaar is
    can_show_split = (not split_mode) and (len(my_hand) == 2) and can_split(my_hand) and (balance >= original_bet)
    if can_show_split:
        key_lines.append("E=Split")

    # Check of double down beschikbaar is
    can_show_double = False
    if split_mode:
        # Bij split: check voor actieve hand
        hb = hand_bets[current_hand_index] if current_hand_index < len(hand_bets) else original_bet
        can_show_double = (len(split_hands[current_hand_index]) == 2) and (balance >= hb)
    else:
        # Normale hand:
        can_show_double = (len(my_hand) == 2) and (balance >= original_bet)

    if can_show_double and not double_down_used:
        key_lines.append("TAB=Double down")

    # Alle keybinds
    for i, line in enumerate(key_lines):
        line_surface = smaller_font.render(line, True, "white")
        screen.blit(line_surface, (50, 30 + i * 35))

    # SALDO EN INZET
    # saldo linksonder
    screen.blit(smaller_font.render(f"Balance: €{balance}", True, "white"), (50, HEIGHT - 100))

    # Bereken en teken totale inzet (inclusief split/double down)
    total_bet_display = get_total_bet_display()
    screen.blit(smaller_font.render(f"Total bet: €{total_bet_display}", True, "white"), (50, HEIGHT - 70))


# ANIMATION FUNCTIES
def update_animations():
    global dealing, flip_anim, animations

    # Update alle actieve kaart animaties
    for anim in animations[:]:  # [:] maakt een kopie zodat we veilig kunnen verwijderen
        now = pygame.time.get_ticks()
        elapsed = now - anim['start_time']

        # Als de animatie klaar is (elapsed > duration), markeer als inactief
        if elapsed >= anim['duration']:
            anim['active'] = False

        # Verwijder inactieve animaties
        if not anim['active']:
            animations.remove(anim)

    # Update flip animatie (voor dealer's hole card)
    if flip_anim:
        now = pygame.time.get_ticks()
        elapsed = now - flip_anim['start_time']

        if elapsed >= flip_anim['duration']:
            flip_anim['active'] = False

        # Verwijder als voltooid
        if not flip_anim['active']:
            flip_anim = None

    # Check of dealing klaar is (alle animaties voltooid)
    if dealing and len(animations) == 0:
        dealing = False


# EVENT HANDLING
def handle_menu_click(pos):
    global game_state, current_bet, show_bet_popup, active, outcome, my_hand, dealer_hand, bankrupt_popup, run

    buttons = draw_menu()

    if buttons and buttons[0].collidepoint(pos):  # Start knop
        # Pas inzet aan als saldo lager is dan max_bet
        if balance < max_bet:
            current_bet = min(current_bet, balance)
        game_state = "playing"
        show_bet_popup = True
        active = False
        outcome = 0
        my_hand, dealer_hand = [], []
    elif buttons and buttons[1].collidepoint(pos):  # Rules knop
        game_state = "rules"
    elif buttons and buttons[2].collidepoint(pos):  # Quit knop
        return False

    # Bankrupt popup quit knop
    if bankrupt_popup and len(buttons) >= 4 and buttons[3].collidepoint(pos):
        return False

    return True

def handle_rules_click(pos):
    global game_state

    buttons = draw_rules()

    if buttons and buttons[0].collidepoint(pos):  # Back knop
        game_state = "menu"

def handle_bet_popup_click(pos):
    global balance, current_bet, show_bet_popup, active, hand_active, initial_deal, reveal_dealer, outcome, split_mode, split_hands, current_hand_index, double_down_used, original_bet, hand_bets, game_deck, animations, flip_anim, dealing, dealer_has_drawn

    buttons = draw_bet_popup()

    if buttons[0].collidepoint(pos):  # Plus knop
        # Verhoog inzet met €100
        effective_max = balance if balance < max_bet else max_bet
        if current_bet + 100 <= effective_max:
            current_bet = min(current_bet + 100, effective_max)
        else:
            current_bet = effective_max
    elif buttons[1].collidepoint(pos):  # Min knop
        # Verlaag inzet met €100
        current_bet = max(current_bet - 100, min_bet)
    elif buttons[2].collidepoint(pos):  # Deal knop
        # Start nieuwe ronde
        effective_max = balance if balance < max_bet else max_bet
        if current_bet > effective_max:
            current_bet = effective_max
        if current_bet <= balance:
            # Trek inzet af van saldo
            balance -= current_bet
            original_bet = current_bet
            hand_bets = [original_bet]

            # Reset alle game variabelen
            active = True
            hand_active = True
            initial_deal = True
            reveal_dealer = False
            outcome = 0
            split_mode = False
            split_hands = []
            current_hand_index = 0
            double_down_used = False
            show_bet_popup = False
            dealer_has_drawn = False  # Reset dealer_has_drawn flag

            game_deck = copy.deepcopy(one_deck * decks) # Maak nieuw deck

            # Reset animaties
            animations.clear()
            flip_anim = None
            dealing = False

def handle_result_popup_click(pos):
    global show_bet_popup, outcome, my_hand, dealer_hand, split_mode, split_hands, current_hand_index, hand_bets, current_bet, hand_active, reveal_dealer, result_time, result_title, result_lines, result_net, game_state, animations, flip_anim, dealing, payout_done

    buttons = popup_result()

    if buttons[0].collidepoint(pos):  # New game knop
        # Start nieuwe ronde
        show_bet_popup = True
        outcome = 0
        my_hand, dealer_hand = [], []
        payout_done = False
        split_mode = False
        split_hands = []
        current_bet = original_bet
        current_hand_index = 0
        hand_bets = []
        hand_active = False
        reveal_dealer = False
        result_time = None
        result_title = ""
        result_lines = []
        result_net = 0
        animations.clear()
        flip_anim = None
        dealing = False
    elif buttons[1].collidepoint(pos):  # Menu knop
        # Terug naar hoofdmenu
        game_state = "menu"
        show_bet_popup = False
        my_hand, dealer_hand = [], []
        outcome = 0
        reveal_dealer = False
        split_mode = False
        split_hands = []
        hand_bets = []
        result_time = None
        result_title = ""
        result_lines = []
        result_net = 0
        animations.clear()
        flip_anim = None
        dealing = False

def handle_playing_keydown(key):
    global my_hand, game_deck, dealer_hand, split_hands, current_hand_index, hand_active, reveal_dealer, double_down_used, balance, hand_bets, split_mode, player_score, dealing

    # ENTER - HIT
    if key == pygame.K_RETURN:
        handle_hit()
    # SPACE - STAND
    elif key == pygame.K_SPACE:
        handle_stand()
    # TAB - DOUBLE DOWN
    elif key == pygame.K_TAB:
        handle_double_down()
    # E - SPLIT
    elif key == pygame.K_e:
        handle_split()

def handle_hit():
    global my_hand, game_deck, split_hands, current_hand_index, hand_active, player_score, dealing, animations, flip_anim, reveal_dealer

    if split_mode:
        # Split mode: pak kaart voor actieve hand
        split_hands[current_hand_index], game_deck = deal_cards(split_hands[current_hand_index], game_deck)

        # Bereken positie voor nieuwe kaart
        all_hands = split_hands
        hand_y = HEIGHT//2 + 50
        spacing_between_hands = 80
        total_width = len(all_hands[0])*CARD_WIDTH + spacing_between_hands + len(all_hands[1])*CARD_WIDTH
        start_x = (WIDTH - total_width)//2

        if current_hand_index == 0:
            hand_x = start_x
        else:
            hand_x = start_x + len(all_hands[0])*CARD_WIDTH + spacing_between_hands

        card_x = hand_x + (len(split_hands[current_hand_index])-1)*CARD_WIDTH
        create_deal_animation(split_hands[current_hand_index][-1], (card_x, hand_y))

        # Check voor bust
        sc = calculate_score(split_hands[current_hand_index])
        if sc > 21:  # Bust
            hand_active = False
            reveal_dealer = True
    else:
        # Normale hand: pak kaart
        my_hand, game_deck = deal_cards(my_hand, game_deck)
        hand_y = HEIGHT//2 + 50
        hand_x = (WIDTH - len(my_hand)*CARD_WIDTH)//2
        card_x = hand_x + (len(my_hand)-1)*CARD_WIDTH
        create_deal_animation(my_hand[-1], (card_x, hand_y))

        player_score = calculate_score(my_hand)
        if player_score > 21:  # Bust
            hand_active = False
            reveal_dealer = True

def handle_stand():
    global hand_active, current_hand_index, split_mode, reveal_dealer, dealer_hand, flip_anim

    hand_active = False
    reveal_dealer = True

    # flip animatie voor dealer's hole card (alleen als we bij hand 1 zijn of geen split)
    if not split_mode or (split_mode and current_hand_index == 1):
        dealer_start = (WIDTH - len(dealer_hand)*CARD_WIDTH)//2
        hole_card_pos = (dealer_start + CARD_WIDTH, 50)
        create_flip_animation(dealer_hand[1], hole_card_pos)


def handle_double_down():
    global split_mode, split_hands, current_hand_index, balance, hand_bets, my_hand, game_deck, double_down_used, hand_active, reveal_dealer, dealer_hand, flip_anim, animations, dealing

    if split_mode:
        # Double down in split mode
        active_hand = split_hands[current_hand_index]
        if len(active_hand) == 2:
            hb = hand_bets[current_hand_index] if current_hand_index < len(hand_bets) else original_bet
            if balance >= hb and not double_down_used:
                # Trek geld af en verdubbel inzet
                balance -= hb
                hand_bets[current_hand_index] = hb * 2

                # Pak één kaart
                split_hands[current_hand_index], game_deck = deal_cards(split_hands[current_hand_index], game_deck)

                # Bereken positie voor nieuwe kaart
                all_hands = split_hands
                hand_y = HEIGHT//2 + 50
                spacing_between_hands = 80
                total_width = len(all_hands[0])*CARD_WIDTH + spacing_between_hands + len(all_hands[1])*CARD_WIDTH
                start_x = (WIDTH - total_width)//2

                if current_hand_index == 0:
                    hand_x = start_x
                else:
                    hand_x = start_x + len(all_hands[0])*CARD_WIDTH + spacing_between_hands

                card_x = hand_x + (len(split_hands[current_hand_index])-1)*CARD_WIDTH
                create_deal_animation(split_hands[current_hand_index][-1], (card_x, hand_y))

                double_down_used = True
                hand_active = False
                # Reveal dealer als we bij tweede hand zijn
                if current_hand_index == 1:
                    reveal_dealer = True
                    dealer_start = (WIDTH - len(dealer_hand)*CARD_WIDTH)//2
                    hole_card_pos = (dealer_start + CARD_WIDTH, 50)
                    create_flip_animation(dealer_hand[1], hole_card_pos)
    else:
        # Double down in normale hand
        if len(my_hand) == 2 and not double_down_used and balance >= original_bet:
            # Trek geld af en verdubbel inzet
            balance -= original_bet
            if len(hand_bets) == 0:
                hand_bets = [original_bet]
            hand_bets[0] = hand_bets[0] * 2

            # Pak één kaart
            my_hand, game_deck = deal_cards(my_hand, game_deck)
            hand_y = HEIGHT//2 + 50
            hand_x = (WIDTH - len(my_hand)*CARD_WIDTH)//2
            card_x = hand_x + (len(my_hand)-1)*CARD_WIDTH
            create_deal_animation(my_hand[-1], (card_x, hand_y))

            double_down_used = True
            hand_active = False
            reveal_dealer = True
            # Maak flip animatie voor dealer's hole card
            dealer_start = (WIDTH - len(dealer_hand)*CARD_WIDTH)//2
            hole_card_pos = (dealer_start + CARD_WIDTH, 50)
            create_flip_animation(dealer_hand[1], hole_card_pos)

def handle_split():
    global my_hand, split_mode, split_hands, balance, original_bet, hand_bets, current_hand_index, game_deck, animations, dealing, hand_active, reveal_dealer

    if not split_mode and len(my_hand) == 2 and balance >= original_bet:
        # Check of we kunnen splitten
        if can_split(my_hand) and balance >= original_bet:
            # Trek geld af voor tweede hand
            balance -= original_bet

            # Activeer split mode
            split_mode = True
            split_hands = [[my_hand[0]], [my_hand[1]]]  # Maak twee handen met elk één kaart
            hand_bets = [original_bet, original_bet]  # Beide handen hebben dezelfde inzet
            my_hand = split_hands[0]
            current_hand_index = 0  # Start met eerste hand

            # Deel eerste kaart aan eerste hand
            split_hands[0], game_deck = deal_cards(split_hands[0], game_deck)

            # Bereken positie voor nieuwe kaart
            all_hands = split_hands
            hand_y = HEIGHT//2 + 50
            spacing_between_hands = 80
            total_width = len(all_hands[0])*CARD_WIDTH + spacing_between_hands + len(all_hands[1])*CARD_WIDTH
            start_x = (WIDTH - total_width)//2
            hand_x = start_x
            card_x = hand_x + CARD_WIDTH
            create_deal_animation(split_hands[0][-1], (card_x, hand_y))

            hand_active = True
            reveal_dealer = False


# GAME LOGIC
def initial_deal_cards():
    global my_hand, dealer_hand, game_deck, player_score, dealer_score, initial_deal, hand_bets, outcome, result_title, result_lines, result_net, payout_done, hand_active, reveal_dealer, result_time, balance

    dealer_start = (WIDTH - 2*CARD_WIDTH)//2
    hand_y = HEIGHT//2 + 50
    player_start = (WIDTH - 2*CARD_WIDTH)//2

    # Deel 2 kaarten aan speler en dealer
    for i in range(2):
        # Deel kaart aan speler
        my_hand, game_deck = deal_cards(my_hand, game_deck)
        # Deel kaart aan dealer
        dealer_hand, game_deck = deal_cards(dealer_hand, game_deck)

        # Maak animaties voor beide kaarten
        # Elke kaart heeft steeds delay meer dan de vorige
        create_deal_animation(my_hand[i], (player_start + i*CARD_WIDTH, hand_y), delay=i*500)

        # Tweede dealer kaart is verborgen (achterkant)
        is_back = (i == 1)
        create_deal_animation(dealer_hand[i], (dealer_start + i*CARD_WIDTH, 50), is_back=is_back, delay=i*200)

    initial_deal = False

    # Initialiseer hand_bets als we niet in split mode zijn
    if not split_mode:
        hand_bets = [original_bet]

    # Bereken scores
    player_score = calculate_score(my_hand)
    dealer_score = calculate_score(dealer_hand)

    # CHECK VOOR BLACKJACK
    if player_score == 21 and dealer_score != 21:
        # Speler heeft blackjack! Betaalt 3:2 (1.5x inzet)
        outcome = 5
        balance += int(original_bet * 2.25)  # Inzet terug + 1.5x winst
        hand_active = False
        reveal_dealer = True
        payout_done = True
        result_time = pygame.time.get_ticks()
        result_title = "Blackjack!"
        result_lines = [f"The dealer has {dealer_score}, you have {player_score}.", f"You win €{int(original_bet * 1.25)}!"]
        result_net = int(original_bet * 1.25)
    elif dealer_score == 21 and player_score != 21:
        # Dealer heeft blackjack, speler verliest
        outcome = 1
        hand_active = False
        reveal_dealer = True
        payout_done = True
        result_time = pygame.time.get_ticks()
        result_title = "You lost..."
        result_lines = [f"The dealer has {dealer_score}, you have {player_score}.", "You lose."]
        result_net = -original_bet
    elif dealer_score == 21 and player_score == 21:
        # Beide hebben blackjack - push (gelijkspel)
        outcome = 4
        balance += original_bet  # Inzet terug
        payout_done = True
        hand_active = False
        reveal_dealer = True
        result_time = pygame.time.get_ticks()
        result_title = "Push!"
        result_lines = [f"The dealer has {dealer_score}, you have {player_score}.","Push."]
        result_net = 0

def handle_dealer_draws():
    global dealer_hand, game_deck, dealer_score, dealer_has_drawn

    if dealer_has_drawn:
        return

    dealer_has_drawn = True

    dealer_score = calculate_score(dealer_hand)

    while dealer_score < 17:
        # Pak een kaart
        dealer_hand, game_deck = deal_cards(dealer_hand, game_deck)
        
        dealer_score = calculate_score(dealer_hand)

        # Maak animatie voor nieuwe kaart
        dealer_start = (WIDTH - len(dealer_hand)*CARD_WIDTH)//2
        card_x = dealer_start + (len(dealer_hand)-1)*CARD_WIDTH
        create_deal_animation(dealer_hand[-1], (card_x, 50), delay=300)

def check_normal_hand_outcome():
    global player_score, dealer_score, outcome, balance, hand_bets, result_title, result_lines, result_net, payout_done, current_bet, result_time, reveal_dealer, dealer_hand, flip_anim, my_hand, game_deck

    player_score = calculate_score(my_hand)

    if player_score > 21:
        # Speler bust
        outcome = 1
        result_title = "You busted!"
        result_lines = [f"You have busted ({player_score}).", "You lose."]
        result_net = -hand_bets[0] if len(hand_bets)>0 else -original_bet
        payout_done = True
        result_time = pygame.time.get_ticks()
    else:
        # Speler niet bust - vergelijk met dealer
        handle_dealer_draws()
        dealer_score = calculate_score(dealer_hand)
        reveal_dealer = True
        dealer_start = (WIDTH - len(dealer_hand)*CARD_WIDTH)//2
        hole_card_pos = (dealer_start + CARD_WIDTH, 50)
        create_flip_animation(dealer_hand[1], hole_card_pos)

        if dealer_score > 21:
            # Dealer bust
            outcome = 2
            hb = hand_bets[0] if len(hand_bets)>0 else original_bet
            balance += hb * 2
            result_title = "Dealer busted!"
            result_lines = [f"The dealer has busted ({dealer_score}).",  f"You have {player_score}.", f"You win €{hb}!"]
            result_net = hb
        elif player_score > dealer_score:
            # Speler heeft hogere score
            outcome = 2
            hb = hand_bets[0] if len(hand_bets)>0 else original_bet
            balance += hb * 2
            result_title = "You won!"
            result_lines = [f"The dealer has {dealer_score}, you have {player_score}.", f"You win €{hb}!"]
            result_net = hb
        elif dealer_score > player_score:
            # Dealer heeft hogere score
            outcome = 1
            result_title = "You lost..."
            result_lines = [f"The dealer has {dealer_score}, you have {player_score}.", "You lose."]
            result_net = - (hand_bets[0] if len(hand_bets)>0 else original_bet)
        else:
            # Gelijke score - push
            outcome = 4
            hb = hand_bets[0] if len(hand_bets)>0 else original_bet
            balance += hb
            result_title = "Push!"
            result_lines = [f"The dealer has {dealer_score}, you have {player_score}.", "Push."]
            result_net = 0

        payout_done = True
        current_bet = original_bet
        result_time = pygame.time.get_ticks()

def check_split_hand_outcome():
    global split_hands, dealer_score, outcome, balance, hand_bets, result_lines, result_title, result_net, payout_done, current_bet, result_time, reveal_dealer, dealer_hand, flip_anim, game_deck

    # Reveal dealer en laat hem kaarten trekken
    if not reveal_dealer:
        handle_dealer_draws()
        reveal_dealer = True

        dealer_start = (WIDTH - len(dealer_hand)*CARD_WIDTH)//2
        hole_card_pos = (dealer_start + CARD_WIDTH, 50)
        create_flip_animation(dealer_hand[1], hole_card_pos)

    dealer_score = calculate_score(dealer_hand)

    # Bereken uitkomst voor beide handen
    score_left = calculate_score(split_hands[0])
    score_right = calculate_score(split_hands[1])
    net_gain = 0  # Totale winst/verlies

    result_lines = [f"Dealer: {dealer_score}"]

    # LINKER HAND
    hb_left = hand_bets[0] if len(hand_bets) > 0 else original_bet
    if score_left > 21:
        # Bust - verloren
        result_lines.append(f"Left hand ({score_left}): BUST - lose €{hb_left}")
        net_gain -= hb_left
    elif dealer_score > 21 or score_left > dealer_score:
        # Gewonnen (dealer bust of hogere score)
        result_lines.append(f"Left hand ({score_left}): WIN - €{hb_left}")
        net_gain += hb_left
        balance += hb_left * 2  # Inzet terug + winst
    elif score_left < dealer_score:
        # Verloren (lagere score)
        result_lines.append(f"Left hand ({score_left}): LOSE - €{hb_left}")
        net_gain -= hb_left
    else:
        # Push (gelijke score)
        result_lines.append(f"Left hand ({score_left}): PUSH")
        balance += hb_left  # Inzet terug

    # RECHTER HAND
    hb_right = hand_bets[1] if len(hand_bets) > 1 else original_bet
    if score_right > 21:
        # Bust - verloren
        result_lines.append(f"Right hand ({score_right}): BUST - lose €{hb_right}")
        net_gain -= hb_right
    elif dealer_score > 21 or score_right > dealer_score:
        # Gewonnen
        result_lines.append(f"Right hand ({score_right}): WIN - €{hb_right}")
        net_gain += hb_right
        balance += hb_right * 2
    elif score_right < dealer_score:
        # Verloren
        result_lines.append(f"Right hand ({score_right}): LOSE - €{hb_right}")
        net_gain -= hb_right
    else:
        # Push
        result_lines.append(f"Right hand ({score_right}): PUSH")
        balance += hb_right

    # TOTAAL RESULTAAT
    result_lines.append("")  # Lege regel voor spacing
    if net_gain > 0:
        result_lines.append(f"Total: WIN €{net_gain}!")
        result_title = "You won!"
    elif net_gain < 0:
        result_lines.append(f"Total: LOSE €{abs(net_gain)}")
        result_title = "You lost..."
    else:
        result_lines.append("Total: PUSH")
        result_title = "Push!"

    payout_done = True
    outcome = 1  # Zet outcome zodat popup verschijnt
    current_bet = original_bet
    result_time = pygame.time.get_ticks()


game_deck = copy.deepcopy(one_deck * decks) # Maak een nieuw deck met alle kaarten

run = True
show_bet_popup = False
payout_done = False
result_time = None

while run:
    timer.tick(fps)
    screen.fill('black') # Maak het scherm zwart (wordt overschreven door draw functies)
    buttons = [] # Lijst voor knoppen

    # UPDATE ANIMATIES
    update_animations()

    # MAIN MENU
    if game_state == "menu":
        buttons = draw_menu()
    elif game_state == "rules":
        buttons = draw_rules()
    elif game_state == "playing":
        draw_playing()
        if show_bet_popup:
            buttons = draw_bet_popup()
            payout_done = False
        elif outcome != 0 and result_time is not None:
            # Wacht met resultaat popup tot delay voorbij is
            if pygame.time.get_ticks() - result_time >= result_delay_ms:
                buttons = popup_result()

    # EVENT HANDLING
    for event in pygame.event.get():
        # QUIT
        if event.type == pygame.QUIT:
            run = False

        # MOUSE CLICK EVENT
        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == "menu":
                run = handle_menu_click(event.pos)
            elif game_state == "rules":
                handle_rules_click(event.pos)
            elif game_state == "playing":
                if show_bet_popup and buttons:
                    handle_bet_popup_click(event.pos)
                elif outcome != 0 and buttons:
                    handle_result_popup_click(event.pos)

        # KEYBOARD CONTROLS
        if event.type == pygame.KEYDOWN and game_state == "playing" and active and hand_active and not show_bet_popup and not dealing:
            handle_playing_keydown(event.key)

    # GAME LOGIC
    if game_state == "playing" and active and not show_bet_popup:
        if initial_deal:
            initial_deal_cards()

        # Update player score
        if not split_mode:
            player_score = calculate_score(my_hand)

        if outcome == 0 and not dealing:
            # Controleer of we een outcome moeten bepalen
            if not hand_active and reveal_dealer:
                if split_mode and current_hand_index == 0:
                    # Ga naar tweede hand in split mode
                    current_hand_index = 1
                    hand_active = True
                    reveal_dealer = False

                    # Deel kaart aan tweede hand als die nog maar 1 kaart heeft
                    if len(split_hands[1]) == 1:
                        split_hands[1], game_deck = deal_cards(split_hands[1], game_deck)

                        # Bereken positie voor nieuwe kaart
                        all_hands = split_hands
                        hand_y = HEIGHT//2 + 50
                        spacing_between_hands = 80
                        total_width = len(all_hands[0])*CARD_WIDTH + spacing_between_hands + len(all_hands[1])*CARD_WIDTH
                        start_x = (WIDTH - total_width)//2
                        hand_x = start_x + len(split_hands[0])*CARD_WIDTH + spacing_between_hands
                        card_x = hand_x + CARD_WIDTH
                        create_deal_animation(split_hands[1][-1], (card_x, hand_y))
                elif split_mode and current_hand_index == 1:
                    # Klaar met beide handen in split mode
                    check_split_hand_outcome()
                else:
                    # Normale hand of eerste check na deal
                    if len(my_hand) > 0:  # Zorg ervoor dat we kaarten hebben
                        check_normal_hand_outcome()

    # CHECK VOOR BANKRUPT
    if balance <= 0 and not bankrupt_popup:
        bankrupt_popup = True
        game_state = "menu"

    pygame.display.flip()

pygame.quit()