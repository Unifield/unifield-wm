#!/usr/bin/python
# -*- coding: utf-8 -*-

 

#lpstat -d voir imprimante par défaut
#lpstat -p liste des imprimante



#print "prodbon.py"



# variables


import datetime




# dans openerp :
				# au moment de la validation commande
				# transmettre dico sale, salel, partner
				#import prodbon
				#prodbon.impression_bon(sale, salel, partner)
				#prodbon.impression_hote_bizerba(partner)					



crlf = "\n\r"
long = 0







def impression_bon(sale, salel, partner):
	
	#print partner
	import os
	nblig = 0
	
	
	
	def lne(p1,p2):
		return(  (p1 + " " * p2)[0:p2]  )
	
	
	

	def affext(nblig, p1):
		#print p1
		ficsor.write(p1)
		if p1 == crlf:
			nblig += 1
		return nblig

	order_ref = sale[0]['client_order_ref'] and sale[0]['client_order_ref'] or sale[0]['name']
	ficname = "/Data/prodbon/" + order_ref  + ".txt"
	ficsor = open( ficname ,"w")
	
	#ficsor.write(" " +   "\n")

	
	page = 1
	
	
	nblig = affext(nblig,"-" * 79)
	nblig = affext(nblig,crlf)
	
	nblig = affext(nblig,"DISTRIBUTION ILLER :")
	nblig = affext(nblig," " * 30)
	nblig = affext(nblig," date")
	nblig = affext(nblig," " * 04)
	nblig = affext(nblig," heure")
	nblig = affext(nblig," " * 02)
	nblig = affext(nblig," page")
	
	
	nblig = affext(nblig,crlf)
	
	nblig = affext(nblig," " * 05)
	nblig = affext(nblig,"** BON DE CONTROLE OPENERP **") 
	
	nblig = affext(nblig," " * 15)
	#nblig = affext(nblig,str(datetime.datetime.now())[0:19])
	
	#nblig = affext(nblig, datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S") )
	nblig = affext(nblig, datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S") )
	
	nblig = affext(nblig," " * 02)
	nblig = affext(nblig,str(page).zfill(2))
	nblig = affext(nblig,crlf)
	
	nblig = affext(nblig,"CLIENT	  :" )
	nblig = affext(nblig," " * 05)
	nblig = affext(nblig, sale[0]['code'] )
	nblig = affext(nblig," " * 7)
	nblig = affext(nblig, sale[0]['partner_id'][1] )
	nblig = affext(nblig,crlf)
	
	
	 
	nblig = affext(nblig,"NU BON	  :" )
	nblig = affext(nblig," " * 05)
	nblig = affext(nblig, sale[0]['client_order_ref'] or sale[0]['name'] )
	
	nblig = affext(nblig,crlf)
	
	
	nblig = affext(nblig,"DATE LIVR.:" )
	nblig = affext(nblig," " * 05)
	trav = sale[0]['date_order'] # 2014-07-02
	nblig = affext(nblig, trav[8:10] + "/" + trav[5:7] + "/" + trav[0:4] + " " * 4 )
	nblig = affext(nblig, partner[0]['city'])
	nblig = affext(nblig,crlf)
	
	
	nblig = affext(nblig,"UTILIS.	  :" )
	nblig = affext(nblig," " * 05)
	nblig = affext(nblig, sale[0]['user_id'][1] )
	nblig = affext(nblig,crlf)

	
	nblig = affext(nblig,"TOURNEE	  :" )
	nblig = affext(nblig," " * 05)
	nblig = affext(nblig, sale[0]['tournee_id'][1] )
	nblig = affext(nblig,crlf)
	
	
	nblig = affext(nblig,"COMMENTAIRE :" )
	#nblig = affext(nblig, sale[0]['commentaire_livraison'] )
	
	nblig = affext(nblig,crlf)
	
	
	nblig = affext(nblig,"=" * 79)
	nblig = affext(nblig,crlf)
	
	
	nblig = affext(nblig,"!" + "ARTICLE" + "!" + " DESIGNATION " + " " * 16 + "poste     Pu   " + "!" + "	QTE	   "+ "!" + "  POIDS   " + "!")
	nblig = affext(nblig,crlf)
	nblig = affext(nblig, "!	!" + " PREPARATION " + " " * 16 + "empStock       " +"!" + " COMMANDEE   " + "!" + "  REEL    " + "!") 
	nblig = affext(nblig,crlf)
	
	nblig = affext(nblig,"=" * 79)
	nblig = affext(nblig,crlf)
	
	
	
	
	for i in range(0, len(salel) ):
		#nblig = affext(nblig, salel[i]['product_id'][1][0:39])



		
		trav  =  "!%s %s %s %7.2f  ! " % (salel[i]['product_id'][1][1:7], salel[i]['product_id'][1][9:39], salel[i]['type_prep'], salel[i]['price_unit'])
		
		#nblig = affext(nblig, salel[i]['product_uom']) 
		
		trav +=  "%6.3f %s ! %s !" %     (salel[i]['product_uos_qty'], lne(salel[i]['type_cond'],4), " " * 8 )
		nblig = affext(nblig,trav)
		nblig = affext(nblig,crlf)
		
		
		trav = "!%s! %s ! %s !" % ( lne(salel[i]['notes'],52),  " " * 11,  lne(salel[i]['product_uom'][1],8)  )
		nblig = affext(nblig,trav)
		nblig = affext(nblig,crlf)
		
		
		nblig = affext(nblig,"=" * 79)
		#nblig = affext(nblig,str(i).zfill(2))
		nblig = affext(nblig,crlf)
		
		

	trav = "!%s %s!" %  (  "Nombre bac rouge : ",  " " * 57 )
	nblig = affext(nblig,trav)
	nblig = affext(nblig,crlf)
	
	trav = "!%s %s %s %s!" %  ( "Preparateur      :",  " " * 21,  "Nb elements  :", " " * 21)
	nblig = affext(nblig,trav)
	nblig = affext(nblig,crlf)
	
	nblig = affext(nblig,"=" * 79)
	nblig = affext(nblig,crlf)
		
		# "%4.2f"  % price_unit
		
	
	#print salel[0]
	
	ficsor.close()
	
	
# lp -d KYO3140COMPTA 153925.txt   
#l’imprimante FS1118 ne fait rien ; elle est activée depuis le sam 10 mar 2012 11:40:59 CET
#l’imprimante KM5050 ne fait rien ; elle est activée depuis le jeu 24 jui 2014 11:41:54 CEST
#l’imprimante KYO3140COMPTA ne fait rien ; elle est activée depuis le jeu 24 jui 2014 09:27:55 CEST
#l’imprimante KYOKM5050 ne fait rien ; elle est activée depuis le jeu 24 jui 2014 11:44:47 CEST

       
	cmd = 'lp  '  + " -d "  + "KYO3140COMPTA"  +  " "  + ficname
	#os.system( cmd )
	
	
	return




#{'property_ids': [], 'product_uos_qty': 3.3500000000000001, 'type_tarif': False, 'product_uom': [1, 'PCE'], 
# 'sequence': 10, 'price_unit': 9.3599999999999994, 'product_uom_qty': 3.3500000000000001, 'price_subtotal': 31.359999999999999, 
#'product_uos': False, 'id': 175064, 'number_packages': 1, 'invoiced': False, 'delay': 0.0, 
#'name': 'TRIPES MODE DE CAEN THIOL PAR		   ', 'move_ids': [], 'commission': 0.93999999999999995, 'state': 'draft', 
#'order_partner_id': [6052, "HOTEL REST A L'ETOILE"], 'product_packaging': False, 'type': 'make_to_stock', 
#'type_prep': 'PREP', 'poste_id': False, 'procurement_id': False, 'order_id': [28551, 'i_1407_01  F-573150  020714'], 
#'discount': 0.0, 'num_lot': '1462314			 ', 'price_net': 9.3599999999999994, 'tax_id': [3], 
#'product_id': [743, '[064700] TRIPES MODE DE CAEN THIOL PAR 3,350KG   '], 'type_cond': 'KILO', 
#'invoice_lines': [], 'notes': " ", 'th_weight': 0.0, 'address_allotment_id': False}


def cde_decoup():
	return 
	
	

def retour_bizerba():
	
	return 
	
	


def impression_hote_bizerba(sale, salel, partner):

	
	
	return 
	
	
	
	
	
	
	






# a intercaler sur la validation commandes 
# import prodbon


# 1) impression du bon
# 2) creation hote.txt bizerba 




if  __name__=="__main__":
	
	print "prodbon main "
	
	
	
	
	
	
	
