import pygame #Import the PyGame package which enables GUI.
import time #Import time module to pause between AI moves. 
import random #Import the random module to choose a random move when playing against the AI in easy mode. 
import sqlite3 #Import the sqlite3 module to read and manipulate the database.
import os #Impot os to access files in the same directory. 
from pathlib import Path #Use the pathlib module to open the database file. 

pygame.init() #Initialise pygame.

class game():
    def __init__(self):
        mainGameLoop = True #While True the program will continue to run. 
        self.boardFlip = False #Boolean for whether the board flip feature is to be turned on or off. 
        self.tileColours = False #Boolean for whether the tile colour move indicator is to be turned on or off. 
        self.gameMode = 1 #Integer which stores the game mode (1-3). 
        self.window = pygame.display.set_mode(screenResolution)
        #Display the background image: 
        self.bg = pygame.image.load("chessbackground.PNG")
        self.bg = pygame.transform.scale(self.bg, (1500,900))
        self.database = leaderboardDatabase() #Instantiate the leaderboard database. 


    def gameEvents(self):
        #Method to get the mouseState and mouse position. 
        run = True
        mainGameLoop = True
        mouseState = 0
        mouseX = pygame.mouse.get_pos()[0]
        mouseY = pygame.mouse.get_pos()[1]
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                run = False
                mainGameLoop = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouseState = 1
            if event.type == pygame.MOUSEBUTTONUP:
                mouseState = 0

        return run, mouseState,mouseX,mouseY, mainGameLoop

    def getPieceTotalMoves(self, movePiece, playerColour, piecePositionY, piecePositionX):
        #Method to get and return all of the valid moves a piece can move to. 
        castleMoves = []
        enPassantMoves = []
        #If the piece to move is a white Pawn, get its valid moves using the calculateWhitePawnMoves method.
        if movePiece.getName()[0:2] == "wP":
            validSquares,validTakeSquares, enPassantMoves = self.calculateWhitePawnMoves(piecePositionY,piecePositionX,movePiece.getFirstMove(), playerColour)

        #If the piece to move is a black Pawn, get its valid moves using the calculateBlackPawnMoves method. 
        elif movePiece.getName()[0:2] == "bP":
            validSquares,validTakeSquares, enPassantMoves = self.calculateBlackPawnMoves(piecePositionY,piecePositionX,movePiece.getFirstMove(), playerColour)

        #If the piece to move is a Queen, get its valid moves using the calculateQueenMoves method. 
        elif movePiece.getName()[0:2] == "bQ" or movePiece.getName()[0:2] == "wQ":
            validSquares, validTakeSquares = self.calculateQueenMoves(piecePositionY,piecePositionX, playerColour)

        #If the piece to move is a Rook, get its valid moves using the calculateRookMoves method. 
        elif movePiece.getName()[0:2] == "bR" or movePiece.getName()[0:2] == "wR":
            validSquares, validTakeSquares = self.calculateRookMoves(piecePositionY,piecePositionX, playerColour)

        #If the piece to move is a Knight, get its valid moves using the calculateKnightMoves method. 
        elif movePiece.getName()[0:2] == "bN" or movePiece.getName()[0:2] == "wN":
            validSquares, validTakeSquares = self.calculateKnightMoves(piecePositionY,piecePositionX, playerColour)

        #If the piece to move is a King, get its valid moves using the calculateKingMoves method. 
        elif movePiece.getName()[0:2] == "bK" or movePiece.getName()[0:2] == "wK":
            validSquares, validTakeSquares, castleMoves = self.calculateKingMoves(piecePositionY,piecePositionX, playerColour)

        #If the piece to move is a Bishop, get its valid moves using the calculateBishopMoves method. 
        elif movePiece.getName()[0:2] == "bB" or movePiece.getName()[0:2] == "wB":
            validSquares,validTakeSquares = self.calculateBishopMoves(piecePositionY,piecePositionX, playerColour)
        return validSquares, validTakeSquares, castleMoves, enPassantMoves

    def completeEnPassantMove(self,movePositionY, movePositionX, movePiece, piecePositionY, piecePositionX):
        #Method to complete an En Passant Move.
        #Get the object name of the piece to move.
        movePiece = self.game.pieceLookUp(movePiece.getName())
        #Add the piece to its new position and remove it from its previous square.
        if movePiece.getColour() == "w":
            takePiece = self.game.getPieceOnSquare(movePositionY+1, movePositionX)
            self.game.addTakenBlackPiece(takePiece)
        else:
            takePiece = self.game.getPieceOnSquare(movePositionY-1,movePositionX)
            self.game.addTakenWhitePiece(takePiece)
        self.game.addPieceToSquare(movePositionY, movePositionX, movePiece)
        self.game.removePieceFromSquare(piecePositionY, piecePositionX)
        if movePiece.getColour() == "w":
            #Get the piece that will be taken and store it as tempPiece, if the move is invalid, it will need to be put back.
            tempPiece = self.game.getPieceOnSquare(movePositionY+1,movePositionX)
            #Remove the taken piece from the board. 
            self.game.removePieceFromSquare(movePositionY+1,movePositionX)
            self.checkForCheck() 
            if self.game.getWCheck() == True:
                #If the move results in check, the move is invalid and must be undone. 
                self.game.resetMove(movePositionY, movePositionX, piecePositionY, piecePositionX, movePiece)
                self.game.addPieceToSquare(movePositionY+1,movePositionX, tempPiece)
                return False

        else:
            #Get the piece that will be taken and store it as tempPiece, if the move is invalid, it will need to be put back.
            tempPiece = self.game.getPieceOnSquare(movePositionY-1,movePositionX)
            #Remove the taken piece from the board. 
            self.game.removePieceFromSquare(movePositionY-1,movePositionX)
            if self.game.getBCheck() == True:
                #If the move results in check, the move is invalid and must be undone. 
                self.game.resetMove(movePositionY, movePositionX, piecePositionY, piecePositionX, movePiece)
                self.game.addPieceToSquare(movePositionY+1,movePositionX, tempPiece)
                return False

        #If the move does not result in check, the move is successful and True is returned. 
        return True

    def completeCastleMove(self,movePositionY, movePositionX, movePiece, playerColour, piecePositionY, piecePositionX):
        #Method to complete a castlign move. 
        #Get the object name of the King piece:
        movePiece= self.game.pieceLookUp(movePiece.getName())
        if [movePositionY,movePositionX] ==[7,2]:
            self.game.addPieceToSquare(7, 2, movePiece)
            self.game.removePieceFromSquare(piecePositionY,piecePositionX)
            rookPiece = self.game.getPieceOnSquare(7,0)
            self.game.addPieceToSquare(7, 3, rookPiece)
            self.game.removePieceFromSquare(7,0)
            self.checkForCheck()
            if self.game.getWCheck() ==True:
                self.game.addPieceToSquare(7,0,rookPiece)
                self.game.removePieceFromSquare(7,3)
                self.game.addPieceToSquare(piecePositionY, piecePositionX, movePiece)
                self.game.removePieceFromSquare(7,2)
                return False

        elif [movePositionY,movePositionX] ==[7,6]:
            self.game.addPieceToSquare(7, 6, movePiece)
            self.game.removePieceFromSquare(piecePositionY,piecePositionX)
            rookPiece = self.game.getPieceOnSquare(7, 7)
            self.game.addPieceToSquare(7, 5, rookPiece)
            self.game.removePieceFromSquare(7,7)
            if self.game.getWCheck() ==True:
                self.game.addPieceToSquare(7,7,rookPiece)
                self.game.removePieceFromSquare(7,5)
                self.game.addPieceToSquare(piecePositionY, piecePositionX, movePiece)
                self.game.removePieceFromSquare(7,6)
                return False

        elif [movePositionY,movePositionX] ==[0,2]:
            self.game.addPieceToSquare(0, 2, movePiece)
            self.game.removePieceFromSquare(piecePositionY,piecePositionX)
            rookPiece = self.game.getPieceOnSquare(0, 0)
            self.game.addPieceToSquare(0, 3, rookPiece)
            self.game.removePieceFromSquare(0,0)
            if self.game.getBCheck() ==True:
                self.game.addPieceToSquare(0,0,rookPiece)
                self.game.removePieceFromSquare(0,3)
                self.game.addPieceToSquare(piecePositionY, piecePositionX, movePiece)
                self.game.removePieceFromSquare(0,2)
                return False

        elif [movePositionY,movePositionX] ==[0,6]:
            self.game.addPieceToSquare(0,6, movePiece)
            self.game.removePieceFromSquare(piecePositionY,piecePositionX)
            rookPiece = self.game.getPieceOnSquare(0, 7)
            self.game.addPieceToSquare(0, 5, rookPiece)
            self.game.removePieceFromSquare(0,6)
            if self.game.getBCheck() ==True:
                self.game.addPieceToSquare(0,6,rookPiece)
                self.game.removePieceFromSquare(0,5)
                self.game.addPieceToSquare(piecePositionY, piecePositionX, movePiece)
                self.game.removePieceFromSquare(0,6)
                return False
        return True

    def getDifficultMove(self,playerColour):
        #Method to get a difficult move for the difficult AI player. 
        #bestMoveFirstDepth list stores data about the best move using the first depth. 
        bestMoveFirstDepth = [0]
        #bestMoveSecondDepth list stores data about the best move looking one move ahead using the second depth. 
        bestMoveSecondDepth = [0]
        #validTake boolean stores whether a piece can be taken on the players turn. 
        validTake = False
        #Iterate through every square on the board:
        for Y in range(8):
            for X in range(8):
                pieceOnSquare = self.game.getPieceOnSquare(Y,X)
                #Check whether there is a piece on the square and whether it is the same colour as the player.  
                if pieceOnSquare !="" and pieceOnSquare.getColour() == playerColour:
                    #Get all of the valid moves of that player. 
                    validSquares, validTakeSquares, castleMoves, enPassantMoves = self.getPieceTotalMoves(pieceOnSquare,playerColour,Y,X)
                    #Iterate through all of the valid take squares:
                    for i in validTakeSquares:
                        #Get the piece that would be taken as a result of the move:
                        takePieceOnSquare = self.game.getPieceOnSquare(i[0],i[1])
                        #Check whether the piece that would be taken is NOT the King. 
                        if takePieceOnSquare.getPiece()!="King":
                            #Get the evaluation score of the piece using the .getEvaluationScore() method of the chessPiece class. 
                            pieceEvaluationScore = takePieceOnSquare.getEvaluationScore()
                            #Set the goodMove boolean equal to True. 
                            goodMove = True
                            tempPiece2 = self.game.getPieceOnSquare(i[0],i[1])
                            self.game.addPieceToSquare(i[0],i[1], pieceOnSquare)
                            self.game.removePieceFromSquare(Y,X)
                            #Get the opponents total valid squares. 
                            if playerColour =="w":
                                opponentTotalValidSquares, opponentTotalValidTakeSquares, castleMoves, enPassantMoves = self.game.getTotalPlayerMoves("b")
                            else:
                                opponentTotalValidSquares, opponentTotalValidTakeSquares, castleMoves, enPassantMoves = self.game.getTotalPlayerMoves("w")

                            #Iterate through oponentTotalValidSquares.
                            for k in opponentTotalValidTakeSquares:
                                piece = self.game.getPieceOnSquare(k[0], k[1])
                                if piece == pieceOnSquare:
                                    goodMove = False

                            #Move the pieces back
                            self.game.removePieceFromSquare(i[0],i[1])
                            self.game.addPieceToSquare(Y,X,pieceOnSquare)
                            self.game.addPieceToSquare(i[0],i[1],tempPiece2)
                            #If the bestMoveFirstDepth list is empty, add this move to it.
                            validTake = True
                            if bestMoveFirstDepth == []:
                                bestMoveFirstDepth = [pieceEvaluationScore, pieceOnSquare, Y, X, i[0], i[1]]

                            else:
                                tempBestMove = [pieceEvaluationScore, pieceOnSquare, Y, X, i[0], i[1]]
                                #If this move is better than the move already stored in the bestMoveFirstDepth list, then replace it with the new move.
                                if tempBestMove[0] > bestMoveFirstDepth[0]:
                                    bestMoveFirstDepth = tempBestMove

                    #Iterate through ALL of the valid moves for every piece: 
                    for i in validSquares: 
                        #Move the piece
                        if self.game.isSquareEmpty(i[0],i[1]) == False:
                            self.game.removePieceFromSquare(Y,X)
                            #Store the piece that would be taken under the variable name tempPiece.
                            tempPiece = self.game.getPieceOnSquare(i[0],i[1])
                        else:
                            tempPiece = ""

                        #Get the validSquares and validTakeSquares of the piece in its new position. 
                        self.game.addPieceToSquare(i[0],i[1],pieceOnSquare)
                        validSquaresDepthTwo, validTakeSquaresDepthTwo, castleMoves, enPassantMoves = self.getPieceTotalMoves(pieceOnSquare,playerColour,i[0],i[1])
                        #Iterate through the validTakeSquaresDepthTwo list. 
                        for j in validTakeSquaresDepthTwo:
                            #Get the piece that would be taken as a result of the move and store in variable takePieceOnSquare. 
                            takePieceOnSquare = self.game.getPieceOnSquare(j[0],j[1])
                            if takePieceOnSquare!="" and takePieceOnSquare.getPiece()!="King":
                                #Get the evaluation score of the taken piece using the .getEvaluationScore() method of the chessPiece class.
                                pieceEvaluationScore = takePieceOnSquare.getEvaluationScore()
                                #Set the goodMove boolean equal to True. 
                                goodMove = True
                                tempPiece2 = self.game.getPieceOnSquare(j[0],j[1])
                                self.game.addPieceToSquare(j[0],j[1], pieceOnSquare)
                                self.game.removePieceFromSquare(i[0],i[1])
                                #Get the opponents total valid squares. 
                                if playerColour =="w":
                                    opponentTotalValidSquares, opponentTotalValidTakeSquares, castleMoves, enPassantMoves = self.game.getTotalPlayerMoves("b")

                                else:
                                    opponentTotalValidSquares, opponentTotalValidTakeSquares, castleMoves, enPassantMoves = self.game.getTotalPlayerMoves("w")

                                #Iterate through oponentTotalValidSquares. 
                                for k in opponentTotalValidTakeSquares:
                                    piece = self.game.getPieceOnSquare(k[0], k[1])
                                    if piece == pieceOnSquare:
                                        goodMove = False
                                #Move the pieces back
                                self.game.removePieceFromSquare(j[0],j[1])
                                self.game.addPieceToSquare(i[0],i[1],pieceOnSquare)
                                self.game.addPieceToSquare(j[0],j[1],tempPiece2)
                                validTake = True
                                if bestMoveSecondDepth == []:
                                    bestMoveSecondDepth = [pieceEvaluationScore, pieceOnSquare, Y, X, i[0], i[1]]

                                else:
                                    tempBestMove = [pieceEvaluationScore, pieceOnSquare, Y, X, i[0], i[1]]
                                    if tempBestMove[0] > bestMoveSecondDepth[0]:
                                        bestMoveSecondDepth = tempBestMove

                        #Move the pieces back
                        self.game.removePieceFromSquare(i[0],i[1])
                        self.game.addPieceToSquare(Y,X,pieceOnSquare)
                        self.game.addPieceToSquare(i[0],i[1],tempPiece)

        if validTake == True:
            #If the bestMoveSecondDepth is a better than the bestMoveFirstDepth, return the second depth move. 
            if bestMoveSecondDepth[0] > bestMoveFirstDepth[0]:
                return bestMoveSecondDepth[1], bestMoveSecondDepth[4],bestMoveSecondDepth[5], bestMoveSecondDepth[2], bestMoveSecondDepth[3]
            #If the bestMoveFirstDepth is greater than or equal to the bestMoveSecondDepth, return the first depth move. 
            else:
                return bestMoveFirstDepth[1], bestMoveFirstDepth[4],bestMoveFirstDepth[5], bestMoveFirstDepth[2], bestMoveFirstDepth[3]

        else:
            #If there is not a piece to take, generate an evaluated move based upon pieces evaluation score. 
            movePiece, movePositionY, movePositionX,  piecePositionY, piecePositionX = self.getEvaluatedMove(playerColour)
            return movePiece, movePositionY, movePositionX,  piecePositionY, piecePositionX

    def getEvaluatedMove(self,playerColour):
        #Method to get an evaluated move for the average AI player. 
        moveDict = {} #Dictionary to hold all of the moves for each piece. The piece is the key, the moves stored in a list are the values.
        bestMove = [] #Stores the best move calculated so far.
        validTake = False #Boolean which indicates whether the piece being analysed can take an opponents piece. 
        for Y in range(8):
            for X in range(8):
                #Get the piece on the square. 
                pieceOnSquare = self.game.getPieceOnSquare(Y,X)
                if pieceOnSquare !="":
                    if pieceOnSquare.getColour() == playerColour:
                        #Check whether the piece is the same colour as the player and get its total valid moves. 
                        validSquares, validTakeSquares, castleMoves, enPassantMoves = self.getPieceTotalMoves(pieceOnSquare,playerColour,Y,X)
                        #Add all of the valid moves for the piece to a dictionary which holds all of the valid moves of all of the pieces.
                        if validSquares !=[]:
                            moveDict[pieceOnSquare]=[validSquares, Y, X] #The key is the piece name, and the data includes the pieces valid squares and current position on the board.

                        #If the piece can take any of the oppoents pieces, analyse these moves:    
                        if validTakeSquares !=[]:
                            for i in validTakeSquares:
                                #Get the opponents piece that would be taken and get its 'evaluation score'. 
                                takePieceOnSquare = self.game.getPieceOnSquare(i[0],i[1])
                                pieceEvaluationScore = takePieceOnSquare.getEvaluationScore()

                                #Complete the move temporarily.
                                self.game.addPieceToSquare(i[0],i[1], pieceOnSquare)
                                self.game.removePieceFromSquare(Y,X)

                                #Get the opponents total valid squares. 
                                if playerColour =="w":
                                    opponentTotalValidSquares, opponentTotalValidTakeSquares, castleMoves, enPassantMoves = self.game.getTotalPlayerMoves("b")
                                else:
                                    opponentTotalValidSquares, opponentTotalValidTakeSquares, castleMoves, enPassantMoves = self.game.getTotalPlayerMoves("w")      

                                #Check whether this move would put the piece at risk from the opponents from their next move:
                                goodMove = True
                                for k in opponentTotalValidTakeSquares:
                                    piece = self.game.getPieceOnSquare(k[0], k[1])
                                    if piece == pieceOnSquare:
                                        goodMove = False
                                #Put the pieces back to how they were before:
                                self.game.addPieceToSquare(Y,X,pieceOnSquare)
                                self.game.addPieceToSquare(i[0],i[1],takePieceOnSquare)
                                #If the move does not result in risk of the piece being taken, it is considered a 'Good move'. 
                                if goodMove == True:
                                    validTake = True #This means that the player can definitely take a piece on their go. 
                                    if bestMove == []:
                                        #If there is currently no best move, add it to the bestMove array. 
                                        bestMove = [pieceEvaluationScore, pieceOnSquare, Y, X, i[0], i[1]]

                                    else:
                                        #If a best move already exists, check if this move is better. 
                                        tempBestMove = [pieceEvaluationScore, pieceOnSquare, Y, X, i[0], i[1]]
                                        if tempBestMove[0] > bestMove[0]:
                                            bestMove = tempBestMove


        #If validTake is True, return the best move previously calculated. 
        if validTake == True:
            return bestMove[1], bestMove[4],bestMove[5], bestMove[2], bestMove[3]

        #If there is not a piece to take, generate a random move.                                
        randomPiece, randomPieceDataList = random.choice(list(moveDict.items())) #Select a random piece
        length = len(randomPieceDataList[0]) #Gets the number of valid moves for the piece. 
        randomMove = randomPieceDataList[0][random.randint(0,length-1)] #Selects a random move for the random piece. 
        return randomPiece, randomMove[0], randomMove[1], randomPieceDataList[1], randomPieceDataList[2]

    def getRandomMove(self, playerColour):
        #Method to get a random AI move for the easy AI player. 
        moveDict = {} #Dictionary to hold all of the moves for each piece. The piece is the key, the moves stored in a list are the values.
        for Y in range(8):
            for X in range(8):
                totalValidSquares= []
                pieceOnSquare = self.game.getPieceOnSquare(Y,X)
                if pieceOnSquare !="":
                    if pieceOnSquare.getColour() == playerColour:
                        validSquares, validTakeSquares, castleMoves, enPassantMoves = self.getPieceTotalMoves(pieceOnSquare,playerColour,Y,X)
                        #Add all of the valid take squares, add them to the valid squares list. 
                        for i in (validTakeSquares):
                            #Get the piece on the square where the pieceOnSquare is moving to.
                            tempPiece = self.game.getPieceOnSquare(i[0],i[1])
                            #Temporarily complete the move.
                            self.game.addPieceToSquare(i[0], i[1], pieceOnSquare)
                            self.game.removePieceFromSquare(Y, X)
                            #Check if the move has resulted in check. 
                            self.checkForCheck()
                            #Undo the temporary move. 
                            self.game.removePieceFromSquare(i[0],i[1])
                            self.game.addPieceToSquare(i[0],i[1], tempPiece)
                            self.game.addPieceToSquare(Y, X, pieceOnSquare)
                            #Check if teh move did result in check.
                            if playerColour == "w" and self.game.getWCheck() != True: 
                                totalValidSquares.append(i)
                            elif playerColour =="b" and self.game.getBCheck() != True:
                                totalValidSquares.append(i)

                        for i in (validSquares):
                            #Temporariy complete the move. 
                            self.game.addPieceToSquare(i[0], i[1], pieceOnSquare)
                            self.game.removePieceFromSquare(Y, X)
                            #Check if the move has resulted in check.
                            self.checkForCheck()
                            #Undo the temporary move. 
                            self.game.removePieceFromSquare(i[0],i[1])
                            self.game.addPieceToSquare(Y, X, pieceOnSquare)
                            #Check if the move did result in check.
                            if playerColour == "w" and self.game.getWCheck() != True: 
                                totalValidSquares.append(i)
                            elif playerColour =="b" and self.game.getBCheck() != True:
                                totalValidSquares.append(i)

                        #Add all of the valid moves for the piece to a dictionary which holds all of the valid moves of all of the pieces.
                        if totalValidSquares !=[]:
                            #The key is the piece name, and the data includes the pieces valid squares and current position on the board.
                            moveDict[pieceOnSquare]=[totalValidSquares, Y, X] 

        randomPiece, randomPieceDataList = random.choice(list(moveDict.items())) #Select a random piece
        length = len(randomPieceDataList[0]) #Gets the number of valid moves for the piece. 
        randomMove = randomPieceDataList[0][random.randint(0,length-1)] #Selects a random move for the random piece. 
        return randomPiece, randomMove[0], randomMove[1], randomPieceDataList[1], randomPieceDataList[2]

    def completeMove(self,movePiece, piecePositionX, piecePositionY, movePositionX, movePositionY, validSquares, validTakeSquares, castleMoves, enPassantMoves):
        #Method to complete a move. 
        self.checkForCheck()
        playerColour = movePiece.getColour()

        #Firsty check if the move is an En Passant move.
        if ([movePositionY,movePositionX]) in (enPassantMoves):
            self.completeEnPassantMove(movePositionY, movePositionX, movePiece, piecePositionY, piecePositionX)
            return True

        #Secondly, check if the move is a castling move.        
        if ([movePositionY,movePositionX]) in (castleMoves):
            isCastleMoveComplete = self.completeCastleMove(movePositionY, movePositionX, movePiece, playerColour, piecePositionY, piecePositionX)
            return isCastleMoveComplete

        #If the move is not a castle or En Passant, it must be a normal move. 
        if ([movePositionY,movePositionX]) in (validSquares) or ([movePositionY,movePositionX]) in validTakeSquares:
            #Get the piece to be taken as a result of the move, if applicable. 
            takePiece = self.game.getPieceOnSquare(movePositionY, movePositionX)
            if takePiece !="":
                if (takePiece.getPiece())=="King":
                    #If the take piece is the King, this move is not possible as the King cannot ever be taken. 
                    return False

            #Check if the player isn't in check:
            if (playerColour =="w" and self.game.getWCheck() == False) or (playerColour =="b" and self.game.getBCheck() == False):
                #If the piece player isn't in check, the move can be completed. 
                #Complete the move and check if check has arisen as a result of the move.      
                self.game.updateChessBoard(piecePositionY, piecePositionX, movePositionY, movePositionX, movePiece)
                self.checkForCheck()
                #If the player has move themselves into check, the move is invalid and undone. 
                if (self.game.getBCheck()==True and playerColour == "b") or (self.game.getWCheck()==True and playerColour == "w"):
                    self.game.resetMove(movePositionY, movePositionX, piecePositionY, piecePositionX, movePiece)
                    return False

                else:
                    #If the player has not moved themselves into check, the move is valid.
                    #If a piece was taken, it is added to the relevant taken pieces list. 
                    if takePiece!="":
                        if takePiece.getColour() == "w":
                            self.game.addTakenWhitePiece(takePiece)
                        else:
                            self.game.addTakenBlackPiece(takePiece)
                    return True

            else: #If the player is in check their move MUST move them out of check:
                self.game.updateChessBoard(piecePositionY, piecePositionX, movePositionY, movePositionX, movePiece)                  
                self.checkForCheck() #Now the move has been completed, check if it has removed the King from check.                       
                if playerColour == "w": #If the player is white
                    if self.game.getWCheck()==True: #If the player is still in check the the move is not possible, therefore the piece are put back:
                         self.game.resetMove(movePositionY, movePositionX, piecePositionY, piecePositionX, movePiece)
                         self.game.addPieceToSquare(movePositionY, movePositionX, takePiece)
                         return False

                    else: #If the player is no longer in check, the move is successful, therefore True can be returned.
                        #If a piece was taken, it is added to the relevant taken pieces list. 
                        if takePiece!="":
                            if takePiece.getColour() == "w":
                                self.game.addTakenWhitePiece(takePiece)
                            else:
                                self.game.addTakenBlackPiece(takePiece)
                        return True

                else: #If the player is black.
                     if self.game.getBCheck()==True: #If the player is still in check the the move is not possible, therefore the piece are put back:
                         self.game.resetMove(movePositionY, movePositionX, piecePositionY, piecePositionX, movePiece)
                         self.game.addPieceToSquare(movePositionY, movePositionX, takePiece)
                         return False
                        
                     else: #If the player is no longer in check, the move is successful, therefore True can be returned.
                         #If a piece was taken, it is added to the relevant taken pieces list. 
                        if takePiece!="":
                            if takePiece.getColour() == "w":
                                self.game.addTakenWhitePiece(takePiece)
                            else:
                                self.game.addTakenBlackPiece(takePiece)
                        return True           
        else:
            #If the move is not a Castle, En Passant or valid move, False is returned. 
            return False

    def completeAIMove(self, movePiece, piecePositionX, piecePositionY, movePositionX, movePositionY, playerColour):
        #Method to complete an AI move. 
        if (playerColour =="w"and  self.game.getWCheck() == False) or (playerColour =="b" and self.game.getBCheck() == False):
            #If the piece player isn't in check, the move can be completed.
            self.game.updateChessBoard(piecePositionY, piecePositionX, movePositionY, movePositionX, movePiece)
            self.checkForCheck()
            if (self.game.getBCheck()==True and playerColour == "b") or (self.game.getWCheck()==True and playerColour == "w"):
                #If the player is still in check the the move is not possible, therefore the piece are put back:
                self.game.resetMove(movePositionY, movePositionX, piecePositionY, piecePositionX,movePiece)
                return False
            else:           
                return True
            
        else: #If the player is in check their move MUST move them out of check:
            self.game.updateChessBoard(piecePositionY, piecePositionX, movePositionY, movePositionX, movePiece)                  
            self.checkForCheck() #Now the move has been completed, check if it has removed the King from check.               
            if playerColour == "w": #If the player is white:
                if self.game.getWCheck()==True: #If the player is still in check the the move is not possible, therefore the piece are put back:
                     self.game.resetMove(movePositionY, movePositionX, piecePositionY, piecePositionX, movePiece)
                     return False
                else: #If the player is no longer in check, the move is successful, therefore True can be returned. 
                    return True
            else: #If the player is black.
                 if self.game.getBCheck()==True: #If the player is still in check the the move is not possible, therefore the piece are put back:
                     self.game.resetMove(movePositionY, movePositionX, piecePositionY, piecePositionX, movePiece)
                     return False
                 else: #If the player is no longer in check, the move is successful, therefore True can be returned. 
                    return True

    def calculateWhitePawnMoves(self, piecePositionY, piecePositionX, firstMove, playerColour):
        #Method to get all of the squares a white pawn could move to.
        #Define two empty arrays for storing the valid squares and one for the valid moves that results in a piece being taken.
        validSquares = []
        validTakeSquares= []
        enPassantMoves = []
        validSquares,validTakeSquares= self.verifyPawnMoveValidity(piecePositionY-1,piecePositionX,validSquares,validTakeSquares) 
        #If the Pawn hasn't moved before, check if it can move forwards two squares. 
        if firstMove == True and [piecePositionY-1,piecePositionX] in validSquares:
            validSquares, validTakeSquares = self.verifyPawnMoveValidity(piecePositionY-2,  piecePositionX,validSquares,validTakeSquares)

        #Use the method isPawnMoveValid to check every permutation of move the piece can undertake.                      
        validSquares, validTakeSquares = self.verifyPawnTakeValidity(piecePositionY-1,  piecePositionX-1,validSquares,validTakeSquares, playerColour)
        validSquares, validTakeSquares = self.verifyPawnTakeValidity(piecePositionY-1,  piecePositionX+1,validSquares,validTakeSquares, playerColour)        
        self.game.isEnPassantMoveValid(playerColour, False, piecePositionY-1, piecePositionX+1, enPassantMoves)
        self.game.isEnPassantMoveValid(playerColour, False, piecePositionY-1, piecePositionX-1, enPassantMoves) 
        return validSquares, validTakeSquares, enPassantMoves

    def calculateBlackPawnMoves(self, piecePositionY, piecePositionX, firstMove, playerColour):
        #Method to get all the squares a black pawn could move to. 
        #Define two empty arrays for storing the valid squares and one for the valid moves that results in a piece being taken.
        validSquares = []
        validTakeSquares= []
        enPassantMoves = []

        if self.boardFlip == False:
            validSquares,validTakeSquares= self.verifyPawnMoveValidity(piecePositionY+1,piecePositionX,validSquares,validTakeSquares)
            if firstMove == True and [piecePositionY+1,piecePositionX] in validSquares:
                validSquares, validTakeSquares= self.verifyPawnMoveValidity(piecePositionY+2,  piecePositionX,validSquares,validTakeSquares)

            validSquares, validTakeSquares = self.verifyPawnTakeValidity(piecePositionY+1,  piecePositionX-1,validSquares,validTakeSquares, playerColour)
            validSquares, validTakeSquares= self.verifyPawnTakeValidity(piecePositionY+1,  piecePositionX+1,validSquares,validTakeSquares, playerColour)
 

        else:
            #If boardFlip is enabled, the black pawns will be at the bottom of the screen, therefore the calculateWhitePawnMoves method can just be used. 
            validSquares, validTakeSquares, enPassantMoves = self.calculateWhitePawnMoves(piecePositionY,piecePositionX,firstMove, playerColour)

        self.game.isEnPassantMoveValid(playerColour, False, piecePositionY+1, piecePositionX+1, enPassantMoves)
        self.game.isEnPassantMoveValid(playerColour, False, piecePositionY+1, piecePositionX-1, enPassantMoves) 
        return validSquares, validTakeSquares, enPassantMoves

    def calculateRookMoves(self, piecePositionY, piecePositionX, pieceColour):
        #method to get all of the squares the rook could move to. 
        #Define two empty arrays for storing the valid squares and one for the valid moves that results in a piece being taken.
        validSquares = []
        validTakeSquares = []

        #Use the method isMoveValid to check every permutation of move the piece can undertake. 
        for i in range(1,9):
            validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY + i, piecePositionX, validSquares, validTakeSquares, pieceColour)
            if stop == True:
                break

        for i in range(1,9):    
            validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY, piecePositionX+i, validSquares, validTakeSquares, pieceColour)
            if stop == True:
                break
            
        for i in range(1,9):
            validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY - i, piecePositionX, validSquares, validTakeSquares, pieceColour)
            if stop == True:
                break
        for i in range(1,9):    
            validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY, piecePositionX-i, validSquares, validTakeSquares, pieceColour)
            if stop == True:
                break 

        return validSquares, validTakeSquares

    def calculateKnightMoves(self, piecePositionY, piecePositionX, pieceColour):
        #Method to get all of the squares the knight could move to. 
        #Define two empty arrays for storing the valid squares and one for the valid moves that results in a piece being taken.
        validSquares = []
        validTakeSquares = []

        #Use the method isMoveValid to check every permutation of move the piece can undertake. 
        validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY+2, piecePositionX-1, validSquares, validTakeSquares, pieceColour)
        validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY-1, piecePositionX+2, validSquares, validTakeSquares, pieceColour)
        validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY-2, piecePositionX-1, validSquares, validTakeSquares, pieceColour)
        validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY+2, piecePositionX+1, validSquares, validTakeSquares, pieceColour)
        validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY+1, piecePositionX+2, validSquares, validTakeSquares, pieceColour)
        validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY-1, piecePositionX-2, validSquares, validTakeSquares, pieceColour)
        validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY+1, piecePositionX-2, validSquares, validTakeSquares, pieceColour)
        validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY-2, piecePositionX+1, validSquares, validTakeSquares, pieceColour)

        return validSquares, validTakeSquares

    def calculateBishopMoves(self, piecePositionY, piecePositionX, pieceColour):
        #Method to get all of the squares the bishop could move to. 
        #Define two empty arrays for storing the valid squares and one for the valid moves that results in a piece being taken.
        validSquares = []
        validTakeSquares = []
                                                                           
        #Use the method isMoveValid to check every permutation of move the piece can undertake. 
        for i in range(1,9):
            validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY+i, piecePositionX+i, validSquares, validTakeSquares, pieceColour)
            if stop == True:
                break

        for i in range(1,9):
            validSquares, validTakeSquares,stop = self.verifyMoveValidity(piecePositionY-i, piecePositionX-i, validSquares, validTakeSquares, pieceColour)
            if stop == True:
                break

        for i in range(1,9):
            validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY-i, piecePositionX+i, validSquares, validTakeSquares, pieceColour)
            if stop == True:
                break

        for i in range(1,9):
            validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY+i, piecePositionX-i, validSquares, validTakeSquares, pieceColour)
            if stop == True:
                break

        return validSquares, validTakeSquares

    def calculateKingMoves(self, piecePositionY, piecePositionX, pieceColour):
        #Method to get all of the squares the king could move to. 
        #Define two empty arrays for storing the valid squares and one for the valid moves that results in a piece being taken.
        validSquares = []
        validTakeSquares =[]
        castleMoves = []

        #Use the method isMoveValid to check every permutation of move the piece can undertake. 
        validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY+1, piecePositionX, validSquares, validTakeSquares, pieceColour)
        validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY-1, piecePositionX, validSquares, validTakeSquares, pieceColour)
        validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY, piecePositionX+1, validSquares, validTakeSquares, pieceColour)
        validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY, piecePositionX-1, validSquares, validTakeSquares, pieceColour)
        validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY-1, piecePositionX-1, validSquares, validTakeSquares, pieceColour)
        validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY+1, piecePositionX-1, validSquares, validTakeSquares, pieceColour)
        validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY+1, piecePositionX+1, validSquares, validTakeSquares, pieceColour)
        validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY-1, piecePositionX+1, validSquares, validTakeSquares, pieceColour)
        if pieceColour == "w":
            pieceOnKingSquare = self.game.getPieceOnSquare(7,4)
            if pieceOnKingSquare!="":
                if pieceOnKingSquare.getPiece() == "King" and pieceOnKingSquare.getFirstMove() == True:
                    castleMoves =self.game.isCastleMoveValid(pieceColour)
        else:
            pieceOnKingSquare = self.game.getPieceOnSquare(0,4)
            if pieceOnKingSquare !="":
                if pieceOnKingSquare.getPiece() == "King" and pieceOnKingSquare.getFirstMove() == True:
                    castleMoves =self.game.isCastleMoveValid(pieceColour)
                    
                

            
    
        return validSquares, validTakeSquares, castleMoves

    def calculateQueenMoves(self, piecePositionY, piecePositionX, pieceColour):
        #Method to get all the squares the queen could move to. 
        #Define two empty arrays for storing the valid squares and one for the valid moves that results in a piece being taken.
        validSquares = []
        validTakeSquares = []

        #Use the method isMoveValid to check every move the piece could possibly take. 
        for i in range(1,9):
            validSquares, validTakeSquares, stop  = self.verifyMoveValidity(piecePositionY+i, piecePositionX+i, validSquares, validTakeSquares, pieceColour)
            if stop == True:
                break

        for i in range(1,9):
            validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY-i, piecePositionX-i, validSquares, validTakeSquares, pieceColour)
            if stop == True:
                break

        for i in range(1,9):
            validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY-i, piecePositionX+i, validSquares, validTakeSquares, pieceColour)
            if stop == True:
                break

        for i in range(1,9):
            validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY+i, piecePositionX-i, validSquares, validTakeSquares, pieceColour)
            if stop == True:
                break

        for i in range(1,9):
            validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY + i, piecePositionX, validSquares, validTakeSquares, pieceColour)
            if stop == True:
                break

        for i in range(1,9):    
            validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY, piecePositionX+i, validSquares, validTakeSquares, pieceColour)
            if stop == True:
                break

        for i in range(1,9):
            validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY - i, piecePositionX, validSquares, validTakeSquares, pieceColour)
            if stop == True:
                break

        for i in range(1,9):    
            validSquares, validTakeSquares, stop = self.verifyMoveValidity(piecePositionY, piecePositionX-i, validSquares, validTakeSquares, pieceColour)
            if stop == True:
                break

        return validSquares, validTakeSquares #Return the two arrays containing all moves the piece can complete. 

    def verifyMoveValidity(self, Y, X, validSquares, validTakeSquares, pieceColour):
        #Method to check whether a move is legal and valid. 
        stop = False    
        if 0<=X<=7 and 0<=Y<=7:
            if self.game.isSquareEmpty(Y,X)==True:
                validSquares.append([Y,X])
            else:
                pieceOnSquare = self.game.getPieceOnSquare(Y,X)
                pieceOnSquareColour = pieceOnSquare.getColour()
                if pieceOnSquareColour!= pieceColour:
                    validTakeSquares.append([Y,X])                   
                stop = True
        return validSquares,validTakeSquares, stop

    def verifyPawnMoveValidity(self,Y, X, validSquares, validTakeSquares):
        #Method to check whether a pawn can move legally. 
        if 0<=X<=7 and 0<=Y<=7:
            if self.game.isSquareEmpty(Y,X)==True:
                validSquares.append([Y,X])

        return validSquares,validTakeSquares

    def verifyPawnTakeValidity(self,Y, X, validSquares, validTakeSquares, playerColour):
        #Method to check whether a pawn can take another piece legally. 
        if 0<=X<=7 and 0<=Y<=7:
            if self.game.isSquareEmpty(Y,X)==False:
                pieceOnSquare = self.game.getPieceOnSquare(Y,X)
                pieceOnSquareColour = pieceOnSquare.getColour()
                if pieceOnSquareColour!= playerColour:
                    validTakeSquares.append([Y,X])

        return validSquares,validTakeSquares

    def changePlayer(self):
        #Method to change the player at the end of each players turn.
        if self.player == self.player1:
            self.player = self.player2
        else:
            self.player = self.player1

    def renderBoardAlgebra(self):
        #Method to display the numbers and letters at the side of the chessboard. 
        font = pygame.font.SysFont('comicsansms', 23)
        pygame.draw.rect(self.window, DARKBROWN,(700,90,50,700))
        pygame.draw.rect(self.window, DARKBROWN,(15,90,50,700))
        pygame.draw.rect(self.window, DARKBROWN,(70,700,600,50))
        pygame.draw.rect(self.window, DARKBROWN,(70,10,600,50))

        if self.flipBoard ==False:
            self.window.blit(font.render('8', True, (WHITE)), (700, 90))
            self.window.blit(font.render('7', True, (WHITE)), (700, 170))
            self.window.blit(font.render('6', True, (WHITE)), (700, 250))
            self.window.blit(font.render('5', True, (WHITE)), (700, 330))
            self.window.blit(font.render('4', True, (WHITE)), (700, 410))
            self.window.blit(font.render('3', True, (WHITE)), (700, 490))
            self.window.blit(font.render('2', True, (WHITE)), (700, 570))
            self.window.blit(font.render('1', True, (WHITE)), (700, 660))

            self.window.blit(font.render('8', True, (WHITE)), (15, 90))
            self.window.blit(font.render('7', True, (WHITE)), (15, 170))
            self.window.blit(font.render('6', True, (WHITE)), (15, 250))
            self.window.blit(font.render('5', True, (WHITE)), (15, 330))
            self.window.blit(font.render('4', True, (WHITE)), (15, 410))
            self.window.blit(font.render('3', True, (WHITE)), (15, 490))
            self.window.blit(font.render('2', True, (WHITE)), (15, 570))
            self.window.blit(font.render('1', True, (WHITE)), (15, 660))

            self.window.blit(font.render('A', True, (WHITE)), (70, 700))
            self.window.blit(font.render('B', True, (WHITE)), (150, 700))
            self.window.blit(font.render('C', True, (WHITE)), (235, 700))
            self.window.blit(font.render('D', True, (WHITE)), (320, 700))
            self.window.blit(font.render('E', True, (WHITE)), (400, 700))
            self.window.blit(font.render('F', True, (WHITE)), (480, 700))
            self.window.blit(font.render('G', True, (WHITE)), (560, 700))
            self.window.blit(font.render('H', True, (WHITE)), (640, 700))

            self.window.blit(font.render('A', True, (WHITE)), (70, 10))
            self.window.blit(font.render('B', True, (WHITE)), (150, 10))
            self.window.blit(font.render('C', True, (WHITE)), (235, 10))
            self.window.blit(font.render('D', True, (WHITE)), (320, 10))
            self.window.blit(font.render('E', True, (WHITE)), (400, 10))
            self.window.blit(font.render('F', True, (WHITE)), (480, 10))
            self.window.blit(font.render('G', True, (WHITE)), (560, 10))
            self.window.blit(font.render('H', True, (WHITE)), (640, 10))

        if self.flipBoard == True:
            #If the flipBoard boolean is True, flip the board algebra. 
            self.window.blit(font.render('1', True, (WHITE)), (700, 90))
            self.window.blit(font.render('2', True, (WHITE)), (700, 170))
            self.window.blit(font.render('3', True, (WHITE)), (700, 250))
            self.window.blit(font.render('4', True, (WHITE)), (700, 330))
            self.window.blit(font.render('5', True, (WHITE)), (700, 410))
            self.window.blit(font.render('6', True, (WHITE)), (700, 490))
            self.window.blit(font.render('7', True, (WHITE)), (700, 570))
            self.window.blit(font.render('8', True, (WHITE)), (700, 660))

            self.window.blit(font.render('1', True, (WHITE)), (15, 90))
            self.window.blit(font.render('2', True, (WHITE)), (15, 170))
            self.window.blit(font.render('3', True, (WHITE)), (15, 250))
            self.window.blit(font.render('4', True, (WHITE)), (15, 330))
            self.window.blit(font.render('5', True, (WHITE)), (15, 410))
            self.window.blit(font.render('6', True, (WHITE)), (15, 490))
            self.window.blit(font.render('7', True, (WHITE)), (15, 570))
            self.window.blit(font.render('8', True, (WHITE)), (15, 660))

            self.window.blit(font.render('H', True, (WHITE)), (70, 700))
            self.window.blit(font.render('G', True, (WHITE)), (150, 700))
            self.window.blit(font.render('F', True, (WHITE)), (235, 700))
            self.window.blit(font.render('E', True, (WHITE)), (320, 700))
            self.window.blit(font.render('D', True, (WHITE)), (400, 700))
            self.window.blit(font.render('C', True, (WHITE)), (480, 700))
            self.window.blit(font.render('B', True, (WHITE)), (560, 700))
            self.window.blit(font.render('A', True, (WHITE)), (640, 700))
            
            self.window.blit(font.render('H', True, (WHITE)), (70, 10))
            self.window.blit(font.render('G', True, (WHITE)), (150, 10))
            self.window.blit(font.render('F', True, (WHITE)), (235, 10))
            self.window.blit(font.render('E', True, (WHITE)), (320, 10))
            self.window.blit(font.render('D', True, (WHITE)), (400, 10))
            self.window.blit(font.render('C', True, (WHITE)), (480, 10))
            self.window.blit(font.render('B', True, (WHITE)), (560, 10))
            self.window.blit(font.render('A', True, (WHITE)), (640, 10))

        pygame.draw.rect(self.window,(137, 76, 22),(725,0,900,140))
        pygame.draw.rect(self.window,(137, 76, 22),(780,650,900,750))
        font = pygame.font.SysFont('comicsansms', 20)
        self.window.blit(font.render('Resign', True, (WHITE)), (740, 150))
        self.window.blit(font.render('Save Game', True, (WHITE)), (845,150))

        pygame.draw.line(self.window,BLACK,(40,48),(690,48),3)
        pygame.draw.line(self.window,BLACK,(690,50),(690,700),3)
        pygame.draw.line(self.window,BLACK,(38,50),(38,700),3)
        pygame.draw.line(self.window,BLACK,(40,700),(690,700),3)

    def displayTakenPieces(self,window):
        #Method to display the taken pieces at the side of the board. 
        #Display the take white pieces by using the method getTakenWhitePieceList. 
        takenWhitePieces = self.game.getTakenWhitePieceList()
        XB = 730
        YB = 400
        XW = 730
        YW = 200

        #Iterate through the list and display each piece on the screen. 
        for piece in takenWhitePieces:
            img = piece.getImage()
            self.window.blit(img,(XW,YW))
            XW = XW + 50
            if XW >900:
                XW = 730
                YW +=50

        #Display the take black pieces by using the method getTakenBlackPieceList.
        takenBlackPieces = self.game.getTakenBlackPieceList()
        #Iterate through the list and display each piece on the screen. 
        for piece in takenBlackPieces:
            img = piece.getImage()
            self.window.blit(img,(XB,YB))
            XB = XB + 50
            if XB >900:
                XB = 730
                YB +=50

    def renderNotValid(self,window):
        #Method to display a message to the window when the player attempts to move illegally. 
        pygame.draw.rect(self.window, DARKBROWN,(785,690,150,50))
        font = pygame.font.SysFont('rockwell', 25)
        self.window.blit(font.render('Invalid Move', True, (WHITE)), (785, 690))
        pygame.display.flip()

    def checkForCheck(self):
        #Method to check whether the player is in check. 
        #Firstly assume that no-one is in check:
        self.game.setWCheck(False)
        self.game.setBCheck(False)
        #Iterate through every piece on the board:
        for Y in range(8):
            for X in range(8):
                pieceOnSquare = self.game.getPieceOnSquare(Y,X)
                if pieceOnSquare !="":
                    pieceOnSquareColour=pieceOnSquare.getColour() #Gets the piece colour using the .getColour() method of the chessPiece class.
                    #Get the validSquares and validTakeSquares lists of that piece:
                    validSquares,validTakeSquares, castleMoves, enPassantMoves = self.getPieceTotalMoves(pieceOnSquare, pieceOnSquareColour, Y, X) 
                    #Check if the King can be taken, if so, check has arisen:
                    for i in validTakeSquares:
                        takePieceOnSquare = self.game.getPieceOnSquare(i[0],i[1])
                        if takePieceOnSquare.getPiece()== "King":
                            #If piece is white and the King black, the black King is in check:
                            if pieceOnSquareColour == "w" and takePieceOnSquare.getColour() == "b":                               
                                self.game.setBCheck(True)
                                return
                            #If piece is black and the King white, the white King is in check:
                            elif pieceOnSquareColour == "b" and takePieceOnSquare.getColour() == "w":
                                self.game.setWCheck(True)
                                return

    def checkForCheckmate(self, playerColour):
        #Method to check whether checkmate has been reached. 
        for Y in range(8):
            for X in range(8):
                #Get the piece on the square and store it as pieceOnSquare.
                pieceOnSquare = self.game.getPieceOnSquare(Y,X)
                if pieceOnSquare !="":
                    #If there is a piece on the square get its colour using the .getColour() method of the chessPiece class.
                    pieceOnSquareColour=pieceOnSquare.getColour() 
                    #Get the validSquares and validTakeSquares lists of that piece:
                    if pieceOnSquareColour == playerColour:
                        validSquares,validTakeSquares, castleMoves, enPassantMoves = self.getPieceTotalMoves(pieceOnSquare, pieceOnSquareColour, Y, X) 
                        for i in validSquares:
                            #Temporarily complete the move. 
                            self.game.removePieceFromSquare(Y,X)
                            self.game.addPieceToSquare(i[0],i[1],pieceOnSquare)
                            #Check if the move has resulted in check. 
                            self.checkForCheck()
                            #Undo the temporary move.
                            self.game.removePieceFromSquare(i[0],i[1])
                            self.game.addPieceToSquare(Y,X,pieceOnSquare)

                            #Check if the move did result in check. 
                            if playerColour == "w":
                                if self.game.getWCheck()== False:
                                    #If the move removes the player from check, return False.
                                    return False
                            else:
                                if self.game.getBCheck() == False:
                                    #If the move removes the player from check, return False. 
                                    return False

                        for i in validTakeSquares:
                            #Temporarily complete the move. 
                            self.game.removePieceFromSquare(Y,X)
                            tempPiece = self.game.getPieceOnSquare(i[0],i[1])
                            self.game.addPieceToSquare(i[0],i[1],pieceOnSquare)
                            #Check if the move results in check. 
                            self.checkForCheck()
                            self.game.removePieceFromSquare(i[0],i[1])
                            self.game.addPieceToSquare(Y,X,pieceOnSquare)
                            self.game.addPieceToSquare(i[0],i[1],tempPiece)
                            #Check if the move did result in check. 
                            if playerColour == "w":
                                if self.game.getWCheck() == False:
                                    #If the move removes the player from check, return False.
                                    return False
                            else:
                                if self.game.getBCheck() == False:
                                    #If the move removes the player from check, return False.
                                    return False
                                
        #If a move that removes the threat of check isn't found, the attribute checkMate is set to True. 
        self.game.setCheckMate(True)
        #Get and set the winner of the game: 
        if self.player == self.player1:
            self.game.setWinner(self.player2)
        else:
            self.game.setWinner(self.player1)

        return True

    def IncrementNoPawnMoves(self,pawnMoves):
        #Method to increment pawn moves. 
        pawnMoves +=1
        if pawnMoves == 100:
            return pawnMoves, True
        return pawnMoves, False

    def saveGame(self):
        #Method to save the current game state on a game still in progress to a CSV file. 
        pygame.draw.rect(self.window,DARKBROWN,(720,180,300,40))
        run = True
        font = pygame.font.SysFont('rockwell', 15)
        filename = "" #String filename stores the name of the file to be saved. 
        self.window.blit(font.render('File Name:', True, (WHITE)), (740, 180))
        while run == True:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        #If the player presses enter, the game will be saved. 
                        run = False
                        pygame.draw.rect(self.window,DARKBROWN,(720,180,300,40))
                        #Display a message to the window informing that the game has been saved. 
                        self.window.blit(font.render('Game successfully saved as '+ str(filename), True, (WHITE)), (740, 180))
                        
                    elif event.key == pygame.K_BACKSPACE:
                        #If the player presses the backspace, remove the last character from the filename string. 
                        filename = filename[:-1]
                        pygame.draw.rect(self.window,DARKBROWN,(720,180,300,40))
                        self.window.blit(font.render('File Name:', True, (WHITE)), (740, 180))
                        self.window.blit(font.render(filename, True, (WHITE)), (850, 180))

                    else:
                        #If the player presses a letter, get it and add it to the filename string. 
                        filename += event.unicode
                        self.window.blit(font.render(filename, True, (WHITE)), (850, 180))
            pygame.display.flip()#Flip the display to show the player the text as they enter it.

        #Now we have the filename, we open or create the file and write to it:    
        file = open(filename+".txt", "w")
        for Y in range(8):
            for X in range(8):
                pieceToBeSaved = self.game.getPieceOnSquare(Y,X)
                if pieceToBeSaved!="":
                    file.write(pieceToBeSaved.getName() + ",")
                else:
                    file.write("X" + ",") 
            file.write("\n")

        #Write all of the taken white pieces to the file.     
        for i in self.game.getTakenWhitePieceList():
            file.write(i.getName() + ", ")     
        file.write("\n")

        #Write all of the taken black pieces to the file. 
        for i in self.game.getTakenBlackPieceList():
            file.write(i.getName() + ",")
        file.write("\n")

        #Write player data to the file. 
        file.write(self.player1.getName()+ ",")
        file.write(str(0)+ ",")
        file.write(self.player1.getColour()+ ",")
        file.write(self.player1.getAIStatus()+ ",")
        file.write("\n")
        file.write(self.player2.getName()+ ",")
        file.write(str(0)+ ",")
        file.write(self.player2.getColour()+ ",")
        file.write(self.player2.getAIStatus()+ ",")
        file.write("\n")
        file.write(str(self.gameMode))
        #Close the file and return. 
        file.close()


    def getPieceAndSquare(self, tileColours, playerColour):
        #Method to get the piece and square the user selects on their turn. 
        run, mouseState,mouseX,mouseY, mainGameLoop  = self.gameEvents() #Check for any events and get mouse position.
        hasPlayerChosenPiece = False
        hasPlayerChosenSquare = False
        piecePositionX = 0
        piecePositionY = 0
        movePositionX = 0
        movePositionY = 0
        while hasPlayerChosenPiece == False and run == True:
            hasPlayerChosenPiece, movePiece, piecePositionX, piecePositionY = self.game.locateClickedPiece(mouseX,mouseY,mouseState,playerColour) #Check for any events and get mouse position.
            run, mouseState,mouseX,mouseY, mainGameLoop  = self.gameEvents() #Check for any events and get mouse position.
            #Check if the Main Menu button is selected. 
            if 735 <mouseX < 800 and 140 < mouseY < 180 and mouseState == 1:
                confirmResign = self.gameMenu()
                if confirmResign == True:
                    #If the player clicks resign, the game ends.
                    run = False
                    hasPlayerChosenPiece = True
                    hasPlayerChosenSquare = True
            if 835 <mouseX < 950 and 140 < mouseY < 180 and mouseState == 1:
                self.saveGame()

        if self.tileColours == True and run==True :           
            self.game.changeSquareColour(piecePositionY, piecePositionX,BLUE)
            validSquares, validTakeSquares, castleMoves, enPassantMoves = self.getPieceTotalMoves(movePiece,playerColour,piecePositionY, piecePositionX)
            for i in validSquares:
                self.game.changeSquareColour(i[0],i[1],GREEN)
            for i in validTakeSquares:
                self.game.changeSquareColour(i[0],i[1],RED)
            for i in castleMoves:
                self.game.changeSquareColour(i[0],i[1],GREEN)
            for i in enPassantMoves:
                self.game.changeSquareColour(i[0],i[1],GREEN)

            self.game.displayGamePieces()
            pygame.display.flip()

        while hasPlayerChosenSquare == False and run == True:
            hasPlayerChosenSquare, movePositionX, movePositionY = self.game.locateClickedSquare(mouseX,mouseY,mouseState, playerColour)#Check for any events and get mouse position.
            run, mouseState,mouseX,mouseY, mainGameLoop  = self.gameEvents() #Check for any events and get mouse position.
            #Check if the Main Menu button is selected. 
            if 735 <mouseX < 800 and 140 < mouseY < 180 and mouseState == 1:
                confirmResign = self.gameMenu()
                if confirmResign == True:
                    #If the player clicks resign, the game ends.
                    run = False

            if 835 <mouseX < 950 and 140 < mouseY < 180 and mouseState == 1:
                self.saveGame()

        return movePiece, piecePositionX, piecePositionY, movePositionX, movePositionY, run

    def isPawnPromotionValid(self,playerColour, boardFlip, piecePositionY):
        #Method to check whether pawn promotion is applicable.
        #Check to see if the players pawn has reached the other side of the board. 
        if playerColour == "w" or boardFlip == True:
            if piecePositionY == 0:
                return True

        elif playerColour =="b":
            if piecePositionY == 7:
                return True
        return False

    def pawnPromotion(self, playerColour, movePiece, movePositionY, movePositionX):
        #Method to get the piece the player wishes to promote their pawn to when applicable. 
        run = True
        pygame.draw.rect(self.window, LIGHTBROWN,(250,250,180,180))
        pygame.draw.line(self.window,BLACK,(250,250),(430,250),5)
        pygame.draw.line(self.window,BLACK,(250,250),(250,430),5)
        pygame.draw.line(self.window,BLACK,(430,430),(430,250),5)
        pygame.draw.line(self.window,BLACK,(430,430),(250,430),5)

        if playerColour == "b":
            rook = pygame.image.load("Chess_rdt60.png").convert_alpha()
            knight = pygame.image.load("Chess_ndt60.png").convert_alpha()
            bishop = pygame.image.load("Chess_bdt60.png").convert_alpha()
            queen = pygame.image.load("Chess_qdt60.png").convert_alpha()

        else:
            rook = pygame.image.load("Chess_rlt60.png").convert_alpha()
            knight = pygame.image.load("Chess_nlt60.png").convert_alpha()
            bishop = pygame.image.load("Chess_blt60.png").convert_alpha()
            queen = pygame.image.load("Chess_qlt60.png").convert_alpha()

        #Display the pieces the player can choose from.     
        self.window.blit(rook,(255,270))
        self.window.blit(knight,(355,270))
        self.window.blit(bishop,(255,350))
        self.window.blit(queen,(355,350))
        pygame.display.flip()

        #Get the piece the user selects. 
        while run == True:
            run, mouseState,mouseX,mouseY, mainGameLoop  = self.gameEvents() #Check for any events and get mouse position.
            if 255 <mouseX < 300 and 270 < mouseY < 320 and mouseState == 1 and playerColour =="b":
                pawnPromotionPiece = chessPiece("bRPP", "Rook", 50)
                run = False

            elif 255 <mouseX < 300 and 270 < mouseY < 320 and mouseState == 1 and playerColour =="w":
                pawnPromotionPiece = chessPiece("wRPP", "Rook", 50)
                run = False

            elif 355 <mouseX < 400 and 270 < mouseY < 320 and mouseState == 1 and playerColour =="b":
                pawnPromotionPiece = chessPiece("bNPP", "Knight", 30)
                run = False

            elif 355 <mouseX < 400 and 270 < mouseY < 320 and mouseState == 1 and playerColour =="w":
                pawnPromotionPiece = chessPiece("wNPP", "Knight", 30)
                run = False

            elif 255 <mouseX < 300 and 370 < mouseY < 420 and mouseState == 1 and playerColour =="b":
                pawnPromotionPiece = chessPiece("bBPP", "Bishop", 30)
                run = False
                
            elif 255 <mouseX < 300 and 370 < mouseY < 420 and mouseState == 1 and playerColour =="w":
                pawnPromotionPiece = chessPiece("wBPP", "Bishop", 30)
                run = False

            elif 355 <mouseX < 400 and 370 < mouseY < 420 and mouseState == 1 and playerColour =="b":
                 pawnPromotionPiece = chessPiece("bQPP", "Queen", 90)
                 run = False

            elif 355 <mouseX < 400 and 370 < mouseY < 420 and mouseState == 1 and playerColour =="w":
                 pawnPromotionPiece = chessPiece("wQPP", "Queen", 90)
                 run = False

        #Update the board with the new promoted piece. 
        self.game.updateBoardPawnPromotion(movePiece, pawnPromotionPiece, movePositionY, movePositionX)
        #Return the new piece. 
        return pawnPromotionPiece

    def gameMenu(self):
        run = True
        font = pygame.font.SysFont('comicsansms', 16)
        pygame.draw.rect(self.window, LIGHTBROWN,(250,250,250,150))
        pygame.draw.line(self.window,BLACK,(250,250),(500,250),3)
        pygame.draw.line(self.window,BLACK,(250,250),(250,400),3)
        pygame.draw.line(self.window,BLACK,(500,250),(500, 400),3)
        pygame.draw.line(self.window,BLACK,(500,400),(250,400),3)
        self.window.blit(font.render('Are you sure you want to resign?', True, (BLACK)), (255, 270))
        font = pygame.font.SysFont('comicsansms', 14)
        self.window.blit(font.render("Resign and save", True, (BLACK)), (255, 300))
        self.window.blit(font.render("Resign and don't save", True, (BLACK)), (255, 330))
        self.window.blit(font.render("Continue", True, (BLACK)), (255, 360))
        pygame.display.flip()

        while run == True:
            #Check for any events and get mouse position.
            run, mouseState,mouseX,mouseY, mainGameLoop  = self.gameEvents() 
            if 255 <mouseX < 400 and 300 < mouseY < 320 and mouseState == 1:
                self.saveGame()
                run = False
                
            elif 255 <mouseX < 400 and 330 < mouseY < 350 and mouseState == 1:
                run = False

            elif 255 <mouseX < 400 and 360 < mouseY < 380 and mouseState == 1:
                self.game.displayGameBoard()
                self.game.displayGamePieces()
                pygame.display.flip()
                return False

        self.game.displayGameBoard()
        self.game.displayGamePieces()
        pygame.display.flip()
        return True

    def checkGameButtons(self):
        #Method to check if any buttons have been selected on the screen. 
        run = True
        #Check for any events and get mouse position.
        run, mouseState,mouseX,mouseY, mainGameLoop  = self.gameEvents() 
        #Check if the Main Menu button is selected. 
        if 735 <mouseX < 800 and 140 < mouseY < 180 and mouseState == 1:
            confirmResign = self.gameMenu()
            if confirmResign == True:
                run = False
        if 835 <mouseX < 950 and 140 < mouseY < 180 and mouseState == 1:
            self.saveGame()
        return run

    def renderCheckAndPlayer(self, window, playerColour):
        #Method to display check messages and indicators to show which players go it is. 
        font = pygame.font.SysFont('comicsansms', 25)
        if self.game.getWCheck() == True:
            self.window.blit(font.render('White Check', True, (WHITE)), (785, 650))
        elif self.game.getBCheck() ==True:
            self.window.blit(font.render('Black Check', True, (WHITE)), (785, 650))
        font = pygame.font.SysFont('comicsansms', 70)
        if playerColour == "w":     
            self.window.blit(font.render('W', True, (WHITE)), (800, 30))
        else:
            self.window.blit(font.render('B', True, (BLACK)), (800, 30))

    def loadFile(self, filename):
        #Method to load the contents of a saved game file. 
        file = open(filename+".txt", "r") #Open the game file in read mode. 
        matrix = [] #Empty list to store the game board read from the game file. 
        count = 0 #Counter used for counting the number of lines read from the game file. 
        for line in file:
            count +=1 #Increment count by 1 as another line has been read. 
            matrix.append(line.split(","))
            if count ==8:
                break #When 8 lines of the game file has been read, stop the iteration. 
        file.close() #Close the file.
        
        #Instantiate the game object using the imported game board from the file. 
        game = chessBoard(8,8,1,matrix) 
        file = open(filename+".txt", "r")
        lines=file.readlines()
        #Load in the taken white pieces:
        try:
            whitePieces=(lines[8].split(","))
            for piece in whitePieces:
                if piece!="\n":
                    pieceObject = game.pieceLookUp(piece)
                    game.addTakenWhitePiece(pieceObject)
        except:
            pass
        #Load in the taken black pieces: 
        try:
            blackPieces=(lines[9].split(","))
            for piece in blackPieces:
                if piece!="\n":
                    pieceObject = game.pieceLookUp(piece)
                    game.addTakenBlackPiece(pieceObject)
        except:
            pass
        
        file.close()
        #Load in data about the players (eg AI, Name, Moves exc...)
        file = open(filename+".txt", "r")
        lines=file.readlines()
        player1Data=(lines[10].split(","))
        player2Data=(lines[11].split(","))
        player1 = chessPlayer(player1Data[0], player1Data[2], player1Data[1], player1Data[3])
        player2 = chessPlayer(player2Data[0], player2Data[2],player2Data[1], player2Data[3])
        gameMode = (int(lines[12]))
        return game, player1, player2, gameMode

    def getWindow(self):
        #Method for returning the game window. 
        return self.window

class menuScreens(game):
    def __init__(self):
        self.gameMode = 1
        game.__init__(self)

    def mainMenuScreen(self):
        run = True
        #Display the main menu: 
        pygame.display.set_caption("Chess - Main Menu")
        self.window.blit(self.bg, (0, 0))
        font = pygame.font.SysFont('rockwell', 60)
        self.window.blit(font.render('Chess', True, (WHITE)), (60, 100))
        font = pygame.font.SysFont('rockwell', 25)
        self.window.blit(font.render('Regular Game', True, (WHITE)), (60, 250))
        self.window.blit(font.render('Human vs AI Game', True, (WHITE)), (60, 300))
        self.window.blit(font.render('AI vs AI Game', True, (WHITE)), (60, 350))
        self.window.blit(font.render('Load Saved Game', True, (WHITE)), (60, 400))
        self.window.blit(font.render('Rules', True, (WHITE)), (60, 450))
        self.window.blit(font.render('Leaderboard', True, (WHITE)), (60, 500))
        font = pygame.font.SysFont('rockwell', 40)
        self.window.blit(font.render('Quit', True, (WHITE)), (60, 650))
        pygame.display.flip()

        while run == True:
            #Instantiate the game object
            self.game = chessBoard(8,8,0, None) 
            #Check for any events and get mouse position.
            run, mouseState, mouseX, mouseY, mainGameLoop = self.gameEvents() 
            #Human Vs Human
            if 60 < mouseX < 280 and 240 < mouseY < 270 and mouseState == 1: 
                run = False
                #There are to be 2 human player playing.
                self.humanPlayers = 2
                #Instantiate player 1.
                self.player1 = chessPlayer("AI1", "w", 0, "F")
                #Instantiate player 2.
                self.player2 = chessPlayer("AI2", "b", 0, "F") 
                back = self.usernameScreen()
                if back == False:
                    back = self.boardFlipScreen()
                    if back == False:
                        back = self.boardSquareHighlighterScreen()
                        if back == False:
                            self.boardScreen()

            elif 60 < mouseX < 200 and 290 < mouseY < 320 and mouseState == 1:
                #AI Vs Human
                #Instantiate the game object
                self.game = chessBoard(8,8,0, None) 
                run = False
                #There is to be only 1 human player playing. 
                self.humanPlayers = 1
                #Instantiate player 1.
                self.player1 = chessPlayer("AI1", "w", 0, "F")
                #Instantiate player 2.
                self.player2 = chessPlayer("AI2", "b", 0, "T") 
                back = self.usernameScreen()
                if back == False:
                    back = self.boardSquareHighlighterScreen()
                    if back == False:
                        back = self.gameModeScreen()
                        if back == False:
                            back = self.playerColourScreen()
                            if back == False:
                                self.boardScreen()
  

            elif 60 < mouseX < 200 and 340 < mouseY < 370 and mouseState == 1:
                #AI Vs AI Game
                #Instantiate the game object
                self.game = chessBoard(8,8,0, None)
                #Instantiate player 1.
                self.player1 = chessPlayer("AI1", "w", 0, "T")
                #Instantiate player 2.
                self.player2 = chessPlayer("AI2", "b", 0, "T") 
                run = False
                back = self.gameModeScreen()
                if back == False:
                    self.boardScreen()

            elif 60 < mouseX < 200 and 390 < mouseY < 420 and mouseState == 1:
                #Load Saved Game.
                run = False
                back = self.loadSavedGameScreen()
                if back == False:
                    self.boardScreen()

            elif 60 < mouseX < 200 and 440 < mouseY < 470 and mouseState == 1:
                #Rules
                run = False
                self.rulesScreen()

            elif 60 < mouseX < 200 and 490 < mouseY < 520 and mouseState == 1:
                #Rules
                run = False
                self.leaderboardScreen()

            elif 60 < mouseX < 200 and 640 < mouseY < 680 and mouseState == 1:
                #Quit
                return False        
        return True

    def boardScreen(self):
        #Method to 
        #Define Variables
        pygame.display.set_caption("Chess - Normal Game")
        self.player = self.player1 #Set player1 to be the first player of the game.
        run = True #While run is True the game will continue to run.
        isMoveComplete = True #Boolean value to indicate whether a move is successfully completed. 
        self.flipBoard = False #Boolean value to indicate whether the board needs to be flipped on the players go. 
        pawnNoMoves = 0 #Variable to store the number of moves without a pawn being moved. 
        self.window.fill(DARKBROWN) #Fill the background with the colour dark brown. 
        while run == True:
            #SET UP THE BOARD FOR NEXT MOVE: 
            #Get the colour of the player.
            playerColour = self.player.getColour()
            #Display the board, pieces, taken pieces and board algebra. 
            self.renderBoardAlgebra()
            self.displayTakenPieces(self.window)
            self.renderCheckAndPlayer(self.window,playerColour)                   
            self.game.displayGameBoard()
            self.game.displayGamePieces()
            pygame.display.flip()
            #check to see if any player is in check. 
            self.checkForCheck()
            #If the previous move was invalid, display a message stating it was not valid. 
            if isMoveComplete == False:
                self.renderNotValid(self.window)

            #Check whether the player is in checkmate using the checkForCheckmate method. 
            checkMate = self.checkForCheckmate(playerColour)
        
            #If the player is in checkmate, end the game. 
            if checkMate == True:
                nextButton = False
                pygame.draw.rect(self.window, DARKBROWN,(740,650,200,200))
                font = pygame.font.SysFont('comicsansms', 25)
                self.window.blit(font.render('Checkmate', True, (WHITE)), (740, 650))
                font = pygame.font.SysFont('comicsansms', 30)
                self.window.blit(font.render('Next', True, (WHITE)), (880, 645))
                winner = self.game.getWinner()
                pygame.display.flip()

                while nextButton == False:
                    #Check for any events and get mouse position.
                    run, mouseState,mouseX,mouseY, mainGameLoop  = self.gameEvents() 
                    if 870 <mouseX < 950 and 645 < mouseY < 680 and mouseState == 1:
                        nextButton = True
                        
                #Reset variables
                run = False
                self.winnerScreen()

            #If no-one is in checkmate, the player can take their turn:
            else:
                if self.player.getAIStatus() == "F":
                    #If the player is not AI, use the getPieceAndSquare method to get their move. 
                    movePiece, piecePositionX, piecePositionY, movePositionX, movePositionY, run=self.getPieceAndSquare(self.tileColours, playerColour)
                    if run == True:
                        validSquares, validTakeSquares, castleMoves, enPassantMoves = self.getPieceTotalMoves(movePiece, playerColour, piecePositionY, piecePositionX)
                        isMoveComplete = self.completeMove(movePiece, piecePositionX, piecePositionY, movePositionX, movePositionY, validSquares, validTakeSquares, castleMoves, enPassantMoves)

                else: #If the player is an AI player, get an AI move. 
                    run = self.checkGameButtons()
                    if self.gameMode ==1:
                        #Get random move if the gameMode is Easy
                        movePiece, movePositionY, movePositionX,  piecePositionY, piecePositionX = self.getRandomMove(playerColour) 

                    elif self.gameMode ==2:
                        #Get evaluated move if the gameMode is Average
                        movePiece, movePositionY, movePositionX,  piecePositionY, piecePositionX = self.getEvaluatedMove(playerColour) 

                    elif self.gameMode == 3:
                        #Get difficult move if the gameMode is Difficult. 
                        movePiece, movePositionY, movePositionX,  piecePositionY, piecePositionX = self.getDifficultMove(playerColour)

                    pieceOnSquare = self.game.getPieceOnSquare(movePositionY,movePositionX)
                    #If the move will result in a piece being taken, add it to the relevan taken pieces array:
                    if pieceOnSquare!= "" and playerColour =="w":
                        self.game.addTakenBlackPiece(pieceOnSquare)
                    elif pieceOnSquare!= "" and playerColour =="b":
                        self.game.addTakenWhitePiece(pieceOnSquare)

                    #Use the completeAIMove method to complete the move, as well as check it is valid. 
                    isMoveComplete = self.completeAIMove(movePiece, piecePositionX, piecePositionY, movePositionX, movePositionY, playerColour)
                    while isMoveComplete == False:
                        #If the move is not valid, keep getting a random move until one is valid. 
                        movePiece, movePositionY, movePositionX,  piecePositionY, piecePositionX = self.getRandomMove(playerColour) 
                        isMoveComplete = self.completeAIMove(movePiece, piecePositionX, piecePositionY, movePositionX, movePositionY, playerColour)

                    #Use the time.delay functionality to pause the game so that it appears that the AI is "thinking". 
                    pygame.time.delay(1000)                         

                if run == True:
                    #If the move is completed successfully, change player and check for draw:
                    #Check for any events and get mouse position.
                    run, mouseState,mouseX,mouseY, mainGameLoop  = self.gameEvents() 
                    if isMoveComplete==True:
                        pieceName= movePiece.getPiece()
                        run = self.checkGameButtons()
                        if pieceName != "Pawn":
                            #If the piece moved was NOT a pawn, add one to the pawnNoMoves variable. 
                            pawnNoMoves, draw= self.IncrementNoPawnMoves(pawnNoMoves)
                            if draw == True:
                                #If pawnNoMoves equals 100, ask the player(s) if they wish to draw. 
                                draw = self.drawScreen()
                                if draw == True:
                                    run = False
                                else:
                                    self.window.fill(DARKBROWN)
                                    
                        else:
                            #If the piece moved is a pawn, reset the pawnNoMoves variable to 0. 
                            pawnNoMoves = 0
                            #Check to see if pawn promotion is valid. 
                            if self.player.getAIStatus() =="F":
                                pawnPromotionValid = self.isPawnPromotionValid(playerColour, self.boardFlip, movePositionY)
                                if pawnPromotionValid == True:
                                    #If pawn promotion is valid, use the pawnPromotion method to complete the special move. 
                                    pawnPromotionPiece = self.pawnPromotion(playerColour, movePiece, movePositionY, movePositionX)
                            else:
                                pawnPromotionValid = self.isPawnPromotionValid(playerColour, self.boardFlip, movePositionY)
                                if pawnPromotionValid == True:
                                    #If pawn promotion is valid and the player is AI, automatically promote the pawn to a Queen. 
                                    if playerColour =="w":
                                        pawnPromotionPiece = chessPiece("wQPP", "Queen", 90)
                                    else:
                                        pawnPromotionPiece = chessPiece("bQPP", "Queen", 90)
                                        
                                    self.game.updateBoardPawnPromotion(movePiece, pawnPromotionPiece, movePositionY, movePositionX)

                        if movePiece.getFirstMove() == True and movePiece.getPiece() == "Pawn":
                           #If the pawn moved two squares, set twoSquareMove to True (Useful for En Passant Moves). 
                            if playerColour == "w":
                                if movePositionY == piecePositionY-2:
                                    movePiece.setTwoSquareMove()
                            else:
                                if movePositionY == piecePositionY +2:
                                    movePiece.setTwoSquareMove()
                            #Set the pieces attribute firstMove to True. 
                            movePiece.setFirstMove()
                        movePiece.setFirstMove()
                        #Increment the players moves change the player.
                        self.player.incrementMoves()
                        self.changePlayer()
                        
                        if self.boardFlip == True:
                            #If boardFlip is True, flip the board. 
                            self.game.flipBoard()

                    if self.boardFlip == True:        
                        if self.flipBoard == True:
                            self.flipBoard = False
                        else:
                            self.flipBoard = True

    def rulesScreen(self):
        run = True
        font = pygame.font.SysFont('comicsansms', 25)
        pygame.display.set_caption("Chess - Rules")
        self.window.blit(self.bg, (0, 0))
        #Load the black Pawn piece image
        blackPawn = pygame.image.load("Chess_pdt60.png").convert_alpha()
        self.window.blit(blackPawn,(90,90))
        self.window.blit(font.render('Pawn:', True, (WHITE)), (200, 100))
        #Load the black Rook piece image
        blackRook = pygame.image.load("Chess_rdt60.png").convert_alpha()
        self.window.blit(blackRook,(90,180))
        self.window.blit(font.render('Rook:', True, (WHITE)), (200, 195))
        #Load the black Knight piece image
        blackKnight = pygame.image.load("Chess_ndt60.png").convert_alpha()
        self.window.blit(blackKnight,(90,270))
        self.window.blit(font.render('Knight:', True, (WHITE)), (200, 285))
        #Load the black Bishop image
        blackBishop = pygame.image.load("Chess_bdt60.png").convert_alpha()
        self.window.blit(blackBishop,(90,360))
        self.window.blit(font.render('Bishop:', True, (WHITE)), (200, 375))
        #Load the black Queen piece image
        blackQueen = pygame.image.load("Chess_qdt60.png").convert_alpha()
        self.window.blit(blackQueen,(90,450))
        self.window.blit(font.render('Queen:', True, (WHITE)), (200, 465))
        #Load the black King piece image
        blackKing = pygame.image.load("Chess_kdt60.png").convert_alpha()
        self.window.blit(blackKing,(90,540))
        self.window.blit(font.render('King:', True, (WHITE)), (200, 555))
        #Display descriptions of each piece:
        font = pygame.font.SysFont('comicsansms', 16)
        #Pawn Description:
        self.window.blit(font.render("Moved forwards one square at a time, or two", True, (WHITE)), (320, 100))
        self.window.blit(font.render("squares if it hasn't been moved before.", True, (WHITE)), (320, 120))
        #Rook Description:
        self.window.blit(font.render("Moves in a straight line horizontally or vertically,", True, (WHITE)), (320, 195))
        self.window.blit(font.render("however not diagonally.", True, (WHITE)), (320, 215))
        #Knight Description:
        self.window.blit(font.render('The knight moves in an L shape manner. This is', True, (WHITE)), (320, 285))
        self.window.blit(font.render('the only piece which can jump over pieces, however', True, (WHITE)), (320, 305))
        self.window.blit(font.render('this does not mean the piece is taken.', True, (WHITE)), (320, 325))
        #Bishop Description:
        self.window.blit(font.render('The bishop moves only diagonally for as  ', True, (WHITE)), (320, 375))
        self.window.blit(font.render('many squares as the player decides.', True, (WHITE)), (320, 395))
        #Queen Description:
        self.window.blit(font.render('The Queen can move in ANY direction', True, (WHITE)), (320, 465)) 
        self.window.blit(font.render('for as many squares as the user decides', True, (WHITE)), (320, 485))
        #King Description:
        self.window.blit(font.render('The King can move only one square', True, (WHITE)), (320, 555))  
        self.window.blit(font.render('but in any direction', True, (WHITE)), (320, 575))
        #Back button:
        font = pygame.font.SysFont('comicsansms',35)
        self.window.blit(font.render('Back', True, (WHITE)), (100, 660))
        while run == True:
            run, mouseState,mouseX,mouseY, mainGameLoop  = self.gameEvents()
            #Check if back button has been selected. 
            if 60 < mouseX <220 and 600 < mouseY < 700 and mouseState == 1:
                run = False
            pygame.display.flip()

    def leaderboardScreen(self):
        #Methdo to display the leaderboard. 
        pygame.display.set_caption("Chess - Leaderboard")
        run = True
        #By default order the database by quickest win. 
        sortBy = "QUICKESTWIN" 
        while run == True:
            self.window.blit(self.bg, (0, 0))
            y = 0
            font = pygame.font.SysFont('comicsansms',35)
            self.window.blit(font.render('Back', True, (WHITE)), (100, 660))
            font = pygame.font.SysFont('comicsansms',25)
            self.window.blit(font.render('Fewest Moves', True, (WHITE)), (500, 660))
            self.window.blit(font.render('Wins', True, (WHITE)), (700, 660))
            self.window.blit(font.render('Losses', True, (WHITE)), (800, 660))
            font = pygame.font.SysFont('rockwell', 25)
            self.window.blit(font.render('Name', True, (WHITE)), (120,80))
            self.window.blit(font.render('Fewest Moves', True, (WHITE)), (320,80))
            self.window.blit(font.render('Wins', True, (WHITE)), (520,80))
            self.window.blit(font.render('Losses', True, (WHITE)), (620,80))

            #Use the orderDatabase method to get the data in the database returned in the specified order. 
            leaderboardData = self.database.orderDatabase(sortBy)

            #Display each record in the database. 
            for row in leaderboardData:
                self.window.blit(font.render(str(row[1]), True, (WHITE)), (120, 150+y))
                self.window.blit(font.render(str(row[2]), True, (WHITE)), (420, 150+y))
                self.window.blit(font.render(str(row[3]), True, (WHITE)), (520, 150+y))
                self.window.blit(font.render(str(row[4]), True, (WHITE)), (620, 150+y))
                y = y+100
   
            run, mouseState,mouseX,mouseY, mainGameLoop  = self.gameEvents()
            #Check if back button has been selected. 
            if 60 < mouseX <220 and 600 < mouseY < 700 and mouseState == 1:
                run = False

            elif 490 < mouseX <650 and 600 < mouseY < 700 and mouseState == 1:
                sortBy = "QUICKESTWIN"

            elif 690 < mouseX <750 and 600 < mouseY < 700 and mouseState == 1:
                sortBy = "GAMESWON"
  
            elif 790 < mouseX <850 and 600 < mouseY < 700 and mouseState == 1:
                sortBy = "GAMESLOST"
  
            pygame.display.flip()

    def loadSavedGameScreen(self):
        #Method to load a saved game file. 
        run = True
        savedGamesToDisplay = False
        back = False
        invalid = False
        filename = ""
        #Define the self.window name and font
        pygame.display.set_caption("Chess - Load Saved Game")
        while run == True:
            self.window.blit(self.bg, (0, 0))
            if savedGamesToDisplay == True:
                self.displaySavedGames()
            font = pygame.font.SysFont('rockwell', 60)
            self.window.blit(font.render('Chess', True, (WHITE)), (100, 100))
            font = pygame.font.SysFont('rockwell', 20)
            self.window.blit(font.render('Back', True, (WHITE)), (60, 600))
            self.window.blit(font.render('Display all saved games', True, (WHITE)), (60, 550))
            font = pygame.font.SysFont('rockwell', 20)
            self.window.blit(font.render('Enter File Name:', True, (WHITE)), (60, 300))
            if invalid == True:
                self.window.blit(font.render('Invalid Filename', True, (WHITE)), (60, 400))
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if os.path.isfile(filename+".txt"):
                            #If the file exists, use the loadFile method to load the game. 
                            file = open(filename+".txt","r")
                            file.close()
                            self.game, self.player1, self.player2, self.gameMode = self.loadFile(filename)
                            run = False
                        else:
                            invalid = True
                            filename = ""
                    elif event.key == pygame.K_BACKSPACE:
                        filename = filename[:-1]
                    else:
                        filename += event.unicode
                elif event.type== pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    if 60 < pos[0] < 200 and 600 < pos[1] < 640:
                        run = False
                        back = True
                    elif 60<pos[0]<200 and 550 <pos[1]<590:
                        savedGamesToDisplay = True
                         
                             
                        
            #Display the filename the user enters as they enter it.                        
            font = pygame.font.SysFont('rockwell', 20)
            self.window.blit(font.render(filename, True, (WHITE)), (240, 300))
            pygame.display.flip()
        return back
    
    def displaySavedGames(self):
        #Method to display already saved games. 
        font = pygame.font.SysFont('rockwell', 20)
        self.window.blit(font.render('Saved Games:', True, (WHITE)), (600, 20))
        y = 60
        path = "/Users/Jack/Desktop/Final"
        savedGames = [f for f in os.listdir(path) if f.endswith('.txt')]
        for file in savedGames:
            self.window.blit(font.render(str(file), True, (WHITE)), (600, y))
            y = y+30

    def drawScreen(self):
        #Method to display the option to accept or not accept a draw. 
        #If both players are AI, accept a draw. 
        if self.player1.getAIStatus() == True and self.player2.getAIStatus() == True:
            accepteDrawScreen()
            return True

        #If a human is playing, ask them is they wish to accept a draw:
        font = pygame.font.SysFont('rockwell', 50) 
        run = True
        self.window.blit(self.bg, (0, 0))
        self.window.blit(font.render("Would you like to accept a draw?", True, (WHITE)), (60, 150))
        font = pygame.font.SysFont('rockwell', 20)
        self.window.blit(font.render('You can agree to draw as there have been 50 consecutive moves without a pawn being moved:', True, (WHITE)), (60, 220))

        #Main Menu button:
        font = pygame.font.SysFont('rockwell', 25)
        self.window.blit(font.render('Accept Draw', True, (WHITE)), (60, 300))
        self.window.blit(font.render("Continue Game", True, (WHITE)), (60, 350))
        pygame.display.flip()

        while run == True:
            run, mouseState,mouseX,mouseY, mainGameLoop  = self.gameEvents()
            #Check if Main Menu button has been selected.
            if 60 < mouseX < 200 and 290 < mouseY < 320 and mouseState == 1:
                self.acceptedDrawScreen()
                return True
            elif 60 < mouseX < 200 and 340 < mouseY < 370 and mouseState == 1:
                return False
            
    def acceptedDrawScreen(self):
        #Method to display to the user that a draw has been agreed. 
        font = pygame.font.SysFont('rockwell', 50) 
        run = True
        self.window.blit(self.bg, (0, 0))
        self.window.blit(font.render("Draw!", True, (WHITE)), (60, 150))
        font = pygame.font.SysFont('rockwell', 20)
        self.window.blit(font.render('50 consecutive moves have occured without a pawn being moved:', True, (WHITE)), (60, 220))
        font = pygame.font.SysFont('comicsansms',25)
        self.window.blit(font.render('Return to Main Menu', True, (WHITE)), (60, 660))
        pygame.display.flip()
        while run == True:
            run, mouseState,mouseX,mouseY, mainGameLoop  = self.gameEvents()
            #Check if Main Menu button has been elected. 
            if 90< mouseX <290 and 640 < mouseY < 680 and mouseState == 1:
                run = False
        
    def winnerScreen(self):
        #Method to display the winner screen. 
        font = pygame.font.SysFont('rockwell', 50) 
        run = True
        self.player = self.game.getWinner()
        self.window.blit(self.bg, (0, 0))
        self.window.blit(font.render(self.player.getName() + " Wins!", True, (WHITE)), (100,150))
        if self.player.getName() != "AI1" or self.player.getName() != "AI2":
            recordExists = self.database.doesRecordExist(self.player.getName())
            #Check to see if the player already has a record in the player database. 
            if recordExists == True:
                self.database.updateRecord(self.player.getName(), self.player.getMoves(), True )   
            else:
                self.database.writeToDatabase(self.player.getName(), self.player.getMoves(), True)
        self.changePlayer()
        if self.player.getName() != "AI1" or self.player.getName() != "AI2":
            recordExists = self.database.doesRecordExist(self.player.getName())
            #Check to see if the player already has a record in the player database. 
            if recordExists == True:
                self.database.updateRecord(self.player.getName(), self.player.getMoves(), False)     
            else:
                self.database.writeToDatabase(self.player.getName(), self.player.getMoves(), False)

        #Main Menu button:
        font = pygame.font.SysFont('comicsansms',25)
        self.window.blit(font.render('Return to Main Menu', True, (WHITE)), (100, 660))
        pygame.display.flip()

        while run == True:
            run, mouseState,mouseX,mouseY, mainGameLoop  = self.gameEvents()
            #Check if Main Menu button has been elected. 
            if 90< mouseX <290 and 640 < mouseY < 680 and mouseState == 1:
                run = False
                
    def boardSquareHighlighterScreen(self):
        #Method to display the board square move highlighter setting screen. 
        run = True
        back = False
        #Define the self.window name and font
        pygame.display.set_caption("Chess - Main Menu")
        self.window.blit(self.bg, (0, 0))
        font = pygame.font.SysFont('rockwell', 60)
        self.window.blit(font.render('Chess', True, (WHITE)), (60, 100))

        font = pygame.font.SysFont('rockwell', 25)
        self.window.blit(font.render('Board Square Move Highlighter', True, (WHITE)), (60, 200))
        self.window.blit(font.render('(When a piece is selected, the valid squares it can be moved to will be highlighted)', True, (WHITE)), (60, 250))

        self.window.blit(font.render('On', True, (WHITE)), (60, 300))
        self.window.blit(font.render("Off", True, (WHITE)), (60, 350))
        font = pygame.font.SysFont('rockwell', 40)
        self.window.blit(font.render('Back', True, (WHITE)), (60, 600))
        pygame.display.flip()

        while run == True:
            #Check for any events and get mouse position.
            run, mouseState, mouseX, mouseY, mainGameLoop = self.gameEvents() 
            if 60 < mouseX < 200 and 290 < mouseY < 320 and mouseState == 1:
                run = False
                self.tileColours = True
            elif 60 < mouseX < 200 and 340 < mouseY < 370 and mouseState == 1:
                run = False
                self.tileColours = False
            elif 60 < mouseX < 200 and 600 < mouseY < 640 and mouseState == 1:
                run = False
                back = True

        return back

    def usernameScreen(self):
        #Method to display the username entry screen. 
        back = False
        for i in range(0,self.humanPlayers):
            run = True
            username = ""
            while run == True:
                #Display screen name:
                pygame.display.set_caption("Chess - Main Menu / Login")
                self.window.blit(self.bg, (0, 0))
                font = pygame.font.SysFont('rockwell', 60)
                self.window.blit(font.render('Chess', True, (WHITE)), (60, 100))
                font = pygame.font.SysFont('rockwell', 30)
                self.window.blit(font.render('Player ' + str(i+1)+' Name:', True, (WHITE)), (60, 180))
                self.window.blit(font.render('Back', True, (WHITE)), (60, 600))
                font = pygame.font.SysFont('rockwell', 20)
                self.window.blit(font.render('Username:', True, (WHITE)), (60, 300))
                #Variable username set to an empty string ready to store the value of the username the player enters. 
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            #If the user enters return, set whatever they typed as their username. 
                            run = False
                            if i == 0:
                                #Check whether the username is empty:
                                if username !="":
                                    self.player1.setName(username)
                                else:
                                    run = True
                                    username = ""
                            else:
                                #Check whether the username is different to player 1 and not empty:
                                if username!= self.player1.getName() and username!="":
                                    self.player2.setName(username)
                                else:
                                    run = True
                                    username = ""
                        elif event.key == pygame.K_BACKSPACE:
                            #If the user presses the backspace, remove one character from the username string. 
                            username = username[:-1]
                        else:
                            #If any other character was selected, concatenate it to the username string. 
                            username += event.unicode                           
                    elif event.type== pygame.MOUSEBUTTONDOWN:
                        #If the user presses the mouse down, check to see if the clicked back. 
                        pos = pygame.mouse.get_pos()
                        if 60 < pos[0] < 200 and 600 < pos[1] < 640:
                            run = False
                            back = True                           
                #Display the username to the window as the user types it. 
                font = pygame.font.SysFont('rockwell', 20)
                self.window.blit(font.render(username, True, (WHITE)), (200, 300))
                pygame.display.flip()
                if back == True:
                    break
        return back

    def boardFlipScreen(self):
        #Method to display the board flip option screen. 
        run = True
        back = False
        while run == True:
            #Define the self.window name and font
            pygame.display.set_caption("Chess - Main Menu")
            self.window.blit(self.bg, (0, 0))
            font = pygame.font.SysFont('rockwell', 60)
            self.window.blit(font.render('Chess', True, (WHITE)), (60, 100))
            font = pygame.font.SysFont('rockwell', 25)
            self.window.blit(font.render('Board Flip:', True, (WHITE)), (60, 200))
            self.window.blit(font.render('(Flips the board so both players play from the same perspective)', True, (WHITE)), (60, 250))

            self.window.blit(font.render('On', True, (WHITE)), (60, 300))
            self.window.blit(font.render("Off", True, (WHITE)), (60, 350))

            font = pygame.font.SysFont('rockwell', 40)
            self.window.blit(font.render('Back', True, (WHITE)), (60, 600))
            pygame.display.flip()
            while run == True:
                #Check for any events and get mouse position.
                run, mouseState, mouseX, mouseY, mainGameLoop = self.gameEvents() 
                if 60 < mouseX < 200 and 290 < mouseY < 320 and mouseState == 1:
                    run = False
                    self.boardFlip = True
                elif 60 < mouseX < 200 and 340 < mouseY < 370 and mouseState == 1:
                    run = False
                    self.boardFlip = False
                elif 60 < mouseX < 200 and 600 < mouseY < 640 and mouseState == 1:
                    run = False
                    back = True
        return back

    def gameModeScreen(self):
        #Method to display the game mode option screen. 
        run = True
        back = False
        font = pygame.font.SysFont('rockwell', 60) 
        #Define the self.window name and font
        pygame.display.set_caption("Chess - Main Menu / Select Game Mode")
        self.window.blit(self.bg, (0, 0))

        self.window.blit(font.render('Chess', True, (WHITE)), (60, 100))
        font = pygame.font.SysFont('rockwell', 25)

        self.window.blit(font.render('Easy', True, (WHITE)), (60, 300))
        self.window.blit(font.render('Average', True, (WHITE)), (60, 350))
        self.window.blit(font.render('Difficult', True, (WHITE)), (60, 400))

        font = pygame.font.SysFont('rockwell', 40)
        self.window.blit(font.render('Back', True, (WHITE)), (60, 600))
        pygame.display.flip()
        while run == True:
            #Check for any events and get mouse position.
            run, mouseState, mouseX, mouseY, mainGameLoop = self.gameEvents() 
            if 60 < mouseX < 200 and 290 < mouseY < 320 and mouseState == 1:
                run = False                        
                self.gameMode = 1
            elif 60 < mouseX < 200 and 340 < mouseY < 370 and mouseState == 1:
                run = False
                self.gameMode = 2
            elif 60 < mouseX < 200 and 390 < mouseY < 420 and mouseState == 1:
                run = False
                self.gameMode = 3
            elif 60 < mouseX < 200 and 600 < mouseY < 640 and mouseState == 1:
                run = False
                back = True
        return back

    def playerColourScreen(self):
        #Method to display the player colour option screen. 
        run = True
        back = False
        #Define the self.window name and font
        pygame.display.set_caption("Chess - Main Menu / Select Colour")
        self.window.blit(self.bg, (0, 0))
        font = pygame.font.SysFont('rockwell', 60)
        self.window.blit(font.render('Chess', True, (WHITE)), (60, 100))
        font = pygame.font.SysFont('rockwell', 25)
        self.window.blit(font.render('Select Piece To Play As:', True, (WHITE)), (60, 250))
        self.window.blit(font.render('White', True, (WHITE)), (60, 300))
        self.window.blit(font.render("Black", True, (WHITE)), (60, 350))
        font = pygame.font.SysFont('rockwell', 40)
        self.window.blit(font.render('Back', True, (WHITE)), (60, 600))
        pygame.display.flip()
        while run == True:
            #Check for any events and get mouse position.
            run, mouseState, mouseX, mouseY, mainGameLoop = self.gameEvents() 
            if 60 < mouseX < 200 and 290 < mouseY < 320 and mouseState == 1:
                run = False
                self.player1.setColour("w")

            elif 60 < mouseX < 200 and 340 < mouseY < 370 and mouseState == 1:
                run = False
                self.player1, self.player2 = self.player2, self.player1
                self.player1.setColour("w")
                self.player2.setColour("b")

            elif 60 < mouseX < 200 and 600 < mouseY < 640 and mouseState == 1:
                run = False
                back = True
        return back



class chessBoard():
    def __init__(self,columnsIn, rowsIn, preSavedGameIn, savedMatrixIn):
        self.columns = columnsIn #Stores the number of columns for the board.
        self.rows = rowsIn #Stores the number of rows for the board.
        self.chessBoard = [] #Attribute to store the chessboard. 
        self.checkMate = False #Boolean attribute to store whether whether checkmate is True or False. 
        self.wCheck = False #Boolean value for whether the white king is in check.
        self.bCheck = False #Boolean value for whether the black king is in check.
        self.whiteTakenPieces = [] #Attribute to store all of the white pieces taken from the board. 
        self.blackTakenPieces = [] #Attribute to store all of the black pieces from the board.

        #Create the board.       
        for Y in range(self.rows):
            self.chessBoard.append([])
            for X in range(self.columns):
                #For each item in the board matrix append a square object.
                self.chessBoard[Y].append(boardSquare(Y, X ,self.columns, self.rows)) 

        #Instantiate all the pieces and add them to their starting positions on the board.
        #Instantiate the black pieces:        
        self.piece1 = chessPiece("bR","Rook", 50)
        self.piece2 = chessPiece("bN","Knight", 30)
        self.piece3 = chessPiece("bB","Bishop", 30)
        self.piece4 = chessPiece("bQ","Queen", 90)
        self.piece5 = chessPiece("bK","King", 900)
        self.piece6 = chessPiece("bB2","Bishop", 30)
        self.piece7 = chessPiece("bN2","Knight", 30)
        self.piece8 = chessPiece("bR2","Rook", 50)

        #Instantiate the black Pawns:  
        self.piece9= chessPiece("bP1","Pawn", 10)
        self.piece10= chessPiece("bP2","Pawn", 10)
        self.piece11= chessPiece("bP3","Pawn", 10)
        self.piece12= chessPiece("bP4","Pawn", 10)
        self.piece13= chessPiece("bP5","Pawn", 10)
        self.piece14= chessPiece("bP6","Pawn", 10)
        self.piece15= chessPiece("bP7","Pawn", 10)
        self.piece16= chessPiece("bP8","Pawn", 10)

        #Instantiate the white Pawns
        self.piece17= chessPiece("wP1","Pawn", 10)
        self.piece18= chessPiece("wP2","Pawn", 10)
        self.piece19= chessPiece("wP3","Pawn", 10)
        self.piece20= chessPiece("wP4","Pawn", 10)
        self.piece21= chessPiece("wP5","Pawn", 10)
        self.piece22= chessPiece("wP6","Pawn", 10)
        self.piece23= chessPiece("wP7","Pawn", 10)
        self.piece24= chessPiece("wP8","Pawn", 10)

        #Instantiate the white pieces
        self.piece25 = chessPiece("wR","Rook", 50)
        self.piece26 = chessPiece("wN","Knight", 30)
        self.piece27 = chessPiece("wB","Bishop", 30)
        self.piece28 = chessPiece("wQ","Queen", 90)
        self.piece29 = chessPiece("wK","King", 900)
        self.piece30 = chessPiece("wB2","Bishop", 30)
        self.piece31 = chessPiece("wN2","Knight", 30)
        self.piece32 = chessPiece("wR2","Rook", 50)

        #Dictionary with piece names being the key and the associated value the piece object name. 
        self.pieceDict = {
            "bR":self.piece1,
            "bN": self.piece2,
            "bB": self.piece3,
            "bQ": self.piece4,
            "bK": self.piece5,
            "bB2": self.piece6,
            "bN2": self.piece7,
            "bR2": self.piece8,
            "wR": self.piece25,
            "wN": self.piece26,
            "wB": self.piece27,
            "wQ": self.piece28,
            "wK": self.piece29,
            "wB2": self.piece30,
            "wN2": self.piece31,
            "wR2": self.piece32,
            "bP1": self.piece9,
            "bP2": self.piece10,
            "bP3": self.piece11,
            "bP4": self.piece12,
            "bP5": self.piece13,
            "bP6": self.piece14,
            "bP7": self.piece15,
            "bP8": self.piece16,
            "wP1": self.piece17,
            "wP2": self.piece18,
            "wP3": self.piece19,
            "wP4": self.piece20,
            "wP5": self.piece21,
            "wP6": self.piece22,
            "wP7": self.piece23,
            "wP8": self.piece24,
            }

        if preSavedGameIn == 0: #If the startStateIn is 0, the player is starting a new game. 
            #Add all the piece objects to the correct starting squares:
            self.chessBoard[0][0].addPieceToSquare(self.piece1)               
            self.chessBoard[0][1].addPieceToSquare(self.piece2)                  
            self.chessBoard[0][2].addPieceToSquare(self.piece3)                   
            self.chessBoard[0][3].addPieceToSquare(self.piece4)                   
            self.chessBoard[0][4].addPieceToSquare(self.piece5)                   
            self.chessBoard[0][5].addPieceToSquare(self.piece6)                 
            self.chessBoard[0][6].addPieceToSquare(self.piece7)                   
            self.chessBoard[0][7].addPieceToSquare(self.piece8)

            self.chessBoard[1][0].addPieceToSquare(self.piece9)            
            self.chessBoard[1][1].addPieceToSquare(self.piece10)            
            self.chessBoard[1][2].addPieceToSquare(self.piece11)            
            self.chessBoard[1][3].addPieceToSquare(self.piece12)            
            self.chessBoard[1][4].addPieceToSquare(self.piece13)            
            self.chessBoard[1][5].addPieceToSquare(self.piece14)            
            self.chessBoard[1][6].addPieceToSquare(self.piece15)            
            self.chessBoard[1][7].addPieceToSquare(self.piece16)

            self.chessBoard[6][0].addPieceToSquare(self.piece17)
            self.chessBoard[6][1].addPieceToSquare(self.piece18)
            self.chessBoard[6][2].addPieceToSquare(self.piece19)
            self.chessBoard[6][3].addPieceToSquare(self.piece20)
            self.chessBoard[6][4].addPieceToSquare(self.piece21)
            self.chessBoard[6][5].addPieceToSquare(self.piece22)
            self.chessBoard[6][6].addPieceToSquare(self.piece23)
            self.chessBoard[6][7].addPieceToSquare(self.piece24)

            self.chessBoard[7][0].addPieceToSquare(self.piece25)
            self.chessBoard[7][1].addPieceToSquare(self.piece26)
            self.chessBoard[7][2].addPieceToSquare(self.piece27)
            self.chessBoard[7][3].addPieceToSquare(self.piece28)
            self.chessBoard[7][4].addPieceToSquare(self.piece29)
            self.chessBoard[7][5].addPieceToSquare(self.piece30)
            self.chessBoard[7][6].addPieceToSquare(self.piece31)
            self.chessBoard[7][7].addPieceToSquare(self.piece32)

        elif preSavedGameIn == 1: #If the gameStateIn is 1, the player is loading a pre-existing game that must be loaded in.
            for Y in range(self.rows):
                for X in range(self.columns):
                    #Piece holds the value of the piece name, which is read from the savedMatrix array. 
                    piece = savedMatrixIn[Y][X]
                    if piece !="X": #Checks if there is a piece on the square. 
                        pieceObject = self.pieceLookUp(piece) #If there is a piece on the square, use the pieceLookUp method to get the piece object. 
                        self.chessBoard[Y][X].addPieceToSquare(pieceObject)

    def displayGameBoard(self):
        #Method to display the squares on the chessboard. 
        for Y in range(self.rows):
            for X in range(self.columns):
                #If the square does not have a piece on it, the square can simply be displayed empty.
                #Call the 'showSquare' method to display the square.
                self.chessBoard[Y][X].showSquare()  

    def displayGamePieces(self):
        #Method to display the pieces on the chessboard. 
        for Y in range(self.rows):
            for X in range(self.columns):
                if self.chessBoard[Y][X].isEmpty() ==False:
                    #If there is a piece on the square the piece name is retrieved and the square is displayed with the piece on it. 
                    piece = self.chessBoard[Y][X].getPiece() #Get the piece object on the square
                    piecename =piece.getPiece() #Get the piece name and store it in a variable called 'piecename'.
                    pieceimage= piece.getImage() #Get the image and store it in a variable called pieceimage
                    self.chessBoard[Y][X].showPieceOnSquare(piecename,pieceimage) #Call the 'show' method to display the square

    def locateClickedPiece(self, mouseX, mouseY, mouseState, playerColour):
        #Method to see if a particular piece has been clicked by the user.
        #Iterate through every piece on the board. 
        for Y in range(self.rows):
            for X in range(self.columns):
                #Check to see if the mouse state is 1. 
                if mouseState == 1: 
                    #If the piece has been selected, its X and Y positions are retrieved as well as its name. 
                    squareSelected, piecePositionX, piecePositionY, movePiece = self.chessBoard[Y][X].hasPieceOnSquareBeenClicked(mouseX, mouseY, playerColour)
                    if squareSelected == True:
                        return True, movePiece, piecePositionX, piecePositionY

        #Return False if all squares have been checked and none have been selected.
        return False, None, None, None

    def locateClickedSquare(self, mouseX, mouseY, mouseState, playerColour):
        #Method to see if a particular square on the board has been clicked by the user.
        #Iterate through every square on the board in the 2D array. 
        for Y in range(self.rows):
            for X in range(self.columns):
                #If the mouse state is 1, in other words the user has clicked something. 
                if mouseState == 1:                      
                    #If the square has been selected, the X and Y positions are retrieved. 
                    squareSelected, movePositionX, movePositionY = self.chessBoard[Y][X].hasSquareBeenClicked(mouseX,mouseY)
                    if squareSelected == True:
                        #Return True if the square has been clicked and its Y and X positions. 
                        return True, movePositionX, movePositionY
        #Return False if all squares have been checked and none have been selected.
        return False, None, None

    def flipBoard(self):
        #Method to flip the current state of the board.
        #mewBoard array stores the state of the flipped board.
        newBoard = [] 
        for Y in range(self.rows):
            newBoard.append([])
            for X in range(self.columns):
                #For each item in the board matrix append a square object.
                newBoard[Y].append(boardSquare(Y, X,self.columns,self.rows))

        for Y in range(self.rows):
            for X in range(self.columns):
                if self.chessBoard[Y][X].isEmpty()==False:
                    piece = self.chessBoard[Y][X].getPiece()
                    newBoard[(self.rows-1)-Y][(self.columns-1)-X].addPieceToSquare(piece) #Append the piece to the new position on the new board. 

        self.chessBoard = newBoard #Replace the old chessboard with the new chessboard.                   

    def getPieceOnSquare(self, Y, X):
        #Method to get return the piece on a square if there is one. 
        pieceOnSquare = "" #Sets the variable pieceOnSquare to an empty string. 
        pieceOnSquareColour = "" #Sets the variable pieceOnSquareColour to an empty string. 
        if self.chessBoard[Y][X].isEmpty() == False: #Checks if the square has a piece on it. 
            pieceOnSquare = self.chessBoard[Y][X].getPiece() #Gets the piece object on the square using the .getPiece() method. 
            pieceOnSquareColour = pieceOnSquare.getColour() #Gets the piece colour on the square using the .getColour() method on the pieceOnSquare object.
        return pieceOnSquare #Return the piece object on the square. 

    def removePieceFromSquare(self, Y, X):
        #Method to remove a piece from a board square. 
        self.chessBoard[Y][X].removePieceFromSquare()

    def addPieceToSquare(self, Y, X, movePiece):
        #Method to add a piece to a board square. 
        self.chessBoard[Y][X].addPieceToSquare(movePiece)

    def addTakenWhitePiece(self, pieceIn):
        #Method to add a taken white piece to the list self.whiteTakenPieces. 
        self.whiteTakenPieces.append(pieceIn)

    def addTakenBlackPiece(self, pieceIn):
        #Method to add a taken black piece to the list self.blackTakenPieces. 
        self.blackTakenPieces.append(pieceIn)

    def getTakenWhitePieceList(self):
        #Returns the list of taken white pieces. 
        return self.whiteTakenPieces

    def getTakenBlackPieceList(self):
        #Returns the list of taken black pieces. 
        return self.blackTakenPieces

    def getCheckMateStatus(self):
        #Returns the value of the boolean self.checkMate
        return self.checkMate 

    def setWCheck(self, whiteCheckIn):
        #Set the value of the wCheck boolean.
        self.wCheck = whiteCheckIn

    def setBCheck(self, blackCheckIn):
        #Set the value of the bCheck boolean. 
        self.bCheck = blackCheckIn

    def getWCheck(self):
        #Returns the value of the boolean self.wCheck.
        return self.wCheck

    def getBCheck(self):
        #Returns the value of the boolean self.bCheck. 
        return self.bCheck

    def setCheckMate(self, checkmateIn):
        #Setter for the checkmate boolean.
        self.checkMate = checkmateIn

    def setWinner(self,winnerIn):
        #Sets the value of self.winner.
        self.winner = winnerIn

    def getWinner(self):
        #Returns the value self.winner. 
        return self.winner

    def pieceLookUp(self,pieceName):
        #Method to lookup the associated object for a chess piece.
        return self.pieceDict[pieceName]

    def isSquareEmpty(self, Y, X):
        return self.chessBoard[Y][X].isEmpty()

    def changeSquareColour(self, piecePositionY, piecePositionX, colour):
        #Changes the colour of the border of the square.
        self.chessBoard[piecePositionY][piecePositionX].displayColouredSquare(colour)

    def updateLookupTable(self, newKey, pieceObject):
        #Adds a new piece object to the piece dictionary (used for when prawn promotion takes place.
        self.pieceDict[newKey] = pieceObject

    def updateBoardPawnPromotion(self, movePiece, pawnPromotionPiece, Y, X):
        #Update the pieces on the board after pawn promotion. 
        self.updateLookupTable(pawnPromotionPiece.getName(), pawnPromotionPiece)
        self.chessBoard[Y][X].removePieceFromSquare()
        self.chessBoard[Y][X].addPieceToSquare(pawnPromotionPiece)

    def updateChessBoard(self,piecePositionY, piecePositionX, movePositionY,movePositionX,movePiece):
        #Update the postion of the moved pieces on the board.
        self.chessBoard[piecePositionY][piecePositionX].removePieceFromSquare() #Remove the piece from its current square.
        self.chessBoard[movePositionY][movePositionX].addPieceToSquare(movePiece)

    def resetMove(self,movePositionY, movePositionX, piecePositionY, piecePositionX, movePiece):
        #Method to undo the move just taken. 
        self.chessBoard[movePositionY][movePositionX].removePieceFromSquare()#Add the piece to the new square.
        self.chessBoard[piecePositionY][piecePositionX].addPieceToSquare(movePiece) #Remove the piece from its current square.

    def isEnPassantMoveValid(self, playerColour, boardFlip, Y, X, enPassantMoves):
        #Method to check if En Passant move is valid.
        #Check to see if the player is white and whether an En Passant move would not result in them leaving the boundary of the board. 
        if playerColour =="w" and (Y+1) <=7 and 0<=X<=7:
            if self.chessBoard[Y+1][X].isEmpty() == False:
                pieceOnSquare = self.chessBoard[Y+1][X].getPiece()
                if pieceOnSquare.getPiece() =="Pawn" and pieceOnSquare.getColour() =="b":
                    if pieceOnSquare.getTwoSquareMove() == True:
                        enPassantMoves.append([Y,X])

        #Check to see if the player is black and whether an En Passant move would not result in them leaving the boundary of the board. 
        elif playerColour =="b" and (Y-1) >=0 and 0<=X<=7:
             if self.chessBoard[Y-1][X].isEmpty() == False:
                 pieceOnSquare = self.chessBoard[Y-1][X].getPiece()
                 if pieceOnSquare.getPiece() =="Pawn" and pieceOnSquare.getColour() =="w":
                    if pieceOnSquare.getTwoSquareMove() == True:
                        enPassantMoves.append([Y,X])

        return enPassantMoves #Return the enPassantMoves array. 

    def getTotalPlayerMoves(self, playerColour):
        #Method to get ALL possible moves using EVERY piece of a player.
        validSquares = []
        validTakeSquares = []
        castleMoves = []
        enPassantMoves = []
        for Y in range(self.rows):
            for X in range (self.columns):
                if self.chessBoard[Y][X].isEmpty() == False:
                    if (self.chessBoard[Y][X].getPiece()).getColour() == playerColour:
                        movePiece = self.chessBoard[Y][X].getPiece() #Gets the piece on the square using the .getPiece() method of the chessPiece class.
                        #Get the validSquares and validTakeSquares lists of that piece:
                        validSquaresCurrent, validTakeSquaresCurrent, castleMoves, enPassantMoves = system.getPieceTotalMoves(movePiece,playerColour,Y,X)
                        for i in validTakeSquaresCurrent:
                            validSquares.append(i)
                        for i in validTakeSquaresCurrent:
                            validTakeSquares.append(i)

        return validSquares, validTakeSquares, castleMoves, enPassantMoves #Return all four arrays that contain all the players possible moves. 

    def isCastleMoveValid(self, playerColour):
        #Method to check whether a user is able to complete a valid castle move. 
        castleMoves = []
        #Check if any of the four possible castling scenarios are valid.    
        if playerColour =="w":
            if self.chessBoard[7][1].isEmpty() == True and self.chessBoard[7][2].isEmpty() == True and self.chessBoard[7][3].isEmpty() == True and self.piece25.getFirstMove() == True  and self.piece29.getFirstMove() == True:
                castleMoves.append([7,2])
            elif self.chessBoard[7][5].isEmpty() == True and self.chessBoard[7][6].isEmpty()==True and self.piece32.getFirstMove() == True  and self.piece29.getFirstMove() == True:
                castleMoves.append([7,6])
        else:
            if self.chessBoard[0][1].isEmpty() == True and self.chessBoard[0][2].isEmpty() == True and self.chessBoard[0][3].isEmpty() == True and self.piece1.getFirstMove() == True  and self.piece5.getFirstMove() == True:
                castleMoves.append([0,2])
            elif self.chessBoard[0][5].isEmpty() == True and self.chessBoard[0][6].isEmpty()== True  and self.piece8.getFirstMove() == True  and self.piece5.getFirstMove() == True:
                castleMoves.append([0,6])
        return castleMoves #Return the castleMoves array. 

class boardSquare():
    def __init__(self,Y, X, columnsIn, rowsIn):
        self.columns = columnsIn #Number of columns for the board.
        self.rows = rowsIn #Number of rows for the board.
        self.boardPositionX = X #The position of the square horizontally.(0,7).
        self.boardPositionY = Y #The position of the square vertically. (0,7).
        #If there is a piece on the square, the piece object is stored in this variable.
        self.pieceOnBoardSquare = "" 
        #Gets the X position of the square.
        self.x = (X * (boardResolution[0] / self.columns))+40
        #Gets the Y position of the square.
        self.y = (Y * ((boardResolution[1] - 100) / self.rows))  + topBarXSize

    def isEmpty(self):
        #Method to check whether the board square is occupied by a chess piece or not. 
        if self.pieceOnBoardSquare == "":
            return True #Return True is the square is empty. 
        return False #Return False if the square is occupied. 

    def addPieceToSquare(self,pieceIn):
        #Add the piece object to the pieceOnBoardSquare variable.
        self.pieceOnBoardSquare = pieceIn 

    def removePieceFromSquare(self):
        #Remove the piece from the square
        self.pieceOnBoardSquare = "" 

    def getPiece(self):
        #Return the name of the piece on the square on the board.
        return self.pieceOnBoardSquare 

    def showSquare(self):
        #Method to display the board square to the self.window. 
        window= system.getWindow()
        if self.boardPositionX % 2 == 0:
            if self.boardPositionY % 2 == 0:
                pygame.draw.rect(window,LIGHTBROWN,(self.x,self.y,(boardResolution[0] / self.columns),((boardResolution[1] - 100) / self.rows)))
                pygame.draw.rect(window,LIGHTBROWN,(self.x,self.y,(boardResolution[0] / self.columns),((boardResolution[1] - 100) / self.rows)),2)

            else:                
                pygame.draw.rect(window,DARKBROWN,(self.x,self.y,(boardResolution[0] / self.columns),((boardResolution[1] - 100) / self.rows)))
                pygame.draw.rect(window,DARKBROWN,(self.x,self.y,(boardResolution[0] / self.columns),((boardResolution[1] - 100) / self.rows)),2)

        else:
            if self.boardPositionY % 2 == 0:
                pygame.draw.rect(window,DARKBROWN,(self.x,self.y,(boardResolution[0] / self.columns),((boardResolution[1] - 100) / self.rows)))
                pygame.draw.rect(window,DARKBROWN,(self.x,self.y,(boardResolution[0] / self.columns),((boardResolution[1] - 100) / self.rows)),2)

            else:
                pygame.draw.rect(window,LIGHTBROWN,(self.x,self.y,(boardResolution[0] / self.columns),((boardResolution[1] - 100) / self.rows)))
                pygame.draw.rect(window,LIGHTBROWN,(self.x,self.y,(boardResolution[0] / self.columns),((boardResolution[1] - 100) / self.rows)),2)

        return window

    def showPieceOnSquare(self,piecename,pieceimage):
        #Method to display the piece on the square to the window.
        window= system.getWindow()
        window.blit(pieceimage,(self.x + 10,self.y + 10))

    def hasSquareBeenClicked(self, X, Y):
        #Method to check if the board square has been clicked. 
        window= system.getWindow()
        #Check to see if the current mouse x and y positions match the positions of the square. 
        if (self.x  < X < self.x + 80) and (self.y  < Y < self.y + 80):
            return True,self.boardPositionX, self.boardPositionY
        return False, self.boardPositionX, self.boardPositionY

    def hasPieceOnSquareBeenClicked(self, X, Y, playerColour):
        #Method to check if the piece on the square has been clicked. 
        window= system.getWindow()#Get the window GUI.
        #Check to see if the current mouse x and y positions match the positions of the square.
        if (self.x  < X < self.x + 80) and (self.y  < Y < self.y + 80):
            if self.pieceOnBoardSquare !="":
                if self.pieceOnBoardSquare.getColour() == playerColour:
                    return True,self.boardPositionX, self.boardPositionY,self.pieceOnBoardSquare
                else:
                    pygame.draw.rect(window, DARKBROWN,(785,690,150,50))
                    font = pygame.font.SysFont('rockwell', 25)
                    window.blit(font.render('Invalid Piece', True, (WHITE)), (785, 690))
                    pygame.display.flip()
                    return False,X,Y,None

        return False,X,Y,None

    def displayColouredSquare(self, colourIn):
        #Method to display the square with a different coloured border. 
        window= system.getWindow()
        pygame.draw.rect(window,colourIn,(self.x,self.y,(boardResolution[0] / self.columns),((boardResolution[1] - 100) / self.rows)),2)

class chessPiece():
    def __init__(self,nameIn,pieceIn,evaluationScoreIn):
        self.name = nameIn #Uniquely identifiable code for each individual chess piece. 
        self.colour = nameIn[0] #Colour of the piece
        self.piece = pieceIn #Name of the chess piece.
        self.firstMove = True
        self.evaluationScore = evaluationScoreIn
        if self.colour =="w":
            if self.piece =="Pawn":
                #Load the white Pawn piece image
                self.twoSquareMove = False 
                self.image = pygame.image.load("Chess_plt60.png").convert_alpha()
            elif self.piece == "Rook":
                #Load the white Rook piece image
                self.image = pygame.image.load("Chess_rlt60.png").convert_alpha()
            elif self.piece == "Knight":
                #Load the white Knight piece image
                self.image = pygame.image.load("Chess_nlt60.png").convert_alpha()
            elif self.piece == "Bishop":
                #Load the white Bishop piece image
                self.image = pygame.image.load("Chess_blt60.png").convert_alpha()
            elif self.piece == "Queen":
                #Load the white Queen piece image
                self.image = pygame.image.load("Chess_qlt60.png").convert_alpha()
            elif self.piece == "King":
                #Load the white King piece image
                self.image = pygame.image.load("Chess_klt60.png").convert_alpha()

        else:
            if self.piece =="Pawn":
                #Load the black Pawn piece image
                self.twoSquareMove = False
                self.image = pygame.image.load("Chess_pdt60.png").convert_alpha()
            elif self.piece == "Rook":
                #Load the black Rook piece image
                self.image = pygame.image.load("Chess_rdt60.png").convert_alpha()
            elif self.piece == "Knight":
                #Load the black Knight piece image
                self.image = pygame.image.load("Chess_ndt60.png").convert_alpha()
            elif self.piece == "Bishop":
                #Load the black Pawn Bishop image
                self.image = pygame.image.load("Chess_bdt60.png").convert_alpha()
            elif self.piece == "Queen":
                #Load the black Queen piece image
                self.image = pygame.image.load("Chess_qdt60.png").convert_alpha()
            elif self.piece == "King":
                #Load the black King piece image
                self.image = pygame.image.load("Chess_kdt60.png").convert_alpha()     

    def getPiece(self):
        #Method to return the value of self.piece which holds the name of the type of chess piece (eg: pawn)
        return self.piece

    def getName(self):
        #Method to return the value of self.name which holds the unique name of the piece (eg: wP8)
        return self.name

    def getImage(self):
        #Method to return the image of the chess piece. 
        return self.image

    def getColour(self):
        #Method to return the colour of the piece. 
        return self.colour

    def getFirstMove(self):
        #Method to return the boolean whether the piece has been move before. 
        return self.firstMove

    def setFirstMove(self):
        #Method to set the value of self.firstMove when a piece has been moved for the first time. 
        self.firstMove = False

    def getEvaluationScore(self):
        #Method to return the evaluation score of the chess piece. 
        return self.evaluationScore

    def setTwoSquareMove(self):
        #Method to set the boolean self.twoSquareMove for pawns only. 
        self.twoSquareMove = True

    def getTwoSquareMove(self):
        #Method to return the value of the boolean self.twoSquareMove - only used for pawn pieces. 
        return self.twoSquareMove 

class chessPlayer():
    def __init__(self,nameIn, colourIn, movesIn, AIIn):
        self.name = nameIn #Attribute to hold the name of the player. 
        self.moves = movesIn #Attribute to hold the number of move a player has had. 
        self.colour = colourIn #Attribute to store the colour of the pieces the player is moving. 
        self.AI = AIIn #Attribute to store whether or not the player is an AI player or not.
        
    def getName(self):
        #Method to get the name of the player. 
        return self.name

    def setName(self, nameIn):
        #Method to get the name of the player. 
        self.name = nameIn

    def incrementMoves(self):
        #Method to increment the players moves by one after they have had their turn. 
        self.moves = int(self.moves) +1

    def getMoves(self):
        #Method to get the number of moves a player has taken during the game. 
        return self.moves

    def setColour(self, colourIn):
        #Method to set the colour of the player. 
        self.colour = colourIn

    def getColour(self):
        #Method to get the colour of the player. 
        return self.colour

    def setAI(self,AIIn):
        #Method to set whether the player is an AI player. 
        self.AI = AIIn

    def getAIStatus(self):
        #Method to get whether or not a player is an AI player.
        return self.AI
    
class leaderboardDatabase():
    def __init__(self):
        my_file = Path("playerDatabase.db")
        if my_file.is_file():
            #If the file exist, open it. 
            self.conn = sqlite3.connect('playerDatabase.db')

        else:
            #If the file does not already exist, create a new one. 
            self.conn = sqlite3.connect('playerDatabase.db')
            self.conn.execute('''CREATE TABLE LEADERBOARD
                     (ID INT PRIMARY KEY     NOT NULL,
                     NAME           TEXT    NOT NULL,
                     QUICKESTWIN           INT    NOT NULL,
                     GAMESWON           INT    NOT NULL,
                     GAMESLOST           INT    NOT NULL);''')

    def writeToDatabase(self, nameIn, movesIn, winIn):
        #Method to write a new record to the database. 
        ID = 1 #Unique ID for the record. 
        cursor = self.conn.execute("SELECT ID, NAME, QUICKESTWIN,GAMESWON, GAMESLOST from LEADERBOARD")
        for row in cursor:
           ID = ID +1 #If that ID already exists, add one. 
        if winIn == True:
            #Insert the winner into the leaderboard. 
            self.conn.execute("INSERT INTO LEADERBOARD (ID,NAME, QUICKESTWIN, GAMESWON, GAMESLOST)\
            VALUES (?, ?, ?,?,? )",(ID, nameIn, movesIn, 1, 0));
        else:
            #Insert the loser into the leaderboard. 
            self.conn.execute("INSERT INTO LEADERBOARD (ID,NAME, QUICKESTWIN, GAMESWON, GAMESLOST)\
            VALUES (?, ?, ?,?,? )",(ID, nameIn, "-", 0, 1));

        #Save the changes made to the database. 
        self.conn.commit()

    def updateRecord(self, nameIn, movesIn, winIn):
         #Method to update an existing record in the database. 
         record = self.searchForRecord(nameIn)
         if movesIn!="-" and record[2]!="-":
             if movesIn <= record[2]:
                 movesIn = movesIn
             elif record[2] == 0:
                 movesIn = movesIn
             else:
                 movesIn = record[2]
         cursor = self.conn.execute("SELECT ID, NAME, QUICKESTWIN, GAMESWON, GAMESLOST from LEADERBOARD")

         if winIn == True:
             #If the player has won, add one to their total games won.
             cursor.execute("UPDATE LEADERBOARD SET QUICKESTWIN = ?, GAMESWON = ? WHERE NAME = ?",(movesIn, record[3]+1, nameIn))
         else:
             #If the player has lost, add one to their total games lost.
             cursor.execute("UPDATE LEADERBOARD SET QUICKESTWIN = ?, GAMESLOST = ? WHERE NAME = ?",(movesIn, record[4]+1, nameIn))
         #Save the changes made to the database. 
         self.conn.commit()         

    def searchForRecord(self,nameIn):
        #Method to search and return a specific record in the database. 
        cursor = self.conn.execute("SELECT ID, NAME, QUICKESTWIN, GAMESWON, GAMESLOST from LEADERBOARD where NAME = ?",(nameIn,));
        for row in cursor:
            return (row[0], row[1], row[2], row[3], row[4])#Return the record for the specified name. 

    def doesRecordExist(self,nameIn):
        #Method to verify whether a record for a particular name already exists in the database.
         cursor = self.conn.execute("SELECT ID, NAME, QUICKESTWIN, GAMESWON, GAMESLOST from LEADERBOARD where NAME = ?",(nameIn,));
         for row in cursor:
             if nameIn in row:
                 #If the name is found in the record of a database, return True. 
                 return True
         #If the record is not found in the database, return False.
         return False
        
    def orderDatabase(self, orderByIn):
        #Method to reorder the database based on a particular attribute. 
        if orderByIn =="QUICKESTWIN":
            #Order the database by who has won a game of chess the quickest. 
            cursor = self.conn.execute("SELECT * FROM LEADERBOARD ORDER BY QUICKESTWIN ASC")
        elif orderByIn =="GAMESWON":
            #Order the database by who has won the most games. 
            cursor = self.conn.execute("SELECT * FROM LEADERBOARD ORDER BY GAMESWON DESC;")
        elif orderByIn =="GAMESLOST":
            #Order the database by who has lost the most games. 
            cursor = self.conn.execute("SELECT * FROM LEADERBOARD ORDER BY GAMESLOST DESC;")
        return cursor
boardResolution = (650,750) #Size of the chessboard.
screenResolution= (1000,750) #Size of the window.
topBarXSize = 50 #Holds the size of the top bar of the game. 

#Define RGB colours to be used during the game: 
WHITE = (255,255,255)
BLACK = (0,0,0)
LIGHTBROWN = (220,192,144)
MEDIUMBROWN = (181, 101, 29)
DARKBROWN = (137, 76, 22)
GREEN = (127,255,0)
RED = (255,69,0)
BLUE = (0,255,255)

mainGameLoop = True #Boolean that stays True until the game is over.
system = menuScreens() #Instantaite a specific instance of the menuScreens class called system. 
while mainGameLoop ==True:
    mainGameLoop = system.mainMenuScreen() #While the game is to continue, call the mainMenu methid of the main class.
pygame.quit()

