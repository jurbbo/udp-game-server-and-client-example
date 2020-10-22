# -*- coding: utf-8 -*-
"""
Stupid UDP Game server:
    
    Stupidness:
        
        Returns and does everything that is asked. Does not even check if client really is a "connected" player.    
    
    GameClient (gameclient.py) class has functions:
    
        Varibles:
            
            self.HOST = Host name.
            self.PORT = Port value.
            self.players = [] = Players on server.
            self._lastposition_players = [] = Last position of players.
            self.you = Player(None,None,None,None) = This player's own data. Player's data is also in self.players list. 
            self.serveronline = False = If True, connection to server has been established after __init__
            self.sukka = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) = Socket object.
        
    
        __init__(HOST, PORT):
            Will connect to server. Will init server response reader thread. If less that 8 players on server, 
            will get player data. If server does not respond will raise flag serverisonline to false. 
            Otherwise serverisonline = true.
    
    
        sendLocation
            Will send player location data. Server will respond with locations of other active players. Reader
            thread (initialized in __init__), will receive server response and change self.players object.
            
        getPlayers_setLastpostion_players
            Getter for self.players. Will also set last location.
        
        init_reader_and_player_variable
            Will initialize reader thread and make empty players list.
    
        reader_TimeOutterForExit(self, datatypebits):
            Will send exit code for server. Reader thread will close itself when server responds with exit.
            
    
        reader_TimeOutterForBeginning(self,datatypebits):
            Will send new player creation request for server and wait for response.
            
        
    
    
    PROTOCOL DATA MODEL:
        
        
        - Small data FRAME for fast performance: 
            - Using bit orientated thinking, not whole bytes. (with bitstring library)
            - Protocol UDP.
            
            General protocol form:
    
            - [FRAME TYPE (2 bits)][OPTIONAL PROTOCOL DATA][END BIT (1 bit) = "1"]
            
            (Why end bit? Othwerwise, if end of the data object has lot of zeros, conversion from bits to bytes migth lose data)
            
            Frame types:
            
            TYPE 00 (dec 0) --- Request / response to join to game.
            TYPE 01 (dec 1) --- Request all data / response with all data.
            TYPE 10 (dec 2) --- Set / Get coordinates
            TYPE 11 (dec 3) --- Request / response for quit game.
            
            - if FRAME TYPE == "00": 
                
                Client request for join:   
                [FRAMETYPE = "00"][END BIT = "1"]    
            
                Server repsponse for join:
                
                ON SUCCESS:
                [FRAMETYPE = "00"][SUCCESS=1 (1 bit)][PLAYER NUMBER (3 bits)][PLAYER COLOR (3 bits)]
                [START COORDINATES X (10 bits)][START COORDINATES Y (10 bits)][END BIT = "1"]
                
                ON FAILURE (if there is no room for new players, max players= 8):
                [FRAMETYPE = "00"][SUCCESS=0 (1 bit)][END BIT = "1"]
            
            - if FRAME TYPE == "01":
                
                Client request for get all player data from server:
                [FRAMETYPE = "01"]
                
                Server response:
                [FRAMETYPE = "01"]
                [PLAYER NUMBER (3 bits)][PLAYER COLOR (3 bits)][X (10 bits)][Y (10 bits)]
                [PLAYER NUMBER (3 bits)][PLAYER COLOR (3 bits)][X (10 bits)][Y (10 bits)]
                [PLAYER NUMBER (3 bits)][PLAYER COLOR (3 bits)][X (10 bits)][Y (10 bits)]
                x8 ... all the players. Empty slots will be 26 bits of zero. 
                [END BIT = "1"] 
                
                
            - if FRAME TYPE == "02":
                
                Client set data to server:
                [FRAMETYPE = "02"][PLAYER NUMBER (3 bits)][X (10 bits)][Y (10 bits)]
        
                Server response with all active players (but not the data of the one who requested):
                [FRAMETYPE = "02"][PLAYER AMOUNT (3 bits)]
                [PLAYER NUMBER (3 bits)][X (10 bits)][Y (10 bits)]
                [END BIT = "1"]
                
            - if FRAME TYPE == "03":
                
                Client request for leave the game:
                [FRAME TYPE = "03"][PLAYER NUMBER (3 bits)][END BIT = "1"]
                
                Server response for leave game for all players:
                [FRAME TYPE = "03"][PLAYER NUMBER (3 bits)][END BIT = "1"]
                
    
"""

import pygame
from game_client import GameClient

class Player:
    def __init__(self, x, y, color, number):
        self.x = x
        self.y = y
        self.color = color
        self.number = number

WHITE =     (255, 255, 255)
BLUE =      (  0, 100, 255)
GREEN =     (100, 255,   0)
STRANGE =     (100, 200, 200)
WEIRD =     (57, 100, 20)
RED =       (255,   0,   0)
BLACK =       (0,   0,   0)    

HOST = "localhost"
PORT = 7000

oldPositions = []
for i in range(8):
    oldPositions.append(Player(None, None, None, None))


def drawPlayers(players, black):
    for player in players:
        if player.number != None:
            coord = (player.x, player.y)
            if not black:
                pygame.draw.circle(screen, intToColor(player.color), coord, 10)
                oldPositions[player.number] = player
            elif black:
                pygame.draw.circle(screen, BLACK, coord, 10)
                
 
def intToColor(colorInt):
    
    if colorInt == 1:
        return BLUE
    if colorInt == 2:
        return GREEN
    if colorInt == 3:
        return RED
    if colorInt == 4:
        return WEIRD
    if colorInt == 5:
        return STRANGE 


print ("Connecting to Stupid UDP Game Server using {h} : {p}.".format(p= PORT, h = HOST))


done = False
x = 0
y = 0 

gameClient = GameClient(HOST, PORT)


if gameClient.serveronline == True:
    
    pygame.init()
    screen = pygame.display.set_mode((800, 400))
    
    start = pygame.time.get_ticks()
    while not done:
       
        drawPlayers(oldPositions, True) ## Black on old positions..
        
        players = gameClient.players
        ##oldPositions = gameClient.players
        
        gameClient.you.y += y
        gameClient.you.x += x
        
        gameClient.sendLocation()
        
        end = pygame.time.get_ticks() - start
        pygame.time.wait(10-end)
        start = pygame.time.get_ticks()
         
        for event in pygame.event.get():
                    
                if event.type == pygame.KEYUP:
                    y = 0
                    x = 0
            
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        y = -1
                    if event.key == pygame.K_DOWN:
                        y = 1
                    if event.key == pygame.K_RIGHT:
                        x = 1
                    if event.key == pygame.K_LEFT:
                        x =-1
                    
                if event.type == pygame.K_ESCAPE:
                    done = True
                if event.type == pygame.QUIT:
                    done = True
        
        drawPlayers(gameClient.getPlayers_setLastpostion_players(), False) # Color on new positions..
        pygame.display.flip()
        
    pygame.quit()
    gameClient.close()
    
else:
    
    print ("Server is not online. Pygame unit not starting...")