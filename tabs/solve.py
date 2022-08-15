import json
import re
from typing import Dict, List
import pandas as pd
from st_aggrid import AgGrid
import streamlit as st
from tabs.hint import generate_hint

def apply_solve_css(grid, wordCSSDF=None):

    customCss = {
        '.ag-header': {
            "display": "none"
        },
        '.ag-cell': {
            'text-align': "center !important",
            'border': 'solid 1px black !important'
        }
    }

    if grid == "words":
        # print("new colour df ")
        # print(wordCSSDF)
        # print(st.session_state["solve_cur_guess_colour"])
        for rowInd, row in wordCSSDF.iterrows():
            for colInd, val in enumerate(row.tolist()):
                if val == "GREEN":
                    print("GREEN")
                    customCss[f'.ag-row[row-id="{rowInd}"] .ag-cell[col-id="{colInd}"]'] = {
                        "background-color": "green !important",
                        "color": "white !important"
                    }
                if val == "GREY":
                    print("GREY")
                    customCss[f'.ag-row[row-id="{rowInd}"] .ag-cell[col-id="{colInd}"]'] = {
                        "background-color": "grey !important",
                        "color": "white !important"
                    }
                if val == "YELLOW":
                    print("YELLOW")
                    customCss[f'.ag-row[row-id="{rowInd}"] .ag-cell[col-id="{colInd}"]'] = {
                        "background-color": "orange !important",
                        "color": "white !important"
                    }
        st.session_state["wordCSS"] = customCss
    else:
        greenCols = set()

        for wordCSS in st.session_state["wordCSS"]:
            if ".ag-row" in wordCSS:
                if "green" in st.session_state["wordCSS"][wordCSS]["background-color"]:
                    colID = wordCSS.split(" ")[1]
                    customCss[colID] = {
                        "background-color": "green !important",
                        "color": "white !important"
                    }
                    greenCols.add(colID.split('"')[1])

        for greenCol in greenCols:
            st.session_state["solve_letter_df"].loc[
                :,
                str(greenCol)
            ] = ""


        # for rowInd, row in wordCSSDF.iterrows():
        #     for colInd, val in enumerate(row.tolist()):
        #         if val == "GREEN":
        #             customCss[f'.ag-cell[col-id="{colInd}"]'] = {
        #                 "background-color": "green !important",
        #                 "color": "white !important"
        #             }
        #             st.session_state["solve_letter_df"].loc[
        #                 :,
        #                 str(colInd)
        #             ] = ""

        st.session_state["letterCSS"] = customCss

    return customCss

def gen_blank_df_solve(dfName):
    return pd.DataFrame(
        {
            "0": [""] * 6,
            "1": [""] * 6,
            "2": [""] * 6,
            "3": [""] * 6,
            "4": [""] * 6,
        }
    )


def reset_solve():
    print("reset solve")
    st.session_state["intialisation_complete"] = True
    st.session_state["solve_game_ended"] = False
    st.session_state["solve_game_found"] = False
    st.session_state["solve_game_not_found"] = False
    st.session_state["solve_word_to_guess"] = ""
    st.session_state["solve_cur_guess_df"] = gen_blank_df_solve("guessGrid")
    st.session_state["solve_cur_guess_colour"] = gen_blank_df_solve("guessColour")
    st.session_state["solve_letter_df"] = gen_blank_df_solve("letterGrid")
    st.session_state["not_found"] = False
    st.session_state["not_selected"] = False
    st.session_state["wordbox"] = ""


# TODO: algorithm for next word to guess:

def generate_next_solve(
    greenLettersDict: Dict,
    yellowLettersDict: Dict,
    greyLettersList: List[str],
    wordListDF: pd.DataFrame
    ):
    wordListDF = wordListDF.copy()
    # firstly, wordle words rarely end in s
    wordListDF = wordListDF.loc[~wordListDF["word"].str.endswith("S"), :]

    mostLikely, leastLikely = [], []

    # first exclude all words containing letters that are invalid

    greyLetterList = greyLettersList
    
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
    missingLetterIndex = []

    for colInd in greenLettersDict:
        if greenLettersDict[colInd] == "":
            missingLetterIndex.append(colInd)
        else:
            expandedWordListDF = expandedWordListDF.loc[
                expandedWordListDF[colInd] == greenLettersDict[colInd],
                :
            ]

    yellowLetters = []
    yellowLetterList = []

    for colInd in yellowLettersDict:
        for colVal in yellowLettersDict[colInd]:
            yellowLetters.append([colInd, colVal])
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
                        "count": count,
                        "percRemainingWordsWithLetter": round((colCounts.head(maxlen)[ind] / colCounts.sum())* 100)
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


def next_word_guess(likelyWords, likelyLetters):

    expandedWord = likelyWords.apply(
        lambda x: list(x),
    )

    expandedWordListDF = pd.DataFrame(
        expandedWord.tolist()
    )

    # print(expandedWordListDF)

    # print(likelyLetters)

    # make the lookup a bit quicker

    for col in likelyLetters:
        likelyLetters[col] = {
            "colLetters": [x["letter"] for x in likelyLetters[col]],
            "colCounts": {x["letter"]: x for x in likelyLetters[col]}
        }
        

    # simple scoring - the number of words with each letter
    # is the score for each row

    def scoreRow(row):
        score = 0
        for ind, colVal in enumerate(row):
            try:
                score += likelyLetters[ind]["colCounts"][colVal]["count"]
            except KeyError:
                pass
        return score

    expandedWordListDF["score"] = expandedWordListDF.apply(
        lambda x: scoreRow(x),
        axis=1
    )

    mostLikelyWord = likelyWords.loc[
        expandedWordListDF["score"].argmax()
    ]

    return mostLikelyWord


def get_next_word(wordList, setWord=False, nextWordIndex=None):

    greenLetters = {x: "" for x in range(0, 5)}
    # order isn't important for grey letters
    greyLetters = set()
    yellowLetters = {x: [] for x in range(0, 5)}
    allYellowLetters = []

    for x in yellowLetters:
        allYellowLetters.extend(yellowLetters[x])

    # do the scoring

    def scoreCol(colInd, colLetter, wordLetter):
        # can skip this one

        if colLetter == wordLetter:
            greenLetters[colInd] = wordLetter
            # we don't want to run the yellow step, so
            # continue otherwise all green letters are
            # yellow letters too.
        # grey letters aren't in the word
        if colLetter not in st.session_state["solve_word_to_guess"]:
            greyLetters.add(colLetter)
        # yellow letters - there may be more than one of
        # the same letter in a word- like L in STALL
        if colLetter in st.session_state["solve_word_to_guess"]:
            # we don't want to add to the yellow letters list
            # if the number of yellow letters would
            # be more than the number of that letter in the 
            # word
            # yellowLetterSum =  sum([yellowLetters[x].count(colLetter) for x in yellowLetters])
            # wordLetterCount = st.session_state["solve_word_to_guess"].count(wordLetter)

            yellowLetters[colInd].append(colLetter)


    for colInd, letter in enumerate(list(st.session_state["solve_word_to_guess"])):
        st.session_state["solve_cur_guess_df"].loc[
            :,
            str(colInd)
        ].apply(
            lambda x: scoreCol(colInd, x, letter)
        )
    
    # print(st.session_state["solve_cur_guess_colour"])

    def colourCol(colInd, colLetter, wordLetter):
        # can skip this one
        # print("*"*5)
        if colLetter == "":
            # print("none")
            # print(colLetter)
            return ""

        if colLetter == wordLetter:
            # we don't want to run the yellow step, so
            # continue otherwise all green letters are
            # yellow letters too.
            return colLetter + "-GREEN"
        # grey letters aren't in the word
        if colLetter not in st.session_state["solve_word_to_guess"]:
            # print("no letter")
            # print(colLetter, st.session_state["solve_word_to_guess"])
            return colLetter + "-GREY"

        return colLetter + "-YELLOW"


    wordCssDF = gen_blank_df_solve("word")


    for colInd, letter in enumerate(list(st.session_state["solve_word_to_guess"])):

        wordCssDF.loc[
            :,
            str(colInd)
        ] = st.session_state["solve_cur_guess_df"].loc[
            :,
            str(colInd)
        ].apply(
            lambda x: colourCol(colInd, x, letter),
        )
    
    # coulour the yellow ones

    def colourYellow(row):
        rowLetterCount = {}
        for colInd, colVal in enumerate(row):
            rowLetterCount.setdefault(colVal, 0)
            if colVal in allYellowLetters:
                rowLetterCount[colVal] += 1
            
                if rowLetterCount[colVal] > st.session_state["solve_word_to_guess"].count(colVal):
                    row[colInd] = "GREY"
                else:
                    row[colInd] =  "YELLOW"
            else:
                if row[colInd] != "":
                    row[colInd] = row[colInd][2:]
        return row

    wordCssDF = wordCssDF.apply(
        lambda x: colourYellow(x),
        axis=1
    )

    mostLikely, mostLikelyWords, allLikelyLetters  = generate_next_solve(
        greenLettersDict=greenLetters,
        yellowLettersDict=yellowLetters,
        greyLettersList=list(greyLetters),
        wordListDF=wordList
    )

    nextWord = next_word_guess(
        likelyWords=mostLikelyWords,
        # mutability
        likelyLetters=dict(allLikelyLetters)
    )

    # wordCSS = apply_solve_css("words", wordCssDF)

    # print(json.dumps(wordCSS, indent=4))

    if setWord:

        st.session_state["solve_cur_guess_df"].loc[
            nextWordIndex,
            :
        ] = list(nextWord)

    wordCSS = apply_solve_css("words", wordCssDF)
    # st.session_state["wordCSS"] = dict(wordCSS)
    

    return nextWord, allLikelyLetters, wordCSS, wordCssDF#, wordCSS



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
        
        solveRow = st.button("Solve next row")

        if solveRow and not st.session_state["solve_game_ended"]:
            st.session_state["setNext"] = True

            nextWordIndex = st.session_state["solve_cur_guess_df"]["0"].tolist().index("")


            print("next word index ", nextWordIndex)

            curGuess, allLikelyLetters, curCSS, wordCSSDF = get_next_word(
                wordList,
                setWord=True,
                nextWordIndex=nextWordIndex
            )

            if curGuess == st.session_state["solve_word_to_guess"]:
                st.session_state["solve_game_ended"] = True
                st.session_state["solve_game_found"] = True
            
            
            
            if curGuess:
                st.write(f"Current word: {curGuess}")

            nextWord, _, _, _= get_next_word(
                wordList
            )

            st.write(f"Next word: {nextWord}")

            # print(wordCSS)

            print(st.session_state["wordCSS"])
            print(st.session_state["solve_cur_guess_df"])

            print("curCSS")
            print(curCSS)
            print("session state")
            print(st.session_state["wordCSS"])

            curCSS = st.session_state["wordCSS"]

            if curCSS != st.session_state["wordCSS"]:
                print("NO!")
                st.session_state["wordCSS"] = dict(curCSS)
                st.session_state["setNext"] = False
                st.experimental_rerun()
            
                    # get the max length of each col:
            maxLen = 0
            for col in allLikelyLetters:
                if maxLen < len(allLikelyLetters[col]):
                    maxLen = len(allLikelyLetters[col])
            
            for col in allLikelyLetters:
                if len(allLikelyLetters[col]) < maxLen:
                    allLikelyLetters[col].extend([""] * (maxLen - len(allLikelyLetters[col])))

            for col in allLikelyLetters:
                allLikelyLetters[col] = [
                    f"{x['letter']} {x['percRemainingWordsWithLetter']}%" if x else ""
                    for x in allLikelyLetters[col]
                ]

            st.session_state["solve_letter_df"] = pd.DataFrame(
                allLikelyLetters
            )

            st.session_state["solve_letter_df"].columns = [str(x) for x in st.session_state["solve_letter_df"]]

            st.session_state["solve_letter_css"] = apply_solve_css(
                "letters"
            )

            st.experimental_rerun()


        
        # if curCSS != st.session_state["wordCSS"]:
        #     print("still NO!")

        # st.write(st.session_state["wordCSS"])

        # wordCSS = apply_solve_css("words", pd.DataFrame())

        if not st.session_state.get("wordCSS"):
            st.session_state["wordCSS"] = apply_solve_css("words", pd.DataFrame())

        solve_grid_status = AgGrid(
            st.session_state["solve_cur_guess_df"],
            # editable=False,
            fit_columns_on_grid_load=True,
            theme="material",
            custom_css=st.session_state["wordCSS"],
            height=300,
            width=200,
            reload_data=True,
            update_mode='model_changed',
            key="solve_grid_word"
        )

        # the word to choose next is the word which removes the
        # most letters from the most likely word.

        # therefore the word that has the highest number of letters
        # that are in the remaining words will exclude the most letters
        # each time.

        # create the green, yellow, grey letter df
        # needed by the generate_hint function

        st.write("Likely letter, (% times letter appears in remaining words):")

        likely_letters = AgGrid(
            st.session_state["solve_letter_df"],
            editable=False,
            fit_columns_on_grid_load=True,
            theme="material",
            custom_css=apply_solve_css("letters"),
            height=300,
            width=200,
            reload_data=True,
            update_mode='model_changed',
            key="letter_grid"
        )
        





