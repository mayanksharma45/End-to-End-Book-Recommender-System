import os
import sys
import pickle
import streamlit as st
import numpy as np
from pathlib import Path
from books_recommender.logger.log import logging
from books_recommender.config.configuration import AppConfiguration
from books_recommender.pipeline.training_pipeline import TrainingPipeline
from books_recommender.exception.exception_handler import AppException

BASE_DIR = Path(__file__).resolve().parent

ARTIFACTS_DIR = BASE_DIR / "artifacts"
TRAINED_MODEL_PATH = ARTIFACTS_DIR / "trained_model" / "model.pkl"
BOOK_PIVOT_PATH = ARTIFACTS_DIR / "serialized_objects" / "book_pivot.pkl"
FINAL_RATING_PATH = ARTIFACTS_DIR / "serialized_objects" / "final_rating.pkl"

TEMPLATES_DIR = BASE_DIR / "templates"
BOOK_NAMES_PATH = TEMPLATES_DIR / "book_names.pkl"



class Recommendation:
    def __init__(self,app_config = AppConfiguration()):
        try:
            self.recommendation_config= app_config.get_recommendation_config()
        except Exception as e:
            raise AppException(e, sys) from e


    def fetch_poster(self, suggestion):
        try:
            poster_url = []

            book_pivot = pickle.load(open(BOOK_PIVOT_PATH, "rb"))
            final_rating = pickle.load(open(FINAL_RATING_PATH, "rb"))

            # suggestion is now a list of indices
            for idx in suggestion:
                book_name = book_pivot.index[idx]
                row_index = final_rating[final_rating["title"] == book_name].index[0]
                poster_url.append(final_rating.loc[row_index, "image_url"])

            return poster_url

        except Exception as e:
            raise AppException(e, sys) from e


        


    def recommend_book(self, book_name):
        try:
            books_list = []

            model = pickle.load(open(TRAINED_MODEL_PATH, "rb"))
            book_pivot = pickle.load(open(BOOK_PIVOT_PATH, "rb"))

            book_id = np.where(book_pivot.index == book_name)[0][0]

            distance, suggestion = model.kneighbors(
                book_pivot.iloc[book_id, :].values.reshape(1, -1),
                n_neighbors=6
            )

            # 🔥 FIX: flatten suggestion array
            suggestion = suggestion[0]

            poster_url = self.fetch_poster([suggestion])

            for idx in suggestion:
                books_list.append(book_pivot.index[idx])

            return books_list, poster_url

        except Exception as e:
            raise AppException(e, sys) from e




    def train_engine(self):
        try:
            obj = TrainingPipeline()
            obj.start_training_pipeline()
            st.text("Training Completed!")
            logging.info(f"Recommended successfully!")
        except Exception as e:
            raise AppException(e, sys) from e

    
    def recommendations_engine(self,selected_book):
        try:
            recommended_books,poster_url = self.recommend_book(selected_book)
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.text(recommended_books[1])
                st.image(poster_url[1])
            with col2:
                st.text(recommended_books[2])
                st.image(poster_url[2])

            with col3:
                st.text(recommended_books[3])
                st.image(poster_url[3])
            with col4:
                st.text(recommended_books[4])
                st.image(poster_url[4])
            with col5:
                st.text(recommended_books[5])
                st.image(poster_url[5])
        except Exception as e:
            raise AppException(e, sys) from e



if __name__ == "__main__":
    st.header('End to End Books Recommender System')
    st.text("This is a collaborative filtering based recommendation system!")

    obj = Recommendation()

    #Training
    if st.button('Train Recommender System'):
        obj.train_engine()

    book_names = pickle.load(open(BOOK_NAMES_PATH, "rb"))
    selected_book = st.selectbox(
        "Type or select a book from the dropdown",
        book_names)
    
    #recommendation
    if st.button('Show Recommendation'):
        obj.recommendations_engine(selected_book)