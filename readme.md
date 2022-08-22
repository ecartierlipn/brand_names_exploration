# Repository of data and web exploration app for Natalia Soler's PhD thesis

This repository contains around 600 French and Spanish brand names (subdirectory words), their contexts (up to 10,000) in JSI Timestamped Web corpus (subdirectory data/jsi_contexts) and a streamlit app to explore these data (timeline, metadata distribution and evolution, lexico-syntactic patterns).

The streamlit app is publicly available here : [Streamlit app](https://ecartierlipn-brand-names-exploration-data-exploration-nh964l.streamlitapp.com/).

## Local installation

First check you have Python 3.8+ and Github installed on your computer.
Go to the parent folder where you would like to copy the repo then clone the repository

```
git clone https://github.com/ecartierlipn/brand_names_exploration.git
```

go to brand_names_exploration subdirectory and install the dependencies :

```
pip install -requirements.txt
```

Then run the streamlit app :

```
streamlit run data_exploration.py
```

## Tuning the app

The local installation enables to (manually) edit the word contexts before exploration (filename for each word : `data/jsi_contexts/<fra|spa>_jsi_newsfeed_virt.<word>.complete_csv`). 

To retrieve the JSI Timestamped web corpus contexts for each word (or other words you would like to add) and parse the results before exploration, you can use `sketchengine_extract_contexts_from_wordlist.py` (you need to provide your sketchengine APYI key). You can add new words in word list in files in `words` subdirectory, just by adding a word in a new line.

## Credits

- Linguistic data (words): [Natalia Soler](https://www.lattice.cnrs.fr/membres/doctorants/natalia-soler/)                                                                                                                                                                                                          

- Linguistic data (word contexts): [JSI Timestamped web corpus](https://www.sketchengine.eu/jozef-stefan-institute-newsfeed-corpus/)
                                                                                                                                                                                                          
- Software : [Emmanuel Cartier](https://lipn.univ-paris13.fr/~cartier/)                                                                                                                                                                                                          

Check `requirements.txt` file for python libraries.





