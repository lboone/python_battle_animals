from settings import *
from pytmx.util_pygame import load_pygame
from os.path import dirname, abspath,join
from sprites import Sprite, AnimatedSprite, MonsterPatchSprite, BorderSprite, CollidableSprite
from entities import Player, Character
from groups import AllSprites
from support import *
from game_data import TRAINER_DATA
from dialog import DialogTree

class Game:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Battle Animals")
        self.clock = pygame.time.Clock()

        # groups
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.character_sptrites = pygame.sprite.Group()

        self.import_assets()
        self.setup(self.tmx_maps['world'], 'house')

        self.dialog_tree = None
    
    def import_assets(self):
        self.tmx_maps = {
            'world': load_pygame(rel_path('..', 'data', 'maps', 'world.tmx')), 
            'hospital': load_pygame(rel_path('..', 'data', 'maps', 'hospital.tmx')),                          
        }
        self.overworld_frames = {
            'water': import_folder("..", "graphics", "tilesets", "water"),
            'coast': coast_importer(24, 12, '..', 'graphics', 'tilesets','coast'),
            'characters': all_character_import('..','graphics','characters')}
        
        self.fonts = {
            'dialog': pygame.font.Font(rel_path('..', 'graphics', 'fonts', 'PixeloidSans.ttf'), 30),
        }

    def setup(self, tmx_map, player_start_pos):

        # Terrain
        for layer in ['Terrain', 'Terrain Top']:
            for x, y, surf in tmx_map.get_layer_by_name(layer).tiles():
                Sprite((x * TILE_SIZE, y * TILE_SIZE), surf, self.all_sprites, WORLD_LAYERS['bg'])
        
        # water
        for obj in tmx_map.get_layer_by_name("Water"):
            for x in range(int(obj.x), int(obj.x + obj.width), TILE_SIZE):
                for y in range(int(obj.y), int(obj.y + obj.height), TILE_SIZE):
                    AnimatedSprite((x, y), self.overworld_frames['water'], self.all_sprites, WORLD_LAYERS['water'])

        # coast
        for obj in tmx_map.get_layer_by_name("Coast"):
            terrain = obj.properties['terrain']
            side = obj.properties['side']
            AnimatedSprite((obj.x, obj.y), self.overworld_frames['coast'][terrain][side], self.all_sprites, WORLD_LAYERS['bg'])


        # objects
        for obj in tmx_map.get_layer_by_name("Objects"):
            if obj.name == "top":
                Sprite((obj.x, obj.y), obj.image, self.all_sprites, WORLD_LAYERS['top'])
            else:
                CollidableSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))

        # collision objects
        for obj in tmx_map.get_layer_by_name("Collisions"):
            BorderSprite(
                pos=(obj.x, obj.y),
                surf=pygame.Surface((obj.width, obj.height)),
                groups=self.collision_sprites
            )

        # grass patches
        for obj in tmx_map.get_layer_by_name("Monsters"):
            MonsterPatchSprite(
                pos=(obj.x, obj.y),
                surf=obj.image,
                groups=self.all_sprites,
                biome=obj.properties['biome']
            )

        # entities
        for obj in tmx_map.get_layer_by_name("Entities"):
            if obj.name == "Player": 
                if obj.properties['pos'] == player_start_pos:
                    self.player = Player(
                        pos = (obj.x, obj.y), 
                        frames = self.overworld_frames['characters']['player'], 
                        groups = self.all_sprites,
                        facing_direction=obj.properties['direction'],
                        collision_sprites=self.collision_sprites)
            else:
                Character( pos = (obj.x, obj.y), 
                        frames = self.overworld_frames['characters'][obj.properties['graphic']], 
                        groups = (self.all_sprites, self.collision_sprites, self.character_sptrites), 
                        facing_direction=obj.properties['direction'],
                        character_data=TRAINER_DATA[obj.properties['character_id']],
                        player=self.player,
                        create_dialog=self.create_dialog,
                        collision_sprites=self.collision_sprites,
                        radius=obj.properties['radius'])

    def input(self):
        if not self.dialog_tree:
            keys = pygame.key.get_just_pressed()
            if keys[pygame.K_SPACE]:
                for character in self.character_sptrites:
                    if check_connections(100, self.player, character):
                        # block player input
                        self.player.block()
                        # make entities face each other
                        character.change_facing_direction(self.player.rect.center)
                        # step through dialog
                        self.create_dialog(character)

    def create_dialog(self, character):
        if not self.dialog_tree:
            self.dialog_tree = DialogTree(character, self.player, self.all_sprites, self.fonts['dialog'], self.end_dialog)
    
    def end_dialog(self, character):
        self.dialog_tree = None
        self.player.unblock()

    def run(self):
        while True:
            dt = self.clock.tick() / 1000
            # event loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

            # game logic
            self.input()
            self.all_sprites.update(dt)
            self.display_surface.fill('black')
            self.all_sprites.draw(self.player.rect.center)

            # overlays
            if self.dialog_tree:
                self.dialog_tree.update()
            
            pygame.display.update()

if __name__ == "__main__":
    game = Game()
    game.run()