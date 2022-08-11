import streamlit as st
import pandas as pd
from tabs.play import show_play
from tabs.hint import show_hint
from tabs.solve import show_solve

wordList = pd.read_csv("wordList.csv")

# drop all words that aren't 5 letters long
# wordList = pd.read_csv("wordgrid.csv")
# wordList = wordList.loc[wordList["word"].str.len() == 5, :]
# wordList.reset_index(inplace=True, drop=True)
# wordList.to_csv("wordList.csv", index=False)

if __name__ == "__main__":

    # st.set_page_config(layout="wide")
    play, hint, solve = st.tabs(["Play", "Hint", "Solve"])

    with play:
        show_play(wordList)

    with hint:
        show_hint(wordList)

    with solve:
        show_solve(wordList)