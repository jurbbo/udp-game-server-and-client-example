#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 10:55:52 2019

@author: jarkko

STUPID UDP GAME SERVER -- version 0.1

"""

##from _thread import start_new_thread
import threading as Thread
import queue as Queue
import socket
from bitstring import BitArray
from time import sleep
from random import randrange
import sys

STANDARD_HOST_PORT = (("localhost", 7000))
print_lock = Thread.Lock()

class PacketCounter:
    def __init__(self):
        self.receivedPackages = 0
        self.sentPackages = 0
        self.sentBytes = 0
        self.receivedBytes = 0
    
    def printAll(self):
        print("\nReceived: ")
        print("Packages:\t", self.receivedPackages)
        print("Bytes:\t\t", self.receivedBytes)
        print("\nSent:\t")
        print("Packages:\t", self.sentPackages)
        print("Bytes:\t\t", self.sentBytes)

players = []
taskQueue = Queue.Queue(maxsize=0)
packetCounter = PacketCounter()

class Player:
    
    def __init__(self, x, y, color, number):
        self.x = x
        self.y = y
        self.color = color
        self.number = number

class DataResponser:
    
    def __init__(self, data, sukka, addr):
        self.sukka = sukka
        self.addr = addr
        self.bitArray = toBits(data)
        ## PLAYER DATA
        self.type = self.analyzetype()
        self.number = self.analyzenumber()
        self.x = self.analyzeX()
        self.y = self.analyzeY()

        self.analyzeANDresponseToClient()

    ### Analyze and response method:
    def analyzeANDresponseToClient(self):
        if self.type == 0:
            
            newPlayerNumber = createPlayerSlot(100 + randrange(100),30 + randrange(400),1 + randrange(5))
            
            ## New player creation and data ship to client.
            if (newPlayerNumber != None and newPlayerNumber<8):
                
                print ("Setting a new player ({addr}), player number {number}".format(addr=self.addr, number = newPlayerNumber))
                '''
                NEW PLAYER NUMBER REQUEST
                
                [FRAMETYPE = "00"][SUCCESS=1 (1 bit)][PLAYER NUMBER (3 bits)][PLAYER COLOR (3 bits)]
                [START COORDINATES X (10 bits)][START COORDINATES Y (10 bits)]
                '''
                typesuccessbit = BitArray(bin="001")
              
                typesuccessbit.append(defaultPlayerBit(players[newPlayerNumber].x,players[newPlayerNumber].y, players[newPlayerNumber].color, newPlayerNumber))
                
                packetCounter.sentBytes += sendData(typesuccessbit, self.addr, self.sukka)
                packetCounter.sentPackages += 1
            
            ## Too many players. Sending error flag to client.    
            else:
     
                print ("New player request from {addr}. Cannot create new player. Server is full! (MAX 8 PLAYERS)".format(addr = self.addr))
                a = BitArray(bin="00000000")
                packetCounter.sentBytes += sendData(a, self.addr, self.sukka)
                packetCounter.sentPackages += 1
                
                ###print("User cannot be added: ", self.addr)
    
            
        ## Client request for all player data
        if self.type == 1:
            
            '''
            REQUEST FOR ALL PLAYER DATA!
            
            server response:
            [FRAMETYPE = "01"]    ((( NOT ACTIVE FEATURE :: [PLAYER AMOUNT (3 bits)] )))
            [PLAYER NUMBER (3 bits)][PLAYER COLOR (3 bits)][X (10 bits)][Y (10 bits)]
            '''
                        
            typesuccessbit = BitArray(bin="01")  ## Type = 01 , Player Amount = 111 = 7 = all player data is sent 
            allPlayersBit = BitArray()
         
            for i in range(8):
                playerbit = defaultPlayerBit(players[i].x, players[i].y, players[i].color, players[i].number)
                allPlayersBit.append(playerbit)
            
            typesuccessbit.append(allPlayersBit)
            
            packetCounter.sentBytes += sendData(typesuccessbit, self.addr, self.sukka)
            packetCounter.sentPackages += 1
            
        
        ## Client sets player coordinates.
        if self.type == 2:
            
            players[self.number].x = self.x
            players[self.number].y = self.y
            
            '''
            CLIENT REQUEST FOR SETTING COORDINATES
            
            Client frame:
            [FRAMETYPE = "02"][PLAYER NUMBER (3 bits)][X (10 bits)][Y (10 bits)]
            '''
            
            ## Respond with players playing.
            '''
            [FRAMETYPE = "01"][PLAYER AMOUNT (3 bits)] 
            -- if amount is 3 players -- 
            [PLAYER NUMBER (3 bits)][PLAYER COLOR (3 bits)][X (10 bits)][Y (10 bits)]
            [PLAYER NUMBER (3 bits)][PLAYER COLOR (3 bits)][X (10 bits)][Y (10 bits)]
            [PLAYER NUMBER (3 bits)][PLAYER COLOR (3 bits)][X (10 bits)][Y (10 bits)]
            
            Total bits --> 5 + (26 * 3)
            '''
            amountOfActivePlayers = 0
            
            type_allplaying = BitArray(bin="10")
            allPlayersBit = BitArray()
            
             
            
            for i in range(8):
                ## ... don't send data of the one who requested the data ... 
                if players[i].number != None and players[i].number != self.number:
                    playerbit = defaultPlayerBit(players[i].x, players[i].y, players[i].color, players[i].number)
                    allPlayersBit.append(playerbit)
                    amountOfActivePlayers +=1
            
            type_allplaying.append(BitArray('uint:3={value}'.format(value=amountOfActivePlayers)))
            type_allplaying.append(allPlayersBit)
            packetCounter.sentBytes += sendData(type_allplaying, self.addr, self.sukka)
            packetCounter.sentPackages += 1
            
        
        ## Client removes own player data (quits...)
        if self.type == 3:
                        
            print("Player {number} leaves the game. Goodbye!".format(number = self.number))

            players[self.number].number = None
            players[self.number].x = None
            players[self.number].y = None
            players[self.number].color = None
            
            packetCounter.sentBytes += sendData(BitArray(bin="11"), self.addr, self.sukka)
            packetCounter.sentPackages += 1

   
    ### These methods parse response data bit to decimal form.         
    def analyzenumber(self):
        if self.type == 2 or self.type == 3:
            numberbyte = self.bitArray[2:5]
            return (binToInt(numberbyte))
        else:
            return None    
            
    def analyzeX(self):
        if self.type == 2:
            xbyte = self.bitArray[5:15]
            return (binToInt(xbyte))            
        else:
            return None
        
    def analyzeY(self):
        if self.type == 2:
            ybyte = self.bitArray[15:25]
            return (binToInt(ybyte))            
        else:
            return None
         
    def analyzetype(self):
        typebyte = self.bitArray[0:2]
        return (binToInt(typebyte))
    ## End of bit-parsers.              

def defaultPlayerBit(x,y,color, number): ## Default player data to protocol bit format.
    
    if number != None:
        playerbit = BitArray('uint:3={value}'.format(value=number))
        xbit = BitArray('uint:10={value}'.format(value=x))
        ybit = BitArray('uint:10={value}'.format(value=y))
    
        if color != None:
            colorbit = BitArray('uint:3={value}'.format(value=color))
        else:
            ## If no color, value bits are "000".
            colorbit = BitArray('uint:3=0')
        playerbit.append(colorbit)
        
        playerbit.append(xbit)
        playerbit.append(ybit)
    
    else:
        playerbit = BitArray('uint:26=0')

    return playerbit
    
def createPlayerSlot(x, y, color):

    for i in range(8):
        if players[i].number == None:
            players[i].x = x
            players[i].y = y
            players[i].color = color
            players[i].number = i
            return i
    return None
            
def toBits(bytearraydata):   ## Received byte array to bit array.

    bitArray = BitArray()
    for databyte in bytearraydata:
        bitByte = BitArray('uint:8={value}'.format(value=databyte))
        bitArray.append(bitByte)
    return bitArray    
    
    
def binToInt(binArray):
    
    counter = len(binArray)-1
    retVal = 0
    
    for bin in binArray:
        if bin == True:
            retVal += 2**counter
        counter -= 1
    return retVal

## Changes BitArray to ByteArray. If there are bits missing from last byte, last bits will be zeros. 

def toBytes(bitArray):  ## Bit array to byte array.

    data = bitArray
    allBytes = bytearray(b'')
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
        
        allBytes.extend([binToInt(dataSlice)])
    
    return allBytes

  
def threaded_data_analyzer(soppa,data):
    
    try:
        bitArray = BitArray()
        for databyte in data:
            bitByte = BitArray('uint:8={value}'.format(value=databyte))
            bitArray.append(bitByte)
            print(databyte)
        
        ##bitStream = BitStream(data)
        ##print (bitStream.pos)
        print(bitArray.bin)
        print_lock.release()
    except Exception as ex:
        print (ex)
 
def responseTaskWorker(sukka, taskQueue, stopTask):
    while True:
        queuefillingup=0
        queuelen = taskQueue.qsize()
        if queuelen > 50:
            queuefillingup+=1
            if queuefillingup > 100:
                print ("Server is slowing down... Tasks in analyze/response queue: ", queuelen)
                queuefillingup=0
                                         
        if not taskQueue.empty():
            data = taskQueue.get()
            ##print (data)
            DataResponser(data["data"], sukka, data["addr"])
            taskQueue.task_done()
        else:
            sleep(0.01)
        if stopTask.is_set():
            print("Response task runner shutting down...")
            break
    return
    
def readUDPStream(soppa, worker):
    
    (data,addr) = soppa.recvfrom(64)
    ##print('Connection from: ', addr[0])
    # Start a new thread and return its identifier 
    ##print(data)
    taskQueue.put({"data": data, "addr": addr})
    if len(data) == 1:
        print ("data length 0")
    packetCounter.receivedBytes += len(data)
    packetCounter.receivedPackages += 1
    
    #print_lock.acquire()
    #start_new_thread(threaded_data_analyzer, (soppa, data,)) 

    
def init_worker(soppa, stopTask):
    
    worker = Thread.Thread(target=responseTaskWorker, args=(soppa,taskQueue,stopTask))
    worker.setDaemon(True)
    worker.start()
    return worker
    
def init_server(hostport):
    
    for i in range(8):
        players.append(Player(None, None, None, None))
    
    try:
        soppa = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        soppa.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        soppa.bind(hostport)
        
    except socket.error as er:
        print ("Server failed to start! Error: {error}".format(error = er))
        return
    
    return soppa

def sendData(bits, host, sukka):
    #print (len(bytessit))
    bits.append(BitArray(bin="1"))
    bytessit = toBytes(bits)
    sendBytes = sukka.sendto(bytessit, host)
    return sendBytes


def setting_HostAndPort():
    arg_count = len(sys.argv)
    if arg_count == 3:
        host = sys.argv[1]
        try:
            port = int(sys.argv[2])
            return (host, port)
        except ValueError:  
            print ("Port number {port} not valid.".format(port = sys.argv[2]))
            return None
    else:
        print ("Using default host:port (localhost:7000). Use python game_server.py <HOST> <PORT> to specify host and port.")
        return STANDARD_HOST_PORT
        

    
def main():
    print ("Stupid UDP Game Server, version 0.1")
    HOST_PORT = setting_HostAndPort()
    if HOST_PORT == None:
        return
    stopTask = Thread.Event() # This is used to stop the response worker thread when server closes.       
    soppa = init_server(HOST_PORT)
    worker = init_worker(soppa, stopTask)
    
    if soppa:
        print("UDP Game server started at {host}!".format(host = HOST_PORT))
    else:
        print("Server cannot start. Try another host/port. Usage: python game_server.py <HOST> <PORT>")
        return
    
    try:
        while True:        
            readUDPStream(soppa, worker)
            
    except KeyboardInterrupt:
        print("\nServer is closing...")
    except socket.error as er:
        print ("Server failed while running. Server shutting down! Error: {error}".format(error = er))
        return
    
    stopTask.set()
    worker.join()
    print("Server is shut!")
    soppa.close()
    
    sleep(0.5)
    
    packetCounter.printAll()

    return
    
if __name__ == "__main__":
    main()

    