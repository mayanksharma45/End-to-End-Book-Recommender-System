import sys
import pickle
import streamlit as st
import numpy as np
from pathlib import Path
from books_recommender.logger.log import logging
from books_recommender.pipeline.training_pipeline import TrainingPipeline

# ------------------------------------------------------------------
# PATH SETUP
# ------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

ARTIFACTS_DIR = BASE_DIR / "artifacts"
TRAINED_MODEL_PATH = ARTIFACTS_DIR / "trained_model" / "model.pkl"
BOOK_PIVOT_PATH = ARTIFACTS_DIR / "serialized_objects" / "book_pivot.pkl"
FINAL_RATING_PATH = ARTIFACTS_DIR / "serialized_objects" / "final_rating.pkl"

TEMPLATES_DIR = BASE_DIR / "templates"
BOOK_NAMES_PATH = TEMPLATES_DIR / "book_names.pkl"


# ------------------------------------------------------------------
# RECOMMENDATION CLASS
# ------------------------------------------------------------------
class Recommendation:

    def fetch_poster(self, neighbors):
        """Fetch poster URLs safely (NO pandas slicing)."""
        poster_url = []

        book_pivot = pickle.load(open(BOOK_PIVOT_PATH, "rb"))
        final_rating = pickle.load(open(FINAL_RATING_PATH, "rb"))

        for idx in neighbors:
            idx = int(idx)  # guarantee scalar

            book_name = book_pivot.index[idx]

            row = final_rating.loc[final_rating["title"] == book_name]

            if row.empty:
                poster_url.append(None)
            else:
                poster_url.append(row["image_url"].values[0])

        return poster_url

    def recommend_book(self, book_name):
        model = pickle.load(open(TRAINED_MODEL_PATH, "rb"))
        book_pivot = pickle.load(open(BOOK_PIVOT_PATH, "rb"))

        book_id = int(np.where(book_pivot.index == book_name)[0][0])

        _, neighbors = model.kneighbors(
            book_pivot.iloc[book_id].values.reshape(1, -1),
            n_neighbors=6
        )

        neighbors = [int(i) for i in neighbors.flatten()][1:]  # skip input book

        recommended_books = [book_pivot.index[i] for i in neighbors]

        poster_url = self.fetch_poster(neighbors)

        return recommended_books, poster_url


    def train_engine(self):
        obj = TrainingPipeline()
        obj.start_training_pipeline()
        st.success("Training Completed!")
        logging.info("Training completed successfully")

    def recommendations_engine(self, selected_book):
        recommended_books, poster_url = self.recommend_book(selected_book)

        cols = st.columns(5)
        for i in range(5):
            with cols[i]:
                st.text(recommended_books[i])
                if poster_url[i]:
                    st.image(poster_url[i])


# ------------------------------------------------------------------
# STREAMLIT UI
# ------------------------------------------------------------------
if __name__ == "__main__":
    st.header("📚 End-to-End Book Recommender System")
    st.write("Collaborative filtering based recommendation system")

    obj = Recommendation()

    if st.button("Train Recommender System"):
        obj.train_engine()

    book_names = pickle.load(open(BOOK_NAMES_PATH, "rb"))

    selected_book = st.selectbox(
        "Select a book",
        book_names
    )

    if st.button("Show Recommendation"):
        obj.recommendations_engine(selected_book)
