import pandas as pd
from st_aggrid import AgGrid
import streamlit as st

def apply_guess_css():

    customCss = {
        '.ag-header': {
            "display": "none"
        },
        '.ag-cell': {
            'text-align': "center !important",
            'border': 'solid 1px black !important'
        }
    }

    for rowInd, row in st.session_state["solve_cur_guess_df"].iterrows():
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

    return customCss

def gen_blank_df_solve(dfName):
    return pd.DataFrame(
        {
            "0": [""] * 5,
            "1": [""] * 5,
            "2": [""] * 5,
            "3": [""] * 5,
            "4": [""] * 5,
            "5": [""] * 5
        }
    )


def reset_solve():
    st.session_state["intialisation_complete"] = True
    st.session_state["solve_word_to_guess"] = ""
    st.session_state["solve_cur_guess_df"] = gen_blank_df_solve("guessGrid")
    st.session_state["solve_letter_df"] = gen_blank_df_solve("letterGrid")
    st.session_state["not_found"] = False
    st.session_state["not_selected"] = False
    st.session_state["wordbox"] = ""


# TODO: algorithm for next word to guess:



# streamlit display

def show_solve(wordList):
    solveCol1, solveCol2, solveCol3 = st.columns(3)
    solveCol1.subheader("Wordle solve")
    # make button in line with header
    solveCol2.write(" ")
    solveCol3.write(" ")
    solveReset = solveCol3.button("Reset")

    st.write("Provide a word, and see how the algorithm at each stage tries to solve the game!")
    if solveReset:
        reset_solve()
        st.experimental_rerun()
    
    if not st.session_state.get("intialisation_complete"):
        reset_solve()
        st.experimental_rerun()

    solveCol4, solveCol5, solveCol6 = st.columns(3)

    if not st.session_state.get("solve_word_to_guess"):
    
        wordBox = solveCol4.text_input(
            "Enter a 5 letter word",
            key="wordbox",
            max_chars=5,
        )

        solveCol5.write("\t        OR\t")

        change = solveCol6.selectbox(
            label="Click to select a word",
            options=[''] + wordList["word"].tolist()
        )

        if st.session_state.get("not_found"):
            solveCol4.write("Sorry, that word wasn't found")

        if st.session_state.get("not_selected"):
            solveCol6.write("Please enter or select a word")

        chooseWordButton = st.button(
            "Solve for word"
        )

        if chooseWordButton:
            if st.session_state["wordbox"]:
                if (wordList["word"].eq(st.session_state["wordbox"].upper())).any():
                    st.session_state["solve_word_to_guess"] = wordBox.upper()
                    st.session_state["not_found"] = False
                    st.experimental_rerun()
                else:
                    st.session_state["not_found"] = True
                    st.session_state["not_selected"] = False
                    st.experimental_rerun()
            else:
                if change:
                    st.session_state["solve_word_to_guess"] = change
                    st.experimental_rerun()
                else:
                    st.session_state["not_selected"] = True
                    st.experimental_rerun()
    else:
        st.write(f"Word to be guessed: {st.session_state['solve_word_to_guess']}")
        
        st.button("Solve next row")

        solve_grid_status = AgGrid(
            st.session_state["solve_cur_guess_df"],
            editable=False,
            fit_columns_on_grid_load=True,
            theme="material",
            custom_css=apply_guess_css(),
            height=300,
            width=200,
            reload_data=True,
            update_mode='model_changed',
            key="solve_grid"
        )

        nextGuess = ""

        st.write(f"Next word to guess: {nextGuess}")

        st.write("Letter probabilities")

        likely_letters = AgGrid(
            st.session_state["solve_letter_df"],
            editable=False,
            fit_columns_on_grid_load=True,
            theme="material",
            custom_css=apply_guess_css(),
            height=300,
            width=200,
            reload_data=True,
            update_mode='model_changed',
            key="letter_grid"
        )





