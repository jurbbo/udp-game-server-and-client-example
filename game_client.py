
#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 24 11:06:20 2019

@author: jarkko
"""

import socket
from bitstring import BitArray
from time import sleep
import threading as Thread

class Player:
    def __init__(self, x, y, color, number):
        self.x = x
        self.y = y
        self.color = color
        self.number = number

## Changes bitArray to integer form. Integer is unsigned.
def bitToInt(bitArray):
    
    counter = len(bitArray)-1
    retVal = 0
    
    for bin in bitArray:
        if bin == True:
            retVal += 2**counter
        counter -= 1
    return retVal

##
    
def defaultClientPlayerBit(x,y, number): ## Default player data to protocol bit format.
    
    if number != None:
        playerbit = BitArray('uint:3={value}'.format(value=number))
        xbit = BitArray('uint:10={value}'.format(value=x))
        ybit = BitArray('uint:10={value}'.format(value=y))
        playerbit.append(xbit)
        playerbit.append(ybit)   
    else:
        playerbit = BitArray('uint:26=0')
    
    return playerbit
    

### These methods parse server response data bit to decimal form.    
class PlayerDataAnalyzer: 
    def __init__(self, data, yournumber):
        self.bitArray = toBits(data)
        self.players = []
        for i in range(8):
            self.players.append(Player(None, None, None, None))
            
        self.type = self.analyzeType()
        
        if self.type == 0:
            self.success = self.analyzeSuccessBit()
            
            if self.success == True:
                
                if yournumber == None:
                    self.yourplayernumber = self.analyzeYourNumber()
                else:
                    self.yourplayernumber = yournumber
                
                self.yourcolor = self.analyzeYourColor()
                self.yourX = self.analyzeYourX()
                self.yourY = self.analyzeYourY()
        
        if self.type == 2:
            self.analyzeAllPlayerData()
        
            '''
            ON SUCCESS:
            [FRAMETYPE = "00"][SUCCESS=1 (1 bit)][PLAYER NUMBER (3 bits)][PLAYER COLOR (3 bits)]
            [START COORDINATES X (10 bits)][START COORDINATES Y (10 bits)]
                        
            ON FAILURE (if there is no room for new players, max players= 8):
            [FRAMETYPE = "00"][SUCCESS=0 (1 bit)]
            '''
    def getPlayers(self):
        return self.players


    #Bit parsers.
    def analyzeAllPlayerData(self):
        
        ## Respond with players playing.
        '''
        [FRAMETYPE = "01"][PLAYER AMOUNT (3 bits)] 
        -- if amount is 3 players -- 
        [PLAYER NUMBER (3 bits)][PLAYER COLOR (3 bits)][X (10 bits)][Y (10 bits)]
        [PLAYER NUMBER (3 bits)][PLAYER COLOR (3 bits)][X (10 bits)][Y (10 bits)]
        [PLAYER NUMBER (3 bits)][PLAYER COLOR (3 bits)][X (10 bits)][Y (10 bits)]
        
        Total bits --> 5 + (26 * 3)
        '''
        
        amountOfPlayingPlayers = bitToInt(self.bitArray[2:5])
        for i in range(amountOfPlayingPlayers):
            baseNumber = 5+(i*26)
            number = bitToInt(self.bitArray[baseNumber:baseNumber+3])
            color = bitToInt(self.bitArray[baseNumber+3:baseNumber+6])
            x = bitToInt(self.bitArray[baseNumber+6:baseNumber+16])
            y = bitToInt(self.bitArray[baseNumber+16:baseNumber+26])
            self.players[number].number = number
            self.players[number].x = x
            self.players[number].y = y
            self.players[number].color = color
            
    
    def analyzeSuccessBit(self):
        if self.type == 0:
            successbit = self.bitArray[2]
            return successbit
        else:
            return False
        
    def analyzeYourNumber(self):
        if self.type == 0:
            yournumberbits = self.bitArray[3:6]
            return (bitToInt(yournumberbits))
        else:
            return None
    
    def analyzeYourColor(self):
        if self.type == 0:
            yourcolorbits = self.bitArray[6:9]
            return (bitToInt(yourcolorbits))
        else:
            return None
          
    def analyzeYourX(self):
        if self.type == 0:
            xbits = self.bitArray[9:19]
            return (bitToInt(xbits))            
        else:
            return None
        
    def analyzeYourY(self):
        if self.type == 0:
            ybits = self.bitArray[19:29]
            return (bitToInt(ybits))            
        else:
            return None
             
    def analyzeType(self):
        typebyte = self.bitArray[0:2]
        return (bitToInt(typebyte))
## End of bit-parsers.       


def reader_WaitsAndReads(sukka, datatype, you, stopTask):
    while True:
        try:
            (data, addr) = sukka.recvfrom(128)
            dataBits = toBits(data)
            
            print (dataBits.bin)
            
            if (bitToInt(dataBits[0:2]) == datatype):
                if datatype == 0:
                    if len(dataBits) > 2:
                        yourdata = PlayerDataAnalyzer(data, None)
                        
                        if yourdata.success:
                            you.x = yourdata.yourX
                            you.y = yourdata.yourY
                            you.color = yourdata.yourcolor
                            you.number = yourdata.yourplayernumber
                            
                            print ("Player data received. ")
                            print ("Your player number: {n}, your x: {x}, your y: {y}, your color: {c}".format(n=you.number, x = you.x, y = you.y, c = you.color))                   
                            stopTask.set()
                            
                        else:  ## Server sent 0 as success bit -->
                            print("Server refused access request. Server is full of players.")
                
                if datatype == 3:
                    print ("Server has successfully removed user data.")
                    stopTask.set()
                    
        finally:
            return


## Changes BitArray to ByteArray. If there are bits missing from last byte, last bits will be zeros. 
def toBits(bytearraydata):   ## Received byte array to bit array.

    bitArray = BitArray()
    for databyte in bytearraydata:
        bitByte = BitArray('uint:8={value}'.format(value=databyte))
        bitArray.append(bitByte)
    return bitArray    

    
def toBytes(bitArray):
    
    data = bitArray
    allBytes = bytearray()
    while data:
        dataSlice = BitArray()
        
        if len(data)>7:
            dataSlice = data[:8]
            del data[:8]
            
        else:
            dataSlice = data
            binaryString = "0b"
            for i in range(8-len(data)):
                binaryString += '0'
            dataSlice.append(binaryString)
            data = None
        
        ##print ([binToInt(dataSlice)])
        allBytes.extend([bitToInt(dataSlice)])
    
    return allBytes


def data_reader(sukka, players, you):
    
    while True:
        
        try:
            (data,addr) = sukka.recvfrom(64)
            serverResponse = PlayerDataAnalyzer(data, you.number)
        
            if serverResponse.type == 3:
                print("Server confirms: User has been deleted from server.")
                break
        
            if serverResponse.type == 2:
                
                for player in serverResponse.getPlayers():
                    if player.number != None:
                        players[player.number] = player
                        
        except Exception as ex:
            print ("Error inside reader thread: ", ex)
    #print_lock.acquire()
    #start_new_thread(threaded_data_analyzer, (soppa, data,)) 

def sendData(bits, host, sukka):
    #print (len(bytessit))
    bits.append(BitArray(bin="1"))
    bytessit = toBytes(bits)
    sukka.sendto(bytessit, host)

class GameClient:
    
    def __init__(self, HOST, PORT):
        self.HOST = HOST
        self.PORT = PORT
        self.players = []
        self._lastposition_players = []
        self.you = Player(None,None,None,None)
        self.serveronline = False
        self.sukka = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        if (self.reader_TimeOutterForBeginning(BitArray(bin="00"))):
            self.serveronline = True
            self.reader = self.init_reader_and_player_variable()
    
        
    def close(self):
        self.reader_TimeOutterForExit(BitArray(bin="11"))
        self.reader.join()
        self.sukka.close()
        print("Client closed.")
    
    def getPlayers_setLastpostion_players(self):
        self._lastposition_players = self.players
        return self._lastposition_players
        
    def sendLocation(self):
        self.players[self.you.number] = self.you
        a = BitArray(bin="10")
        a.append(defaultClientPlayerBit(self.you.x,self.you.y,self.you.number))
        sendData(a, (self.HOST, self.PORT), self.sukka)
        
    def init_reader_and_player_variable(self):
    
        for i in range(8):
            self.players.append(Player(None, None, None, None))
        
        self._lastposition_players = self.players
    
        reader = Thread.Thread(target=data_reader, args=(self.sukka, self.players, self.you, ))
        reader.setDaemon(True)
        reader.start()
        return reader
    
    def reader_TimeOutterForExit(self, datatypebits):
    
        datatypebitsToSender = datatypebits
        datatypebitsToSender.append(BitArray('uint:3={value}'.format(value=self.you.number)))
        sendData(datatypebitsToSender, (self.HOST, self.PORT), self.sukka)
    
    
    ## Starts reader thread, waits for timeout.
    def reader_TimeOutterForBeginning(self,datatypebits):
            
        ## Starting receiver thread.
        number = bitToInt(datatypebits)
        stopTask = Thread.Event()
        rreader = Thread.Thread(target=reader_WaitsAndReads, args=(self.sukka,bitToInt(datatypebits), self.you, stopTask,))
        rreader.setDaemon(True)
        rreader.start()
    
        ## Sending request to get new player data.    
        time = 0.0
        sleep(0.1)
        
        datatypebitsToSender = datatypebits
         
        sendData(datatypebitsToSender, (self.HOST, self.PORT), self.sukka)
        
        while time < 5:
            sleep(0.5)
            time += 0.5
            if stopTask.is_set():
                if rreader.is_alive:
                    rreader.join()
                return True
        
        if number == 0:
            print ("Time out... cannot get player data from server. Turn your game server on and try again.")
        
        return False
    
    