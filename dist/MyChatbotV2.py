# -*- coding: utf-8 -*-
#
#Created on Sun Mar  3 20:50:12 2024
#
#@author: Mathieu
#
#
#TODO:
#    X.  Permissions de commandes basées sur is_mod, is_sub et is_vip
#    X.  Cooldown de commandes basées sur is_mod, is_sub et is_vip
#    3.1 Maintenir un fichier json pour UserCardCollection      <----- En place.  À tester
#    3.2 Ajouter une commande pour avoir le status de notre collection
#
#
#
#

##########################################################################################################################################################
# Module dependencies
##########################################################################################################################################################
from twitchio.ext import commands
import hashlib
from datetime import datetime
import json
import sys
import random
import os
import csv
import pandas as pd
import re
#import pysftp
from git import Repo            #  V2.0
#import asyncio

##########################################################################################################################################################
# Twitch config
##########################################################################################################################################################
twitch_token = os.environ.get('TWITCH_TOKEN')
twitch_channel = 'keto_warrior'

#print(twitch_token)
#print(f'Trace: {twitch_token}')
#sys.exit()


##########################################################################################################################################################
# Répertoires
##########################################################################################################################################################
repo_path = 'E:/TarotGit/k3t0warri0r-coder.github.io'                                              # V2.0
CardCollectionPath = repo_path + '/liste_cartes.csv'
WebPageIndex       = repo_path + '/dist/index.html'
WebPageStyle       = repo_path + '/dist/style.css'
CardCollectionFileSingles = repo_path+'/dist/collectioninfo/'                                      # V2.0
CardCollectionTop5 = 'E:\\Development\\Chatbot\\TarotCollection\\tarot_collection_top5.txt'
CardCollectionTop50 = repo_path+'/dist/top50.txt'

# Specify the path to your repository
repo = Repo(repo_path)                                                                             # V2.0

##########################################################################################################################################################
# Command related global values
##########################################################################################################################################################

print('##############################################################################################')
print('Chatbot Keto Warrior')
print('##############################################################################################')


CardTypeLabels = {'R':'Régulière',
                  'F':'Foil',
                  'M':'Mythique'}
global CardCollection
CardCollection = []
with open(CardCollectionPath, mode='r', newline='', encoding='utf-8') as file:
    # Create a CSV reader object
    csv_reader = csv.reader(file)
    
    # Iterate over each row in the CSV file
    for row in csv_reader:
        CardCollection += [row[0]]
print(f'o Collection chargée.  Nombre de cartes: {len(CardCollection)}')

GlobalUserCooldown = {}
ConstantBaseTimestamp = datetime.fromisoformat('2024-01-01')

def main():

    global parm_odds_of_foil , parm_odds_of_mythic

    UpdateWebPages()

    global UserCardCollection    # Historique de cartes collectionnées

    UserCardCollection = {}
    for SingleCardCollection in os.listdir(CardCollectionFileSingles):
        if SingleCardCollection.endswith(".json"):
            try:
                with open(CardCollectionFileSingles+SingleCardCollection) as json_file:
                    UserCardCollection[SingleCardCollection.split('.')[0]] = {}
                    UserCardCollection[SingleCardCollection.split('.')[0]].update(json.load(json_file))
            except:
                print('ERROR: No existing tarot collection history')

    card_rarity_profiles = {1:[0.2, 0.05], 2:[0.15, 0.1], 3:[0.95, 0.05]}
    parm_odds_of_foil , parm_odds_of_mythic = card_rarity_profiles[1]    
    #print(card_rarity_profiles[1])

    #parm_odds_of_foil = 0.2
    #parm_odds_of_mythic = 0.05   #0.001

    #Section Achievement
    MaxAchievementLength = 50

    # Location of folders where to create transaction files when a command is called
    TransactionFolders = {'achievement':'E:\\Youtube\\Resources\\Python\\Achievement\\transactions\\'}

    ##########################################################################################################################################################
    # set up the bot
    ##########################################################################################################################################################
    bot = commands.Bot(
        token=twitch_token,
        prefix='!',
        nick=twitch_channel,
        initial_channels=[twitch_channel]
    )

    @bot.event()
    async def event_ready():
        'Called once when the bot goes online.'
        print('==============================================================================================')
        print(f"TRACE::: {twitch_channel} is online!")
        print('##############################################################################################')
        UpdateCollectionGIT(CardCollectionFileSingles+'*.json')
        #ws = bot._ws  # this is only needed to send messages within event_ready
        #await ws.send_privmsg(twitch_channel, "/me has landed!")
    
    #@bot.event()
    @bot.event
    async def event_message(ctx):
        'Runs every time a message is sent in chat.'
        if hasattr(ctx.author, 'name'):
            if ctx.author.name.lower() != twitch_channel.lower():
                print(ctx.author.name, ctx.content)
    
    
    ##########################################################################################################################################################
    # Bot commands
    ##########################################################################################################################################################
    @bot.command(name='test')
    async def test(ctx):
        if not is_allowed(ctx.author,[1,1,1,1]):
            print('User not allowed')
            return
    
        _CooldownRemaining = is_ready('test',ctx.author,30,30,30)
        if _CooldownRemaining > 0:
            await ctx.send(f'/me Désolé {ctx.author.name}, il y a encore {_CooldownRemaining}s de cooldown sur la commande')
        else:
            await ctx.send('test passed!')
            
        hash_object = hashlib.md5(ctx.author.name.encode())
        print(hash_object.hexdigest())
            
        #testmessage = 'votre collection peut être visualisé à: http://blablabla/' + str(hash_object) + 'html'
        #PartialUser.send_whisper(user_id=ctx.author.id,message=testmessage)
            
    
    @bot.command(name='achievement')
    async def achievement(ctx):
        
        if not is_allowed(ctx.author,[1,0,0,0]):
            await ctx.send('/me Vous ne pouvez pas lancer cette commande.')
            return
        
        #print(f'Message complet: {ctx.message.content}')
        msgContent = ' '.join(ctx.message.content.split()[1::])
    
        if len(msgContent) > MaxAchievementLength:
            await ctx.send('/me Longueur max pour un achievement: 50')
            return
    
        now = datetime.now() # current date and time
        TransactionFileName = ctx.message.content[1::].split()[0] + '_' + now.strftime("%m-%d-%Y.%H%M%S")+'.txt'
    
        #print(f'On va produire le fichier {TransactionFileName}')
        outfile = open(TransactionFolders[ctx.message.content[1::].split()[0]] + TransactionFileName, "w", encoding="UTF-8")
        outfile.writelines(msgContent)
        outfile.close()
        # await ctx.send('Yep!')
    
    
    @bot.command(name='tarot')
    async def tarot(ctx):
        
        
        print(f'TRACE: {parm_odds_of_foil} , {parm_odds_of_mythic}')
        
        #1) Modérateur 2) Subscriber 3) VIP 4) autres/tous
        
        if not is_allowed(ctx.author,[1,1,1,1]):
            await ctx.send(f'/me Désolé {ctx.author.name}, vous ne pouvez pas lancer cette commande.')
            return
    
        _CooldownRemaining = is_ready('tarot',ctx.author,10,3600,1800)
        if _CooldownRemaining > 0:
            await ctx.send(f'/me Désolé {ctx.author.name}, il y a encore {_CooldownRemaining//60}m{str(_CooldownRemaining%60).zfill(2)}s de cooldown sur la commande')
            return
    
        if ctx.author.name not in UserCardCollection:
            UserCardCollection[ctx.author.name] = {}
    
        if ctx.author.name == 'UneVieilleHabitude' or ctx.author.name == 'unevieillehabitude':
            (drawn_card_number,drawn_card) = (66,CardCollection[66])
            AddCardCollection(ctx.author.name,drawn_card,'M')
            payload = "/me " + ctx.author.name + " a tiré une la MEILLEURE CARTE en Mythique!!!  Quelle chance.  La carte ... " + '"' + drawn_card + '" ketowaParty ketowaParty ketowaParty'
        else:
            (drawn_card_number,drawn_card) = DealCard(ctx.author.name,'A')
            rarity_number = random.random()
    
            if rarity_number <= parm_odds_of_mythic:  # Carte Mythique
                NouvelleCarte = AddCardCollection(ctx.author.name,drawn_card,'M')
                if NouvelleCarte == 1:
                    payload = "/me " + ctx.author.name + " a tiré une NOUVELLE carte en Mythique!!!  C'est ULTRA rare.  La carte ... " + '"' + drawn_card + '" ketowaParty ketowaParty ketowaParty'
                else:
                    payload = "/me " + ctx.author.name + " a tiré une carte Mythique!!!  C'est ULTRA rare.  La carte ... " + '"' + drawn_card + '" ketowaParty ketowaParty ketowaParty'
                UpdateCollectionGIT(CardCollectionFileSingles+ctx.author.name+'.json')
                #threading.Thread(target=playsound, args=(SoundRef[1],), daemon=True).start()
            elif rarity_number <= parm_odds_of_foil:  # Carte Foil
                NouvelleCarte = AddCardCollection(ctx.author.name,drawn_card,'F')
                if NouvelleCarte == 1:
                    payload = "/me " + ctx.author.name + " a tiré une NOUVELLE carte en FOIL!!!  C'est genre super rare.  La carte ... " + '"' + drawn_card + '" ketowaParty ketowaParty ketowaParty'
                else:
                    payload = "/me " + ctx.author.name + " a tiré une carte FOIL!!!  C'est genre super rare.  La carte ... " + '"' + drawn_card + '" ketowaParty ketowaParty ketowaParty'
                #threading.Thread(target=playsound, args=(SoundRef[0],), daemon=True).start()
            else:                                     # Carte régulière
                NouvelleCarte = AddCardCollection(ctx.author.name,drawn_card,'R')
                if NouvelleCarte == 1:
                    payload = ctx.author.name + " a tiré une nouvelle carte: " + '"' + drawn_card + '"   ' + '(Carte no ' + str(drawn_card_number+1) + ')'
                    UpdateCollectionGIT(CardCollectionFileSingles+ctx.author.name+'.json')
                else:
                    payload = ctx.author.name + " a tiré une carte déjà dans sa collection: " + '"' + drawn_card + '"   ' + '(Carte no ' + str(drawn_card_number+1) + ')'
    
        await ctx.send(payload)
    
    # DEV BEGINS
    
    @bot.command(name='cardprofile')
    async def cardprofile(ctx,profile_id):
        global parm_odds_of_foil , parm_odds_of_mythic
        print(f'Profile: {card_rarity_profiles[int(profile_id)]}')
        parm_odds_of_foil , parm_odds_of_mythic = card_rarity_profiles[int(profile_id)]

    
    
    @bot.command(name='tarotgift')
    async def tarotgift(ctx,viewername,tarotgift_parm):
    
        #1) Modérateur 2) Subscriber 3) VIP 4) autres/tous
        if not is_allowed(ctx.author,[0,0,0,0]):   # NOTE: Si on active pour d'autres, ajouter un cooldown
            await ctx.send(f'/me Désolé {ctx.author.name}, vous ne pouvez pas lancer cette commande.')
            return
        if viewername[0] =='@':
            viewername=(viewername[1::].lower())
        else:
            viewername=(viewername.lower())
    
        _parmparse = re.search("^(A|S|N)(\d+|)(A|S|F|M)$", tarotgift_parm)  
       
        if _parmparse is None:
            print(f"ERROR: Problème avec le paramètre passé à la commande tarotgift: {tarotgift_parm}")
        else:
            drawtype=_parmparse[1]
            carno   =_parmparse[2]
            cardtype=_parmparse[3]
    
        if drawtype=='A':
            (_drawn_card_number,_drawn_card) = DealCard(viewername,'A')
        elif drawtype=='N':
            (_drawn_card_number,_drawn_card) = DealCard(viewername,'N')
        elif drawtype=='S':
            try:
                _drawn_card_number = int(carno)
            except:
                print(f"ERROR: Problème avec le paramètre passé à la commande tarotgift: {tarotgift_parm}")
                return
            if _drawn_card_number < len(CardCollection):
                _drawn_card = CardCollection[_drawn_card_number]
            else:
                print(f"ERROR: La carte est au delà de la collection: {_drawn_card_number}")
                return
    
        if drawtype=='A':
            message_bit1='carte au hazard'
        elif drawtype=='S':
            message_bit1='carte spécifique'
        elif drawtype=='N':
            message_bit1='nouvelle carte'
    
        if cardtype == 'A':
            rarity_number = random.random()
            if rarity_number <= parm_odds_of_mythic:  # Carte Mythique
                NouvelleCarte = AddCardCollection(viewername,_drawn_card,'M')
                cardtype='M'
            elif rarity_number <= parm_odds_of_foil:  # Carte Foil
                NouvelleCarte = AddCardCollection(viewername,_drawn_card,'F')
                cardtype='F'
            else:
                NouvelleCarte = AddCardCollection(viewername,_drawn_card,'R')
                cardtype='R'
        else:
            NouvelleCarte = AddCardCollection(viewername,_drawn_card,cardtype)
    
        if NouvelleCarte==1:
            payload = "/me " + ctx.author.name + f' a donné une {message_bit1} à @{viewername}: {_drawn_card} en {CardTypeLabels[cardtype]} (Nouvelle dans la collection)'
            UpdateCollectionGIT(CardCollectionFileSingles+viewername+'.json')
        else:
            payload = "/me " + ctx.author.name + f' a donné une {message_bit1} à @{viewername}: {_drawn_card} en {CardTypeLabels[cardtype]}'
    
        await ctx.send(payload)
    
    # DEV ENDS
    
    
    
    @bot.command(name='collection')
    async def collection(ctx):
        
        _CooldownRemaining = is_ready('collection',ctx.author,5,30,30)
        if _CooldownRemaining > 0:
            await ctx.send(f'/me Désolé {ctx.author.name}, il y a encore {_CooldownRemaining}s de cooldown sur la commande')
            return
    
        # Debug: Erreur survenue le 12 mai 2024.  Collection ne fonctionne pas mid-stream.  Manque un argument à la ligne 243.
        try:
            (NbT,NbF,NbM) = usercollection(ctx.author.name)
        except:
            print(f'ERREUR COLLECTION: user [{ctx.author.name}], collection [{usercollection(ctx.author.name)}]')
    
        #await ctx.send(f'{ctx.author.name}, tu as présentement {NbT} cartes sur {len(CardCollection)} (incluant {NbF} foil et {NbM} mythique)')
        #await ctx.send(f'{ctx.author.name}, tu as présentement {NbT} cartes sur {len(CardCollection)} (incluant {NbF} foil et {NbM} mythique).  Tu peux voir ta collection à cet addresse: https://vps-53ecf9d1.vps.ovh.ca/dist/index.html?viewer={ctx.author.name}')
        await ctx.send(f'{ctx.author.name}, tu as présentement {NbT} cartes sur {len(CardCollection)} (incluant {NbF} foil et {NbM} mythique).  Tu peux voir ta collection à cet addresse: https://k3t0warri0r-coder.github.io/dist/index.html?viewer={ctx.author.name} et le top50 au: https://k3t0warri0r-coder.github.io/dist/top50.html?viewer={ctx.author.name}')
    
    @bot.command(name='top3')
    async def top3(ctx):
        if not is_allowed(ctx.author,[1,0,0,0]):
            return
    
        usernm_list = []
        usernm_coll = []
        usernm_coll_foil   = []
        usernm_coll_mythic = []
        usernm_detail = []
        
        for usernm in UserCardCollection:
            if usernm != twitch_channel:
                usernm_list.append(usernm)
                
                try:
                    (NbT,NbF,NbM) = usercollection(usernm)
                except:
                    print(f'ERREUR COLLECTION: user [{usernm}], collection [{usercollection(usernm)}]')
    
                usernm_coll.append(NbT)
                usernm_coll_foil.append(NbF)
                usernm_coll_mythic.append(NbM)
                usernm_detail.append(f'{NbT} cartes dont {NbM} M et {NbF} F')
        
        
        df = GetTopCollections()[0:5]
        
        top5 = df.sort_values(by=['Collection', 'Collection-Mythics', 'Collection-Foils'], ascending=False)[0:5]
        
        await ctx.send(f'Top 3 collections: [1] {top5["Username"][0]} ({top5["Message"][0]}), [2] {top5["Username"][1]} ({top5["Message"][1]}), [3] {top5["Username"][2]} ({top5["Message"][2]})')

    # Start bot
    try:
        bot.run()
    except:
        pass
##########################################################################################################################################################
# Section autres fonctions (outils)
##########################################################################################################################################################

def UpdateWebPages():
    #CardCollection
    print(f'o Nombre de cartes dans la collection: {len(CardCollection)}')
    # Validation/mise à jour de la page index
    webpageindex_content = []
    with open(WebPageIndex, 'r', encoding='utf-8') as file:
        section_dictionary  = 0
        section_dictionary2 = 0
        for line_number, line in enumerate(file, start=1):
            # Strip newline characters and extra spaces
            clean_line = line.rstrip('\n')
            
            re_check_fin_section  = re.search("^(\s*.+):\'(\d+)\'}", clean_line)
            re_check_fin_section2 = re.search("^\s*\'(\d+)\':(.+)}", clean_line)
            if re.search("^\s*states_dictionary={", clean_line):
                section_dictionary = 1
                #print(clean_line)
            elif re.search("^\s*states_dictionary2={", clean_line):
                section_dictionary2 = 1
                #print(clean_line)

            if section_dictionary == 1 and re_check_fin_section is not None:
                if int(re_check_fin_section[2]) < (len(CardCollection)):
                    webpageindex_content += [clean_line.rstrip('}')+',']
                    for newcardcnt in range(int(re_check_fin_section[2])+1,len(CardCollection)+1):
                        if newcardcnt == len(CardCollection):
                            webpageindex_content += [f'     "{CardCollection[newcardcnt-1]}":"{newcardcnt}"'+'}']
                        else:
                            webpageindex_content += [f'     "{CardCollection[newcardcnt-1]}":"{newcardcnt}",']
                    section_dictionary = 0
            elif section_dictionary2 == 1 and re_check_fin_section2 is not None:
                if int(re_check_fin_section2[1]) < (len(CardCollection)):
                    webpageindex_content += [clean_line.rstrip('}')+',']
                    for newcardcnt in range(int(re_check_fin_section2[1])+1,len(CardCollection)+1):
                        if newcardcnt == len(CardCollection):
                            webpageindex_content += [f'     "{newcardcnt}":"{CardCollection[newcardcnt-1]}"'+"}"]
                        else:
                            webpageindex_content += [f'     "{newcardcnt}":"{CardCollection[newcardcnt-1]}",']
                    section_dictionary2 = 0
            else:
                webpageindex_content += [clean_line]

    with open(WebPageIndex, "w") as f:
        for item in webpageindex_content:
            f.write(f"{item}\n")
    UpdateCollectionGIT(WebPageIndex)
    print('o Mise à jour fichier index.html comlété')

    webpageindex_content = []
    with open(WebPageStyle, 'r', encoding='utf-8') as file:
        section1  = 0
        section2 = 0
        for line_number, line in enumerate(file, start=1):
            # Strip newline characters and extra spaces
            clean_line = line.rstrip('\n')

            if section1 == 1:
                match = re.search('\s+--c(\d+)front: url\(', clean_line)
                if match:
                    max_card_no = int(match.group(1))

            re_check_fin_section  = re.search("^\s*}", clean_line)
            re_check_fin_section2 = re.search("^\s*$", clean_line)
            if re.search("^\s*--back: url\(https:", clean_line):
                section1 = 1
            elif re.search("^\s*\.card2\.cback {", clean_line):
                section2 = 1

            if section1 == 1 and re_check_fin_section is not None:
                if max_card_no < (len(CardCollection)):
                    for newcardcnt in range(max_card_no+1,len(CardCollection)+1):
                        webpageindex_content += [f'  --c{newcardcnt}front: url(https://k3t0warri0r-coder.github.io/assets/{newcardcnt}.png);']
                        webpageindex_content += [f'  --c{newcardcnt}mfront: url(https://k3t0warri0r-coder.github.io/assets/{newcardcnt}m.png);']
                    section1 = 0
                webpageindex_content += [clean_line]
            elif section2 == 1 and re_check_fin_section2 is not None:
                if max_card_no < (len(CardCollection)):
                    for newcardcnt in range(max_card_no+1,len(CardCollection)+1):
                        webpageindex_content += [f'.card.c{newcardcnt} '+'{']
                        webpageindex_content += ['  --color1: var(--carte1);']
                        webpageindex_content += ['  --color1: var(--carte2);']
                        webpageindex_content += [f'  --front: var(--c{newcardcnt}front);']
                        webpageindex_content += ['}']
                        webpageindex_content += [f'.card.c{newcardcnt}m '+'{']
                        webpageindex_content += ['  --color1: var(--carte1);']
                        webpageindex_content += ['  --color1: var(--carte2);']
                        webpageindex_content += [f'  --front: var(--c{newcardcnt}mfront);']
                        webpageindex_content += ['}']
                        webpageindex_content += [f'.card2.c{newcardcnt} '+'{']
                        webpageindex_content += ['  --color1: var(--carte1);']
                        webpageindex_content += ['  --color1: var(--carte2);']
                        webpageindex_content += [f'  --front: var(--c{newcardcnt}front);']
                        webpageindex_content += ['}']
                    section2 = 0
                webpageindex_content += [clean_line]
            else:
                webpageindex_content += [clean_line]
    with open(WebPageStyle, "w") as f:
        for item in webpageindex_content:
            f.write(f"{item}\n")
    UpdateCollectionGIT(WebPageStyle)
    print('o Mise à jour fichier style.css comlété')


#def UpdateCollectionSFTP():
#    sftp = pysftp.Connection(host="vps-53ecf9d1.vps.ovh.ca", username="debian", private_key="C:/Users/mathi/.ssh/id_rsa",private_key_pass='Tarot4Keto')
#    for file in os.listdir('E:\\Development\\Chatbot\\TarotCollection\\Data\\'):
#        if file[-5::] == '.json':
#            sftp.put(localpath='E:\\Development\\Chatbot\\TarotCollection\\Data\\' + file ,remotepath = "/www/data/tarot_collection/collectioninfo/" + file)
#    sftp.close()
#    print('NOTE: Server collection updated')

def UpdateCollectionGIT(updatefile):
    # Stage the changes
    repo.git.add(updatefile)  # Replace with your file name
    # Commit the changes
    repo.index.commit('Commit chatbot: '+updatefile.split('/')[-1])

    # Push changes to the remote repository
    origin = repo.remote(name="origin")
    origin.push()
    print('NOTE: GIT collection updated')

def AddCardCollection(viewername,cardname,rarity):
    if cardname not in UserCardCollection[viewername]:
        UserCardCollection[viewername][cardname] = {}
        UserCardCollection[viewername][cardname] = (0,0,0)
        new_card = 1
    else:
        new_card = 0
        
    if rarity=='R':
        UserCardCollection[viewername][cardname] = (UserCardCollection[viewername][cardname][0]+1,
                                                    UserCardCollection[viewername][cardname][1],
                                                    UserCardCollection[viewername][cardname][2])
    elif rarity=='F':
        UserCardCollection[viewername][cardname] = (UserCardCollection[viewername][cardname][0],
                                                    UserCardCollection[viewername][cardname][1]+1,
                                                    UserCardCollection[viewername][cardname][2])
    elif rarity=='M':
        UserCardCollection[viewername][cardname] = (UserCardCollection[viewername][cardname][0],
                                                    UserCardCollection[viewername][cardname][1],
                                                    UserCardCollection[viewername][cardname][2]+1)

    #Save to file
    with open(CardCollectionFileSingles+viewername+'.json', "w") as outfile: 
        json.dump(UserCardCollection[viewername], outfile)
        
    # Update display
    df = GetTopCollections()
    df1 = df[0:5]
    with open(CardCollectionTop5, "w") as outfile: 
        for line in df1['Message2'].tolist():
            outfile.write(line + " \n") # works with any number of elements in a line
    with open(CardCollectionTop50, "w") as outfile: 
        outfile.write(df[0:50][['Username', 'Collection', 'Collection-Foils', 'Collection-Mythics']].to_json(orient='index')) # works with any number of elements in a line
    UpdateCollectionGIT(CardCollectionTop50)
    return new_card

def DealCard(viewername,type):
    if viewername not in UserCardCollection:
        UserCardCollection[viewername] = {}

    if type == 'A': # A random card (Any)
        drawn_card_number = random.randint(0,len(CardCollection)-1)
    elif type == 'N': # A new card (New)
        missing_cards = []
        for cpt in range(0,len(CardCollection)):
            if CardCollection[cpt] not in UserCardCollection[viewername]:
                missing_cards.append(cpt)
        drawn_card_number = missing_cards[random.randint(0,len(missing_cards)-1)]
    #CardCollection[drawn_card_number]
    return (drawn_card_number,CardCollection[drawn_card_number])

def GetTopCollections():

    usernm_list = []
    usernm_coll = []
    usernm_coll_foil   = []
    usernm_coll_mythic = []
    usernm_detail = []
    usernm_detail_short = []
    
    for usernm in UserCardCollection:
        if usernm != 'keto_warrior':
            usernm_list.append(usernm)
            
            try:
                (NbT,NbF,NbM) = usercollection(usernm)
            except:
                print(f'ERREUR COLLECTION: user [{usernm}], collection [{usercollection(usernm)}]')

            usernm_coll.append(NbT)
            usernm_coll_foil.append(NbF)
            usernm_coll_mythic.append(NbM)
            usernm_detail.append(f'{NbT} cartes dont {NbM} M et {NbF} F')
            usernm_detail_short.append(f'{usernm} [{NbT}] ({NbM} M et {NbF} F)')
    
    return pd.DataFrame({'Username':usernm_list, 'Collection':usernm_coll, 'Collection-Foils':usernm_coll_foil, 'Collection-Mythics':usernm_coll_mythic, 'Message':usernm_detail, 'Message2':usernm_detail_short}).sort_values(by=['Collection', 'Collection-Mythics', 'Collection-Foils'], ascending=False).reset_index()

def is_allowed(user,rights):
    
    # print(f'TRACE [is_allowed]: {user.name}:: Mod {user.is_mod}, Sub {user.is_subscriber}, VIP {user.is_vip}')
    
    #1) Modérateur 2) Subscriber 3) VIP 4) autres/tous
    if user.name == twitch_channel:
        return True
    elif rights[0] == 1 and user.is_mod:
        return True
    elif rights[1] == 1 and user.is_subscriber:
        return True
    elif rights[2] == 1 and user.is_vip:
        return True
    elif rights[3] == 1:
        return True
    else:
        return False

def is_ready(commandname,user,GlobalCooldown,UserCooldown,SubCooldown):
    if user.name == twitch_channel:
        return 0
    if user not in GlobalUserCooldown:
        #print('... place 1')
        GlobalUserCooldown[user] = {}
        _UserLastCall = ConstantBaseTimestamp
        
    if commandname in GlobalUserCooldown[user]:
        #print('... place 2')
        _UserLastCall = GlobalUserCooldown[user][commandname]
    else:
        #print('... place 3')
        _UserLastCall = ConstantBaseTimestamp
    
    #print('===> TRACE: '+str(_UserLastCall))
    _timeDelta = round((datetime.now()-_UserLastCall).total_seconds())
    print(f'TRACE [is_ready]: {user.name} {_timeDelta}:: Mod {user.is_mod}, Sub {user.is_subscriber}, VIP {user.is_vip}')
    if _timeDelta > UserCooldown:
        print('TRACE [is_ready]: first cond')
        GlobalUserCooldown[user][commandname] = datetime.now()
        return 0
    elif (user.is_subscriber or user.is_mod) and _timeDelta > SubCooldown:
        print('TRACE [is_ready]: second cond')
        GlobalUserCooldown[user][commandname] = datetime.now()
        return 0
    elif user.is_subscriber or user.is_mod:
        return (SubCooldown-_timeDelta)+1
    else:
        return (UserCooldown-_timeDelta)+1

def usercollection(username):
    NbTotal = 0
    NbFoil = 0
    NbMythic = 0
    if username in UserCardCollection:
        NbTotal= len(UserCardCollection[username])
        for carte in UserCardCollection[username]:
            if UserCardCollection[username][carte][1] > 0:
                NbFoil = NbFoil + 1
            if UserCardCollection[username][carte][2] > 0:
                NbMythic = NbMythic + 1
    return (NbTotal,NbFoil,NbMythic)




if __name__ == "__main__":
    main()