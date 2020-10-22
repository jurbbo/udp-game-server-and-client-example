# Simple UDP game server and client -- example for 8 clients

- use python3.

- start game server with `python3 game_server.py`.
- start client with `python3 game.py`.
- 8 clients can connect. Max client number can be changed, if needed.

On standard localhost is used. Other IP addresses can be configured.

    Plase note, that this is a stupid server. Server returns and does everything that it's been asked. 
    Does not even check if client really is a "connected" player.    
    
    GameClient (game_client.py) class has functions:
    
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
                
    
