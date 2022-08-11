import json
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
            "opacity": 0.6,
            "color": "white !important"
        }
    }
    return customCss


def gen_blank_df(colour):
    if colour in ["green", "yellow"]:
        blankDF = pd.DataFrame(
            {
                "0": [""] * 5
            }
        )
    if colour == "grey":
        blankDF = pd.DataFrame(
            {
                "0": [""] * 5,
                "1": [""] * 5
            }
        )
    if colour == "green_letter_hint":
        blankDF = pd.DataFrame(
            {
                "0": [""] * 5,
                "1": [""] * 5,
                "2": [""] * 5,
                "3": [""] * 5,
                "4": [""] * 5
            }
        )
    if colour == "most_likely_words_hint":
        blankDF = blankDF = pd.DataFrame(
            {
                "0": [""] * 5,
            }
        )
    blankDF = blankDF.T
    blankDF.columns = [str(x) for x in blankDF.columns]
    return blankDF

def reset_hint():
    st.session_state["hint_correct_letters_row"] = gen_blank_df("green")
    st.session_state["hint_yellow_letters_row"] = gen_blank_df("yellow")
    st.session_state["hint_grey_letters_df"] = gen_blank_df("grey")

    st.session_state["hint_green_letter_probability"] = gen_blank_df("green_letter_hint")
    st.session_state["hint_most_likely_words"] = gen_blank_df("most_likely_words_hint")


# hint algorithm

def generate_hint(
    greenLettersDF: pd.DataFrame,
    yellowLettersDF: pd.DataFrame,
    greyLettersDF: pd.DataFrame,
    wordListDF: pd.DataFrame):
    # firstly, wordle words rarely end in s
    wordListDF = wordListDF.loc[~wordListDF["word"].str.endswith("S"), :]

    mostLikely, leastLikely = [], []

    # first exclude all words containing letters that are invalid

    greyLetterList = greyLettersDF.stack().values.tolist()
    
    # print(len(wordListDF))
    if greyLetterList.count("") != len(greyLetterList):
        invalidLetterRegex = re.compile(
            f"[{''.join(greyLetterList)}]",
            re.S
        )
        wordListDF = wordListDF.loc[
            ~wordListDF["word"].str.contains(invalidLetterRegex),
            :
        ]

    # now convert the wordList into a matrix of letters

    wordListDF["expandedWord"] = wordListDF["word"].apply(
        lambda x: list(x),
    )

    expandedWordListDF = pd.DataFrame(
        wordListDF["expandedWord"].tolist()
    )

    # now check for words that contain letters in the green list

    greenLetterList = []
    greenLetterIndex = []
    missingLetterIndex = []


    for rowInd, row in greenLettersDF.iterrows():
        for colInd, colVal in enumerate(row.tolist()):
            if colVal != "":
                greenLetterIndex.append(colInd)
                greenLetterList.append([colInd, colVal])
            else:
                missingLetterIndex.append(colInd)

    for greenLetter in greenLetterList:
        expandedWordListDF = expandedWordListDF.loc[
            expandedWordListDF[greenLetter[0]] == greenLetter[1],
            :
        ]

    yellowLetters = []
    yellowLetterList = []

    for rowInd, row in yellowLettersDF.iterrows():
        for colInd, colVal in enumerate(row.tolist()):
            if colVal != "":
                yellowLetterList.append([colInd, colVal])
                yellowLetters.append(colVal)

    if yellowLetterList:
        yellowWords = expandedWordListDF.agg(
            lambda x: "".join([x[y] for y in missingLetterIndex]),
            axis=1
        )

        # print(yellowWords)

        yellowWords = yellowWords[
            yellowWords.str.contains(f"[{''.join(yellowLetters)}]") == True
        ].index

        if len(yellowWords):
            
            # if theres one result it does weird things
            # to positional indexing
            if yellowWords.size == 1:
                expandedWordListDF = expandedWordListDF.loc[
                    yellowWords
                ]
            else:
                expandedWordListDF = expandedWordListDF.iloc[
                    yellowWords,
                    :
                ]

            for colInd, colVal in yellowLetterList:
                expandedWordListDF = expandedWordListDF.loc[
                    ~(expandedWordListDF[colInd] == colVal),
                    :
                ]

    allLikely = {}
    mostLikely = {}
    mostLikelyWords = {}

    if not expandedWordListDF.empty:

        expandedWordListDF["expandedWord"] = expandedWordListDF.agg(
            lambda x: "".join(x[ind] for ind in [0,1,2,3,4]),
            axis = 1
        )
        for col in range(0, 5):
            # print(col)
            if col in missingLetterIndex:
                colCounts = expandedWordListDF[col].value_counts()

                mostLikely.setdefault(col, [])
                allLikely.setdefault(col, [])

                maxlen = colCounts.size if colCounts.size < 5 else 5
                
                for ind in range(0, maxlen):

                    mostLikely[col].append(
                        f"{colCounts.head(maxlen).index[ind]}, { round((colCounts.head(maxlen)[ind] / colCounts.sum())* 100) }%"
                    )

                allLikely[col] = [
                    {
                        "letter": letter,
                        "count": count
                    } for letter, count in zip(colCounts.index, colCounts)
                ]


                if maxlen < 5:
                    mostLikely[col].extend([""] * (5-maxlen))
                # print(mostLikely)
            else:
                mostLikely.setdefault(col, [])
                mostLikely[col].extend([""] * 5)

        mostLikelyWords = expandedWordListDF["expandedWord"]

    return mostLikely, mostLikelyWords, allLikely

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
        st.experimental_rerun()
    
    if "hint_correct_letters_row" not in st.session_state:
        st.write("(If there is a warning message about ag-grid, it should reload after a couple of seconds)")
        st.write("(you might need to double click the table cells - hit enter to add the letter")
        reset_hint()

    greenCol1, greenCol2 = st.columns(2)
    greenCol1.write("Correctly placed letters:")

    greenCss = gen_generic_custom_css("green")

    green_df = AgGrid(
        st.session_state["hint_correct_letters_row"],
        editable=True,
        fit_columns_on_grid_load=True,
        theme="material",
        custom_css=greenCss,
        height=75,
        key="green",
        reload_data=True,
        update_mode='model_changed'
    )

    new_green_df = green_df['data']
    new_green_df = new_green_df.apply(lambda x: x.str.upper())

    greenCol3, greenCol4 = st.columns(2)
    greenCol3.write("Correct letters, in wrong location:")

    yellowCss = gen_generic_custom_css("orange")

    yellow_df = AgGrid(
        st.session_state["hint_yellow_letters_row"],
        editable=True,
        fit_columns_on_grid_load=True,
        theme="material",
        custom_css=yellowCss,
        height=75,
        key="yellow",
        reload_data=True,
        update_mode='model_changed'
    )

    new_yellow_df = yellow_df['data']
    new_yellow_df = new_yellow_df.apply(lambda x: x.str.upper())

    greenCol5, greenCol6 = st.columns(2)
    greenCol5.write("Incorrect letters")

    greyCss = gen_generic_custom_css("grey")

    grey_df = AgGrid(
        st.session_state["hint_grey_letters_df"],
        editable=True,
        fit_columns_on_grid_load=True,
        theme="material",
        custom_css=greyCss,
        height=100,
        # width=200,
        key="grey",
        reload_data=True,
        update_mode='model_changed'
    )

    new_grey_df = grey_df['data']
    new_grey_df = new_grey_df.apply(lambda x: x.str.upper())

    if not st.session_state["hint_correct_letters_row"].equals(new_green_df):
        st.session_state["hint_correct_letters_row"] = new_green_df
        st.experimental_rerun()
    if not st.session_state["hint_yellow_letters_row"].equals(new_yellow_df):
        st.session_state["hint_yellow_letters_row"] = new_yellow_df
        st.experimental_rerun()
    if not st.session_state["hint_grey_letters_df"].equals(new_grey_df):
        st.session_state["hint_grey_letters_df"] = new_grey_df
        st.experimental_rerun()

    # the script is very quick, we don't need a submit.

    # the third argument is used in solve

    # TODO: A nice improvement would be to rank the returned
    # most likely words by the amount of information they reveal.

    mostLikelyLetters, mostLikelyWords, _ = generate_hint(
        greenLettersDF=st.session_state["hint_correct_letters_row"],
        yellowLettersDF=st.session_state["hint_yellow_letters_row"],
        greyLettersDF=st.session_state["hint_grey_letters_df"],
        wordListDF=wordList
    )

    mostLikelyLettersDF = pd.DataFrame(
        mostLikelyLetters
    )

    mostLikelyWordsDF = pd.DataFrame(
        mostLikelyWords
    )

    if not mostLikelyLettersDF.empty:

        mostLikelyLettersDF.columns = [str(x) for x in mostLikelyLettersDF.columns]

        st.session_state["green_letter_hint"] = mostLikelyLettersDF
        st.write("Top 5 most likely letters for remaining spaces")

        most_likely_df = AgGrid(
            st.session_state["green_letter_hint"],
            editable=False,
            fit_columns_on_grid_load=True,
            theme="material",
            custom_css=greenCss,
            height=250,
            # width=200,
            key="hint_letters_df",
            reload_data=True,
            update_mode='model_changed'
        )

        mostLikelyWordsDF.columns = [str(x) for x in mostLikelyWordsDF.columns]

        st.session_state["hint_most_likely_words"] = mostLikelyWordsDF
        st.write("Some words examples to try that use the letters:")

        most_likely_words_df = AgGrid(
            st.session_state["hint_most_likely_words"],
            editable=False,
            fit_columns_on_grid_load=True,
            theme="material",
            custom_css=greenCss,
            height=250,
            # width=200,
            key="hint_words_df",
            reload_data=True,
            update_mode='model_changed'
        )

    else:
        st.write("Sorry, no words found, check the inputs")