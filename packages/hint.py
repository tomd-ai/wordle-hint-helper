import json
import re
import streamlit as st
from st_aggrid import AgGrid
import pandas as pd

# initialisation

def gen_generic_custom_css(background):
    
    # if background == "green":
    #     background = "rgb(132, 222, 71, 0.6)"
    # if background == "orange":
    #     background = "rgb(255, 135, 0, 0.6)"
    # if background == "grey":
    #     background = "rgb(210, 210, 210, 0.6)"

    customCss = {
        '.ag-header': {
            "display": "none"
        },
        '.ag-cell': {
            'text-align': "center !important",
            'border': 'solid 1px black !important',
            "background-color": f"{background} !important",
            "opacity": 0.6,
            "color": "black !important"
        }
    }
    return customCss

def add_solid_style(df, colour, customStyle):
    # print("add row")
    for rowInd, row in df.iterrows():
        for colInd, val in enumerate(row.tolist()):
            if val:
                # print(val)
                customStyle[f'.ag-row[row-id="{rowInd}"] .ag-cell[col-id="{colInd}"]'] = {
                    "background-color": f"{colour} !important",
                    "color": "white !important",
                }

                # print({
                #     "background-color": f"{colour} !important",
                #     "color": "white !important",
                # })
    # print(json.dumps(customStyle, indent=4))
    return customStyle


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
    blankDF = blankDF.T
    blankDF.columns = [str(x) for x in blankDF.columns]
    return blankDF

def reset_hint():
    st.session_state["hint_correct_letters_row"] = gen_blank_df("green")
    st.session_state["hint_yellow_letters_row"] = gen_blank_df("yellow")
    st.session_state["hint_grey_letters_df"] = gen_blank_df("grey")

    st.session_state["hint_green_letter_probability"] = gen_blank_df("green_letter_hint")

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

    # print(len(wordListDF))

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

            print(yellowWords.size)
            if yellowWords.size == 1:
                expandedWordListDF = expandedWordListDF.iloc[
                    [yellowWords[0]],
                    :
                ]
            else:
                expandedWordListDF = expandedWordListDF.iloc[
                    yellowWords[0],
                    :
                ]

            for colInd, colVal in yellowLetterList:
                print(colInd)

                expandedWordListDF = expandedWordListDF.loc[
                    ~(expandedWordListDF[colInd] == colVal),
                    :
                ]
            # except IndexError:
            #     pass


        # expandedWordListDF = expandedWordListDF.loc[
        #     expandedWordListDF[greenLetter[0]] == greenLetter[1],
        #     :
        # ]

    # print(expandedWordListDF)
    mostLikely = {}
    if not expandedWordListDF.empty:

        expandedWordListDF["expandedWord"] = expandedWordListDF.agg(
            lambda x: "".join(x[ind] for ind in [0,1,2,3,4]),
            axis = 1
        )
        for col in range(0, 5):
            print(col)
            if col in missingLetterIndex:
                colCounts = expandedWordListDF[col].value_counts()
                mostLikely.setdefault(col, [])
                maxlen = colCounts.size if colCounts.size < 5 else 5
                
                for ind in range(0, maxlen):

                    mostLikely[col].append(
                        f"{colCounts.head(maxlen).index[ind]}, { round((colCounts.head(maxlen)[ind] / colCounts.sum())* 100) }%"
                    )
                
                if maxlen < 5:
                    mostLikely[col].extend([""] * (5-maxlen))
                print(mostLikely)
            else:
                mostLikely.setdefault(col, [])
                mostLikely[col].extend([""] * 5)

    return mostLikely


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
    # clearGreen = greenCol2.button("Reset", key="clearGreen")
    # if clearGreen:
    #     st.session_state["hint_correct_letters_row"] = gen_blank_df("green")
    #     st.experimental_rerun()

    greenCss = gen_generic_custom_css("green")
    greenCss = add_solid_style(
        df=st.session_state["hint_correct_letters_row"],
        colour="green",
        customStyle=greenCss
    )
    
    green_df = AgGrid(
        st.session_state["hint_correct_letters_row"],
        editable=True,
        fit_columns_on_grid_load=True,
        theme="material",
        custom_css=greenCss,
        height=75,
        # width=200,
        key="green",
        reload_data=True,
        update_mode='model_changed'
    )

    new_green_df = green_df['data']
    new_green_df = new_green_df.apply(lambda x: x.str.upper())

    greenCol3, greenCol4 = st.columns(2)
    greenCol3.write("Correct letters, in wrong location:")
    # clearYellow = greenCol4.button("Reset", key="clearYellow")
    # if clearYellow:
    #     st.session_state["hint_yellow_letters_row"] = gen_blank_df("yellow")
    #     st.experimental_rerun()

    yellowCss = gen_generic_custom_css("orange")
    yellowCss = add_solid_style(
        df=st.session_state["hint_yellow_letters_row"],
        colour="orange",
        customStyle=yellowCss
    )

    yellow_df = AgGrid(
        st.session_state["hint_yellow_letters_row"],
        editable=True,
        fit_columns_on_grid_load=True,
        theme="material",
        custom_css=yellowCss,
        height=75,
        # width=200,
        key="yellow",
        reload_data=True,
        update_mode='model_changed'
    )

    new_yellow_df = yellow_df['data']
    new_yellow_df = new_yellow_df.apply(lambda x: x.str.upper())

    greenCol5, greenCol6 = st.columns(2)
    greenCol5.write("Incorrect letters")
    # clearGrey = greenCol6.button("Reset", key="clearGrey")
    # if clearGrey:
    #     st.session_state["hint_grey_letters_df"] = gen_blank_df(colour="grey")
    #     st.experimental_rerun()

    greyCss = gen_generic_custom_css("grey")
    greyCss = add_solid_style(
        df=st.session_state["hint_grey_letters_df"],
        colour="grey",
        customStyle=greyCss
    )

    grey_df = AgGrid(
        st.session_state["hint_grey_letters_df"],
        editable=True,
        fit_columns_on_grid_load=True,
        theme="material",
        custom_css=greyCss,
        height=75,
        # width=200,
        key="grey",
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
        # print("update yellow")
        # print(st.session_state["hint_yellow_letters_row"])
        st.session_state["hint_yellow_letters_row"] = new_yellow_df
        st.experimental_rerun()
    if not st.session_state["hint_grey_letters_df"].equals(new_grey_df):
        # print(st.session_state["hint_grey_letters_df"])
        st.session_state["hint_grey_letters_df"] = new_grey_df
        st.experimental_rerun()

    # hintButton = st.button("Get hint")

    # if hintButton:
    mostLikely = generate_hint(
        greenLettersDF=st.session_state["hint_correct_letters_row"],
        yellowLettersDF=st.session_state["hint_yellow_letters_row"],
        greyLettersDF=st.session_state["hint_grey_letters_df"],
        wordListDF=wordList
    )

    mostLikelyDF = pd.DataFrame(
        mostLikely
    )

    if not mostLikelyDF.empty:

        mostLikelyDF.columns = [str(x) for x in mostLikelyDF.columns]

        st.session_state["green_letter_hint"] = mostLikelyDF
        st.write("Top 5 most likely letters for remaining spaces")
        most_likely_df = AgGrid(
            st.session_state["green_letter_hint"],
            editable=False,
            fit_columns_on_grid_load=True,
            theme="material",
            custom_css=greenCss,
            height=250,
            # width=200,
            key="hint_df",
            reload_data=True,
            update_mode='model_changed'
        )
    else:
        st.write("Sorry, no words found, check the inputs")