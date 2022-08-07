import re
import streamlit as st
from st_aggrid import AgGrid
import pandas as pd

# initialisation

def gen_generic_custom_css(background):
    customCss = {
        '.ag-header': {
            "display": "none"
        },
        '.ag-cell': {
            'text-align': "center !important",
            'border': 'solid 1px black !important',
            "background-color": f"{background} !important",
            "color": "white !important"
        }
    }
    return customCss


def gen_blank_df(grey=False):
    if not grey:
        blankDF = pd.DataFrame(
            {
                "0": [""] * 5
            }
        )
    else:
        blankDF = pd.DataFrame(
            {
                "0": [""] * 7,
                "1": [""] * 7
            }
        )
    blankDF = blankDF.T
    blankDF.columns = [str(x) for x in blankDF.columns]
    return blankDF

def reset_hint():
    st.session_state["hint_correct_letters_row"] = gen_blank_df()
    st.session_state["hint_yellow_letters_row"] = gen_blank_df()
    st.session_state["hint_grey_letters_df"] = gen_blank_df(grey=True)

# hint algorithm

def generate_hint(
    greenLettersDF,
    yellowLettersDF,
    greyLettersDF: pd.DataFrame,
    wordListDF):
    # firstly, wordle words rarely end in s
    wordListDF = wordListDF.loc[~wordListDF["word"].str.endswith("S"), :]

    mostLikely, leastLikely = [], []

    # first exclude all words containing letters that are invalid

    invalidLetterRegex = re.compile(
        f"[{''.join(greyLettersDF.stack().values.tolist())}]",
        re.S
    )

    print(len(wordListDF))

    wordListDF = wordListDF.loc[
        ~wordListDF["word"].str.contains(invalidLetterRegex),
        :
    ]

    print(len(wordListDF))

    # now convert the wordList into a matrix of letters

    wordListDF["expandedWord"] = wordListDF["word"].apply(
        lambda x: list(x),
    )

    wordListDF = pd.DataFrame(
        wordListDF["expandedWord"].tolist()
    )

    # now check for words that contain letters in the green list

    for rowInd, row in greenLettersDF.iterrows():
        for colInd, col in enumerate(row.tolist()):
            print(colInd, col)
            # TODO: calculate the most likely letter

    print(wordListDF)

    return mostLikely, leastLikely

# streamlit display

def show_hint(wordList):
    hintCol1, hintCol2, hintCol3 = st.columns(3)
    hintCol1.subheader("Wordle hint")
    # make button in line with header
    hintCol2.write(" ")
    hintCol3.write(" ")
    hintReset = hintCol3.button("Reset all")

    st.write("Provides a hint for the game wordle")
    if hintReset:
        reset_hint()
    
    if "hint_correct_letters_row" not in st.session_state:
        st.write("(If there is a warning message about ag-grid, it should reload after a couple of seconds)")
        reset_hint()

    greenCol1, greenCol2 = st.columns(2)
    greenCol1.write("Correctly placed letters:")
    # clearGreen = greenCol2.button("Reset", key="clearGreen")
    # if clearGreen:
    #     st.session_state["hint_correct_letters_row"] = gen_blank_df()
    #     st.experimental_rerun()
    
    green_df = AgGrid(
        st.session_state["hint_correct_letters_row"],
        editable=True,
        fit_columns_on_grid_load=True,
        theme="material",
        custom_css=gen_generic_custom_css("green"),
        height=50,
        width=200,
        reload_data=True,
        update_mode='model_changed'
    )

    new_green_df = green_df['data']
    new_green_df = new_green_df.apply(lambda x: x.str.upper())

    greenCol3, greenCol4 = st.columns(2)
    greenCol3.write("Correct letters, in wrong location:")
    # clearYellow = greenCol4.button("Reset", key="clearYellow")
    # if clearYellow:
    #     st.session_state["hint_yellow_letters_row"] = gen_blank_df()
    #     st.experimental_rerun()

    yellow_df = AgGrid(
        st.session_state["hint_yellow_letters_row"],
        editable=True,
        fit_columns_on_grid_load=True,
        theme="material",
        custom_css=gen_generic_custom_css("orange"),
        height=50,
        width=200,
        reload_data=True,
        update_mode='model_changed'
    )

    new_yellow_df = yellow_df['data']
    new_yellow_df = new_yellow_df.apply(lambda x: x.str.upper())

    greenCol5, greenCol6 = st.columns(2)
    greenCol5.write("Incorrect letters")
    # clearGrey = greenCol6.button("Reset", key="clearGrey")
    # if clearGrey:
    #     st.session_state["hint_grey_letters_df"] = gen_blank_df(grey=True)
    #     st.experimental_rerun()

    grey_df = AgGrid(
        st.session_state["hint_grey_letters_df"],
        editable=True,
        fit_columns_on_grid_load=True,
        theme="material",
        custom_css=gen_generic_custom_css("grey"),
        height=100,
        width=200,
        reload_data=True,
        update_mode='model_changed'
    )

    new_grey_df = grey_df['data']
    new_grey_df = new_grey_df.apply(lambda x: x.str.upper())

    if not st.session_state["hint_correct_letters_row"].equals(new_green_df):
        # print(st.session_state["hint_correct_letters_row"])
        st.session_state["hint_correct_letters_row"] = new_green_df
        st.experimental_rerun()
    if not st.session_state["hint_yellow_letters_row"].equals(new_yellow_df):
        # print(st.session_state["hint_yellow_letters_row"])
        st.session_state["hint_yellow_letters_row"] = new_yellow_df
        st.experimental_rerun()
    if not st.session_state["hint_grey_letters_df"].equals(new_grey_df):
        # print(st.session_state["hint_grey_letters_df"])
        st.session_state["hint_grey_letters_df"] = new_grey_df
        st.experimental_rerun()

    hintButton = st.button("Get hint")

    if hintButton:
        mostLikely, leastLikely = generate_hint(
            greenLettersDF=st.session_state["hint_correct_letters_row"],
            yellowLettersDF=st.session_state["hint_yellow_letters_row"],
            greyLettersDF=st.session_state["hint_grey_letters_df"],
            wordListDF=wordList
        )