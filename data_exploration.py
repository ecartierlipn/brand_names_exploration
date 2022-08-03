#import msilib
import streamlit as st
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_agg import RendererAgg
from matplotlib.backends.backend_pdf import PdfPages

#matplotlib.use("agg")
_lock = RendererAgg.lock
import numpy as np
import re, os, sys, math,base64
import traceback
import pickle
from datetime import datetime
from glob import glob
from st_aggrid import AgGrid, JsCode,DataReturnMode,GridUpdateMode
from st_aggrid.grid_options_builder import GridOptionsBuilder

import streamlit.components.v1 as components

def show_pdf(file_path):
    with open(file_path,"rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def generate_pdf_file(word, corpus,inputdir, outputdir,meta):
    try:
        outputfile = outputdir + corpus  + '.' + word + '.pdf'
        with PdfPages(outputfile) as pdf1:
            # metadata
            d = pdf1.infodict()
            d['Title'] = "Report on : "+ word + " from JSI Timestamped corpus : "  + corpus       
            d['Author'] = 'Emmanuel Cartier, emmanuel.cartier@lipn.univ-paris13.fr'
            d['CreationDate'] = datetime.today()    
            
            # first page of report
            firstPage = plt.figure(figsize=(15,15))
            firstPage.clf()
            maintitle = 'Report on\nword :' + word + '\ncorpus : ' + corpus
            description = '''\nThis report was built by querying the JSI Timestamped we corpus with SkechEngine API and retrieving contexts and metadata of occurrences from 2014 to 2021. The report contains aggregations on metadata (year, country, websites) and lexico-syntaxic patterns\n'''
            metadata = 'Linguistic data (words) : Natalia Soler, natalia.soler@lattice.fr\nSoftware and quantitative analysis : Emmanuel Cartier, emmanuel.cartier@lipn.univ-paris13.fr\n' + str(datetime.today().strftime("%d-%b-%Y"))
            firstPage.text(0.5,0.7,maintitle, bbox=dict(boxstyle="round,pad=1",facecolor='#63A1DF', alpha=0.2, edgecolor='black'), size=34, ha="center")
            firstPage.text(0.05,0.3,description,bbox=dict(boxstyle="round,pad=1",facecolor='#63A1DF', alpha=0.2, edgecolor='black'),  size=16, ha="left", wrap=True) #transform=firstPage.transFigure,
            firstPage.text(0.5,0.1,metadata,bbox=dict(boxstyle="round,pad=1",facecolor='#63A1DF', alpha=0.2, edgecolor='black'),  size=14, ha="center") #transform=firstPage.transFigure,
            
            pdf1.savefig()
            plt.close()


            inputfile = inputdir +corpus + '.' + word + '.complete.csv'
            if os.path.isfile(inputfile) is False:
                message = "No file for this word : " + word + ', filename : ' + inputfile
                print(message)
                #exit()
                #return message
            df = pd.read_csv(inputfile)
            if df.shape[0]> 0:
                        # clean
                        df = df[~df.kw.str.contains(r"[\W-]", re.I)]
                        df['count'] = 1
                        df['datetime'] = pd.to_datetime(df['date'], infer_datetime_format=True)
                        df['year'] = df['datetime'].dt.strftime('%Y')
                        df['month'] = df['datetime'].dt.strftime('%m')
                        df['year-month'] = df['datetime'].dt.strftime('%Y-%m')
                        #df['keyword'] = n + '/' + n + '/NOM'
                        print(df.info())
                        df2 = df.set_index('datetime')
                        years = sorted(list(df['year'].unique()))

                        ################# whole period
                        fig, ax = plt.subplots( figsize=(15,10))
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
                        for year in years:
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

                        # cleaning

                        # distribution mot-clé, lemme, pos
                        fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(10,10),constrained_layout=True)
                        fig.suptitle("Distribution des formes, lemmes et pos pour le mot clé : " + word + ')', fontsize=14)
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
        
        return (True, True)
    except Exception as e:
        msg = "error while generating pdf file ("+ outputfile + '), error : ' + str(e) + ', error details : '# + traceback.print_exception()
        print(msg)
        return (False, msg)



# functions to plot info on given word
def plot_contexts_info(df, meta=False):
                #df = pd.read_csv(filename)
                # cleaning

                # distribution mot-clé, lemme, pos
                fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(10,10),constrained_layout=True)
                fig.suptitle("Distribution des formes, lemmes et pos pour le mot clé : " + word + ')', fontsize=16)
                df.kw.value_counts().head(10).plot(kind="barh", title='forme', ax=axes[0])
                df.kw_lemma.value_counts().plot(kind="barh", title='lemme', ax=axes[1])
                df.kw_pos.value_counts().plot(kind="barh", title='partie du discours', ax=axes[2])
                st.pyplot(fig,clear_figure=True)
          
                # evolution sur la période (pos)
                if meta:
                    crosstab  = pd.crosstab( columns=df['year'],index=df['kw_pos'],values=df['url'], aggfunc=len, normalize='columns') 

                    sns.set(rc={'figure.figsize':(10,10)})
                    fig, ax = plt.subplots()
                    sns.heatmap(crosstab, cmap="YlGnBu", annot=True, cbar=True,fmt='.2%')
                    ax.set_title("Evolution des informations de partie du discours du mot clé : " + word)
                    st.pyplot(fig,clear_figure=True)

                    # evolution sur la période (formes)
                    crosstab  = pd.crosstab( columns=df['year'],index=df['kw'],values=df['url'], aggfunc=len, normalize='columns') 
                    sns.set(rc={'figure.figsize':(10,10)})
                    fig, ax = plt.subplots()
                    sns.heatmap(crosstab, cmap="YlGnBu", annot=True, cbar=True,fmt='.2%')
                    ax.set_title("Evolution des formes du mot clé")
                    st.pyplot(fig,clear_figure=True)
                
                # patron syntaxiques
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
                st.pyplot(fig,clear_figure=True)

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
                st.pyplot(fig,clear_figure=True)

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

                    st.pyplot(fig,clear_figure=True)


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
                st.pyplot(fig,clear_figure=True)

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
                st.pyplot(fig,clear_figure=True)




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
                st.pyplot(fig,clear_figure=True)

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
                st.pyplot(fig,clear_figure=True)

def plot_meta_info(df):
                #df = pd.read_csv(inputfile)
                if df.shape[0]> 0:
                    df['count'] = 1
                    df['datetime'] = pd.to_datetime(df['date'], infer_datetime_format=True)
                    df['year'] = df['datetime'].dt.strftime('%Y')
                    df['month'] = df['datetime'].dt.strftime('%m')
                    df['year-month'] = df['datetime'].dt.strftime('%Y-%m')
                    #df['keyword'] = n + '/' + n + '/NOM'
                    print(df.info())
                    df2 = df.set_index('datetime')
                    years = sorted(list(df['year'].unique()))

                    ################# whole period
                    fig, ax = plt.subplots()
                    weekgrp = df2.groupby(pd.Grouper(freq='M')).count()
                    #yeargrproll = yeargrp
                    #print(yeargrp)
                    weekgrp['url'].plot(linewidth=0.5, ax=ax, marker='.', linestyle='-',label='par mois')
                    weekgrp.rolling(3, center=True).mean()['url'].plot(linewidth=2.0, ax=ax, linestyle='-',label='rolling mean (3 months)')
                    ax.set_title("Evolution sur toute la période")
                    ax.legend()
                    st.pyplot(fig,clear_figure=True)                    
                    
                    ################# per year subplots
                    fig, axes = plt.subplots(nrows=4, ncols=2, figsize=(15,10))
                    i = 0
                    j = 0
                    for year in years: #range(2014,2021)
                        weekgrp.loc[str(year)]['url'].plot(linewidth=0.5, title=str(year),ax=axes[i][j], label='par mois')
                        weekgrp.rolling(3, center=True).mean().loc[str(year)]['url'].plot(linewidth=2, title=str(year),ax=axes[i][j], label="rolling mean (3)")
                        axes[i][j].legend()
                        if j == 1:
                            i = i + 1
                            j = 0
                        else :
                            j = j + 1
                    plt.tight_layout()
                    st.pyplot(fig,clear_figure=True)                    
                    
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
                    st.pyplot(fig,clear_figure=True)                    

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
                    st.pyplot(fig,clear_figure=True)                    

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
                        st.pyplot(fig,clear_figure=True)                    
                else:
                    st.write('No data for this word')

def get_word_corpus_count(inputdir='/Volumes/Transcend/natalia/'):
    files = glob(inputdir+"*.complete.csv")
    print(len(files))
    res =[]
    for f in files:
        word = f.split('/')[-1].split('.')[1]
        corpus = f.split('/')[-1].split('.')[0]
        count = sum(1 for line in open(f))-1
        res.append({'word':word, 'corpus':corpus, 'freq':count})
    df = pd.DataFrame(res)
    df.to_csv('data/allcorpora.allwords.counts.csv', index=False)

#get_word_corpus_count()
#exit()
def plot_overall_analysis(filename, wordboth):
    try:
        df = pd.read_csv(filename)
        print(df.info())
        df.drop_duplicates(inplace=True)
        df = df[df.freq>0]
        df.drop_duplicates(subset=['word','corpus'], keep="last", inplace=True)
        corpora = list(df.corpus.unique())
        print(corpora)
        #exit()
        df1 = df[df.corpus==corpora[0]]
        df2 = df[df.corpus==corpora[1]]
        df0 = df[df.word.isin(wordboth)]
        both=  list(df0.word.unique())
        all = list(df.word.unique())
            
        col0, col1, col2  = st.columns(3)
        with col0:
                    st.info( "Both languages : "+ str(len(both)) + " words over " + str(len(all)))
                    gbint = GridOptionsBuilder.from_dataframe(df0)
                    return_mode_value = DataReturnMode.__members__['FILTERED']
                    update_mode_value = GridUpdateMode.__members__['MODEL_CHANGED']            
                    gbint.configure_pagination()
                    #gbint.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='count', editable=False)
                    gbint.configure_column('word', minWidth=50, rowGroup=True, hide=True)
                    gbint.configure_column('freq', sort="desc", aggFunc='sum')
                    gbint.configure_column('corpus',cellRenderer=substring_renderer, width=10)
                    #gbint.configure_column("id_sent", wrapText=True, flex=2, cellRenderer=html_jscode, autoHeight=True, width=700) # , cellStyle=cellstyle_jscode , , cellStyle={"resizable": True,"autoHeight": True,"wrapText": True}
                    gbint.configure_side_bar()
                    gbint.configure_selection("single")
                    gridOptions = gbint.build()
                    ag_resp2int = AgGrid(
                                    df0, 
                                    data_return_mode=return_mode_value, 
                                    update_mode=update_mode_value,
                                    fit_columns_on_grid_load=True,                
                                    gridOptions=gridOptions, 
                                    allow_unsafe_jscode=True,
                                    #width=400,
                                    enable_enterprise_modules=True
                                    )#, enable_enterprise_modules=True
                    #selected_sent_int1 = ag_resp2int['selected_rows']
                    #if len(selected_sent_int1)==1:
                    #    st.write(selected_sent_int1)

        with col1:
                    st.info(corpora[0] + ": "+ str(df1.shape[0]) + " words")
                    gbint1 = GridOptionsBuilder.from_dataframe(df1[['word','freq']])
                    return_mode_value = DataReturnMode.__members__['FILTERED']
                    update_mode_value = GridUpdateMode.__members__['MODEL_CHANGED']            
                    gbint1.configure_pagination()
                    gbint1.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='count', editable=False)
                    gbint1.configure_column('freq', sort="desc")
                    #gbint.configure_column("id_sent", wrapText=True, flex=2, cellRenderer=html_jscode, autoHeight=True, width=700) # , cellStyle=cellstyle_jscode , , cellStyle={"resizable": True,"autoHeight": True,"wrapText": True}
                    gbint1.configure_side_bar()
                    gbint1.configure_selection("single")
                    gridOptions1 = gbint1.build()
                    ag_resp2int = AgGrid(
                                    df1[['word','freq']], 
                                    data_return_mode=return_mode_value, 
                                    update_mode=update_mode_value,
                                    #fit_columns_on_grid_load=True,                
                                    gridOptions=gridOptions1, 
                                    #allow_unsafe_jscode=True,
                                    #height=400,
                                    enable_enterprise_modules=True
                                    )#, enable_enterprise_modules=True
                    #selected_sent_int1 = ag_resp2int['selected_rows']
                    #if len(selected_sent_int1)==1:
                    #    st.write(selected_sent_int1)

        with col2:
                    st.info(corpora[1] + ": "+ str(df2.shape[0]) + " words")
                    gbint2 = GridOptionsBuilder.from_dataframe(df2[['word','freq']])
                    return_mode_value = DataReturnMode.__members__['FILTERED']
                    update_mode_value = GridUpdateMode.__members__['MODEL_CHANGED']            
                    gbint2.configure_pagination()
                    gbint2.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='count', editable=False)
                    gbint2.configure_column('freq', sort="desc") 
                   #gbint.configure_column('kw', sort="desc")
                    #gbint.configure_column("id_sent", wrapText=True, flex=2, cellRenderer=html_jscode, autoHeight=True, width=700) # , cellStyle=cellstyle_jscode , , cellStyle={"resizable": True,"autoHeight": True,"wrapText": True}
                    gbint2.configure_side_bar()
                    gbint2.configure_selection("single")
                    gridOptions2 = gbint2.build()
                    ag_resp3int = AgGrid(
                                    df2[['word','freq']], #[['keyword','sentence','website']]
                                    data_return_mode=return_mode_value, 
                                    update_mode=update_mode_value,
                                    #fit_columns_on_grid_load=True,                
                                    gridOptions=gridOptions2, 
                                    #allow_unsafe_jscode=True,
                                    #height=400,
                                    enable_enterprise_modules=True
                                    )#, enable_enterprise_modules=True
                    #selected_sent_int2 = ag_resp2int['selected_rows']
                    #if len(selected_sent_int2)==1:
                    #    st.write(selected_sent_int2)






    except Exception as e:
        print("error while opening/parsing file : " + filename + ', error :' + str(e))
        print(traceback.print_exc())

# AG-grid display layout (javascript code as JsCode class)
html_jscode = JsCode("""
  function(params) {
      return "<div>"+params.value+"</div>";
  };
  """)

#url_renderer=JsCode("""function(params) {return '<a href="' + params.value + '" target="_blank"><i class="fa-solid fa-arrow-up-right-from-square"></i></a>'}""")
url_renderer = JsCode("""
function(params) {
    return '<a href="' + params.value + '" target="_blank">' + params.value.substring(0,15)  + '...</a>'
    }
""")
#url_renderer=JsCode("""function(params) {return '<a href="' + params.value + '" target="_blank"><i class="fa-solid fa-arrow-up-right-from-square"></i></a>'}""")
text_url_renderer = JsCode("""
function(params) {
    var regexp = new RegExp(params.data.kw, 'i');
    return params.value.replace(regexp, "<mark>$&</mark>") + '&nbsp;<a href="' + params.data.url + '" target="_blank">('+ params.data.website + ', ' + params.data.date + ')</a>'
    }
""")


substring_renderer = JsCode("""
function(params) {
    console.log(params);
    if (params.value){
        return params.value.substring(0,3);
    }
    else{
        return null;
    }
}
""")


cellstyle_jscode = JsCode("""
function(params) {
        return {
            resizable: true,
            autoHeight: true,
            wrapText: true
        }
};
""")

jscodeRow = JsCode("""
            function(params) {
                if (params.data.spec === 1) {
                    return {
                        'color': 'white !important',
                        'backgroundColor': 'red !important'
                    }
                }
            };
            """)

jscode_rowformat = {
    "spec-style": 'data.spec == 1',
    "common-style": 'data.spec == 0',
}
jscode_rowformat_bk = {
    "spec-style": 'api.data.spec == 1',
    "common-style": 'api.data.spec == 0',
}

custom_css = {
    ".spec-style": {"background-color": "red !important"},
    ".common-style": {"background-color":'green !important'},#"color": "red !important",
}




# main
#definitions of protocols
dfdesc = pd.DataFrame([
                    ['XML-Roberta','XLM-R (XLM-RoBERTa) is a generic cross lingual sentence encoder that obtains state-of-the-art results on many cross-lingual understanding (XLU) benchmarks. It is trained on 2.5T of filtered CommonCrawl data in 100 languages. For details, see : https://github.com/pytorch/fairseq/tree/main/examples/xlmr'],
                    ['CamemBERT base','CamemBERT is a state-of-the-art language model for French based on the RoBERTa architecture pretrained on the French subcorpus of the newly available multilingual corpus OSCAR. For details, see : https://camembert-model.fr/'],
                    ['FlauBERT base','FlauBERT is a French BERT trained on a very large and heterogeneous French corpus. For details, see :  https://github.com/getalp/Flaubert'],
                    ['FastText model (sub-word Embeddings)','FastText is a sub-word embeddings enabling to represent even out-of-vocabulary lexemes by using subword information. Here we use the pretrained language model for French and a model trained on the Gallica corpus. For details, see :  https://fasttext.cc/docs/en/crawl-vectors.html (for Common Crawl French model) and https://arxiv.org/abs/1607.04606 (scientific paper)'],

                ], columns=['Model','Description'])


st.set_page_config(page_title="Etude des marques en français et Espagnol",
                   page_icon="💡",layout="wide")

# bootstrap style
#st.markdown('<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">', unsafe_allow_html=True)
            # bootstrap js to handle nav and other stuff
#st.markdown('''
#    <!-- jQuery first, then Popper.js, then Bootstrap JS -->
#    <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
#    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.12.9/umd/popper.min.js" integrity="sha384-ApNbgh9B+Y1QKtv3Rn7W3mgPxhU9K/ScQsAP7hUibX39j7fakFPskvXusvfa0b4Q" crossorigin="anonymous"></script>
#    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>
#''',unsafe_allow_html=True)


padding = 4
st.markdown(f""" <style>
    .reportview-container .main .block-container{{
        padding-top: 0rem;
        padding-right: {padding}rem;
        padding-left: {padding}rem;
        padding-bottom: {padding}rem;
    }} 
    .css-1d391kg{{
        padding-top: 5rem; }} 
    .row-common {{
        font-weight: bold;
        background-color: #aa2e25 !important;
    }}
    .row-specific {{
        font-weight: bold;
        background-color: #357a38 !important;
    }}
    </style> """, unsafe_allow_html=True)

# CSS to inject contained in a string
#hide_dataframe_row_index = """
#            <style>
#            .row_heading.level0 {display:none}
#            .blank {display:none}
#            </style>
#            """

# Inject CSS with Markdown
#st.markdown(hide_dataframe_row_index, unsafe_allow_html=True)

# Side Bar #######################################################
#st.sidebar.subheader("Parameters")
credits='''
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">                                                                                                    
<hr/>
<b>Credits</b><ul>
<li>Linguistic data (words): Natalia Soler&nbsp;<a href="https://www.lattice.cnrs.fr/membres/doctorants/natalia-soler/" target="new"><i class="fa-solid fa-arrow-up-right-from-square"></i></a> </li>                                                                                                                                                                                                          
<li>Linguistic data (corpora): JSI Timestamped web corpus&nbsp;<a href="https://www.sketchengine.eu/jozef-stefan-institute-newsfeed-corpus/" target="new"><i class="fa-solid fa-arrow-up-right-from-square"></i></a> </li>                                                                                                                                                                                                          
<li>Software : Emmanuel Cartier&nbsp;<a href="https://lipn.univ-paris13.fr/~cartier/" target="new"><i class="fa-solid fa-arrow-up-right-from-square"></i></a> </li>                                                                                                                                                                                                          
<li>Software : Aggrid&nbsp;<a href="https://www.ag-grid.com/javascript-data-grid/grid-features/?utm_source=ag-grid-readme&utm_medium=repository&utm_campaign=github" target="new"><i class="fa-solid fa-arrow-up-right-from-square"></i></a> </li>                                                                                                                                                                                                          


</ul>
'''
external_info='''
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">                                                                                                    
<hr/>
<b>External information</b><ul>
<li>WIPO Brand Database<a href="https://branddb.wipo.int/branddb/en/" target="new"><i class="fa-solid fa-arrow-up-right-from-square"></i></a> </li>                                                                                                                                                                                                          
<li>BabelNet<a href="https://babelnet.org/" target="new"><i class="fa-solid fa-arrow-up-right-from-square"></i></a> </li>                                                                                                                                                                                                          
</ul>
'''

st.title("Exploration of Brand Contexts and Metadata (French and Spanish)")
st.write("This web interface enables to explore about 700 brand names and their usage in web-based newspapers (JSI Web corpus family). It enables to explore the contexts and metadata.\nThis supports Natalia Soler's Phd thesis by presenting the brand names database and a quantitative analysis of contexts.\nbelow you will find overall statistics on lexemes frequency in French and Spanish JSI Timestamped corpora, as well as common lexemes.\n You can also explore specific lexemes by choosing a corpus (or both) and a lexemes on the sidebar. You could then get metadata and contextual visualisations and explore the raw data. All can be downloaded.")
inputdir='data/jsi_contexts/'
#inputdir='/Volumes/Transcend/natalia/'
outputdir='data/jsi_contexts/'

# preprocessed files
#outputdir = 'data/'



lang_corresp ={'fra_jsi_newsfeed_virt':'French','spa_jsi_newsfeed_virt':'Spanish'}
tokens=[]
token="Choose a token"
# load lexem input files
files = glob(inputdir+"*.complete.csv")
# just wordlist to get words with data in both corpus
wordlist = [f.split('/')[-1].split('.')[1] for f in files]
print(len(wordlist))
wordlistboth = set([x for x in wordlist if wordlist.count(x) > 1])
print(sorted(wordlistboth),len(wordlistboth))
wordlistone = set([x for x in wordlist if wordlist.count(x) == 1])
print(len(wordlistone))
word = 'Choose a lexeme'
corpusdic = {f.split('/')[-1].split('.')[0]:f for f in files}
corpora = list(corpusdic.keys())
#print(words)
allcorp = "+".join(corpora)
corpora.insert(0,allcorp)
corpora.insert(0,"Choose a corpus")
corpus = st.sidebar.selectbox(label="Corpus",
                                    options=sorted(corpora))

# before going further plot overall results
filename_glob = inputdir + 'allcorpora.allwords.counts.csv'
general_info = st.empty()
#general_info = st.expander("General information")
with general_info.expander("General information"):
    plot_overall_analysis(filename_glob,wordlistboth)


if corpus != 'Choose a corpus' and word=="Choose a lexeme":
    general_info.empty()
    #credits_sb.empty()
    if re.search('\+',corpus):
        words = sorted(list(wordlistboth))
        words.insert(0,"Choose a lexeme")
        word = st.sidebar.selectbox(label="Lexeme",
                                            options=words, index=0)
        #credits_sb.write(credits, unsafe_allow_html=True)
    else:
        files = [f for f in files if re.search(corpus, f)]
        wordsdic = {f.split('/')[-1].split('.')[1]:f for f in files}
        words = sorted(list(wordsdic.keys()))
        words.insert(0,"Choose a lexeme")
        word = st.sidebar.selectbox(label="Lexeme",
                                            options=words, index=0)
        #st.sidebar.write(credits, unsafe_allow_html=True)
if word != 'Choose a lexeme' and corpus != 'Choose a corpus':
    st.sidebar.write(external_info, unsafe_allow_html=True)
    st.sidebar.write(credits, unsafe_allow_html=True)
            
    if re.search('\+',corpus):
            corpora = corpus.split('+')
            df1 = pd.read_csv(inputdir+corpora[0]+ '.' + word + ".complete.csv")
            df1 = df1[~df1.kw.str.contains(r"[\W-]", re.I)]
            df2 = pd.read_csv(inputdir+corpora[1]+ '.' + word + ".complete.csv")
            df2 = df2[~df2.kw.str.contains(r"[\W-]", re.I)]
            total_sent1 = df1.shape[0]
            total_sent2 = df2.shape[0]
            columns = ['kw', 'sentence',  'website', 'date', 'country',
                    'left_w5', 'left_l5', 'left_p5',
                     'left_w4','left_l4', 'left_p4',
                    'left_w3', 'left_l3', 'left_p3',
                    'left_w2','left_l2', 'left_p2',
                    'left_w1', 'left_l1', 'left_p1', 
                    'right_w1','right_l1', 'right_p1', 
                    'right_w2', 'right_l2', 'right_p2', 
                    'right_w3', 'right_l3', 'right_p3', 
                    'right_w4', 'right_l4', 'right_p4', 
                    'right_w5','right_l5', 'right_p5',
                    'url',]

            if False:
                with st.expander("Metadata Analysis"):
                    col1, col2  = st.columns(2)
                    with col1:
                        st.info(corpora[0] + ": "+ str(total_sent1) + " sentences")
                        plot_meta_info(df1)
                    with col2:
                        st.info(corpora[1] + ": "+ str(total_sent2) + " sentences")
                        plot_meta_info(df2)

                with st.expander('Lexico syntaxic patterns'):
                    col1, col2  = st.columns(2)
                    with col1:
                        st.info(corpora[0] + ": "+ str(total_sent1) + " sentences")
                        plot_contexts_info(df1, meta=False)
                    with col2:
                        st.info(corpora[1] + ": "+ str(total_sent2) + " sentences")
                        plot_contexts_info(df2, meta=False)
            else:
                with st.expander("Metadata and Contexts Exploration (pdf file)"):
                    col1, col2 = st.columns(2)
                    with col1:
                        pdffile =outputdir + corpora[0] + '.' + word + '.pdf'
                        if os.path.isfile(pdffile):
                            show_pdf(pdffile)
                        else:
                            res = generate_pdf_file(word, corpora[0],inputdir, outputdir,meta=True)
                            if res[0]:
                                show_pdf(pdffile)
                            else:
                                st.write(res[1])
                        #pdffile =  'data/jsi_contexts/fra_jsi_newsfeed_virt.Walkman.exploration.pdf'
                    with col2:
                        pdffile =outputdir + corpora[1] + '.' + word + '.pdf'
                        if os.path.isfile(pdffile):
                            show_pdf(pdffile)
                        else:
                            res = generate_pdf_file(word, corpora[1],inputdir, outputdir,meta=True)
                            if res[0]:
                                show_pdf(pdffile)
                            else:
                                st.write(res[1])
            with st.expander("All Data (" + word + ')'):
                col1, col2  = st.columns(2)
                with col1:
                    st.info(corpora[0] + ": "+ str(total_sent1) + " sentences")
                    gbint = GridOptionsBuilder.from_dataframe(df1[columns]) #[['kw','sentence','website']]
                    return_mode_value = DataReturnMode.__members__['FILTERED']
                    update_mode_value = GridUpdateMode.__members__['MODEL_CHANGED']            
                    gbint.configure_pagination()
                    gbint.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='count', editable=True, width=10)
                    gbint.configure_column('kw', minWidth=10, sort="desc")
                    #gbint.configure_column('kw_pos', minWidth=10)
                    gbint.configure_column('sentence', minWidth=70, wrapText=True, autoHeight=True, cellRenderer=text_url_renderer)
                    gbint.configure_column('date', minWidth=10)
                    gbint.configure_column("url",hide=False, cellRenderer=url_renderer)
                    gbint.configure_column('country', minWidth=10)
                    gbint.configure_side_bar()
                    gbint.configure_selection("single")
                    gridOptions = gbint.build()
                    ag_resp2int = AgGrid(
                                    df1[columns], #[['kw','sentence','website']]
                                    data_return_mode=return_mode_value, 
                                    update_mode=update_mode_value,
                                    fit_columns_on_grid_load=True,                
                                    gridOptions=gridOptions, 
                                    allow_unsafe_jscode=True,
                                    height=500,
                                    enable_enterprise_modules=True
                                    )#, enable_enterprise_modules=True
                    selected_sent_int1 = ag_resp2int['selected_rows']
                    if len(selected_sent_int1)==1:
                        st.write(selected_sent_int1)

                with col2:
                    st.info(corpora[1] + ": "+ str(total_sent2) + " sentences")
                    gbint = GridOptionsBuilder.from_dataframe(df2[columns]) #[['kw','sentence','website']]
                    return_mode_value = DataReturnMode.__members__['FILTERED']
                    update_mode_value = GridUpdateMode.__members__['MODEL_CHANGED']            
                    gbint.configure_pagination()
                    gbint.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='count', editable=True, width=10)
                    gbint.configure_column('kw', minWidth=10, sort="desc")
                    #gbint.configure_column('kw_pos', minWidth=10)
                    gbint.configure_column('sentence', minWidth=70, wrapText=True, autoHeight=True, cellRenderer=text_url_renderer)
                    gbint.configure_column('date', minWidth=10)
                    gbint.configure_column("url",hide=False, cellRenderer=url_renderer)
                    gbint.configure_column('country', minWidth=10)
                    gbint.configure_side_bar()
                    gbint.configure_selection("single")
                    gridOptions = gbint.build()
                    ag_resp2int = AgGrid(
                                    df2[columns], #[['kw','sentence','website']]
                                    data_return_mode=return_mode_value, 
                                    update_mode=update_mode_value,
                                    fit_columns_on_grid_load=True,                
                                    gridOptions=gridOptions, 
                                    allow_unsafe_jscode=True,
                                    height=500,
                                    enable_enterprise_modules=True
                                    )#, enable_enterprise_modules=True
                    selected_sent_int2 = ag_resp2int['selected_rows']
                    if len(selected_sent_int2)==1:
                        st.write(selected_sent_int2)


    # one word one corpus                       
    else:
            df1 = pd.read_csv(inputdir+corpus+ '.' + word + ".complete.csv")
            df1 = df1[~df1.kw.str.contains(r"[\W-]", re.I)]
            total_sent1 = df1.shape[0]
            #columns = df1.columns
            columns = ['kw', 'sentence',  'website', 'date', 'country',
                    'left_w5', 'left_l5', 'left_p5',
                     'left_w4','left_l4', 'left_p4',
                    'left_w3', 'left_l3', 'left_p3',
                    'left_w2','left_l2', 'left_p2',
                    'left_w1', 'left_l1', 'left_p1', 
                    'right_w1','right_l1', 'right_p1', 
                    'right_w2', 'right_l2', 'right_p2', 
                    'right_w3', 'right_l3', 'right_p3', 
                    'right_w4', 'right_l4', 'right_p4', 
                    'right_w5','right_l5', 'right_p5',
                    'url',]

            if False:
                with st.expander("Metadata Analysis"):
                    st.info(corpus + ": "+ str(total_sent1) + " sentences")
                    plot_meta_info(df1)
                with st.expander('Lexico syntaxic patterns'):
                    st.info(corpus + ": "+ str(total_sent1) + " sentences")
                    plot_contexts_info(df1, meta=False)
            else:
                with st.expander("Metadata and Contexts Exploration (pdf file)"):
                    pdffile =outputdir + corpus + '.' + word + '.pdf'
                    print(pdffile)
                    #exit()
                    if os.path.isfile(pdffile):
                        show_pdf(pdffile)
                    else:
                        res = generate_pdf_file(word,corpus,inputdir, outputdir,meta=True)
                        print(res)
                        if res[0]:
                            show_pdf(pdffile)
                        else:
                            st.write(res[1])
                        
            with st.expander("All Data ("+ word + ')'):
                    st.info(corpus + ": "+ str(total_sent1) + " sentences")
                    gbint = GridOptionsBuilder.from_dataframe(df1[columns]) #[['kw','sentence','website']]
                    return_mode_value = DataReturnMode.__members__['FILTERED']
                    update_mode_value = GridUpdateMode.__members__['MODEL_CHANGED']            
                    gbint.configure_pagination()
                    gbint.configure_default_column(groupable=True, value=True, enableRowGroup=True,aggFunc='count',  editable=True, width=5)
                    gbint.configure_column('kw', minWidth=5, sort="desc")
                    #gbint.configure_column('kw_pos', minWidth=5)
                    gbint.configure_column('sentence', minWidth=70, wrapText=True, autoHeight=True, cellRenderer=text_url_renderer)
                    gbint.configure_column('date', minWidth=5)
                    gbint.configure_column("url",width=3, cellRenderer=url_renderer)
                    gbint.configure_column('country', minWidth=5)
                            #width=300)
                    #gbint.configure_column("url", wrapText=True, flex=2, cellRenderer=html_jscode, autoHeight=True, width=700) # , cellStyle=cellstyle_jscode , , cellStyle={"resizable": True,"autoHeight": True,"wrapText": True}
                    gbint.configure_side_bar()
                    gbint.configure_selection("single")
                    gridOptions = gbint.build()
                    ag_resp2int = AgGrid(
                                    df1[columns], #[['kw','sentence','website']]
                                    data_return_mode=return_mode_value, 
                                    update_mode=update_mode_value,
                                    #fit_columns_on_grid_load=True,                
                                    gridOptions=gridOptions, 
                                    allow_unsafe_jscode=True,
                                    height=500,
                                    enable_enterprise_modules=True
                                    )#, enable_enterprise_modules=True
                    selected_sent_int1 = ag_resp2int['selected_rows']
                    if len(selected_sent_int1)==1:
                        st.write(selected_sent_int1)
