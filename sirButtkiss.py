import pygame
from pygame import mixer
import os
import csv
import random
import button
#import levelEditor
from pygame.locals import *
mixer.init()
pygame.init()

#set the dimensions of the game window
screenWidth = 800
screenHeight = int(screenWidth * 0.8)

#initialize the game window, and tell it what the dimensions are
screen = pygame.display.set_mode((screenWidth, screenHeight))
#title the game window using .set_caption
pygame.display.set_caption('The Adventures of Sir Buttkiss!')

#timer which limits how quickly the game runs
clock = pygame.time.Clock()
FPS = 60

#game variables
GRAVITY = 0.75

SCROLL_THRESH = 300
MAX_LEVELS = 2

ROWS = 16
COLS = 100

tile_size = screenHeight // ROWS
tileTypes = 27

screen_scroll = 0
bg_scroll = 0

level = 0

start_game = False

#define player action variables
movingLeft = False
movingRight = False
shoot = False

#load music/sounds
pygame.mixer.music.load('music/music1.mp3')
pygame.mixer.music.set_volume(0.2)
pygame.mixer.music.play(-1, 0.0, 5000)

jump_fx = pygame.mixer.Sound('music/jump.mp3')
jump_fx.set_volume(0.03)

sword_fx = pygame.mixer.Sound('music/sword.mp3')
sword_fx.set_volume(0.5)

hurt_fx = pygame.mixer.Sound('music/hurt.mp3')
hurt_fx.set_volume(0.5)

heal_fx = pygame.mixer.Sound('music/heal.mp3')
heal_fx.set_volume(0.2)

coin_fx = pygame.mixer.Sound('music/coin.mp3')
coin_fx.set_volume(0.15)
#store tiles in a list
img_list = []
for x in range(tileTypes):
    img = pygame.image.load(f'backgrounds/Sprites/Tiles1/{x}.png')
    img  = pygame.transform.scale(img, (tile_size, tile_size))
    img_list.append(img)

#button images
start = pygame.image.load('backgrounds/start.png').convert_alpha()
exit = pygame.image.load('backgrounds/exit.png').convert_alpha()
restart = pygame.image.load('backgrounds/restart.png').convert_alpha()

start_img = pygame.transform.scale_by(start, 0.3)
exit_img = pygame.transform.scale_by(exit, 0.3)
restart_img = pygame.transform.scale_by(restart, 0.4)

#load images
sword_img = pygame.image.load('sprites/Knight_1/sword.png').convert_alpha()

#the order matters
sky_img = pygame.image.load('backgrounds/Sprites/Background/sky_cloud.png').convert_alpha()
sky_background = pygame.transform.scale_by(sky_img, 1.5)

mts_img = pygame.image.load('backgrounds/Sprites/Background/mountain2.png').convert_alpha()
mountain_background = pygame.transform.scale_by(mts_img, 2)

tree1_img = pygame.image.load('backgrounds/Sprites/Background/pine1.png').convert_alpha()
pines_background = pygame.transform.scale_by(tree1_img, 2)

tree2_img = pygame.image.load('backgrounds/Sprites/Background/pine2.png').convert_alpha()
pines2_background = pygame.transform.scale_by(tree2_img, 2)

#items
coin_image = pygame.image.load('backgrounds/Sprites/Tiles1/21.png').convert_alpha()
health_image = pygame.image.load('backgrounds/Sprites/Tiles1/26.png').convert_alpha()
items = {
    'Coin'      : coin_image,
    'Health'    : health_image
}

#define colors
BG = (129,237,249)
RED = (200,30,20)
WHITE = (255, 255, 255)

font = pygame.font.SysFont('Futura', 40)

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x,y))

def draw_bg():
    screen.fill(BG)
    width = sky_background.get_width()
    for x in range(5):
        screen.blit(sky_background, ((x * width) - bg_scroll * 0.5,0))
        screen.blit(mountain_background,((x * width) - bg_scroll * 0.6, screenHeight - mountain_background.get_height() - 300))
        screen.blit(pines_background, ((x * width) - bg_scroll * 0.7,screenHeight - pines_background.get_height() - 150))
        screen.blit(pines2_background, ((x * width) - bg_scroll * 0.8,screenHeight - pines2_background.get_height() ))

#function to reset level
def resetLevel():
    bandit_group.empty()
    sword_group.empty()
    item_group.empty()
    decoration_group.empty()
    spike_group.empty()
    exit_group.empty()
    horse_group.empty()
    #create empty tile list
    data = []
    for row in range(ROWS):
        r = [-1] * COLS
        data.append(r)
    return data

class Character(pygame.sprite.Sprite):
    def __init__(self, png, x, y, scale, speed):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y

        self.png = png

        self.alive = True
        self.speed = speed

        self.shoot_cooldown = 0

        self.hurt_cooldown = 0

        self.health = 3
        self.max_health = self.health
    
        self.direction = 1
        self.velY = 0
        self.jump = False
        self.inAir = True
        self.flip = False

        self.attack = True
        self.isAttacking = False

        self.animationList=[]
        self.frameIndex=0
        self.action = 0

        self.coin = 0

        #create ai specific variables
        self.move_counter = 0
        self.idling = False
        self.idling_counter = 0
        self.vision = pygame.Rect(0,0,200,20)

        #hitboxes
        self.hitbox = (self.x + 20, self.y, 28, 60)

        self.updateTime = pygame.time.get_ticks()

        #load all images for player
        animationTypes = ['Idle', 'Run', 'Jump', 'Attack1', 'Death']
        for animation in animationTypes:
            #reset temporary list of images
            tempList = []
            #count num of files in each animation folder
            numOfFrames = len(os.listdir(f'sprites/{png}/{animation}'))
            for i in range(numOfFrames):
                charImg = pygame.image.load(f'sprites/{png}/{animation}/{animation}{i}.png').convert_alpha()
                charImg = pygame.transform.scale(charImg, (int(charImg.get_width() * scale), (int(charImg.get_height() * scale))))
                tempList.append(charImg)
                

            self.animationList.append(tempList)

        self.image = self.animationList[self.action][self.frameIndex]
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        self.updateAnimation()
        self.check_alive()
        #update cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -=1

    def move(self, movingLeft, movingRight):
        #reset movement variables
        screen_scroll1 = 0
        dx = 0
        dy = 0
        #assign movement variables if moving left or right
        if movingLeft:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if movingRight:
            dx = self.speed
            self.flip = False
            self.direction = 1

        #jump
        if self.jump == True and self.inAir == False:
            #jump height/velocity
            self.velY = -17
            self.jump = False
            self.inAir = True

        #apply gravity
        self.velY += GRAVITY
        if self.velY > 10:
            self.velY
        dy += self.velY
       
       #check collision
        for tile in world.obstacle_list:
            #check collision on x axis
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
            #check for collision on y axis
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                #check if below the ground
                if self.velY < 0:
                    self.velY = 0
                    dy = tile[1].bottom - self.rect.top
                #check if above the ground
                elif self.velY >= 0:
                    self.velY = 0
                    self.inAir = False
                    dy = tile[1].top - self.rect.bottom

        #check for collision with spikes
        if pygame.sprite.spritecollide(self, spike_group, False):
            self.health = 0
            hurt_fx.play()
        #check for collision with exit sign
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True
        #check if player has fallen off the map incase of bugs
        if self.rect.bottom> screenHeight:
            self.health = 0
            hurt_fx.play()
            

        #check if going off the edges of the screen
        if self.png == 'Knight_1':
            if self.rect.left + dx < 0 or self.rect.right + dx > screenWidth:
                dx = 0

        #update rect position
        self.rect.x += dx
        self.rect.y += dy

        #update scroll based on player position
        if self.png == 'Knight_1':
            if (self.rect.right > screenWidth - SCROLL_THRESH and bg_scroll < (world.level_length * tile_size) - screenWidth)\
                or (self.rect.left < SCROLL_THRESH and bg_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll1 = -dx
        return screen_scroll1, level_complete

    def shoot (self):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = 20
            sword = Sword(self.rect.centerx + (0.9* self.rect.size[0] * self.direction), self.rect.centery, self.direction, 0.06)
            sword_group.add(sword)
            sword_fx.play()
        
    def charge(self, Butt):
        if self.png == 'Light Bandit':
            # Find direction vector (dx, dy) between enemy and player.
            dirvect = pygame.math.Vector2(Butt.rect.x - self.rect.x,
                                        Butt.rect.y - self.rect.y)
            dirvect.normalize()
            # Move along this normalized vector towards the player at current speed.
            dirvect.scale_to_length(self.speed)
            self.rect.move_ip(dirvect)
        
    def ai (self):
         if self.alive and Butt.alive:
            if self.idling == False and random.randint(1, 200) == 1:
                self.updateAction(0)#idle animation
                self.idling = True
                self.idling_counter = 50
            #check if ai is near player
            if self.vision.colliderect(Butt.rect):
                #stop running and face player
                self.updateAction(0)#idle animation
                #run at player player
                self.charge(Butt)
                self.updateAction(1)
            else:

                if self.idling == False:
                    if self.direction == 1:
                        ai_movingRight = True
                    else:
                        ai_movingRight = False
                    ai_movingLeft = not ai_movingRight
                    self.move(ai_movingLeft, ai_movingRight)
                    self.updateAction(1)#run animation
                    self.move_counter += 1
                    #move ai vision WITH the bandits
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)
                    #pygame.draw.rect(screen, RED, self.vision, 1) # draw the vision for development

                    if self.move_counter > tile_size:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <=0:
                        self.idling = False

            self.rect.x += screen_scroll

    def updateAnimation(self):
        ANIMATION_COOLDOWN = 100
        #update image depending on current frame
        self.image = self.animationList[self.action][self.frameIndex]
        #check if enough time has passed since last cooldown update
        if pygame.time.get_ticks() - self.updateTime > ANIMATION_COOLDOWN:
            self.updateTime = pygame.time.get_ticks()
            self.frameIndex += 1
        #if the animation has run out, then reset to start in order to loop
        if self.frameIndex >= len(self.animationList[self.action]):
            if self.action == 4:
                self.frameIndex = len(self.animationList[self.action]) - 1
            else:
                self.frameIndex = 0
    
    def hurt (self):
        if self.hurt_cooldown == 0:
            self.hurt_cooldown = 30
            if pygame.sprite.spritecollide(Butt, bandit_group, False):
                if Butt.alive:
                    Butt.health -= 1
                    hurt_fx.play()
                    self.kill()

    def hurt_update(self):
        self.check_alive()
        #update cooldown
        if self.hurt_cooldown > 0:
            self.hurt_cooldown -=1
            

    def updateAction(self,newAction):
        #check if new action is different than current one
        if newAction != self.action:
            self.action = newAction
            #update animation settings
            self.frameIndex = 0
            self.updateTime = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.updateAction(4)

    def kill_enemy(self):
        if Bandit.alive == False:
            Bandit.updateAction(4)
            if self.frameIndex >= 1:
                bandit_group.remove(Bandit)
                
    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip,False), self.rect)
        #pygame.draw.rect(screen, RED, self.rect, 1) # drawing the character hitboxes for development
        

class Item (pygame.sprite.Sprite):
    def __init__ (self, item_type, x, y, scale):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = items[self.item_type]
        self.image = pygame.transform.scale(self.image, (int(self.image.get_width() * scale), (int(self.image.get_height() * scale))))
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + tile_size // 2, y + (tile_size - self.image.get_height()))
    
        
    def update(self):
        #scroll
        self.rect.x += screen_scroll
        #check if the player has picked up the box
        if pygame.sprite.collide_rect(self, Butt): 
            #check what type of item
            if self.item_type == 'Coin':
                Butt.coin += 1
                coin_fx.play()
            elif self.item_type == 'Health':
                Butt.health += 1
                heal_fx.play()
                if Butt.health > Butt.max_health:
                    Butt.health = Butt.max_health
            self.kill()

class Sword (pygame.sprite.Sprite):
    def __init__(self,x,y,direction, scale):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10
        self.image = sword_img
        self.image = pygame.transform.scale(sword_img, (int(sword_img.get_width() * scale), (int(sword_img.get_height() * scale))))
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        self.direction = direction

    def update(self):
        #move bullet
        self.rect.x +=(self.direction * self.speed) + screen_scroll
        #check if bullet has gone off screen
        if self.rect.right < 0 or self.rect.left > screenWidth:
            self.kill()
        #check for collision with level
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()
        #check collision with characetrs
        
        for Bandit in bandit_group:
            if pygame.sprite.spritecollide(Bandit, sword_group, False):
                if Bandit.alive:
                    Bandit.health -= 3
                    self.kill()
                    #self.rect.kill()
    
class World():
    def __init__(self):
        self.obstacle_list = []

    def process_data(self, data):
        self.level_length = len(data[0])
        #iterate through each value in level data file
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile>= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * tile_size
                    img_rect.y = y * tile_size
                    tile_data = (img, img_rect)
                    if tile >= 1 and tile <= 16: #ground
                        self.obstacle_list.append(tile_data)
                    elif tile == 0:
                        horse = Horse(img, x * tile_size, y * tile_size, 4)
                        horse_group.add(horse) 
                    elif tile == 22:#spikes
                        spike = Spikes(img, x * tile_size, y * tile_size, 0.9)
                        spike_group.add(spike)
                    elif tile >= 17 and tile <= 20: #decorations
                        decoration = Decorations(img, x * tile_size, y * tile_size)
                        decoration_group.add(decoration)
                    elif tile == 23:#create player
                        Butt = Character('Knight_1', x* tile_size, y * tile_size, 1.3, 13)
                    elif tile == 24: #enemy
                        Bandit = Character('Light Bandit', x* tile_size, y * tile_size, 1.6, 4)
                        bandit_group.add(Bandit)
                    elif tile == 25:#exit sign
                        exit = Exit(img, x * tile_size, y * tile_size)
                        exit_group.add(exit)
                    elif tile == 21:#coins
                        item = Item('Coin', x* tile_size, y * tile_size, 0.06)
                        item_group.add(item)
                    elif tile == 26:#heart
                        item = Item('Health', x* tile_size, y * tile_size, 0.05)
                        item_group.add(item)
        return Butt

    def draw(self):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            screen.blit(tile[0], tile[1])
                    
class Decorations(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + tile_size // 2, y + (tile_size - (0.9* self.image.get_height())))

    def update (self):
        self.rect.x += screen_scroll

class Spikes(pygame.sprite.Sprite):
    def __init__(self, img, x, y, scale):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.image = pygame.transform.scale(img, (int(img.get_width() * scale), (int(img.get_height() * scale))))
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + tile_size // 2, y + (tile_size - self.image.get_height()))

    def update (self):
        self.rect.x += screen_scroll

class Horse(pygame.sprite.Sprite):
    def __init__(self, img, x, y, scale):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.image = pygame.transform.scale(img, (int(img.get_width() * scale), (int(img.get_height() * scale))))
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + tile_size // 2, y + (tile_size - (0.85* self.image.get_height())))

    def update (self):
        self.rect.x += screen_scroll
        if pygame.sprite.spritecollide(Butt, horse_group, False):
                if Butt.alive: 
                    end_img.draw()
                    Butt.speed = 0

class Exit(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + tile_size // 2, y + (tile_size - self.image.get_height()))

    def update (self):
        self.rect.x += screen_scroll

class ImageScreen:
    def __init__(self, image_path, width, height):
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (width, height))

    def draw(self):
        screen.blit(self.image, (0, 0))
        
menu_img = ImageScreen('backgrounds/menu.png', screenWidth, screenHeight)
end_img = ImageScreen('backgrounds/end.png', screenWidth, screenHeight)

#create buttons
start_button = button.Button(screenWidth // 2 - 140, screenHeight//2 - 20, start_img, 1)
exit_button = button.Button(screenWidth // 2 - 140, screenHeight//2 + 120, exit_img, 1)
restart_button = button.Button(screenWidth // 2 - 200, screenHeight//2 - 150, restart_img, 1)

#create sprite groups
item_group = pygame.sprite.Group()
sword_group = pygame.sprite.Group()
bandit_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
spike_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()
horse_group = pygame.sprite.Group()

#create empty tile list
world_data = []
for row in range(ROWS):
    r = [-1] * COLS
    world_data.append(r)

#load and create
with open(f'level{level}_data.csv', newline='')as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)

world = World()
Butt = world.process_data(world_data)

#while loop lets us keep the window open until we close it
#otherwise it will only remain open for a fraction of a second
run = True
while run:

    clock.tick(FPS)

    if start_game == False:
        #main menu
        screen.fill(BG)
        menu_img.draw()
        if start_button.draw(screen):
            start_game =True
        if exit_button.draw(screen):
            run = False
        
    else:

        draw_bg()
        #draw world

        item_group.update()
        item_group.draw(screen)

        #show coins
        draw_text(f'COINS:  {Butt.coin}', font, WHITE, 10, 35)
        
        heart_HUD = pygame.transform.scale(health_image, (int(health_image.get_width() * 0.06), (int(health_image.get_height() * 0.06))))
        for x in range(Butt.health):
            screen.blit(heart_HUD, (15 + (x * 50),70))

        world.draw()
        #update and draw groups
        sword_group.update()
        sword_group.draw(screen)

        spike_group.update()
        spike_group.draw(screen)

        exit_group.update()
        exit_group.draw(screen)

        decoration_group.update()
        decoration_group.draw(screen)

        for Bandit in bandit_group:
            Bandit.ai()
            Bandit.update()
            Bandit.draw()
            Bandit.kill_enemy()  

        horse_group.update()
        horse_group.draw(screen)

        Butt.update()
        Butt.draw()
        Butt.hurt()
        Butt.hurt_update()  

        if Butt.alive:
        #update player actions
            if movingLeft or movingRight:
                Butt.updateAction(1)#1 means run
            elif Butt.inAir:
                Butt.updateAction(2)#2 is jump
            elif shoot:
                Butt.shoot()
                Butt.updateAction(3) #attack
            else:
                Butt.updateAction(0)#back to 0 which is idle
            screen_scroll, level_complete = Butt.move(movingLeft, movingRight)
            bg_scroll -= screen_scroll
            #check if player has completed the level
            if level_complete:
                level+=1
                bg_scroll = 0
                world_data = resetLevel()
                if level <= MAX_LEVELS:
                    with open(f'level{level}_data.csv', newline='')as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()
                    Butt = world.process_data(world_data)

        else:
            screen_scroll = 0
            if restart_button.draw(screen):
                bg_scroll = 0
                world_data = resetLevel()

                with open(f'level{level}_data.csv', newline='')as csvfile:
                    reader = csv.reader(csvfile, delimiter=',')
                    for x, row in enumerate(reader):
                        for y, tile in enumerate(row):
                            world_data[x][y] = int(tile)
                world = World()
                Butt = world.process_data(world_data)

    for event in pygame.event.get():
        #QUIT means you've clicked the X
        if event.type == pygame.QUIT:
            run = False

        #keyborad inputs
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                movingLeft = True
            if event.key == pygame.K_d:
                movingRight = True
            if event.key == pygame.K_w and Butt.alive:
                Butt.jump = True
                jump_fx.play()
            if event.key == pygame.K_SPACE: #and Butt.attack:
                Butt.isAttacking = True
                shoot = True
            if event.key == pygame.K_ESCAPE:
                run = False
                
        #keyboard when released
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                movingLeft = False
            if event.key == pygame.K_d:
                movingRight = False
            if event.key == pygame.K_SPACE:
                Butt.isAttacking = False
                shoot = False
            
    #this line actually tells the window to update it's assets
    pygame.display.update()

pygame.quit()         