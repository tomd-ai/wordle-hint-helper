import json
import random
import re
import streamlit as st
from st_aggrid import AgGrid
# from packages.allSolutions import solve_wall
# from packages.newBoard import genNewBoard
import pandas as pd
import numpy as np

wordList = pd.read_csv("wordList.csv")

# drop all words that aren't 5 letters long
# wordList = pd.read_csv("wordgrid.csv")
# wordList = wordList.loc[wordList["word"].str.len() == 5, :]
# wordList.reset_index(inplace=True, drop=True)
# wordList.to_csv("wordList.csv", index=False)

blankBoard = pd.DataFrame(
    {
        "0": ["", "", "", "", "", ""],
        "1": ["", "", "", "", "", ""],
        "2": ["", "", "", "", "", ""],
        "3": ["", "", "", "", "", ""],
        "4": ["", "", "", "", "", ""],
    }
)

def reset_game():
    wordChoice = wordList.loc[~wordList["word"].str.endswith("S"), :].sample(1)
    st.session_state["word"] = wordChoice["word"].tolist()[0]
    st.session_state["definition"] = wordList.at[wordChoice.index[0], "definition"]

    st.session_state["guess_count"] = 0
    st.session_state["grid_layout"] = blankBoard.copy()
    st.session_state["answer_layout"] = blankBoard.copy()
    st.session_state["grey_letters"] = set()
    st.session_state["green_letters"] = set()
    st.session_state["yellow_letters"] = set() # green overrides yellow
    st.session_state["game_ended"] = False


if __name__ == "__main__":
    # st.set_page_config(layout="wide")

    play, hint, solve = st.tabs(["Play", "Hint", "Solve"])
    with play:
        col1, col2, col3 = st.columns(3)
        col1.subheader("Play wordle")
        st.write("(If there is a warning message about ag-grid, it should reload after a couple of seconds)")
        gameWon = False
        gameLost = False
        col2.write("")
        col3.write(" ")

        reset = col3.button("Reset game")

        if "word" not in st.session_state:
            # for some reason, the wordle never ends in S
            # but we still want people to be able to guess
            # ones that end in S
            reset_game()

        if reset:
            reset_game()

        customCss = {
            '.ag-header': {
                "display": "none"
            },
            '.ag-cell': {
                'text-align': "center !important",
                'border': 'solid 1px black !important'
            }
        }

        if not st.session_state["answer_layout"].equals(blankBoard):
            for rowInd, row in st.session_state["answer_layout"].iterrows():
                for colInd, val in enumerate(row.tolist()):
                    if val == "GREEN":
                        customCss[f'.ag-row[row-id="{rowInd}"] .ag-cell[col-id="{colInd}"]'] = {
                            "background-color": "green !important",
                            "color": "white !important"
                        }
                    if val == "GREY":
                        customCss[f'.ag-row[row-id="{rowInd}"] .ag-cell[col-id="{colInd}"]'] = {
                            "background-color": "grey !important",
                            "color": "white !important"
                        }
                    if val == "YELLOW":
                        customCss[f'.ag-row[row-id="{rowInd}"] .ag-cell[col-id="{colInd}"]'] = {
                            "background-color": "orange !important",
                            "color": "white !important"
                        }
        
        # print(json.dumps(customCss, indent=4))

        grid_return = AgGrid(
            st.session_state["grid_layout"],
            editable=False,
            fit_columns_on_grid_load=True,
            theme="material",
            custom_css=customCss,
            height=300,
            width=200,
            reload_data=True,
            update_mode='model_changed'
        )

        # guessed letters:

        # customCssLetters = {

        # }

        customCssLetters = {
            '.ag-header': {
                "display": "none"
            }
        }

        # st.write("Word: ", st.session_state["word"])
        # st.write("Definition:", st.session_state["definition"])

        if not st.session_state["game_ended"]:

            col3, col4 = st.columns(2)

            value = col3.text_input("Enter guess")
            col4.write(" ")
            col4.write(" ")
            guessButton = col4.button("Guess")

            if len(str(value)) == 5 or guessButton:

                value = value.upper()

                # check that the word is a word:

                if len(str(value)) < 5 and value != "":
                    validWord = False
                    st.write(f"Sorry, the word needs to contain at least 5 letters.")
                elif re.match(r"[^a-zA-Z]", value, re.S):
                    validWord = False
                    st.write(f"Sorry, the word needs to contain at least 5 letters.")
                elif not (wordList["word"] == value).any():
                    validWord = False
                    st.write(f"Sorry, '{value}' was not found in the dictionary.")
                else:
                    validWord = True

                curLayout = st.session_state["grid_layout"].copy()
                curLayout["guessedRows"] = curLayout.apply(''.join, axis=1)
                
                if (curLayout["guessedRows"] == value).any():
                    validWord = False
                    # st.write(f"Sorry, '{value}' has already been guessed")

                firstIndex = curLayout.loc[(curLayout['guessedRows'] == '')]
                try:
                    firstIndex = firstIndex.index[0]
                except IndexError:
                    firstIndex = None

                # determine whether the game is over:

                if firstIndex is None:
                    gameLost = True
                    st.session_state["game_ended"] = True

                if validWord and firstIndex is not None:

                    # print(firstIndex)

                    # print(curLayout)

                    letterPos = []
                    greenLetters = []
                    yellowLetters = {}
                    greyLetters = []

                    for guessLetter, answerLetter in zip(value, st.session_state["word"]):
                        # print(guessLetter, answerLetter)
                        if guessLetter == answerLetter:
                            letterPos.append("GREEN")
                            st.session_state["green_letters"].add(guessLetter)
                        elif guessLetter in st.session_state["word"]:
                            st.session_state["yellow_letters"].add(guessLetter)
                            letterPos.append("YELLOW")
                            # there may be cases where there are two
                            # of the same letter in a word.
                            # to avoid showing yellow more times than
                            # the number of times the letter is in the
                            # word, we have to count the number of times
                            # the letter is in the word
                            yellowLetters.setdefault(
                                guessLetter, []
                            )
                            # cast the len to an int to avoid mutability
                            yellowLetters[guessLetter].append(
                                int(len(letterPos))
                            )
                        else:
                            letterPos.append("GREY")
                            st.session_state["grey_letters"].add(guessLetter)

                    for letter in yellowLetters:
                        letterPresenceCount = st.session_state["word"].count(letter)
                        if letterPresenceCount != len(yellowLetters[letter]):
                            for x in range(0, len(yellowLetters[letter]) - letterPresenceCount):
                                letterPos[x] = "GREY"

                    if letterPos.count("GREEN") == 5:
                        gameWon = True
                        st.session_state["game_ended"] = True

                    st.session_state["grid_layout"].loc[firstIndex, :] = list(value)
                    st.session_state["answer_layout"].loc[firstIndex, :] = letterPos

                    st.experimental_rerun()

        letter_guesses = pd.DataFrame(
            {
                "0": ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", " "],
                "1": [" ", "A", "S", "D", "F", "G", "H", "J", "K", "L", " "],
                "2": [" ", " ", "Z", "X", "C", "V", "B", "N", "M", " ", " "]
            }
        )
        # otherwise its a headache to workout - transpose it
        letter_guesses = letter_guesses.T
        # to make ag grid happy
        letter_guesses.columns = [str(x) for x in letter_guesses.columns]

        for rowInd, row in letter_guesses.iterrows():
            for colInd, letter in enumerate(row.tolist()):
                if letter in st.session_state["green_letters"]:
                    customCssLetters[f'.ag-row[row-id="{rowInd}"] .ag-cell[col-id="{colInd}"]'] = {
                        "background-color": "green !important",
                        "color": "white !important"
                    }
                if letter in st.session_state["grey_letters"]:
                    customCssLetters[f'.ag-row[row-id="{rowInd}"] .ag-cell[col-id="{colInd}"]'] = {
                        "background-color": "grey !important",
                        "color": "white !important"
                    }
                if letter in st.session_state["yellow_letters"] and letter not in st.session_state["green_letters"]:
                    customCssLetters[f'.ag-row[row-id="{rowInd}"] .ag-cell[col-id="{colInd}"]'] = {
                        "background-color": "orange !important",
                        "color": "white !important"
                    }
                if letter == " ":
                    customCssLetters[f'.ag-row[row-id="{rowInd}"] .ag-cell[col-id="{colInd}"]'] = {
                        'border': 'solid 0px black !important'
                    }
        
        guessed_grid = AgGrid(
            letter_guesses,
            editable=False,
            fit_columns_on_grid_load=True,
            theme="material",
            custom_css=customCssLetters,
            height=175,
            width=200,
            reload_data=True,
            update_mode='model_changed'
        )
        
            # print(st.session_state["answer_layout"])
        if gameWon:
            st.write(
                f"Well done, you got the word in {st.session_state['guess_count']} guesses!"
            )

            st.write("Word: ", st.session_state["word"])
            st.write("Definition:", st.session_state["definition"])

        if gameLost:
            st.write("Sorry, you are out of guesses. The word was:")
            st.write("Word: ", st.session_state["word"])
            st.write("Definition:", st.session_state["definition"])

