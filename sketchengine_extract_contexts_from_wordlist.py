# Tout d'abord demandez la génération d'une API_KEY (une clé) dans votre compte SketchEngine : 
# https://www.sketchengine.eu/documentation/api-documentation/#toggle-id-1 (Authentification)

# Pour plus d'infos sur les méthodes disponibles : https://www.sketchengine.eu/documentation/methods-documentation/

# chargement des librairies nécessaires 
import requests, time, json
import pandas as pd
import os, re, time
from glob import glob
import traceback

import matplotlib.pyplot as plt
import seaborn as sns
sns.set(rc={'figure.figsize':(11, 4)})
from matplotlib.backends.backend_pdf import PdfPages



# global paramaters : SketchEngine 
USERNAME = 'your username'
API_KEY = 'your api key'
base_url = 'https://api.sketchengine.eu/bonito/run.cgi'


params_word_list = {
    'wltype':'simple',
    'wlattr':'word',
    'wlminfreq':1,
    'wlmaxitems':1000}
    #'wlpat': 're'}


# paramètres de la requête : concordance
params = {
 'format': 'json', # format de la réponse (attention au 30/03/2020 : métainformations disponibles seulement avec json!)
 'asyn':0, # mode de réponse (ici on récupère toute la réponse, c'est plus long mais plus facile à gérer)
 #'corpname': 'preloaded/frantext_trends',
 'attrs': 'word,lemma,tag', # informations pour le mot clé
 'ctxattrs': 'word,lemma,tag', # idem pour les mots du contexte
 #'q':'q[word="afro.+"]', # query
 'viewmode':'sen', # on récupère le mode sentence (phrase vs kwic)
 'structs':'doc.uri,doc.website,doc.date,doc.source_country',# meta-informations (voir résultats requête précédente corp_info)
 'refs':'=doc.uri,=doc.website,=doc.date,=doc.source_country',# meta-informations (voir résultats requête précédente corp_info)
 'pagesize':10000000, # nbre de résultats maximum
}


def corpus_info(corpus):
	''' get corpus info'''
	params = {'gramrels':1, 'registry':1, 'struct_attr_stats':1,'subcorpora':1}
	params['corpname']=corpus
	res =  requests.get(base_url + '/corp_info', params=params, auth=(USERNAME, API_KEY)).json()
	if 'error' in res.keys():
		print("Error in result for query : [" + base_url + '/corp_info?], params : ' + str(params) + ', error : '+ res['error'])
		exit()
	else :
		#print(res)
		return res

def query_sketchengine(params, cmd):
  '''Cette fonction envoie une requête à sketchengine et retourne la réponse
  voir https://www.sketchengine.eu/documentation/methods-documentation/ pour tous les paramètres'''
  try:
    #print(params, cmd)
    if params['format']=='json':
        res = requests.get(base_url + '/' + cmd, params=params, auth=(USERNAME, API_KEY)).json()
        #print(res)
    else:
        res = requests.get(base_url + '/' + cmd, params=params, auth=(USERNAME, API_KEY))
    #print(res)
    return res
  except Exception as e:
    print(traceback.format_exc())
    print("Erreur dans la requête. Message d'erreur : " + str(e))
    return False

def retrieve_wordlist(output_dir, corpora, lang,words):
    #words=['airbus']
    subcorp = 'jsi_'
    cmd = 'wordlist' # concordance search
    fout = open(output_dir + 'jsi.all.counts.csv', mode="w")
    fout.write("word,corpus,count\n")
    for corp in corpora:
        params_word_list['corpname']= corp # change corpus for French / italian, etc.
        params_word_list['format']='json'
        corp_fn = params_word_list['corpname'].split('/')
        for n in words:
            
            print("Retrieving wordlist for " + n)
            query_fn = n 
            query_fn = re.sub(r"\'s","", query_fn)
            if re.search(r"&",query_fn):
                print(n, "  contains a &. Skipping")
                continue
            params_word_list['wlpat'] = '(\w+-?){0,2}(' +  n + '|' + n.title() + ')(-?\w+){0,2}' # attention : obligation de lettres avant le formant ici {1,2}
            filename = output_dir + corp_fn[1] + '.' + query_fn + '.' + cmd + '.' + params_word_list['format']
            print(filename)
            if os.path.isfile(filename)==True:
                print("Skipping this word, already retrieved : " + n)
                continue
            time.sleep(5)
            res = query_sketchengine(params_word_list,cmd) # view = concordance, wordlist =  wordlist (here)
            try:
                #print(res)
                if res:	
                        fout.write(n + ','+corp_fn[1]+','+str(res['total'])+ "\n")

                        with open(filename, mode="w", encoding="utf-8") as fin:
                            if params_word_list['format']=='json':
                                json.dump(res,fin, indent=4)
                            elif params_word_list['format'] == 'csv':
                                fin.write(res.text)
                        print("Corpus utilisé : " + corp_fn[1] +  ", Requête :" + n + ", Stockage des résultats dans :" +  filename)
            except Exception as e:
                print("Erreur dans la récupération de la réponse" + ", Message d'erreur : " + str(e))

    fout.close()

def retrieve_contexts(output_dir, corpora, lang,words):
    if os.path.isfile(output_dir + 'allcorpora.allwords.counts.csv'):
        fout = open(output_dir + 'allcorpora.allwords.counts.csv', mode="a")
    else:
        fout = open(output_dir + 'allcorpora.allwords.counts.csv', mode="w")
        fout.write("word,corpus,freq\n")
    for corp in corpora:
        corp_fn = corp.split('/')
        cmd = 'view' # concordance search
        params['corpname']= corp
        #words = ['airbus']
        for n in words:
            print("Retrieving context for " + n)
            filename = output_dir + corp_fn[1] + '.' + n + '.' + cmd + '.' + params['format']
            if os.path.isfile(filename)==True: #  and re.search("&| ", n) is False
                print("Skipping this word, already retrieved : " + n + ':' +filename)
                continue
            # generating query
            query_fn = n.replace("&", " & ")
            if len(n)< 4: # Ace Bic, etc
                query =  'q[word="'+n.title()+'|'+n.upper()+'"|lemma="'+n.title()+'|'+n.upper()+'"]'
                params['q'] = query # la requête
                #params['q'] = [query, 'r10000']  # la requête
            else:
                query_fn = n.replace("&", " & ")
                words = query_fn.split(" ")
                query_elts = ['[lc="'+w.lower()+'"|lemma_lc="'+w.lower()+'"]' if len(w)<4 else '[lc=".*'+w.lower()+'.*"|lemma_lc=".*'+w.lower()+'.*"]' for w in words]
                query = 'q' + ''.join(query_elts)
                #if len(words[0])<4: # M & M's
                #    query =  'q' + ''.join(['[lc="'+w.lower()+'"|lemma_lc="'+w.lower()+'"]' for w in words])
                #else:
                #    query =  'q' + ''.join(['[lc=".*'+w.lower()+'.*"|lemma_lc=".*'+w.lower()+'.*"]' for w in words])

                #params['q'] = [query, 'r10000'] # la requête
                params['q'] = query # la requête
            print("query : ",  params['q'], ' corpus : ', corp_fn[1])
            time.sleep(2)
            res = query_sketchengine(params,cmd) # view = concordance
            #print(res)
            try:
                if res and 'error' in res:
                    print("error in query :" + res['error'] + ". Check and retry!")
                    exit()
                elif res and 'concsize' in res:	
                    fout.write(n + "," + corp_fn[1] + "," + str(res['concsize'])+ "\n")
                    print(n + "," + corp_fn[1] + "," + str(res['concsize'])+ "\n")
                    # retrieve sample of data 
                    if res['concsize']>10000:
                        params['q']=  [query, 'r10000']
                        time.sleep(2)
                        res = query_sketchengine(params,cmd) # view = concordance
                        if res and 'error' in res:
                            print("error in query :" + res['error'] + ". Check and retry!")
                            exit()
                        else:
                            with open(filename, mode="w", encoding="utf-8") as fin:
                                if params['format']=='json':
                                    json.dump(res,fin, indent=4)
                                elif params['format'] == 'csv':
                                    fin.write(res.text)
                            print("Corpus utilisé : " + corp_fn[1] +  ", Requête :" + query + ", Stockage des résultats dans :" +  filename)

                    # not triggered in this app - query by year and month if necessary to retrieve all contexts
                    elif res['concsize']>10000000000:
                        print(res['concsize'], ' => year search')
                        for year in ('2014','2015','2016','2017','2018','2019','2020','2021'):
                            params['q']=  query + 'within <doc (year="' + year + '") />'
                            #params['q']=   'q[lemma_lc="'+query_fn+'"]'
                            filename = output_dir + corp_fn[1] + '.'+ year + '.' + n + '.' + cmd + '.' + params['format']
                            if os.path.isfile(filename)==False:
                                print("Querying " + year + ' corpus')
                                time.sleep(2)
                                res = query_sketchengine(params,cmd)
                                if res:
                                    # if concsize > 10000 search by month
                                    if res['concsize']>10000:
                                        print(res['concsize'], ' => month search')
                                        for month in ('01','02','03','04','05','06','07','08','09','10','11','12'):
                                            filename = output_dir + corp_fn[1] + '.'+ year + '.'+ month + '.' + n + '.' + cmd + '.' + params['format']
                                            params['q']=  query + 'within <doc (month="' + year + '-' + month + '") />'
                                            if os.path.isfile(filename)==False:
                                                time.sleep(2)
                                                res = query_sketchengine(params,cmd)
                                                if res:
                                                    with open(filename, mode="w", encoding="utf-8") as fin:
                                                        if params['format']=='json':
                                                            json.dump(res,fin, indent=4)
                                                        elif params['format'] == 'csv':
                                                            fin.write(res.text)
                                                    print("Corpus utilisé : " + corp_fn[1] +  ", Requête :" + query_fn + ", Stockage des résultats dans :" +  filename)
                                    else:
                                        with open(filename, mode="w", encoding="utf-8") as fin:
                                            if params['format']=='json':
                                                json.dump(res,fin, indent=4)
                                            elif params['format'] == 'csv':
                                                fin.write(res.text)
                                        print("Corpus utilisé : " + corp_fn[1] +  ", Requête :" + query_fn + ", Stockage des résultats dans :" +  filename)

                            else:
                                print(filename + " already retrieved. Skipping.")
                    
                    else:
                        if res['concsize']>0:
                            #print(res['concsize'], ' => overall search')
                            with open(filename, mode="w", encoding="utf-8") as fin:
                                if params['format']=='json':
                                    json.dump(res,fin, indent=4)
                                elif params['format'] == 'csv':
                                    fin.write(res.text)
                            print("Corpus utilisé : " + corp_fn[1] +  ", Requête :" + query + ", Stockage des résultats dans :" +  filename)
                        else:
                            print("No context for this word (query :" + query + '), corpus : ' + corp_fn[1])
                            #continue
            except Exception as e:
                print("Erreur dans la récupération de la réponse" + ", Message d'erreur : " + str(e) )
                print(traceback.print_exc())

    fout.close()

def generate_csv_file(input_dir, output_dir, corpora, lang,words, meta=False):
    for corp in corpora:
        corp_fn = corp.split('/')
        for n in words:
            filename = input_dir + corp_fn[1] + '.' + n + '.' + 'view.json'
            fileout = output_dir + corp_fn[1] + '.' + n + '.csv'
            print("Parsing " + n + ', filename : ' + filename)
            if os.path.isfile(filename) is False:
                print("FIlename (" + filename + ") does not exists, skipping.")
                continue
            if os.path.isfile(fileout):
                print("Already generated file : " + fileout)
                continue
            try:
                data = []
                with open(filename) as f:
                        datatmp = json.loads(f.read())
                # reconstitue records (array of dictionary)
                if len(datatmp['Lines'])==0:
                    continue
                for lines in datatmp['Lines']:
                        res = {}
                        #print(lines['Refs'])
                        #print(lines)
                        if meta == False:
                            res['website']= lines['Refs'][0]
                        else:
                            res['url']= lines['Refs'][0]
                            res['website']= lines['Refs'][1]
                            res['date']= lines['Refs'][2]
                            res['country']= lines['Refs'][3]
                        res['left_context'] = [lines['Left'][i]['str'] for i in range(0,len(lines['Left']))]
                        # Warning mwe Giorgio Armani
                        #print(lines['Kwic'])
                        keyform = "_".join([lines['Kwic'][i]['str'].strip() for i in range(0,len(lines['Kwic']),2)])
                        keypos = "_".join([lines['Kwic'][i]['str'].split('/')[2] for i in range(1,len(lines['Kwic']),2)])
                        keylemma = "_".join([lines['Kwic'][i]['str'].split('/')[1] for i in range(1,len(lines['Kwic']),2)])
                        res['keyword'] = keyform + '/' + keypos + '/' + keylemma
                        #res['keyword'] = " ".join([lines['Kwic'][i]['str'] + lines['Kwic'][i+1]['str'] for i in range(0,len(lines['Kwic'],2))])
                        #res['keyword'] = lines['Kwic'][0]['str'] + lines['Kwic'][1]['str']
                        res['right_context'] = [ lines['Right'][i]['str'] for i in range(0,len(lines['Right']))]
                        res['sentence'] = " ".join(res['left_context'][0::2]) + " " +  lines['Kwic'][0]['str'] +  " ".join(res['right_context'][0::2])
                        #print(lines['Refs'],lines['Left'],lines['Kwic'],lines['Right'])
                        data.append(res)
                print(len(data), " occurrences")
                df = pd.DataFrame(data)
                # cleaning of keyword
                #print(df.keyword.value_counts().head(30))
                #exit()
                df = df[df.keyword.str.match(r"[^\/]+\/[^\/]+\/[^\/]+$", flags=re.I)]
                #print(df.keyword.value_counts().head(30))
                #exit()
                #print(df.right_context.head(10))
                if df.shape[0]> 0:
                    print(df.info())
                    df.to_csv(fileout, index=False)
                else:
                    print('No data for this word. Check :' + filename)
                    continue

            except Exception as e:
                print("Error with this file : " + filename, str(e))
                print(traceback.print_exc())
                continue

def generate_csv_for_ling_exploration(input_dir, output_dir, corpora, lang,words, meta=False):
    for corp in corpora:
        corp_fn = corp.split('/')
        for word in words:
            try:
                filename = input_dir + corp_fn[1] + '.' + word + '.csv'
                fileout = output_dir + corp_fn[1] + '.' + word + '.complete.csv'
                print("Parsing " + word + ', filename : ' + filename)
                if os.path.isfile(filename) is False:
                    print("No csv file for this word "+ word + ' (' + filename  + ')')
                    continue
                if os.path.isfile(fileout) is True:
                    print("Already parsed "+ word + ' (' + fileout  + ')')
                    continue
                df = pd.read_csv(filename)

                # first step : transform list as string to list
                df["left_context"] = df["left_context"].apply(eval)
                df["right_context"] = df["right_context"].apply(eval)

                # raw sentences
                df['sentence'] = df["left_context"].str[0::2].str.join(' ') + ' ' + df['keyword'].str.replace(r"/.+$",'',regex=True) + ' ' +df["right_context"].str[0::2].str.join(' ')
                #df.sentence.value_counts().head(20)

                # Split keyword into word, lemma, pos
                df.keyword.value_counts()
                df[['kw','kw_lemma','kw_pos']] = df.keyword.str.split("/", n=2, expand=True)
                df['kw_lemma'] = df.kw_lemma.str.lower()
                df['kw_pos'] = df.kw_pos.str.lower()
                df['kw'] = df.kw.str.lower()
                df['kw'] = df.kw.str.strip()

                # first extract 5 words on the left and on the right
                ############ left word/lemma/pos
                df['left_w1'] = df['left_context'].str[-2].str.strip()
                df['left_lp1'] = df['left_context'].str[-1].str.strip()
                df[['left_l1','left_p1']] = df['left_lp1'].str.extract(r"^/([^/]+)/(.+)$", expand = True)
                #print(df.left_w1.value_counts().head(20))
                #print(df.left_p1.value_counts().head(20))
                #print(df.left_l1.value_counts().head(20))

                ######### word2
                df['left_w2'] = df['left_context'].str[-4].str.strip()
                df['left_lp2'] = df['left_context'].str[-3].str.strip()
                df[['left_l2','left_p2']] = df['left_lp2'].str.extract(r"^/([^/]+)/(.+)$", expand = True)

                ######### word3
                df['left_w3'] = df['left_context'].str[-6].str.strip()
                df['left_lp3'] = df['left_context'].str[-5].str.strip()
                df[['left_l3','left_p3']] = df['left_lp3'].str.extract(r"^/([^/]+)/(.+)$", expand = True)

                ######### word4
                df['left_w4'] = df['left_context'].str[-8].str.strip()
                df['left_lp4'] = df['left_context'].str[-7].str.strip()
                df[['left_l4','left_p4']] = df['left_lp4'].str.extract(r"^/([^/]+)/(.+)$", expand = True)

                ######### word5
                df['left_w5'] = df['left_context'].str[-10].str.strip()
                df['left_lp5'] = df['left_context'].str[-9].str.strip()
                df[['left_l5','left_p5']] = df['left_lp5'].str.extract(r"^/([^/]+)/(.+)$", expand = True)

                #print(df.left_w1.value_counts().head(20))

                # the same with right context
                # first extract 5 words on the right and on the right

                ############ right word/lemma/pos
                df['right_w1'] = df['right_context'].str[0].str.strip()
                df['right_lp1'] = df['right_context'].str[1].str.strip()
                df[['right_l1','right_p1']] = df['right_lp1'].str.extract(r"^/([^/]+)/(.+)$", expand = True)
                #print(df.right_w1.value_counts().head(20))
                #print(df.right_p1.value_counts().head(20))
                #print(df.right_l1.value_counts().head(20))

                ######### word2
                df['right_w2'] = df['right_context'].str[2].str.strip()
                df['right_lp2'] = df['right_context'].str[3].str.strip()
                df[['right_l2','right_p2']] = df['right_lp2'].str.extract(r"^/([^/]+)/(.+)$", expand = True)

                ######### word3
                df['right_w3'] = df['right_context'].str[4].str.strip()
                df['right_lp3'] = df['right_context'].str[5].str.strip()
                df[['right_l3','right_p3']] = df['right_lp3'].str.extract(r"^/([^/]+)/(.+)$", expand = True)

                ######### word4
                df['right_w4'] = df['right_context'].str[6].str.strip()
                df['right_lp4'] = df['right_context'].str[7].str.strip()
                df[['right_l4','right_p4']] = df['right_lp4'].str.extract(r"^/([^/]+)/(.+)$", expand = True)

                ######### word5
                df['right_w5'] = df['right_context'].str[8].str.strip()
                df['right_lp5'] = df['right_context'].str[9].str.strip()
                df[['right_l5','right_p5']] = df['right_lp5'].str.extract(r"^/([^/]+)/(.+)$", expand = True)


                reduce_pos = {'PRO:REL':'PRON', 'VER:pres':'VERB', 'VER:infi':'VERB', 
                                '/t.co/MAyG3BjTxL/NOM':None, 'VER:subp':'VERB', 'PRO':'PRON', 'PRP':'ADP', 
                                'PRO:IND':'PRON', 'VER:simp':'VERB', 'KON':'CONJ', 'PRO:PER':'PRON', 'VER:ppre':'VERB', 
                                'NAM':'PROPN', 'DET:ART':'DET', 'VER:pper':'VERB', 'DET:POS':'DET', 'VER:futu':'VERB', 
                                'NOM':'NOUN',  'PUN':'PUNCT', 'activate/NOM':None, 'VER:cond':'VERB', 
                                'PRP:det':'ADP DET', 'SENT':'PUNCT', 'NUM':'ADJ', 'PUN:cit':'PUNCT', 
                                '/t.co/N6wgBy0v9c/NOM':None, 'PRO:DEM':'PRON', 'VER:impf':'VERB'}
                df['left_p1'] = df['left_p1'].replace(reduce_pos)
                df['left_p2'] = df['left_p2'].replace(reduce_pos)
                df['left_p3'] = df['left_p3'].replace(reduce_pos)
                df['left_p4'] = df['left_p4'].replace(reduce_pos)
                df['left_p5'] = df['left_p5'].replace(reduce_pos)
                df['left_p5'] = df['left_p5'].replace(reduce_pos)
                df['right_p5'] = df['right_p5'].replace(reduce_pos)
                df['right_p4'] = df['right_p4'].replace(reduce_pos)
                df['right_p3'] = df['right_p3'].replace(reduce_pos)
                df['right_p2'] = df['right_p2'].replace(reduce_pos)
                df['right_p1'] = df['right_p1'].replace(reduce_pos)

                if meta==True:
                    df['datetime'] = pd.to_datetime(df['date'], infer_datetime_format=True)
                    df['year'] = df['datetime'].dt.strftime('%Y')
                    df['10years'] = df['datetime'].apply(lambda x: (x.year//10)*10)#dt.to_period("10Y")

                df['pattern_around5'] = df['left_p2'] + ' ' +df['left_p1'] + ' ' + word + ' ' + df['right_p1'] + ' ' + df['right_p2']
                df['pattern_around3'] = df['left_p1'] +  ' ' + word + ' '  + df['right_p1']
                df['pattern_left2'] = df['left_p2'] + ' ' + df['left_p1']+ ' ' + word
                df['pattern_left3'] = df['left_p3'] + ' ' + df['left_p2'] + ' ' + df['left_p1']+ ' ' + word 
                df['pattern_left4'] = df['left_p4'] + ' ' +df['left_p3'] + ' ' + df['left_p2'] + ' ' + df['left_p1']+ ' ' + word 
                df['pattern_right2'] = word + ' ' +  df['right_p1'] + ' ' + df['right_p2']
                df['pattern_right3'] = word + ' ' +  df['right_p1'] + ' ' + df['right_p2'] + ' ' + df['right_p3']
                df['pattern_right4'] = word + ' ' +  df['right_p1'] + ' ' + df['right_p2'] + ' ' + df['right_p3']+ ' ' + df['right_p4']

                    ########### et les patrons lexicaux correspondants

                df['pattern_around5_lex'] = df['left_l2'] + ' ' +df['left_l1'] + ' ' + word + ' ' + df['right_l1'] + ' ' + df['right_l2']
                df['pattern_around3_lex'] = df['left_l1'] +  ' ' + word + ' '  + df['right_l1']
                df['pattern_left2_lex'] = df['left_l2'] + ' ' + df['left_l1']+ ' ' + word
                df['pattern_left3_lex'] = df['left_l3'] + ' ' + df['left_l2'] + ' ' + df['left_l1']+ ' ' + word 
                df['pattern_left4_lex'] = df['left_l4'] + ' ' +df['left_l3'] + ' ' + df['left_l2'] + ' ' + df['left_l1']+ ' ' + word 
                df['pattern_right2_lex'] = word + ' ' +  df['right_l1'] + ' ' + df['right_l2']
                df['pattern_right3_lex'] = word + ' ' +  df['right_l1'] + ' ' + df['right_l2'] + ' ' + df['right_l3']
                df['pattern_right4_lex'] = word + ' ' +  df['right_l1'] + ' ' + df['right_l2'] + ' ' + df['right_l3']+ ' ' + df['right_l4']


                df.drop(columns=['left_context','right_context'], inplace=True)
                df = df.loc[:,~df.columns.str.contains('_lp')]
                # save to csv fo exploration
                df.info()
                df.to_csv(fileout, index=False)
            except Exception as e:
                print("error while parsing file / transforming :"  + filename)
                print(traceback.print_exc())
                continue

def metadata_analysis(output_dir, corpora, lang,words):
    for corpus in corpora:
        corp_fn = corpus.split('/')
        # first load corpora info
        with open(output_dir + corp_fn[1] + '.info.json', mode='rb') as corp:
            res = json.loads(corp.read())
            corp_size = res['sizes']['tokencount']

        for n in words:
            with PdfPages(output_dir + corp_fn[1]  + '.' + n + '.pdf') as pdf1:
                inputfile = output_dir + corp_fn[1] + '.' + n + '.csv'
                if os.path.isfile(inputfile) is False:
                    print("No file for this word : " + n + ', filename : ' + inputfile)
                    continue
                df = pd.read_csv(inputfile)
                if df.shape[0]> 0:
                    df['count'] = 1
                    df['datetime'] = pd.to_datetime(df['date'], infer_datetime_format=True)
                    df['year'] = df['datetime'].dt.strftime('%Y')
                    df['month'] = df['datetime'].dt.strftime('%m')
                    df['year-month'] = df['datetime'].dt.strftime('%Y-%m')
                    #df['keyword'] = n + '/' + n + '/NOM'
                    print(df.info())
                    df2 = df.set_index('datetime')

                    ################# whole period
                    fig, ax = plt.subplots()
                    weekgrp = df2.groupby(pd.Grouper(freq='M')).count()
                    #yeargrproll = yeargrp
                    #print(yeargrp)
                    weekgrp['url'].plot(linewidth=0.5, ax=ax, marker='.', linestyle='-',label='par mois')
                    weekgrp.rolling(3, center=True).mean()['url'].plot(linewidth=2.0, ax=ax, linestyle='-',label='rolling mean (3 months)')
                    ax.set_title("Evolution sur toute la période")
                    ax.legend()
                    pdf1.savefig()  # saves the current figure into a pdf page
                    plt.close()
                    
                    
                    ################# per year subplots
                    fig, axes = plt.subplots(nrows=4, ncols=2, figsize=(15,10))
                    i = 0
                    j = 0
                    for year in range(2014,2021):
                        weekgrp.loc[str(year)]['url'].plot(linewidth=0.5, title=str(year),ax=axes[i][j], label='par mois')
                        weekgrp.rolling(3, center=True).mean().loc[str(year)]['url'].plot(linewidth=2, title=str(year),ax=axes[i][j], label="rolling mean (3)")
                        axes[i][j].legend()
                        if j == 1:
                            i = i + 1
                            j = 0
                        else :
                            j = j + 1
                    plt.tight_layout()
                    pdf1.savefig()  # saves the current figure into a pdf page
                    plt.close()
                    
                    ################### ditribution and evolution year country
                    fig, ax = plt.subplots(nrows=2, ncols=1, figsize=(20,10))
                    countries = df[df.country != '===NONE==='].country.value_counts().head(10).index.to_list()
                    df[df.country != '===NONE==='].country.value_counts().head(15).plot(kind="barh",ax=ax[0], title="distribution globale par pays")
                    # annoataion guide : https://robertmitchellv.com/blog-bar-chart-annotations-pandas-mpl.html
                    # set individual bar lables using above list
                    for i in ax[0].patches:
                        # get_width pulls left or right; get_y pushes up or down
                        ax[0].text(i.get_width()+.1, i.get_y()+.31, \
                        str(round((i.get_width()), 2)), fontsize=10, color='dimgrey')

                    # invert for largest on top 
                    ax[0].invert_yaxis()
                    
                    dftmp = df[df.country.isin(countries)]
                    tablecnt2  = pd.crosstab(values=dftmp['url'], index=dftmp['year'],
                            columns=dftmp['country'], aggfunc=len, normalize='index')
                    #print(tablecnt2)
                    
                    tablecnt2.plot(ax=ax[1] ,kind="bar", stacked=True, title="Evolution par pays d'origine")
                    pdf1.savefig()  # saves the current figure into a pdf page
                    plt.close()

                    ################### ditribution and evolution year website
                    fig, ax = plt.subplots(nrows=2, ncols=1, figsize=(20,10))
                    websites = df.website.value_counts().head(20).index.to_list()
                    df.website.value_counts().head(20).plot(kind="barh",ax=ax[0], title="distribution globale par site web")
                    # annoataion guide : https://robertmitchellv.com/blog-bar-chart-annotations-pandas-mpl.html
                    # set individual bar lables using above list
                    for i in ax[0].patches:
                        # get_width pulls left or right; get_y pushes up or down
                        ax[0].text(i.get_width()+.1, i.get_y()+.31, \
                        str(round((i.get_width()), 2)), fontsize=10, color='dimgrey')

                    # invert for largest on top 
                    ax[0].invert_yaxis()
                    
                    dftmp = df[df.website.isin(websites)]
                    tablecnt2  = pd.crosstab(values=dftmp['url'], index=dftmp['year'],
                            columns=dftmp['website'], aggfunc=len, normalize='index')
                    #print(tablecnt2)
                    
                    tablecnt2.plot(ax=ax[1] ,kind="bar", stacked=True, title="Evolution par site web d'origine")
                    pdf1.savefig()  # saves the current figure into a pdf page
                    plt.close()

                    ################### ditribution and evolution year website (per top-ten countries)
                    for cnt in countries:
                        fig, ax = plt.subplots(nrows=2, ncols=1, figsize=(20,10))
                        websites = df[df.country==cnt].website.value_counts().head(20).index.to_list()
                        df[df.country==cnt].website.value_counts().head(20).plot(kind="barh",ax=ax[0], title="distribution globale par site web (pays:" + cnt + ')')
                        # annoataion guide : https://robertmitchellv.com/blog-bar-chart-annotations-pandas-mpl.html
                        # set individual bar lables using above list
                        for i in ax[0].patches:
                            # get_width pulls left or right; get_y pushes up or down
                            ax[0].text(i.get_width()+.1, i.get_y()+.31, \
                            str(round((i.get_width()), 2)), fontsize=10, color='dimgrey')

                        # invert for largest on top 
                        ax[0].invert_yaxis()
                    
                        dftmp = df[(df.website.isin(websites)) & (df.country==cnt)]
                        tablecnt2  = pd.crosstab(values=dftmp['url'], index=dftmp['year'],
                                columns=dftmp['website'], aggfunc=len, normalize='index')
                        #print(tablecnt2)
                    
                        tablecnt2.plot(ax=ax[1] ,kind="bar", stacked=True, title="Evolution par site web d'origine (pays : " + cnt + ')')
                        pdf1.savefig()  # saves the current figure into a pdf page
                        plt.close()


def exploration_analysis(input_dir, output_dir, corpora, lang,words, meta=False):
    for corpus in corpora:
        corp_fn = corpus.split('/')
        # first load corpora info
        with open(output_dir + corp_fn[1] + '.info.json', mode='rb') as corp:
            res = json.loads(corp.read())
            corp_size = res['sizes']['tokencount']

        for word in words:
            with PdfPages(output_dir + corp_fn[1]  + '.' + word + '.exploration.pdf') as pdf1:
                inputfile = input_dir + corp_fn[1] + '.' + word + '.complete.csv'
                if os.path.isfile(inputfile) is False:
                    print("No file for this word : " + word + ', filename : ' + inputfile)
                    continue
                df = pd.read_csv(inputfile)
                # cleaning

                # distribution mot-clé, lemme, pos
                fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(10,10),constrained_layout=True)
                fig.suptitle("Distribution des formes, lemmes et pos pour le mot clé : " + word + ')', fontsize=16)
                df.kw.value_counts().head(10).plot(kind="barh", title='forme', ax=axes[0])
                df.kw_lemma.value_counts().plot(kind="barh", title='lemme', ax=axes[1])
                df.kw_pos.value_counts().plot(kind="barh", title='partie du discours', ax=axes[2])

                pdf1.savefig()  # saves the current figure into a pdf page
                plt.close()
          
                # evolution sur la période (pos)
                if meta:
                    crosstab  = pd.crosstab( columns=df['year'],index=df['kw_pos'],values=df['url'], aggfunc=len, normalize='columns') 

                    sns.set(rc={'figure.figsize':(10,10)})
                    fig, ax = plt.subplots()
                    sns.heatmap(crosstab, cmap="YlGnBu", annot=True, cbar=True,fmt='.2%')
                    ax.set_title("Evolution des informations de partie du discours du mot clé : " + word)
                    pdf1.savefig()  # saves the current figure into a pdf page
                    plt.close()

                    # evolution sur la période (formes)

                    crosstab  = pd.crosstab( columns=df['year'],index=df['kw'],values=df['url'], aggfunc=len, normalize='columns') 

                    sns.set(rc={'figure.figsize':(10,10)})
                    fig, ax = plt.subplots()
                    sns.heatmap(crosstab, cmap="YlGnBu", annot=True, cbar=True,fmt='.2%')
                    ax.set_title("Evolution des formes du mot clé")
                    pdf1.savefig()  # saves the current figure into a pdf page
                    plt.close()

                fig, axes = plt.subplots(nrows=3, ncols=4, figsize=(20,20),constrained_layout=True)
                fig.suptitle("Distribution des patrons syntaxiques (" + word + ')', fontsize=16)
                df.pattern_around5.value_counts().head(10).plot(kind="barh", title='Pattern : W X word Y Z ',  ax=axes[0][0])
                df.pattern_around3.value_counts().head(10).plot(kind="barh", title='Pattern : X word Y', ax=axes[0][1])
                df.pattern_left4.value_counts().head(10).plot(kind="barh", title='Pattern : W X Y Z word',  ax=axes[1][0])
                df.pattern_left3.value_counts().head(10).plot(kind="barh", title='Pattern : X Y Z word',  ax=axes[1][1])
                df.pattern_left2.value_counts().head(10).plot(kind="barh", title='Pattern : X Y word', ax=axes[1][2])
                df.left_p1.value_counts().head(10).plot(kind="barh", title='Pattern : X word', ax=axes[1][3])
                df.pattern_right4.value_counts().head(10).plot(kind="barh", title='Pattern : word W X Y Z',  ax=axes[2][0])
                df.pattern_right3.value_counts().head(10).plot(kind="barh", title='Pattern : word X Y Z',  ax=axes[2][1])
                df.pattern_right2.value_counts().head(10).plot(kind="barh", title='Pattern : word X Y', ax=axes[2][2])
                df.right_p1.value_counts().head(10).plot(kind="barh", title='Pattern : word X', ax=axes[2][3])
                pdf1.savefig()  # saves the current figure into a pdf page
                plt.close()

                # équivalents lexicaux (lemmes)
                fig, axes = plt.subplots(nrows=3, ncols=4, figsize=(20,20),constrained_layout=True)
                fig.suptitle("Distribution des patrons syntaxiques (" + word + ')', fontsize=16)
                df.pattern_around5_lex.value_counts().head(10).plot(kind="barh", title='Pattern : W X word Y Z ',  ax=axes[0][0])
                df.pattern_around3_lex.value_counts().head(10).plot(kind="barh", title='Pattern : X word Y', ax=axes[0][1])
                df.pattern_left4_lex.value_counts().head(10).plot(kind="barh", title='Pattern : W X Y Z word',  ax=axes[1][0])
                df.pattern_left3_lex.value_counts().head(10).plot(kind="barh", title='Pattern : X Y Z word',  ax=axes[1][1])
                df.pattern_left2_lex.value_counts().head(10).plot(kind="barh", title='Pattern : X Y word', ax=axes[1][2])
                df.left_l1.value_counts().head(10).plot(kind="barh", title='Pattern : X word', ax=axes[1][3])
                df.pattern_right4_lex.value_counts().head(10).plot(kind="barh", title='Pattern : word W X Y Z',  ax=axes[2][0])
                df.pattern_right3_lex.value_counts().head(10).plot(kind="barh", title='Pattern : word X Y Z',  ax=axes[2][1])
                df.pattern_right2_lex.value_counts().head(10).plot(kind="barh", title='Pattern : word X Y', ax=axes[2][2])
                df.right_l1.value_counts().head(10).plot(kind="barh", title='Pattern : word X', ax=axes[2][3])
                pdf1.savefig()  # saves the current figure into a pdf page
                plt.close()

                #patterns = ['pattern_around5','pattern_around3','pattern_left3','pattern_left2','pattern_right3','pattern_right2']
                #df['datetime'] = pd.to_datetime(df['date'], infer_datetime_format=True)
                #df['year'] = df['datetime'].dt.strftime('%Y')
                #df['10years'] = df['datetime'].apply(lambda x: (x.year//10)*10)#dt.to_period("10Y")


                if meta:
                    fig, axes = plt.subplots(nrows=3, ncols=3, figsize=(30,30),constrained_layout=True)
                    fig.suptitle("Evolution de la distribution des patrons syntaxiques (" + word + ')', fontsize=16)
                    ######### pattern_around5
                    patterns = df.pattern_around5.value_counts().head(10).index.to_list()
                    dftmp = df[df.pattern_around5.isin(patterns)]
                    crosstab  = pd.crosstab( columns=dftmp['year'],index=dftmp['pattern_around5'],values=dftmp['keyword'], aggfunc=len, normalize='columns') 
                    #sns.set(rc={'figure.figsize':(20,20)})
                    ax = sns.heatmap(crosstab, cmap="YlGnBu", annot=True, cbar=True,fmt='.2%', ax=axes[0][0])
                    ax.set_title("Evolution des 10 patrons W X word Y Z")

                    ######### pattern_around3
                    patterns = df.pattern_around3.value_counts().head(10).index.to_list()
                    dftmp = df[df.pattern_around3.isin(patterns)]
                    crosstab  = pd.crosstab( columns=dftmp['year'],index=dftmp['pattern_around3'],values=dftmp['keyword'], aggfunc=len, normalize='columns') 
                    #sns.set(rc={'figure.figsize':(20,20)})
                    ax = sns.heatmap(crosstab, cmap="YlGnBu", annot=True, cbar=True,fmt='.2%', ax=axes[0][1])
                    ax.set_title("Evolution des 10 patrons X word Y")

                    ######### pattern_left3
                    patterns = df.pattern_left3.value_counts().head(10).index.to_list()
                    dftmp = df[df.pattern_left3.isin(patterns)]
                    crosstab  = pd.crosstab( columns=dftmp['year'],index=dftmp['pattern_left3'],values=dftmp['keyword'], aggfunc=len, normalize='columns') 
                    #sns.set(rc={'figure.figsize':(20,20)})
                    ax = sns.heatmap(crosstab, cmap="YlGnBu", annot=True, cbar=True,fmt='.2%', ax=axes[1][0])
                    ax.set_title("Evolution des 10 patrons principaux X Y Z word")


                    ######### pattern_left2
                    patterns = df.pattern_left2.value_counts().head(10).index.to_list()
                    dftmp = df[df.pattern_left2.isin(patterns)]
                    crosstab  = pd.crosstab( columns=dftmp['year'],index=dftmp['pattern_left2'],values=dftmp['keyword'], aggfunc=len, normalize='columns') 
                    #sns.set(rc={'figure.figsize':(20,20)})
                    ax = sns.heatmap(crosstab, cmap="YlGnBu", annot=True, cbar=True,fmt='.2%', ax=axes[1][1])
                    ax.set_title("Evolution des 10 patrons principaux X Y word")

                    ######### pattern_left1
                    patterns = df.left_p1.value_counts().head(10).index.to_list()
                    dftmp = df[df.left_p1.isin(patterns)]
                    crosstab  = pd.crosstab( columns=dftmp['year'],index=dftmp['left_p1'],values=dftmp['keyword'], aggfunc=len, normalize='columns') 
                    #sns.set(rc={'figure.figsize':(20,20)})
                    ax = sns.heatmap(crosstab, cmap="YlGnBu", annot=True, cbar=True,fmt='.2%', ax=axes[1][2])
                    ax.set_title("Evolution des 10 patrons principaux X word")

                    ######### pattern_right3
                    patterns = df.pattern_right3.value_counts().head(10).index.to_list()
                    dftmp = df[df.pattern_right3.isin(patterns)]
                    crosstab  = pd.crosstab( columns=dftmp['year'],index=dftmp['pattern_right3'],values=dftmp['keyword'], aggfunc=len, normalize='columns') 
                    #sns.set(rc={'figure.figsize':(20,20)})
                    ax = sns.heatmap(crosstab, cmap="YlGnBu", annot=True, cbar=True,fmt='.2%', ax=axes[2][0])
                    ax.set_title("Evolution des 10 patrons principaux word X Y Z")


                    ######### pattern_right2
                    patterns = df.pattern_right2.value_counts().head(10).index.to_list()
                    dftmp = df[df.pattern_right2.isin(patterns)]
                    crosstab  = pd.crosstab( columns=dftmp['year'],index=dftmp['pattern_right2'],values=dftmp['keyword'], aggfunc=len, normalize='columns') 
                    #sns.set(rc={'figure.figsize':(20,20)})
                    ax = sns.heatmap(crosstab, cmap="YlGnBu", annot=True, cbar=True,fmt='.2%', ax=axes[2][1])
                    ax.set_title("Evolution des 10 patrons principaux word X Y")

                    ######### pattern_right1
                    patterns = df.right_p1.value_counts().head(10).index.to_list()
                    dftmp = df[df.right_p1.isin(patterns)]
                    crosstab  = pd.crosstab( columns=dftmp['year'],index=dftmp['right_p1'],values=dftmp['keyword'], aggfunc=len, normalize='columns') 
                    #sns.set(rc={'figure.figsize':(20,20)})
                    ax = sns.heatmap(crosstab, cmap="YlGnBu", annot=True, cbar=True,fmt='.2%', ax=axes[2][2])
                    ax.set_title("Evolution des 10 patrons principaux word X")

                    pdf1.savefig()  # saves the current figure into a pdf page
                    plt.close()


                # pemier mot à guche par partie du discours
                #word='glaner'
                poslist = df.left_p1.value_counts().head(16).index.to_list()


                dftmp = df
                fig, axes = plt.subplots(nrows=4, ncols=4, figsize=(20,20),constrained_layout=True)
                fig.suptitle("30 Lexèmes les plus fréquents selon la partie du discours (premier mot à gauche de " + word + ')', fontsize=16)
                i = 0
                j = 0
                for pos in poslist:
                    dftmp[dftmp.left_p1==pos].left_l1.value_counts().head(30).plot(kind="barh", title=pos, ax=axes[i][j])
                    if j == 3:
                        i = i + 1
                        j = 0
                    else :
                        j = j + 1
                pdf1.savefig()  # saves the current figure into a pdf page
                plt.close()

                # second mot à gauche
                poslist = df.left_p2.value_counts().head(16).index.to_list()


                dftmp = df
                fig, axes = plt.subplots(nrows=4, ncols=4, figsize=(20,20),constrained_layout=True)
                fig.suptitle("30 Lexèmes les plus fréquents selon la partie du discours (second mot à gauche de " + word + ')', fontsize=16)
                i = 0
                j = 0
                for pos in poslist:
                    dftmp[dftmp.left_p2==pos].left_l2.value_counts().head(30).plot(kind="barh", title=pos, ax=axes[i][j])
                    if j == 3:
                        i = i + 1
                        j = 0
                    else :
                        j = j + 1
                pdf1.savefig()  # saves the current figure into a pdf page
                plt.close()




                # pemier mot à droite par partie du discours
                #word='glaner'
                poslist = df.right_p1.value_counts().head(16).index.to_list()


                dftmp = df
                fig, axes = plt.subplots(nrows=4, ncols=4, figsize=(20,20),constrained_layout=True)
                fig.suptitle("30 Lexèmes les plus fréquents selon la partie du discours (premier mot à droite de " + word + ')', fontsize=16)
                i = 0
                j = 0
                for pos in poslist:
                    dftmp[dftmp.right_p1==pos].right_l1.value_counts().head(30).plot(kind="barh", title=pos, ax=axes[i][j])
                    if j == 3:
                        i = i + 1
                        j = 0
                    else :
                        j = j + 1
                pdf1.savefig()  # saves the current figure into a pdf page
                plt.close()

                # second mot à droite
                poslist = df.right_p2.value_counts().head(16).index.to_list()


                dftmp = df
                fig, axes = plt.subplots(nrows=4, ncols=4, figsize=(20,20),constrained_layout=True)
                fig.suptitle("30 Lexèmes les plus fréquents selon la partie du discours (second mot à droite de " + word + ')', fontsize=16)
                i = 0
                j = 0
                for pos in poslist:
                    dftmp[dftmp.right_p2==pos].right_l2.value_counts().head(30).plot(kind="barh", title=pos, ax=axes[i][j])
                    if j == 3:
                        i = i + 1
                        j = 0
                    else :
                        j = j + 1
                pdf1.savefig()  # saves the current figure into a pdf page
                plt.close()

def overall_analysis(filename):
    try:
        df = pd.read_csv(filename)
        print(df.info())
        df.drop_duplicates(inplace=True)
        df.drop_duplicates(subset='word', keep="last", inplace=True)
        print(df.info())
        print(df.groupby(['word','corpus'])['freq'].sum())
    except Exception as e:
        print("error while opening/parsing file : " + filename + ', error :' + str(e))
        print(traceback.print_exc())


def load_words(wordfiles):
    words = {}
    for fn in wordfiles:
        for line in open(fn):
            word = line.strip()#.lower()
            words[word]=1
    return list(words.keys())


###################################################### main

# load words from file
lang='fr'
inputdir = "./words/"
wordfiles = glob(inputdir+'*.txt')
words = load_words(wordfiles)
#words=['sopalin']
#print(words, len(words))

corpora =  ['preloaded/fra_jsi_newsfeed_virt','preloaded/spa_jsi_newsfeed_virt']

# wordlists (obsolete)
#outputroot= './data/'
#output_dir = './data/jsi_wordlists/'
#os.makedirs(output_dir, exist_ok=True)
#retrieve_wordlist(output_dir, corpora, lang,words)


# contexts
outputroot= './data/'
output_dir = './data/jsi_contexts/'
os.makedirs(output_dir, exist_ok=True)
# as a lot of data will be retrieved, please be careful to your disk capacity!
input_dir = output_dir
#input_dir = '/Volumes/Transcend/natalia/'
os.makedirs(input_dir, exist_ok=True)
meta = True # to get metadata (default false)

# corpus info
for corpname in corpora:
    corp_fn = corpname.split('/')
    fileout = output_dir + corp_fn[1] + '.info.json'
    if os.path.isfile(fileout) is False:
        res = corpus_info(corpname)
        if res:
            # sauvegarde dans fichier json dans l'environnnement
            with open(fileout, mode="w", encoding="utf-8") as fin:
                json.dump(res,fin, indent=4)
            print("Réponse enregistrée dans : " + output_dir +  corp_fn[1] + '.info.json')

# overall analysis
filename_glob = input_dir + 'allcorpora.allwords.counts.csv'
# uncomment to get an overall analyis
#overall_analysis(filename_glob)
s

#retrieve_contexts(input_dir, corpora, lang,words) from SketchEngines
generate_csv_file(input_dir, input_dir, corpora, lang,words, meta)
if meta == True:
    metadata_analysis(output_dir, corpora, lang,words)
generate_csv_for_ling_exploration(input_dir,input_dir, corpora, lang,words, meta)
# if you would like to generate a pdf file for each word with all visualizations, remove the exit() command
exit()
exploration_analysis(output_dir, output_dir, corpora, lang,words, meta)