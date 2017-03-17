#!/usr/bin/python
# -*-coding:Utf8 -*

import socket, Rights
from socket import error as SocketError
import errno, shutil
from os import chdir
from os import system
import os
from getpass import getpass
import time


BUFFER_SIZE = 2048

def commandes_server(self, clientsocket):
	tampon = ""
	data = self.clientsocket.recv(BUFFER_SIZE).decode("Utf8")
	data=data.split(" ")

	#Partie gestion des droits
	rights = Rights.Rights(self.path)


	if data[0] == "ls": #commande ls
		chn = " ".join(data)
		chn = chn + " " + self.path #on recupere le path
		res = os.popen(chn).readlines() #on recupère le resultat de ls
		for mot in res : #on le remet sous la forme chaine de caractere
			tampon = tampon + mot
		taille = len(tampon)/BUFFER_SIZE
		tampon = str(taille) + tampon + "\n"
		send(self,tampon,clientsocket) #on envoie le resultat
		del tampon

	elif data[0] == "cd" : #commande cd
		if len(data) != 1 :
			ls = "ls" + " " + self.path #on fait d'abord un ls voir si il est possible de cd
			lst = os.popen(ls).readlines()
			for i, item in enumerate(lst) : 
				lst[i] = item.rstrip()
			if (data[1] in lst) or (data[1] == "..") : #si c'est dans la liste, ou "..", on peut changer le path
				if data[1] == ".." :
					if self.path != "./data" : #si le path est "./data" et l'on souhaite faire "cd ..", on ne le change pas, ce n'est pas possible
						path = self.path.split("/")
						self.path = ""
						for i in range(0,len(path)-1): #mise a jour du nouveau path
							self.path = self.path+path[i]
							self.path = self.path+"/"
				else :
					self.path = self.path + "/" + data[1]
			else :
				print("pas de changement de path car cd pas bon")
		send(self,self.path,clientsocket)
	elif data[0] == "cat" : #commande cat
		if rights.isReadable(self.rights) and data[1] != ".config": #verification si l'on possede les droits
			ls ="ls" + " " + self.path
			lst = os.popen(ls).readlines() #on regarde si le fichier est present
			for i, item in enumerate(lst) :
				lst[i] = item.rstrip()
			if (data[1] in lst) :
				data[1] = self.path+"/"+data[1] #on met a jour le chemin
				chn = " ".join(data)
				res = os.popen(chn).readlines() #on recupere la sortie du cat
				for mot in res :
					tampon = tampon + mot
				taille = len(tampon)/BUFFER_SIZE #on regarde le nombre de message qu'il faut pour envoyer entierement le fichier
				tampon = str(taille) + tampon
				send(self,tampon,clientsocket) #on envoie le message
				del tampon
			else :
				send(self,"0le fichier n'existe pas il n'est pas possible de cat\n",clientsocket)
		else:
			send(self,"0Droits de lectures insuffisants.\n",clientsocket)

	elif data[0] == "mv" : #commande mv
		if rights.isWritable(self.rights) and data[1] != ".config":
			ls ="ls" + " " + self.path
			lst = os.popen(ls).readlines()
			for i, item in enumerate(lst) :
				lst[i] = item.rstrip()
			if (data[1] in lst) :
				data[1] = self.path+"/"+data[1]
				data[2] = self.path+"/"+data[2]
				chn = " ".join(data)
				os.system(chn)
			else :
				print("fichier inconnu")

	elif data[0] == "rm" :
		if rights.isWritable(self.rights):
			if data[1] == "-R":
				if data[2] == ".config":
					send(self,"Fichier de configuration vérouillé.\n", clientsocket)
				else :
					try:
						shutil.rmtree(self.path+"/"+data[2])
						send(self,"Suppression effectuée.\n", clientsocket)
					except Exception as e:
						send(self,"Impossible de supprimer le dossier, erreur.\n", clientsocket)
			else:
				if data[1] == ".config":
					send(self,"Fichier de configuration vérouillé.\n", clientsocket)
				else :
					try:
						os.remove(self.path+"/"+data[1])
						send(self,"Suppression effectuée.\n", clientsocket)
					except Exception as e:
						send(self,"Impossible de supprimer le fichier, erreur.\n", clientsocket)
		else:
			send(self,"Droits d'écriture insuffisants.\n", clientsocket)

	elif data[0] == "mkdir" :
		if rights.isWritable(self.rights):
			data[1] = self.path+"/"+data[1]
			chn = " ".join(data)
			os.system(chn)
			config = open(data[1] + "/.config", "w")
			config.write("[read]\n")
			line = ""
			for l in rights.read :
				line = line + l + ";"
			line = line[:-1]
			config.write(line + "\n[write]\n")
			line = ""
			for l in rights.write :
				line = line + l + ";"
			line = line[:-1]
			config.write(line + "\n[owners]\n")
			line = ""
			for l in rights.owners :
				line = line + l + ";"
			line = line +self.Thread_name
			config.write(line)

	elif data[0] == "touch" :
		if rights.isWritable(self.rights):
			data[1] = self.path+"/"+data[1]
			chn = " ".join(data)
			os.system(chn)

	elif data[0] == "rights":
		config = open(self.path +"/.config", "r")
		config.readline()
		line = "Lecture : " + config.readline().replace(";", ", ") + "Ecriture : "
		config.readline()
		line = line + config.readline().replace(";", ", ") +"\n"
		send(self, line, clientsocket)

	elif data[0] == "admin":
		if rights.isOwner(self.Thread_name):
			#Envoit des données à l'application graphique
			send(self, "yes", clientsocket)			
			config = open(self.path +"/.config", "r")
			config.readline()
			line = config.readline().replace(";", ",").replace(" ", "").rstrip()
			send(self, line, clientsocket)
			config.readline()
			line = config.readline().replace(";", ",").replace(" ", "").rstrip()
			send(self, line, clientsocket)
			config.close()
			#Retour des données
			read = self.clientsocket.recv(BUFFER_SIZE).decode("Utf8")
			write = self.clientsocket.recv(BUFFER_SIZE).decode("Utf8")
			if read.rstrip() == "abort" or write.rstrip() == "abort":
				send(self, "no", clientsocket)
			else:
				read = read.rstrip().replace(" ", "").replace(",", ";")
				write = read.rstrip().replace(" ", "").replace(",", ";")
				#Ecriture des informations
				os.remove(self.path + "/.config")
				config = open(self.path + "/.config", "w")
				config.write("[read]\n")
				config.write(read + "\n[write]\n")
				config.write(write + "\n[owners]\n")
				line = ""
				for l in rights.owners :
					line = line + l + ";"
				line = line[:-1]
				config.write(line)
				#Mise à jour des droits
				rights = Rights.Rights(self.path)
				#Réponse du serveur
				send(self, "ok", clientsocket)
		else:
			send(self, "no", clientsocket)
	elif data[0] == "vim":
	############################  Partie envoie du fichier au client  ################################ 
		
		fich = self.path + "/" + data[1] 
		exist = False
		try:
			fp=open(fich,"rb") #ici nous testons l'exitence du fichier
			fp.close()
			exist = True
		except:
			send(self,"Ce fichier n'existe pas!\n",clientsocket)

		if exist == True :
			num = 0
			fp=open(fich,"rb")
			nboctets = os.path.getsize(fich)
			send(self,str(nboctets),clientsocket)
			print nboctets
			if nboctets > BUFFER_SIZE :
				for i in range((nboctets/BUFFER_SIZE)+1) :
					fp.seek(num,0)
					data = fp.read(BUFFER_SIZE)
					print data
					send(self,data,clientsocket)
					num = num + BUFFER_SIZE
			else :
				data = fp.read()
				send(self,data,clientsocket)
			fp.close()

############################  Partie reception du fichier  ################################ 
		if exist == True :
			nbretour = self.clientsocket.recv(BUFFER_SIZE).decode("Utf8")
			nbretour = int(nbretour)
			fp = open(fich, "wb")
			if nbretour > BUFFER_SIZE :
				for i in range((infos / BUFFER_SIZE) +1) :
					data = self.clientsocket.recv(BUFFER_SIZE).decode("Utf8")
					fp.write(data)
			else :
				data = self.clientsocket.recv(BUFFER_SIZE).decode("Utf8")
				fp.write(data)
			fp.close()
	elif data[0] == 'upload' :

		nbretour = self.clientsocket.recv(BUFFER_SIZE).decode("Utf8")
		nbretour = int(nbretour)
		fich = self.path + "/" + data[1]
		fp = open(fich, "wb")
		if nbretour > BUFFER_SIZE :
			for i in range((nbretour / BUFFER_SIZE) +1) :
				data = self.clientsocket.recv(BUFFER_SIZE).decode("Utf8")
				fp.write(data)
		else :
			data = self.clientsocket.recv(BUFFER_SIZE).decode("Utf8")
			fp.write(data)
		fp.close()
	else:
		print "commande non reconnue"

#Fonction à utiliser pour envoyer un message en texte (utilise un encodage défini)
def send(self, message,clientsocket):
	self.clientsocket.send(message.encode("Utf8"))