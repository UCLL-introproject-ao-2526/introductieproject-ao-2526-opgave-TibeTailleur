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

# CARDANIMATION
class CardAnimation:
    def __init__(self, card, start_pos, end_pos, duration=2000, flip=False, delay=0):
        self.card = card  # Naam van de kaart
        self.start = start_pos  # Start positie (x, y) in pixels
        self.end = end_pos  # Eind positie (x, y) in pixels
        self.duration = duration  # Duur van animatie in milliseconden
        self.start_time = pygame.time.get_ticks() + delay  # Wanneer animatie start (huidige tijd + delay)
        self.flip = flip  # Boolean: moet de kaart omdraaien?
        self.flip_prog = 0 if flip else 1  # Voortgang van flip (0-1), start op 0 als we flippen
        self.active = True  # Boolean: is animatie nog actief?
        self.delay = delay  # Vertraging voor start in milliseconden
        self.pos = start_pos  # Huidige positie van de kaart
        
    def update(self):
        # Als animatie niet meer actief is, doe niets
        if not self.active:
            return
        
        # Haal de huidige tijd op in milliseconden
        now = pygame.time.get_ticks()
        
        # Als we nog in de delay periode zitten, wacht dan
        if now < self.start_time:
            return
        
        # Bereken hoeveel tijd er verstreken is sinds de start
        elapsed = now - self.start_time
        
        # Bereken de voortgang als een getal: 0.0 = net gestart, 1.0 = klaar
        progress = min(elapsed / self.duration, 1.0)
        
        # EASING FUNCTIE - Zorgt voor vloeiende beweging
        t = progress
        eased = 1 - pow(1 - t, 2)
        
        # Bereken de huidige positie tussen start en eind
        # We interpoleren (mengen) tussen start en eind op basis van eased progress
        # Formule: start + (eind - start) * progress
        self.pos = (
            self.start[0] + (self.end[0] - self.start[0]) * eased,  # X positie
            self.start[1] + (self.end[1] - self.start[1]) * eased   # Y positie
        )

        # Als de kaart moet flippen, update dan de flip voortgang
        # Dit wordt gebruikt in de draw functie om de kaart te schalen
        if self.flip:
            self.flip_prog = eased
        
        # Als progress 1.0 is (100%), dan is de animatie klaar
        if progress >= 1.0:
            self.active = False  # Zet animatie op inactief
            self.pos = self.end  # Zorg dat de positie exact op het eindpunt is
        
    def draw(self, surface):
        # Als we nog in de delay periode zitten, teken niets
        if pygame.time.get_ticks() < self.start_time:
            return
        
        try:
            # FLIP ANIMATIE
            if self.flip:          
                if self.flip_prog < 0.5:
                    # Eerste helft van de flip laat de achterkant van de kaart zien
                    img = card_back_img
                    # Bij progress 0.0: scale = 1.0 (volle breedte)
                    # Bij progress 0.5: scale = 0.0 (geen breedte)
                    scale = 1 - (self.flip_prog * 2)
                else:
                    # Tweede helft van de flip laat de voorkant van de kaart zien
                    img = pygame.image.load(f"cards/{self.card}.png")
                    # Bij progress 0.5: scale = 0.0 (geen breedte)
                    # Bij progress 1.0: scale = 1.0 (volle breedte)
                    scale = (self.flip_prog - 0.5) * 2
                
                # Schaal de kaart naar de standaard grootte
                img = pygame.transform.scale(img, (CARD_WIDTH, CARD_HEIGHT))
                
                # Bereken de geschaalde breedte op basis van de scale factor
                scaled_w = int(CARD_WIDTH * scale)
                
                # Alleen tonen als de breedte groter is dan 0
                if scaled_w > 0:
                    # Schaal de kaart naar de berekende breedte (hoogte blijft hetzelfde)
                    img = pygame.transform.scale(img, (scaled_w, CARD_HEIGHT))
                    
                    # Bereken x offset om de kaart op dezelfde plek te houden tijdens flip
                    x_offset = (CARD_WIDTH - scaled_w) // 2
                    
                    # toon de kaart op het scherm
                    surface.blit(img, (self.pos[0] + x_offset, self.pos[1]))
            else:
                if self.card == "BACK":
                    # Gebruik de achterkant afbeelding
                    img = card_back_img
                else:
                    # Laad de specifieke kaart afbeelding
                    img = pygame.image.load(f"cards/{self.card}.png")
                
                # Schaal de kaart
                img = pygame.transform.scale(img, (CARD_WIDTH, CARD_HEIGHT))
                
                # Teken de kaart op de huidige positie
                surface.blit(img, self.pos)
        except:
            # Als er iets fout gaat laat dan de achterkant van de kaart zien
            img = card_back_img
            img = pygame.transform.scale(img, (CARD_WIDTH, CARD_HEIGHT))
            surface.blit(img, self.pos)


# ANIMATIE VARIABELEN
animations = []  # Lijst met alle actieve CardAnimation objecten
dealing = False  # Boolean: zijn we nu kaarten aan het delen?
flip_anim = None  # Speciale animatie voor het omdraaien van de dealer's verborgen kaart

# Positie van het deck (buiten het scherm bovenaan)
DECK_POS = (WIDTH // 2 - CARD_WIDTH // 2, -CARD_HEIGHT - 50)


# HELPER FUNCTIES
def can_split(hand):
    if len(hand) != 2:
        return False
    
    # Haal de waarde van beide kaarten op (zonder de suit)
    # Bijvoorbeeld: "AH" wordt "A", "10C" wordt "10"
    v1 = hand[0][:-1]  # Waarde van eerste kaart
    v2 = hand[1][:-1]  # Waarde van tweede kaart
    
    # Lijst met alle 10's
    tens = ['10','J','Q','K']
    
    # Check of beide kaarten dezelfde waarde hebben
    # OF beide kaarten zijn 10's
    if v1 == v2 or (v1 in tens and v2 in tens):
        return True
    
    return False

def deal_cards(hand, deck):
    # Kies een willekeurige kaart uit het deck
    card = random.choice(deck)
    
    # Voeg de kaart toe aan de hand
    hand.append(card)
    
    # Verwijder de kaart uit het deck (kan niet twee keer gedeeld worden)
    deck.remove(card)
    
    return hand, deck

def calculate_score(hand):
    score = 0  # Start met score 0
    aces = 0  # Houd bij hoeveel Azen we hebben
    
    # Tel alle kaarten op
    for card in hand:
        # Haal de waarde van de kaart op (zonder suit)
        # Bijvoorbeeld: "AH" wordt "A", "10C" wordt "10"
        v = card[:-1]
        
        if v in ['J','Q','K']:
            # Plaatjes tellen als 10
            score += 10
        elif v == 'A':
            score += 11
            aces += 1  # tel aas bij
        else:
            # Nummers tellen als hun waarde
            score += int(v)
    
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
    
    # Zet dealing flag op True (voorkomt andere acties tijdens dealing)
    dealing = True
    
    # Bepaal welke kaart afbeelding we gebruiken
    card_name = "BACK" if is_back else card
    
    # Maak een nieuwe animatie vanaf het deck naar de eindpositie
    anim = CardAnimation(card_name, DECK_POS, end_pos, duration=800, delay=delay)
    
    # Voeg de animatie toe aan de lijst
    animations.append(anim)

def create_flip_animation(card, pos):
    global flip_anim
    
    # Maak een nieuwe flip animatie
    # Start en eind positie zijn hetzelfde (kaart blijft op dezelfde plek)
    flip_anim = CardAnimation(card, pos, pos, duration=600, flip=True)

def get_total_bet_display():
    if split_mode and len(hand_bets) >= 2:
        # Bij split: tel beide inzetten op
        return hand_bets[0] + hand_bets[1]
    elif len(hand_bets) > 0:
        # Bij double down of normale hand: gebruik hand_bets
        return hand_bets[0]
    else:
        # Fallback naar original_bet als hand_bets leeg is
        return original_bet


# DRAW FUNCTIES
def draw_menu():
    # Teken de achtergrond
    screen.blit(background_img, (0, 0))
    
    # Teken het logo gecentreerd bovenaan
    screen.blit(logo_img, ((WIDTH // 2 - logo_img.get_width() // 2), 50))
    
    # KNOPPEN
    spacing = 120  # Verticale ruimte tussen knoppen
    
    start_btn = pygame.Rect((WIDTH - 300)//2, 350, 300, 80)
    rules_btn = pygame.Rect((WIDTH - 300)//2, 350 + spacing, 300, 80)
    quit_btn = pygame.Rect((WIDTH - 300)//2, 350 + spacing * 2, 300, 80)
    
    # KNOPPEN MET HOVER EFFECT
    mouse_pos = pygame.mouse.get_pos()  # Haal muispositie op
    
    # elke knop
    for btn in [start_btn, rules_btn, quit_btn]:
        # Verander kleur bij hover
        color = (200,200,200) if btn.collidepoint(mouse_pos) else (255,255,255)
        
        # Teken de knop achtergrond met afgeronde hoeken
        pygame.draw.rect(screen, color, btn, border_radius=10)
        
        # Teken de knop rand (zwart, 3 pixels dik)
        pygame.draw.rect(screen, (0,0,0), btn, 3, border_radius=10)
    
    # Teken de tekst op elke knop
    for text, btn in zip(["Start","Rules","Quit"], [start_btn, rules_btn, quit_btn]):
        t = smaller_font.render(text, True, (0,0,0))  # Zwarte tekst
        screen.blit(t, t.get_rect(center=btn.center))  # Centreer tekst in knop

    # BANKRUPT POPUP
    if bankrupt_popup:
        # transparante overlay over het hele scherm
        overlay_full = pygame.Surface((WIDTH, HEIGHT))
        overlay_full.set_alpha(200)  # 200/255
        overlay_full.fill((0, 0, 0))  # Zwart
        screen.blit(overlay_full, (0, 0))
        
        # Maak de popup box
        w, h = WIDTH//2, HEIGHT//3
        popup = pygame.Surface((w, h))
        popup.fill("white")  # Witte achtergrond
        pygame.draw.rect(popup, "black", (0,0,w,h), 3, border_radius=15)  # Zwarte rand
        rect = popup.get_rect(center=(WIDTH//2, HEIGHT//2))  # Centreer op scherm
        
        # Bereken verticale centrering voor de tekst
        total_content_height = 60 + 40 + 60  # title + message + button
        start_y = (h - total_content_height) // 2
        
        # Teken titel
        t = font.render("You're broke!", True, "black")
        popup.blit(t, (w//2 - t.get_width()//2, start_y))
        
        # Teken bericht
        msg = smaller_font.render("You lost all your money.", True, "black")
        popup.blit(msg, (w//2 - msg.get_width()//2, start_y + 60))
        
        # Teken quit knop
        quit_btn2 = pygame.Rect(w//2 - 60, start_y + 120, 120, 50)
        pygame.draw.rect(popup, (230,230,230), quit_btn2, border_radius=8)
        pygame.draw.rect(popup, (0,0,0), quit_btn2, 2, border_radius=8)
        qtxt = smaller_font.render("Quit", True, "black")
        popup.blit(qtxt, qtxt.get_rect(center=quit_btn2.center))
        
        # Blit de popup op het scherm
        screen.blit(popup, rect.topleft)
        
        # Pas de quit button positie aan voor de echte scherm coördinaten
        quit_btn2_screen = pygame.Rect(rect.left + quit_btn2.left, rect.top + quit_btn2.top, quit_btn2.width, quit_btn2.height)
        return [start_btn, rules_btn, quit_btn, quit_btn2_screen]

    return [start_btn, rules_btn, quit_btn]

def draw_rules():
    #  achtergrond
    screen.blit(background_img, (0, 0))
    
    # titel
    title = font.render("Rules", True, "white")
    screen.blit(title, (50, 60))
    
    # REGELS
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
    
    # Teken tekst
    bt = smaller_font.render("BACK", True, (0,0,0))
    screen.blit(bt, bt.get_rect(center=back_btn.center))
    
    return [back_btn]

def draw_bet_popup():
    # popup
    w, h = WIDTH//2, HEIGHT//3
    overlay = pygame.Surface((w, h))
    overlay.fill("white")
    pygame.draw.rect(overlay, "black", (0,0,w,h), 3, border_radius=15)
    rect = overlay.get_rect(center=(WIDTH//2, HEIGHT//2))
    screen.blit(overlay, rect.topleft)

    # titel
    title = font.render("Place your bet", True, "black")
    screen.blit(title, (rect.centerx - title.get_width()//2, rect.top + 40))

    # SALDO EN INZET
    bal_text = smaller_font.render(f"Balance: €{balance}", True, "black")
    bet_text = smaller_font.render(f"Bet: €{current_bet}", True, "black")
    screen.blit(bal_text, (rect.centerx - bal_text.get_width()//2, rect.top + 110))
    screen.blit(bet_text, (rect.centerx - bet_text.get_width()//2, rect.top + 150))

    # PLUS EN MIN KNOPPEN
    # Deze knoppen staan naast de inzet tekst
    bet_y = rect.top + 150
    text_height = bet_text.get_height()
    
    plus_btn = pygame.Rect(rect.centerx + 80, bet_y + text_height//2 - 15, 40, 30)
    minus_btn = pygame.Rect(rect.centerx - 130, bet_y + text_height//2 - 15, 40, 30)
    
    deal_btn = pygame.Rect(rect.centerx - 100, bet_y + 80, 200, 60)

    # Teken alle knoppen
    for btn, txt in zip([plus_btn, minus_btn, deal_btn], ["+","-","DEAL"]):
        pygame.draw.rect(screen, (230,230,230), btn, border_radius=8)
        pygame.draw.rect(screen, (0,0,0), btn, 2, border_radius=8)
        t = smaller_font.render(txt, True, "black")
        screen.blit(t, t.get_rect(center=btn.center))

    return [plus_btn, minus_btn, deal_btn]

def popup_result():
    # POPUP HOOGTE OP BASIS VAN CONTENT
    title_height = 80  # Ruimte voor titel
    line_height = 35  # Hoogte per tekst regel
    button_area = 80  # Ruimte voor knoppen
    padding = 40  # Extra ruimte boven en onder
    
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
        screen.blit(txt, (rect.centerx - txt.get_width()//2, line_y))
        line_y += line_height

    # KNOPPEN
    button_y = rect.top + h - 80
    
    # New knop (start nieuwe ronde)
    again_btn = pygame.Rect(rect.centerx - 120, button_y, 100, 50)
    
    # Menu knop (terug naar hoofdmenu)
    menu_btn = pygame.Rect(rect.centerx + 20, button_y, 100, 50)
    
    # Teken beide knoppen
    for btn, txt in zip([again_btn, menu_btn], ["New","Menu"]):
        pygame.draw.rect(screen, (230,230,230), btn, border_radius=8)
        pygame.draw.rect(screen, (0,0,0), btn, 2, border_radius=8)
        t = smaller_font.render(txt, True, "black")
        screen.blit(t, t.get_rect(center=btn.center))

    return [again_btn, menu_btn]

def draw_playing():
    global flip_anim
    
    # Teken achtergrond
    screen.blit(background_img, (0, 0))
    
    # Teken klein logo rechtsboven
    screen.blit(logo_play_img, (WIDTH - logo_play_img.get_width() - 20, 20))

    # DEALER KAARTEN
    # dealer kaarten gecentreerd
    dealer_start = (WIDTH - len(dealer_hand)*CARD_WIDTH)//2

    # Bepaal of we de hole card (tweede kaart) moeten verbergen
    # Dit gebeurt tijdens split mode als we de eerste hand spelen
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
            if anim.active and anim.card == c:
                anim.draw(screen)  # Laat animatie de kaart tekenen
                is_anim = True
                break
        
        # Check voor flip animatie op de hole card (tweede kaart)
        if i == 1 and flip_anim and flip_anim.active:
            flip_anim.draw(screen)  # Laat flip animatie de kaart tekenen
            is_anim = True
        
        # Als de kaart niet geanimeerd wordt, teken hem normaal
        if not is_anim:
            # Bepaal welke afbeelding we moeten tonen
            if i == 0 and not reveal_dealer:
                # Eerste kaart is altijd verborgen tot reveal
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
            
            # Schaal en teken de kaart
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
                    if anim.active and anim.card == c:
                        anim.draw(screen)
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
                if anim.active and anim.card == c:
                    anim.draw(screen)
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
    # Basis controls (altijd beschikbaar)
    key_lines = ["ENTER=Hit", "SPACE=Stand"]

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


# MAIN GAME LOOP
game_deck = copy.deepcopy(one_deck * decks) # Maak een nieuw deck met alle kaarten

# Hoofdloop variabelen
run = True
show_bet_popup = False
payout_done = False
result_time = None

while run:
    timer.tick(fps)
    screen.fill('black') # Maak het scherm zwart (wordt overschreven door draw functies)
    buttons = [] # Lijst voor knoppen

    # UPDATE ANIMATIES
    # Update alle actieve kaart animaties
    for anim in animations[:]:  # [:] maakt een kopie zodat we veilig kunnen verwijderen
        anim.update()  # Update de animatie voor dit frame
        if not anim.active:
            # Verwijder voltooide animaties
            animations.remove(anim)
    
    # Update flip animatie (voor dealer's hole card)
    if flip_anim:
        flip_anim.update()
        if not flip_anim.active:
            flip_anim = None  # Verwijder als voltooid
    
    # Check of dealing klaar is (alle animaties voltooid)
    if dealing and len(animations) == 0:
        dealing = False

    # SCHERM SELECTOR
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
            # MENU KNOPPEN
            if game_state == "menu":
                if buttons and buttons[0].collidepoint(event.pos):  # Start knop
                    # Pas inzet aan als saldo lager is dan max_bet
                    if balance < max_bet:
                        current_bet = min(current_bet, balance)
                    game_state = "playing"
                    show_bet_popup = True
                    active = False
                    outcome = 0
                    my_hand, dealer_hand = [], []
                elif buttons and buttons[1].collidepoint(event.pos):  # Rules knop
                    game_state = "rules"
                elif buttons and buttons[2].collidepoint(event.pos):  # Quit knop
                    run = False
                # Bankrupt popup quit knop
                if bankrupt_popup and len(buttons) >= 4 and buttons[3].collidepoint(event.pos):
                    run = False

            # RULES SCHERM
            elif game_state == "rules":
                if buttons and buttons[0].collidepoint(event.pos):  # Back knop
                    game_state = "menu"

            # PLAYING SCHERM
            elif game_state == "playing":
                if show_bet_popup and buttons:
                    # BET POPUP KNOPPEN
                    if buttons[0].collidepoint(event.pos):  # Plus knop
                        # Verhoog inzet met €100
                        effective_max = balance if balance < max_bet else max_bet
                        if current_bet + 100 <= effective_max:
                            current_bet = min(current_bet + 100, effective_max)
                        else:
                            current_bet = effective_max
                    elif buttons[1].collidepoint(event.pos):  # Min knop
                        # Verlaag inzet met €100
                        current_bet = max(current_bet - 100, min_bet)
                    elif buttons[2].collidepoint(event.pos):  # Deal knop
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
                            
                            game_deck = copy.deepcopy(one_deck * decks) # Maak nieuw deck
                            
                            # Reset animaties
                            result_time = None
                            animations.clear()
                            flip_anim = None
                            dealing = False
                elif outcome != 0 and buttons:
                    # RESULTAAT POPUP KNOPPEN
                    if buttons[0].collidepoint(event.pos):  # New game knop
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
                    elif buttons[1].collidepoint(event.pos):  # Menu knop
                        # Terug naar hoofdmenu
                        game_state = "menu"
                        show_bet_popup = False
                        my_hand, dealer_hand = [], []
                        outcome = 0
                        reveal_dealer = False
                        player_score = 0
                        dealer_score = 0
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

        # KEYBOARD CONTROLS
        if event.type == pygame.KEYDOWN and game_state == "playing" and active and hand_active and not show_bet_popup and not dealing:
            # ENTER - HIT
            if event.key == pygame.K_RETURN:
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
                    if sc > 21:  # Bust - over 21
                        hand_active = False
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

            # SPACE - STAND
            elif event.key == pygame.K_SPACE:
                hand_active = False
                # Reveal dealer als we klaar zijn met beide handen (of geen split)
                if not split_mode or (split_mode and current_hand_index == 1):
                    reveal_dealer = True
                    # Maak flip animatie voor dealer's hole card
                    dealer_start = (WIDTH - len(dealer_hand)*CARD_WIDTH)//2
                    hole_card_pos = (dealer_start + CARD_WIDTH, 50)
                    create_flip_animation(dealer_hand[1], hole_card_pos)

            # TAB - DOUBLE DOWN
            elif event.key == pygame.K_TAB:
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

            # E - SPLIT
            elif event.key == pygame.K_e and not split_mode and len(my_hand) == 2 and balance >= original_bet:
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
    if game_state == "playing" and active and not show_bet_popup:
        # INITIAL DEAL - Deel de eerste kaarten
        if initial_deal:
            # Bereken posities voor kaarten
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
            
            # CHECK VOOR BLACKJAC
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

        # Update player score
        if not split_mode:
            player_score = calculate_score(my_hand)

        # DEALER DRAWS
        if reveal_dealer and outcome == 0 and not dealing:
            dealer_score = calculate_score(dealer_hand)
            while dealer_score < 17:
                # Dealer trekt een kaart
                dealer_hand, game_deck = deal_cards(dealer_hand, game_deck)
                
                # Maak animatie voor nieuwe kaart
                dealer_start = (WIDTH - len(dealer_hand)*CARD_WIDTH)//2
                card_x = dealer_start + (len(dealer_hand)-1)*CARD_WIDTH
                create_deal_animation(dealer_hand[-1], (card_x, 50), delay=300)
                
                # Herbereken score
                dealer_score = calculate_score(dealer_hand)

        if not hand_active and outcome == 0 and not dealing:
            if split_mode and current_hand_index == 0:
                # Ga naar tweede hand
                current_hand_index = 1
                
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
                
                # Activeer tweede hand
                hand_active = True
                reveal_dealer = False
            else:
                # BEPAAL UITKOMST (beide handen klaar of geen split)
                if split_mode:
                    # Reveal dealer en laat hem kaarten trekken
                    if not reveal_dealer:
                        dealer_score = calculate_score(dealer_hand)
                        dealer_start = (WIDTH - len(dealer_hand)*CARD_WIDTH)//2
                        hole_card_pos = (dealer_start + CARD_WIDTH, 50)
                        create_flip_animation(dealer_hand[1], hole_card_pos)
                        reveal_dealer = True
                        
                        # Dealer trekt kaarten tot 17 of hoger
                        while dealer_score < 17:
                            dealer_hand, game_deck = deal_cards(dealer_hand, game_deck)
                            dealer_start = (WIDTH - len(dealer_hand)*CARD_WIDTH)//2
                            card_x = dealer_start + (len(dealer_hand)-1)*CARD_WIDTH
                            create_deal_animation(dealer_hand[-1], (card_x, 50), delay=300)
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
                else:
                    player_score = calculate_score(my_hand)
                    
                    if player_score > 21:
                        # Speler bust - verloren
                        outcome = 1
                        result_title = "You busted!"
                        result_lines = [f"You have busted ({player_score}).", "You lose."]
                        result_net = -hand_bets[0] if len(hand_bets)>0 else -original_bet
                        payout_done = True
                        result_time = pygame.time.get_ticks()
                    else:
                        # Speler niet bust - vergelijk met dealer
                        if not reveal_dealer:
                            # Dealer trekt kaarten
                            dealer_score = calculate_score(dealer_hand)
                            while dealer_score < 17:
                                dealer_hand, game_deck = deal_cards(dealer_hand, game_deck)
                                dealer_start = (WIDTH - len(dealer_hand)*CARD_WIDTH)//2
                                card_x = dealer_start + (len(dealer_hand)-1)*CARD_WIDTH
                                create_deal_animation(dealer_hand[-1], (card_x, 50), delay=300)
                                dealer_score = calculate_score(dealer_hand)
                        
                        if dealer_score > 21:
                            # Dealer bust - speler wint
                            outcome = 2
                            hb = hand_bets[0] if len(hand_bets)>0 else original_bet
                            balance += hb * 2
                            result_title = "Dealer busted!"
                            result_lines = [f"The dealer has busted ({dealer_score}).",  f"You have {player_score}.", f"You win €{hb}!"]
                            result_net = hb
                        elif player_score > dealer_score:
                            # Speler heeft hogere score - wint
                            outcome = 2
                            hb = hand_bets[0] if len(hand_bets)>0 else original_bet
                            balance += hb * 2
                            result_title = "You won!"
                            result_lines = [f"The dealer has {dealer_score}, you have {player_score}.", f"You win €{hb}!"]
                            result_net = hb
                        elif dealer_score > player_score:
                            # Dealer heeft hogere score - speler verliest
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

    # CHECK VOOR BANKRUPT
    if balance <= 0 and not bankrupt_popup:
        bankrupt_popup = True
        game_state = "menu"

    pygame.display.flip()
pygame.quit()